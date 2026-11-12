"""Stage 3 master runner — panel/outcome upgrades (v2 plan V2-3).

Sections, in order:
  3.0  gates: arch version, EGARCH recursion vs arch's conditional-variance
       path, quantile design shape, trade-size threshold sanity;
  3.1  EGARCH-standardized outcomes: fit per (fold, symbol) on TRAIN rows only,
       forward-filter z_{t+1} (and |z|), 10-test grid on the mapped outcome,
       alt outcome, base-on-same-rows comparison, and two sensitivity subsets
       (exclude degenerate fits / exclude non-converged fits);
  3.2  quantile panel: tau in {.10,.25,.50,.75,.90}, statsmodels QuantReg on
       the two-way symbol+date dummy design, Koenker robust covariance,
       checkpointed per (test, tau);
  3.3  trade-size heterogeneity: DuckDB single read-only session, TRAIN-fold
       per-symbol p10/p90 trade-size thresholds, small/medium/large buckets,
       per-bucket buyer HHI / top-3 / EoD concentration, H7/H8 re-runs at
       min-trades 5 (primary), 1 and 10 (sensitivity), success criterion;
  3.4  figures + report number dumps.

Pre-run gates (abort, never silently continue):
  * EGARCH manual recursion matches arch's train sigma path (max rel < 1e-8);
  * quantile design has 7,116 rows and 737 columns (the declared full design);
  * every trade-size (fold, symbol) has finite p10 < p90 and >0 train trades.
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import duckdb
import numpy as np
import pandas as pd

from nepsemsc.features.trade_size import (BUCKET_COLS, BUCKET_FEATURES, BUCKETS,
                                          MIN_BUCKET_TRADES, bucket_summary,
                                          build_trade_size_features,
                                          pivot_bucket_features,
                                          success_criterion, thresholds_table)
from nepsemsc.ml.panel_data import (build_oos_panel, standardize_test,
                                    train_fold_stats, Z_SOURCE_COLS)
from nepsemsc.ml.panel_regression import (fit_double_clustered_v2,
                                          fit_driscoll_kraay)
from nepsemsc.models.egarch_outcomes import (Z_NUMERIC_MAX, build_egarch_outcomes,
                                             fit_egarch, validate_recursion)
from nepsemsc.models.quantile_panel import (TAUS, build_quantile_design,
                                            run_quantile_grid, tail_summary)
from nepsemsc.utils.io import atomic_write_df
from run_panel_regressions import GRID

TABLES = ROOT / "outputs/tables"
FIGURES = ROOT / "outputs/figures"
LOGS = ROOT / "outputs/logs"
for d in (TABLES, FIGURES, LOGS):
    d.mkdir(parents=True, exist_ok=True)

DB = ROOT / "data/duckdb/nepse.duckdb"
SCORES = ROOT / "data/processed/anomaly_scores.parquet"
OUTCOMES = ROOT / "data/processed/daily_outcomes.parquet"
FROZEN = TABLES / "hypothesis_grid_results.csv"
CONTROLS = ["log_volume_z", "market_ret_loo_z"]
ALPHA = 0.10
REL_GATE = 1e-8


def _tick(label: str, t0: float) -> None:
    print(f"  {label}: {time.time() - t0:.1f}s", flush=True)


def _fit_row(panel: pd.DataFrame, hid: str, feature: str, outcome: str,
             spec: str, subset: str, base_bp: float,
             outcome_v1: str, outcome_egarch: str,
             base_sd_units: float = np.nan,
             with_dc: bool = True) -> dict:
    cols = [feature + "_z", *CONTROLS]
    res = fit_driscoll_kraay(panel, outcome, cols, bandwidth=5)
    b = float(res.params[feature + "_z"])
    se = float(res.std_errors[feature + "_z"])
    p = float(res.pvalues[feature + "_z"])
    sd_out = float(pd.to_numeric(panel[outcome], errors="coerce").std(ddof=0))
    p_dc = np.nan
    if with_dc:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dc = fit_double_clustered_v2(panel, outcome, cols)
            p_dc = float(dc.pvalues[feature + "_z"])
        except Exception:  # noqa: BLE001 — counted as NaN, never silent
            p_dc = np.nan
    sign_match = bool(np.sign(b) == np.sign(base_bp)) if base_bp != 0 else False
    return {
        "test_id": hid, "feature": feature,
        "outcome_v1": outcome_v1, "outcome_egarch": outcome_egarch,
        "spec": spec, "subset": subset,
        "beta_bp": 1e4 * b, "se_bp": 1e4 * se,
        "ci_lo_bp": 1e4 * (b - 1.959963984540054 * se),
        "ci_hi_bp": 1e4 * (b + 1.959963984540054 * se),
        "p_dk": p, "p_dc_v2": p_dc, "n_obs": int(res.nobs),
        "outcome_sd": sd_out,
        "beta_sd_units": (b / sd_out) if sd_out and np.isfinite(sd_out) else np.nan,
        "base_sd_units_v1": float(base_sd_units),
        "sd_units_ratio": ((b / sd_out) / base_sd_units
                           if sd_out and np.isfinite(sd_out)
                           and base_sd_units not in (0.0, np.nan) else np.nan),
        "base_bp_v1": float(base_bp),
        "sign_match_base": sign_match,
        "survives_egarch": (bool(sign_match and p < ALPHA)
                            if spec == "egarch_primary" else np.nan),
    }


def _egarch_outcome_for(outcome_v1: str) -> str:
    return "abs_z_fwd1" if outcome_v1.startswith("abs_") else "z_fwd1"


def _alt_egarch_outcome_for(outcome_v1: str) -> str:
    return "z_fwd1" if outcome_v1.startswith("abs_") else "abs_z_fwd1"


def main() -> None:
    t0_all = time.time()
    frozen = pd.read_csv(FROZEN).set_index("test_id")
    base_bp = frozen["bp"].to_dict()

    scores = pd.read_parquet(SCORES)
    outcomes = pd.read_parquet(OUTCOMES)
    panel, train = build_oos_panel(scores, outcomes)
    train_stats = train_fold_stats(train)
    panel = standardize_test(panel, train_stats)
    zcols = [c + "_z" for c in Z_SOURCE_COLS]
    panel = panel.dropna(subset=zcols).reset_index(drop=True)
    base_sd_units = {}
    for _hid, _feat, _out, _sgn in GRID:
        _sd = float(pd.to_numeric(panel[_out], errors="coerce").std(ddof=0))
        base_sd_units[_hid] = (base_bp[_hid] / 1e4) / _sd
    print(f"base panel: {len(panel):,} rows, {panel.date.nunique()} dates",
          flush=True)

    # ------------------------------------------------------------------ 3.0
    print("\n[3.0] gates", flush=True)
    import arch
    print(f"  arch version: {arch.__version__}", flush=True)
    # recursion gate on one real fit (and the module's own validator)
    s0 = scores.copy()
    o0 = outcomes.copy()
    s0["date"] = pd.to_datetime(s0["date"]).dt.date
    o0["date"] = pd.to_datetime(o0["date"]).dt.date
    tr0 = s0[(s0.fold_id == 0) & s0.is_train & (s0.symbol == "NABIL")]["date"]
    r0 = o0[(o0.symbol == "NABIL") & (o0.date.isin(set(tr0)))]["ret"].dropna().to_numpy()
    res0, par0 = fit_egarch(r0)
    rec0 = validate_recursion(res0, par0, r0)
    print(f"  EGARCH recursion max rel: {rec0:.3e}", flush=True)
    if rec0 > REL_GATE:
        raise SystemExit("EGARCH recursion gate failed")

    # ------------------------------------------------------------------ 3.1
    print("\n[3.1] EGARCH-standardized outcomes", flush=True)
    t0 = time.time()
    z_out, fit_log = build_egarch_outcomes(scores, outcomes)
    _tick("fit 40 EGARCH models + forward filter", t0)
    atomic_write_df(fit_log, TABLES / "egarch_fit_log.csv")
    print(f"  fits: {len(fit_log)}, converged={int(fit_log.converged.sum())}, "
          f"degenerate={int(fit_log.flag_degenerate.sum())}, "
          f"z rows={len(z_out):,}", flush=True)
    print(fit_log.groupby("status").size().to_string(), flush=True)

    # accounting
    merged = panel.merge(z_out, on=["date", "symbol", "fold_id"], how="left",
                         indicator=True)
    n_both = int((merged["_merge"] == "both").sum())
    n_missing = int((merged["_merge"] == "left_only").sum())
    accounting = pd.DataFrame([
        {"item": "base_panel_rows", "value": len(panel)},
        {"item": "egarch_z_rows", "value": len(z_out)},
        {"item": "panel_rows_with_z", "value": n_both},
        {"item": "panel_rows_without_z", "value": n_missing},
        {"item": "fits", "value": len(fit_log)},
        {"item": "fits_converged", "value": int(fit_log.converged.sum())},
        {"item": "fits_degenerate", "value": int(fit_log.flag_degenerate.sum())},
        {"item": "fits_with_sigma_underflow",
         "value": int((fit_log.n_forward_sigma_invalid > 0).sum())},
        {"item": "fits_with_boundary_exclusion_only",
         "value": int(((fit_log.n_oos_excluded > 0) &
                       (fit_log.n_forward_sigma_invalid == 0)).sum())},
        {"item": "oos_rows_excluded_total",
         "value": int(fit_log.n_oos_excluded.sum())},
        {"item": "oos_rows_excluded_sigma_underflow",
         "value": int(fit_log.loc[fit_log.n_forward_sigma_invalid > 0,
                                  "n_oos_excluded"].sum())},
        {"item": "oos_rows_excluded_no_next_session",
         "value": int(fit_log.loc[fit_log.n_forward_sigma_invalid == 0,
                                  "n_oos_excluded"].sum())},
        {"item": "z_numeric_max", "value": Z_NUMERIC_MAX},
    ])
    atomic_write_df(accounting, TABLES / "egarch_outcome_accounting.csv")
    print(accounting.to_string(index=False), flush=True)

    rows = []
    subsets = {
        "full": merged,
        "excl_degenerate": merged.loc[
            ~merged.set_index(["fold_id", "symbol"]).index.isin(
                fit_log.loc[fit_log.flag_degenerate, ["fold_id", "symbol"]]
                .apply(tuple, axis=1))],
        "excl_nonconverged": merged.loc[
            ~merged.set_index(["fold_id", "symbol"]).index.isin(
                fit_log.loc[~fit_log.converged, ["fold_id", "symbol"]]
                .apply(tuple, axis=1))],
    }
    for subset, sub in subsets.items():
        sub = sub.dropna(subset=["z_fwd1", "abs_z_fwd1"]).reset_index(drop=True)
        for hid, feature, outcome_v1, _sign in GRID:
            oe = _egarch_outcome_for(outcome_v1)
            oa = _alt_egarch_outcome_for(outcome_v1)
            spec = ("egarch_primary" if subset == "full" else
                    f"egarch_primary_{subset}")
            rows.append(_fit_row(sub, hid, feature, oe, spec, subset,
                                 base_bp[hid], outcome_v1, oe,
                                 base_sd_units[hid]))
            if subset == "full":
                rows.append(_fit_row(sub, hid, feature, oa,
                                     "egarch_alt_outcome", subset,
                                     base_bp[hid], outcome_v1, oa,
                                     base_sd_units[hid]))
                rows.append(_fit_row(sub, hid, feature, outcome_v1,
                                     "base_on_egarch_rows", subset,
                                     base_bp[hid], outcome_v1, outcome_v1,
                                     base_sd_units[hid]))
    eg = pd.DataFrame(rows)
    eg.to_csv(TABLES / "headline_with_egarch_outcome.csv", index=False)
    print("\nEGARCH primary:")
    print(eg[eg.spec == "egarch_primary"][
        ["test_id", "feature", "outcome_egarch", "base_bp_v1", "beta_bp",
         "p_dk", "p_dc_v2", "n_obs", "sign_match_base",
         "survives_egarch"]].round(4).to_string(index=False), flush=True)
    print("\nEGARCH sensitivity (primary outcome):")
    print(eg[eg.spec.str.startswith("egarch_primary")][
        ["test_id", "spec", "beta_bp", "p_dk", "n_obs", "survives_egarch"]]
        .pivot(index="test_id", columns="spec", values=["beta_bp", "p_dk"])
        .round(3).to_string(), flush=True)

    # ------------------------------------------------------------------ 3.2
    print("\n[3.2] quantile panel (10 tests x 5 taus, checkpointed)", flush=True)
    t0 = time.time()
    Xcheck = build_quantile_design(panel, "reciprocity_z")
    print(f"  design: {Xcheck.shape[0]} rows x {Xcheck.shape[1]} cols",
          flush=True)
    if Xcheck.shape != (len(panel), 737):
        raise SystemExit("quantile design shape gate failed")
    ckpt = TABLES / "_quantile_checkpoint.csv"
    q = run_quantile_grid(panel, GRID, ckpt, taus=TAUS)
    q = q.sort_values(["test_id", "tau"]).reset_index(drop=True)
    atomic_write_df(q, TABLES / "quantile_regression.csv")
    tail = tail_summary(q, base_bp)
    atomic_write_df(tail, TABLES / "quantile_tail_summary.csv")
    if ckpt.exists():
        ckpt.unlink()
    _tick("50 quantile fits", t0)
    print("\nquantile tail summary:")
    print(tail[["test_id", "median_bp", "bp_tau10", "bp_tau90",
                "ci_lo_tau10", "ci_hi_tau90", "tail_classification"]]
          .round(3).to_string(index=False), flush=True)

    # quantile figures
    fig, axes = plt.subplots(5, 2, figsize=(12, 14), sharex=True)
    for ax, (hid, feature, outcome_v1, _sign) in zip(axes.ravel(), GRID):
        g = q[q.test_id == hid].sort_values("tau")
        ax.plot(g.tau, g.beta_bp, "o-", color="C0")
        ax.fill_between(g.tau, g.ci_lo_bp, g.ci_hi_bp, color="C0", alpha=0.20)
        ax.axhline(base_bp[hid], color="k", ls="--", lw=0.8,
                   label="v1 DK mean")
        ax.axhline(0.0, color="gray", lw=0.6)
        ax.set_title(f"{hid}: {feature} → {outcome_v1}", fontsize=9)
        ax.set_ylabel("β (bp)")
        ax.tick_params(labelsize=8)
    for ax in axes[-1]:
        ax.set_xlabel("τ")
    axes[0, 0].legend(fontsize=7)
    fig.suptitle("Stage-3 quantile panel: β(τ) with 95% Koenker-robust CI",
                 y=0.995)
    fig.tight_layout()
    fig.savefig(FIGURES / "quantile_all_tests.png", dpi=180)
    plt.close(fig)
    for hid in ("H10", "H7", "H4", "H6", "H8"):
        g = q[q.test_id == hid].sort_values("tau")
        feature, outcome_v1 = (GRID[[x[0] for x in GRID].index(hid)][1],
                               GRID[[x[0] for x in GRID].index(hid)][2])
        fig, ax = plt.subplots(figsize=(5.2, 3.6))
        ax.plot(g.tau, g.beta_bp, "o-", color="C0")
        ax.fill_between(g.tau, g.ci_lo_bp, g.ci_hi_bp, color="C0", alpha=0.20)
        ax.axhline(base_bp[hid], color="k", ls="--", lw=0.8, label="v1 DK mean")
        ax.axhline(0.0, color="gray", lw=0.6)
        ax.set_xlabel("τ"); ax.set_ylabel("β (bp)")
        ax.set_title(f"{hid}: {feature} → {outcome_v1}")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(FIGURES / f"quantile_{hid}.png", dpi=180)
        plt.close(fig)

    # ------------------------------------------------------------------ 3.3
    print("\n[3.3] trade-size heterogeneity", flush=True)
    t0 = time.time()
    symbols = sorted(panel.symbol.unique())
    con = duckdb.connect(str(DB), read_only=True)
    try:
        min_tables = {}
        for min_trades in (MIN_BUCKET_TRADES, 1, 10):
            feat = build_trade_size_features(con, scores, min_trades=min_trades)
            wide = pivot_bucket_features(feat)
            wide["date"] = pd.to_datetime(wide["date"]).dt.date
            rows_sc = scores[["date", "symbol", "fold_id", "is_train"]].copy()
            rows_sc["date"] = pd.to_datetime(rows_sc["date"]).dt.date
            merged_ts = rows_sc.merge(
                wide, on=["fold_id", "date", "symbol"], how="left")
            stats_ts = train_fold_stats(
                merged_ts.loc[merged_ts.is_train], cols=list(BUCKET_COLS))
            merged_ts = standardize_test(merged_ts, stats_ts)
            annual = merged_ts.loc[~merged_ts.is_train, [
                "fold_id", "date", "symbol",
                *[c + "_z" for c in BUCKET_COLS]]]
            p_ts = panel.merge(annual, on=["fold_id", "date", "symbol"],
                               how="left")
            min_tables[min_trades] = (feat, wide, p_ts)
        _tick("trade-size DuckDB aggregation + standardization", t0)
    finally:
        con.close()

    feat5, wide5, p5 = min_tables[MIN_BUCKET_TRADES]
    atomic_write_df(thresholds_table(feat5), TABLES / "trade_size_thresholds.csv")
    summ = []
    for min_trades, (feat, _wide, _p) in min_tables.items():
        s = bucket_summary(feat, min_trades=min_trades)
        s.insert(0, "min_bucket_trades", min_trades)
        summ.append(s)
    summ = pd.concat(summ, ignore_index=True)
    atomic_write_df(summ, TABLES / "trade_size_bucket_summary.csv")
    print("\nbucket summary (primary min=5):")
    print(summ[summ.min_bucket_trades == MIN_BUCKET_TRADES].round(4)
          .to_string(index=False), flush=True)

    ts_rows = []
    for min_trades, (feat, _wide, p_ts) in min_tables.items():
        for metric in BUCKET_FEATURES:
            for bucket in BUCKETS:
                col = f"{metric}_{bucket}_z"
                for hid, outcome in (("H7", "abs_ret_fwd1"),
                                     ("H8", "ret_fwd1")):
                    sub = p_ts.dropna(subset=[col]).reset_index(drop=True)
                    res = fit_driscoll_kraay(
                        sub, outcome, [col, *CONTROLS], bandwidth=5)
                    b = float(res.params[col])
                    se = float(res.std_errors[col])
                    p = float(res.pvalues[col])
                    try:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            dc = fit_double_clustered_v2(
                                sub, outcome, [col, *CONTROLS])
                        p_dc = float(dc.pvalues[col])
                    except Exception:  # noqa: BLE001
                        p_dc = np.nan
                    v1_bp = float(base_bp[hid])
                    ts_rows.append({
                        "metric": metric, "bucket": bucket,
                        "test_id": hid, "outcome": outcome,
                        "base_bp_v1": v1_bp,
                        "sign_match_base": bool(np.sign(b) == np.sign(v1_bp)),
                        "min_bucket_trades": int(min_trades),
                        "spec": ("primary" if min_trades == MIN_BUCKET_TRADES
                                 else f"sensitivity_min{min_trades}"),
                        "beta_bp": 1e4 * b, "se_bp": 1e4 * se,
                        "ci_lo_bp": 1e4 * (b - 1.959963984540054 * se),
                        "ci_hi_bp": 1e4 * (b + 1.959963984540054 * se),
                        "p_dk": p, "p_dc_v2": p_dc,
                        "n_obs": int(res.nobs),
                    })
    ts = pd.DataFrame(ts_rows)
    atomic_write_df(ts, TABLES / "trade_size_heterogeneity.csv")
    print("\ntrade-size H7/H8 (primary EoD):")
    print(ts[(ts.spec == "primary") &
             (ts.metric == "eod_concentration")][
        ["test_id", "bucket", "beta_bp", "se_bp", "p_dk", "p_dc_v2", "n_obs"]]
        .round(4).to_string(index=False), flush=True)

    # success criterion: large >= small in |beta| AND p (raw), plus sign-aware
    crit = success_criterion(ts, base_bp)
    atomic_write_df(crit, TABLES / "trade_size_success_criterion.csv")
    print("\nsuccess criterion (large vs small):")
    print(crit.round(4).to_string(index=False), flush=True)

    # trade-size figure: outcomes x metrics, bars by bucket
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), sharey=False)
    for i, hid in enumerate(("H7", "H8")):
        for j, metric in enumerate(BUCKET_FEATURES):
            ax = axes[i, j]
            d = ts[(ts.spec == "primary") & (ts.test_id == hid) &
                   (ts.metric == metric)].set_index("bucket").loc[list(BUCKETS)]
            ax.bar(BUCKETS, d.beta_bp, yerr=1.96 * d.se_bp, capsize=4,
                   color=["C2", "C0", "C1"])
            ax.axhline(0.0, color="gray", lw=0.6)
            ax.set_title(f"{hid} · {metric}", fontsize=9)
            ax.set_ylabel("β (bp)")
            ax.tick_params(labelsize=8)
    fig.suptitle("Stage-3 trade-size heterogeneity (primary min=5 trades/bucket)")
    fig.tight_layout()
    fig.savefig(FIGURES / "trade_size_heterogeneity.png", dpi=180)
    plt.close(fig)

    # EGARCH figure: z distribution + base-vs-egarch beta
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].hist(z_out.z_fwd1.clip(-8, 8), bins=80, density=True,
                 alpha=0.7, label="z")
    xs = np.linspace(-8, 8, 300)
    axes[0].plot(xs, np.exp(-0.5 * xs ** 2) / np.sqrt(2 * np.pi),
                 "k--", lw=1, label="N(0,1)")
    axes[0].set_title("EGARCH standardized forward returns")
    axes[0].set_xlabel("z"); axes[0].legend(fontsize=8)
    prim = eg[eg.spec == "egarch_primary"].set_index("test_id")
    y = np.arange(len(GRID))
    axes[1].barh(y - 0.2, [base_sd_units[h] for h, *_ in GRID], height=0.4,
                 label="v1 DK mean", color="C0")
    axes[1].barh(y + 0.2, [prim.loc[h, "beta_sd_units"] for h, *_ in GRID],
                 height=0.4, label="EGARCH outcome", color="C1")
    axes[1].set_yticks(y); axes[1].set_yticklabels([h for h, *_ in GRID])
    axes[1].axvline(0.0, color="gray", lw=0.6)
    axes[1].set_xlabel("standardized effect (outcome SD per 1 SD feature)")
    axes[1].legend(fontsize=8)
    axes[1].set_title("v1 vs EGARCH-standardized outcome")
    fig.tight_layout()
    fig.savefig(FIGURES / "egarch_outcomes.png", dpi=180)
    plt.close(fig)

    print(f"\nStage 3 total wall: {time.time() - t0_all:.1f}s", flush=True)


if __name__ == "__main__":
    main()
