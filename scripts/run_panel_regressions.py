"""EXP-0004b/0004c — HYPOTHESIS GRID (10 tests) + PLACEBO (R2) on OOS scores.

Design (pre-declared, plan §2/§3; fold structure EXP-0004a):
  * panel = OOS test-fold rows only (train scores are EDA-only, never pooled);
  * regressors: anomaly_score, buyer_hhi, self_loop_ratio, reciprocity,
    end_of_day_concentration + controls log(total_volume), market_ret_loo;
    2023-02-16 already excluded at scoring;
  * per test block (fold f): winsor 1/99 + z-scaling of regressors with
    TRAIN-fold constants of that fold's universe (DC7); outcomes raw;
    coefficients = return per 1-SD regressor move; bp = 1e4 × coef;
  * 10 grid tests (single-feature regressions + FE + controls), DK(bw=5)
    primary, double-cluster + Fama-MacBeth recorded (SV2 chain);
  * κ-purge pre-check (plan §3.2): if κ>30 on the FULLY standardized design,
    drop the max-VIF tested feature (metric declared 2026-11-09 deviation);
    VIF + IPS(approx) reports saved;
  * IPS approximation: mean per-entity ADF t-bar per regressor (declared;
    exact IPS quantiles not required for the grid);
  * MDE (DC6) = (1.96 + 0.84) × SE in bp for 80% power at α=0.05;
  * placebo (H2/H3 = anomaly rows only, 200 pre-declared seeds): anomaly_score
    permuted across the panel, model refit; significance = placebo share <=0.05
    in the PREDICTED DIRECTION (upper for positive-, lower for negative-pred)
    AND BH-adjusted p <= 0.10 across the 10-grid DK p-values.
Outputs: outputs/tables/hypothesis_grid_results.csv (+placebos, mde),
         outputs/tables/condition_vif_ips_report.csv, evidence log.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.outliers_influence import variance_inflation_factor as vif

from nepsemsc.ml.panel_regression import run_panel
from nepsemsc.ml.panel_data import (build_oos_panel, standardize_test,
                                    train_fold_stats, Z_SOURCE_COLS,
                                    TESTED_FEATURES)
from nepsemsc.ml.placebo import permuted_scores
from nepsemsc.utils.io import atomic_write_df
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.tz import utc_iso

GRID = [  # (id, feature, outcome, predicted_sign)
    ("H1", "self_loop_ratio", "abs_ret_fwd1", "pos"),
    ("H2", "anomaly_score", "abs_ret_fwd1", "pos"),
    ("H3", "anomaly_score", "ret_fwd1", "neg"),
    ("H4", "buyer_hhi", "ret_fwd1", "neg"),
    ("H5", "buyer_hhi", "abs_ret_fwd1", "pos"),
    ("H6", "reciprocity", "ret_fwd1", "amb"),
    ("H7", "end_of_day_concentration", "abs_ret_fwd1", "pos"),
    ("H8", "end_of_day_concentration", "ret_fwd1", "neg"),
    ("H9", "self_loop_ratio", "ret_fwd1", "neg"),
    ("H10", "reciprocity", "abs_ret_fwd1", "pos"),
]
BH_Q = 0.10
PLACEBO_ALPHA = 0.05
N_PERMUTATIONS = 200
MDE_Z = 1.96 + 0.84


def _benjamini_hochberg(pvals: list[float], q: float) -> list[float]:
    p = np.asarray(pvals, float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.clip(adj, 0.0, 1.0)
    return (out <= q).tolist(), out.tolist()


def main() -> None:
    t0 = time.time()
    warnings.filterwarnings(
        "ignore", category=FutureWarning, message="adfuller currently returns")
    scores = pd.read_parquet(ROOT / "data/processed/anomaly_scores.parquet")
    outcomes = pd.read_parquet(ROOT / "data/processed/daily_outcomes.parquet")

    # shared panel builder (nepsemsc.ml.panel_data): OOS rows only, DC7
    # fold-constant winsor/z for ALL regressors incl. the market control
    panel, train = build_oos_panel(scores, outcomes)
    train_stats = train_fold_stats(train)
    panel = standardize_test(panel, train_stats)
    print(f"regression panel rows: {len(panel):,}")

    # ---- design checks: κ on the FULLY standardized design ----
    # (deviation 2026-11-09: raw-scale market control inflated κ to a scale
    # artifact — 86.2; here κ measures collinearity only, purge per §3.2)
    zcols = [c + "_z" for c in Z_SOURCE_COLS]
    panel = panel.dropna(subset=zcols).reset_index(drop=True)
    mat = panel[zcols].to_numpy()
    kappa = float(np.linalg.cond(sm.add_constant(mat, has_constant="add")))
    vifs = {c: float(vif(sm.add_constant(panel[zcols], has_constant="add").to_numpy(), i + 1))
            for i, c in enumerate(zcols)}

    estimable = {c: True for c in TESTED_FEATURES}
    if kappa > 30.0:                      # plan §3.2 pre-purge
        vf = {c: vifs[c + "_z"] for c in TESTED_FEATURES}
        dropped = max(vf, key=lambda key: vf[key])
        estimable[dropped] = False
        print(f"PURGE (§3.2): κ={kappa:.1f} > 30 → drops {dropped} "
              f"(max VIF among tested = {vf[dropped]:.2f})")

    an_of = {c: float("nan") for c in zcols}
    for c in an_of:
        adfs = []
        for _, gser in panel.sort_values(["symbol", "date"]).groupby("symbol", observed=True):
            x = gser[c].dropna().to_numpy()
            if len(x) >= 60:
                adfs.append(adfuller(x, regression="ct", autolag="AIC")[0])
        an_of[c] = float(np.mean(adfs)) if adfs else float("nan")
    report = pd.DataFrame({
        "regressor": zcols,
        "vif": [vifs[c] for c in zcols],
        "ips_mean_adf_t": [an_of[c] for c in zcols]})
    report.attrs["kappa_std_design"] = kappa
    atomic_write_df(report, ROOT / "outputs/tables/condition_vif_ips_report.csv", index=False)
    print(f"κ(std design) = {kappa:.1f} | VIF max = "
          f"{report['vif'].max():.2f} ({report.loc[report['vif'].idxmax(), 'regressor']})")
    print("IPS mean ADF t-bar:", {k: round(v, 2) for k, v in an_of.items()})

    # ---- 10 grid tests ----
    rows, betas_used = [], {}
    for hid, feat, outcome, pred_sign in GRID:
        feat_z = feat + "_z"
        if not estimable.get(feat, True):
            row = {"test_id": hid, "feature": feat, "outcome": outcome,
                   "predicted_sign": pred_sign, "n_obs": len(panel),
                   "estimable": False}
            row.update({k: float("nan") for k in (
                "beta", "bp", "se", "t", "p_dk", "beta_dc", "p_dc",
                "beta_fm", "p_fm", "mde_bp_80pct", "rsq_within")})
            rows.append(row)
            print(f"{hid}: NOT ESTIMABLE under plan §3.2 pre-purge")
            continue
        res = run_panel(panel, outcome, [feat_z, "log_volume_z", "market_ret_loo_z"],
                        se="driscoll_kraay", bandwidth=5)
        b = float(res.params[feat_z]); se = float(res.std_errors[feat_z])
        p = float(res.pvalues[feat_z]); t = float(res.tstats[feat_z])
        bp = 1e4 * b
        mde_bp = 1e4 * MDE_Z * se
        res2 = run_panel(panel, outcome, [feat_z, "log_volume_z", "market_ret_loo_z"],
                         se="double_clustered")
        b2, p2 = float(res2.params[feat_z]), float(res2.pvalues[feat_z])
        res3 = run_panel(panel, outcome, [feat_z, "log_volume_z", "market_ret_loo_z"],
                         se="fama_macbeth", maxlag=5)
        b3, p3 = (res3["coef_stats"][feat_z]["beta"],
                  res3["coef_stats"][feat_z]["pvalue"])
        betas_used[hid] = b
        rows.append({
            "test_id": hid, "feature": feat, "outcome": outcome,
            "predicted_sign": pred_sign, "n_obs": len(panel),
            "estimable": True,
            "beta": b, "bp": bp, "se": se, "t": t, "p_dk": p,
            "beta_dc": b2, "p_dc": p2, "beta_fm": b3, "p_fm": p3,
            "mde_bp_80pct": mde_bp,
            "rsq_within": float(res.rsquared_within) if hasattr(res, "rsquared_within") else float("nan"),
        })
        print(f"{hid} {feat}→{outcome}: β={b:+.6f} ({bp:+.1f} bp/SD) t={t:+.2f} p={p:.4f} "
              f"mde={mde_bp:.1f}bp dc_p={p2:.4f} fm_p={p3:.4f}")

    grid = pd.DataFrame(rows)
    grid["bh_adj_p"] = _benjamini_hochberg(list(grid["p_dk"]), BH_Q)[1]
    grid["bh_sig_q10"] = grid["bh_adj_p"] <= BH_Q

    # ---- placebo (anomaly rows H2/H3) ----
    placebo_cols = []
    for hid, feat, outcome, sign in GRID:
        if hid not in ("H2", "H3"):
            placebo_cols.append(float("nan"))
            continue
        feat_z, cols = feat + "_z", [feat + "_z", "log_volume_z", "market_ret_loo_z"]
        base = panel[cols + [outcome, "symbol", "date"]].copy()
        arr = base[feat_z].to_numpy()
        shares, t_start = [], time.time()
        for k, perm in enumerate(permuted_scores(
                np.require(arr, dtype="float64"), N_PERMUTATIONS), start=1):
            base[feat_z] = perm
            r = run_panel(base.reset_index(drop=True), outcome, cols,
                          se="driscoll_kraay", bandwidth=5)
            shares.append(float(r.params[feat_z]))
            if k in (50, 150):
                print(f"  placebo {hid}: {k}/{N_PERMUTATIONS} ({time.time() - t_start:.0f}s)")
        pb = np.asarray(shares)
        obs = float(betas_used[hid])
        p_share = (float((pb >= obs).mean()) if sign == "pos"
                   else float((pb <= obs).mean()))
        placebo_cols.append(p_share)
        print(f"{hid} placebo share ({'upper' if sign == 'pos' else 'lower'}-sided): "
              f"{p_share:.3f} [REAL]")
    grid["placebo_share"] = placebo_cols
    grid["placebo_sig_a5"] = grid["placebo_share"] <= PLACEBO_ALPHA
    # conjunction (declared): placebo constraint applies ONLY to the
    # placebo-tested anomaly rows (H2/H3). A missing share means the rule
    # is NOT APPLICABLE to that test — never a failure. (Bug fix 2026-11-09,
    # before the numbers of record: fillna(1.0) wrongly counted 8 of 10
    # tests as failing an application that was never declared for them.)
    grid["headline_significant"] = (grid["placebo_share"].fillna(0.0)
                                    .le(PLACEBO_ALPHA) & grid["bh_sig_q10"])
    # sign agreement is REPORT-ONLY (not a gate): does the DK beta match the
    # plan §2 predicted sign? ambiguous = NA
    grid["sign_agrees"] = [
        float("nan") if s == "amb" else ((b > 0) == (s == "pos"))
        for b, s in zip(grid["beta"], grid["predicted_sign"])]
    atomic_write_df(grid, ROOT / "outputs/tables/hypothesis_grid_results.csv", index=False)

    prov.record({
        "ts_utc": utc_iso(),
        "artifact": "outputs/tables/hypothesis_grid_results.csv",
        "kind": "hypothesis_grid_exp0004b_placebo_exp0004c",
        "source_path": "anomaly_scores.parquet (EXP-0004a) + daily_outcomes.parquet",
        "source_url": "derived", "sha256": "", "bytes": 0,
        "rows_sampled": len(panel), "rows_total": len(panel),
        "licence": "derived",
        "evidence": f"n={len(panel)}; sig={int(grid['headline_significant'].sum())}/10; "
                    f"kappa_std={kappa:.1f}; placebo H2="
                    f"{float(grid.loc[grid.test_id == 'H2', 'placebo_share'].iloc[0]):.3f} "
                    f"H3={float(grid.loc[grid.test_id == 'H3', 'placebo_share'].iloc[0]):.3f}",
    })
    print("GRID_DONE", f"in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
