"""Stage 1 master runner — statistical interpretation fixes (v2 plan V2-1).

Executes, in order:
  1.1  base 10 grid fits + frozen-grid replication assertion; governance table
       `hypothesis_grid_results_v2.csv` (frozen v1 grid + classification cols).
  1.2  Romano-Wolf step-down (B=999, common row-level Rademacher draws) ->
       `hypothesis_grid_results_rw.csv`.
  1.3  MDE null classification -> `null_classification.csv`.
  1.4  DC13 placebo-OUTCOME (past |ret|) -> `placebo_outcome_test.csv`.
  1.5  expanded placebo battery (1000 full shuffles, 1000 within-symbol
       5-session block permutations, negative-control feature lead-5 and
       within-block shuffle) -> `placebo_distribution_expanded.csv`.

Pre-run gates (abort on failure, never silently continue):
  * engine validation CSV (contracts C1+C2) present and all PASS;
  * all 10 rebuilt base fits reproduce the frozen v1 grid (rel < 1e-8);
  * all base scale factors identical across tests (same df/design shape);
  * fast feature-permutation engine vs full PanelOLS refits (C3) rel < 1e-8;
  * first 200 score permutations reproduce the frozen v1 placebo shares
    H2 = 0.800, H3 = 0.640 exactly.

Checkpoints are written every 200 draws and deleted on success (plan V2-0).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np
import pandas as pd
from scipy import stats as sps

from nepsemsc.evaluation._panel_boot import BundleError, build_bundle
from nepsemsc.evaluation import feature_perm as fp
from nepsemsc.evaluation.mde import classify_null, null_table
from nepsemsc.evaluation.romano_wolf import bootstrap_family, stepdown
from nepsemsc.ml.panel_data import (build_oos_panel, standardize_test,
                                    train_fold_stats, Z_SOURCE_COLS)
from nepsemsc.ml.panel_regression import fit_driscoll_kraay
from nepsemsc.utils.io import atomic_write_df
from nepsemsc.utils.seeds_v2 import (V2_BLOCK_PERM_SEEDS,
                                     V2_NEGCTRL_SEEDS,
                                     V2_RW_SEEDS,
                                     V2_SCORE_PERM_SEEDS)
from run_panel_regressions import GRID, PLACEBO_ALPHA

TABLES = ROOT / "outputs/tables"
LOGS = ROOT / "outputs/logs"
TABLES.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

COLS = ["{f}_z", "log_volume_z", "market_ret_loo_z"]
REL_GATE = 1e-8


# --------------------------------------------------------------------------- #
def _tick(label: str, t0: float) -> None:
    print(f"  {label}: {time.time() - t0:.1f}s")


def load_panel(outcomes_override: pd.DataFrame | None = None,
               extra: tuple[str, ...] = ()):
    scores = pd.read_parquet(ROOT / "data/processed/anomaly_scores.parquet")
    outcomes = (pd.read_parquet(ROOT / "data/processed/daily_outcomes.parquet")
                if outcomes_override is None else outcomes_override)
    panel, train = build_oos_panel(scores, outcomes, extra_outcome_cols=extra)
    stats = train_fold_stats(train)
    panel = standardize_test(panel, stats)
    panel = panel.dropna(subset=["ret_fwd1"] + [c + "_z" for c in Z_SOURCE_COLS]
                         ).reset_index(drop=True)
    return panel, train, stats, scores, outcomes


def add_abs_ret_lag1(outcomes: pd.DataFrame) -> pd.DataFrame:
    """|ret| of the previous AVAILABLE (non-null) session within symbol.

    Matches the v1 forward-return adjacency convention: null-return sessions
    are skipped when building the lag, not imputed.
    """
    o = outcomes.copy()
    avail = (o.loc[o["ret"].notna(), ["symbol", "date", "ret"]]
             .sort_values(["symbol", "date"]))
    avail["abs_ret_lag1"] = (avail.groupby("symbol", observed=True)["ret"]
                             .shift(1).abs())
    out = o.merge(avail[["symbol", "date", "abs_ret_lag1"]],
                  on=["symbol", "date"], how="left")
    return out


def build_eod_lead5() -> pd.DataFrame:
    """end_of_day_concentration at t+5 (future value placed at t)."""
    f = pd.read_parquet(ROOT / "data/processed/daily_features.parquet")
    f = f.sort_values(["symbol", "date"]).copy()
    f["negctrl_eod_lead5"] = (f.groupby("symbol", observed=True)
                              ["end_of_day_concentration"].shift(-5))
    return f[["date", "symbol", "negctrl_eod_lead5"]]


def add_negctrl_feature(panel_sorted: pd.DataFrame, stats: dict) -> pd.DataFrame:
    """Merge lead-5 EoD and z-scale with the TRAIN-fold EoD constants (DC7)."""
    lead = build_eod_lead5()
    lead["date"] = pd.to_datetime(lead["date"]).dt.date
    p = panel_sorted.copy()
    p["date"] = pd.to_datetime(p["date"]).dt.date
    p = p.merge(lead, on=["date", "symbol"], how="left")
    p["negctrl_eod_lead5_z"] = np.nan
    for fold_id, st in stats.items():
        s = st["end_of_day_concentration"]
        m = p["fold_id"] == fold_id
        p.loc[m, "negctrl_eod_lead5_z"] = (
            (p.loc[m, "negctrl_eod_lead5"].clip(s["q1"], s["q99"]) - s["mu"])
            / s["sd"])
    return p


def validate_frozen_grid(bundles, frozen: pd.DataFrame) -> None:
    if list(frozen["test_id"]) != [b.test_id for b in bundles]:
        raise BundleError("test order mismatch vs frozen grid")
    for b in bundles:
        r = frozen.loc[frozen["test_id"] == b.test_id].iloc[0]
        if int(r["n_obs"]) != b.n_rows:
            raise BundleError(f"[{b.test_id}] n_obs {b.n_rows} != frozen {r['n_obs']}")
        for col, val in (("beta", b.beta[0]), ("se", b.se_obs[0]),
                         ("t", b.t_obs[0]), ("p_dk", b.p_obs[0])):
            ref = float(r[col])
            rel = abs(val - ref) / max(abs(ref), 1e-30)
            if rel > REL_GATE:
                raise BundleError(
                    f"[{b.test_id}] frozen {col} mismatch rel={rel:.2e} "
                    f"(got {val!r}, frozen {ref!r})")
        rel = abs(b.base_rel_err)
        if rel > REL_GATE:
            raise BundleError(f"[{b.test_id}] C1 base rel={rel:.2e}")
    scales = np.array([b.calib_c for b in bundles])
    if scales.max() - scales.min() > 1e-9:
        raise BundleError("base scale factors differ across grid tests")
    print(f"  frozen-grid replication: 10/10 PASS (max C1 rel "
          f"{max(b.base_rel_err for b in bundles):.2e}; scale "
          f"{scales[0]:.12f})")


def validate_c3(engine: fp.PermEngine, panel_sorted: pd.DataFrame,
                feature: str, outcomes: list[str], seeds: list[int]) -> float:
    """Fast feature-permutation fits vs FULL DK refits (3 draws x 2 outcomes)."""
    f = panel_sorted[feature].to_numpy(dtype=float)
    worst = 0.0
    for seed in seeds:
        fperm = fp.permute_full(f, seed)
        fast = fp.perm_fit(engine, fperm)
        base = panel_sorted.copy()
        base[feature] = fperm
        for j, outcome in enumerate(outcomes):
            res = fit_driscoll_kraay(base, outcome,
                                     [feature, "log_volume_z", "market_ret_loo_z"],
                                     bandwidth=5)
            for key, ref in (("beta", float(res.params[feature])),
                             ("se", float(res.std_errors[feature])),
                             ("t", float(res.tstats[feature]))):
                got = float(fast[key][j])
                worst = max(worst, abs(got - ref) / max(abs(ref), 1e-30))
    if worst > REL_GATE:
        raise BundleError(f"C3 feature-permutation engine rel={worst:.2e}")
    print(f"  C3 feature-permutation vs full refits: 3 draws x 2 outcomes, "
          f"max rel {worst:.2e}")
    return worst


def _perm_diag(betas: np.ndarray, pvals: np.ndarray) -> dict:
    """Descriptive calibration of one permutation distribution."""
    b = np.asarray(betas, dtype=float)
    p = np.asarray(pvals, dtype=float)
    n = len(b)
    mu = float(b.mean())
    sd = float(b.std(ddof=1)) if n > 1 else float("nan")
    t = mu / (sd / np.sqrt(n)) if sd and np.isfinite(sd) else float("nan")
    p_mean = float(2.0 * sps.t.sf(abs(t), n - 1)) if np.isfinite(t) else float("nan")
    calib = float((p < 0.05).mean())
    return {"perm_mean_beta": mu, "perm_sd_beta": sd,
            "perm_t_mean": float(t), "perm_p_mean": p_mean,
            "calib_share_p_lt_05": calib,
            "calib_n_p_lt_05": int((p < 0.05).sum())}


def _share_rows(construction: str, test_id: str, feature: str, outcome: str,
                sign: str, betas: np.ndarray, beta_obs: float, n_perm: int,
                seed_range: str, pvals: np.ndarray | None = None) -> list[dict]:
    sh = fp.shares(betas, beta_obs, sign)
    q = np.quantile(betas, [0.025, 0.05, 0.50, 0.95, 0.975])
    diag = (_perm_diag(betas, pvals) if pvals is not None
            else {k: np.nan for k in ("perm_mean_beta", "perm_sd_beta",
                                      "perm_t_mean", "perm_p_mean",
                                      "calib_share_p_lt_05", "calib_n_p_lt_05")})
    rows = []
    for share_type in ("upper", "lower", "two_sided"):
        share = sh[share_type]
        lo, hi = fp.wilson_ci(int(round(share * n_perm)), n_perm)
        row = {
            "construction": construction, "test_id": test_id,
            "feature": feature, "outcome": outcome, "predicted_sign": sign,
            "share_type": share_type, "n_perm": n_perm,
            "seed_range": seed_range, "share": share,
            "share_lo95": lo, "share_hi95": hi,
            "beta_obs": beta_obs, "beta_obs_bp": 1e4 * beta_obs,
            "q025_beta": q[0], "q05_beta": q[1], "q50_beta": q[2],
            "q95_beta": q[3], "q975_beta": q[4],
        }
        row.update(diag)
        rows.append(row)
    if pvals is not None:
        calib = float(np.mean(np.asarray(pvals) < 0.05))
        k = int(np.sum(np.asarray(pvals) < 0.05))
        lo, hi = fp.wilson_ci(k, len(pvals))
        row = {
            "construction": construction, "test_id": test_id,
            "feature": feature, "outcome": outcome, "predicted_sign": sign,
            "share_type": "calib_p_lt_05", "n_perm": n_perm,
            "seed_range": seed_range, "share": calib,
            "share_lo95": lo, "share_hi95": hi,
            "beta_obs": beta_obs, "beta_obs_bp": 1e4 * beta_obs,
            "q025_beta": q[0], "q05_beta": q[1], "q50_beta": q[2],
            "q95_beta": q[3], "q975_beta": q[4],
        }
        row.update(diag)
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
def main() -> None:
    t_all = time.time()
    print("=" * 78)
    print("STAGE 1 — statistical interpretation fixes (v2 plan V2-1)")
    print("=" * 78)

    val_path = TABLES / "v2_engine_validation.csv"
    if not val_path.exists():
        raise SystemExit("engine validation missing — run scripts/validate_v2_engine.py")
    val = pd.read_csv(val_path)
    if not bool(val["pass"].all()):
        raise SystemExit("engine validation FAILED — do not trust bootstrap results")
    print(f"engine validation: {len(val)} draws PASS "
          f"(max rel {val['max_rel'].max():.2e})")

    frozen = pd.read_csv(TABLES / "hypothesis_grid_results.csv")
    panel, train, stats, scores, outcomes = load_panel()
    panel_sorted = panel.sort_values(["symbol", "date"]).reset_index(drop=True)
    print(f"panel rows: {len(panel):,}")

    # ---------------- 1.1 base fits + frozen-grid replication ----------------
    print("\n[1.1] base grid fits + frozen replication")
    t0 = time.time()
    bundles = []
    for hid, feat, outcome, _sign in GRID:
        b, _res = build_bundle(panel_sorted, outcome,
                               [feat + "_z", "log_volume_z", "market_ret_loo_z"],
                               test_id=hid, feature=feat)
        bundles.append(b)
    validate_frozen_grid(bundles, frozen)
    _tick("base fits", t0)

    by_id = {b.test_id: b for b in bundles}
    grid_order = [g[0] for g in GRID]

    # ---------------- 1.2 Romano-Wolf step-down ----------------
    print("\n[1.2] Romano-Wolf step-down (B=999, common row-level Rademacher draws)")
    t0 = time.time()
    cp_rw = TABLES / "_checkpoint_rw_tboot.csv"
    rw = bootstrap_family(bundles, V2_RW_SEEDS, chunk_size=200,
                          checkpoint_path=cp_rw)
    print(f"  bootstrap done ({time.time() - t0:.1f}s); "
          f"draws={rw['B']} tests={len(bundles)}")
    sd = stepdown(rw["p_obs"], rw["p_boot"])
    rw_tab = frozen.copy()
    rw_tab["rw_p"] = sd["rw_p"].to_numpy()
    rw_tab["rw_p_literal_minp_fullset"] = sd["rw_p_literal_minp_fullset"].to_numpy()
    rw_tab["rw_order_ascending_p"] = sd["order_ascending_p"].to_numpy()
    rw_tab["rw_sig_q10"] = rw_tab["rw_p"] <= 0.10
    atomic_write_df(rw_tab, TABLES / "hypothesis_grid_results_rw.csv", index=False)
    if cp_rw.exists():
        cp_rw.unlink()
    print(rw_tab[["test_id", "bp", "p_dk", "rw_p",
                  "rw_p_literal_minp_fullset", "rw_sig_q10"]].to_string(index=False))
    _tick("RW total", t0)

    # ---------------- 1.1 governance classification ----------------
    print("\n[1.1] governance classification -> hypothesis_grid_results_v2.csv")
    fixed = {
        "H1": ("NULL_ROBUST", "bh_fail_loo_stable_null", "v1_result"),
        "H2": ("NULL_ROBUST", "bh_fail_placebo_null_loo_stable", "v1_result"),
        "H3": ("NULL_ROBUST", "bh_fail_placebo_null_loo_stable", "v1_result"),
        "H4": ("EXPLORATORY_POST_HOC", "opposite_sign_to_predeclaration",
               "v1_result"),
        "H5": ("NULL_ROBUST", "bh_fail_loo_stable_null", "v1_result"),
        "H8": ("NULL_FRAGILE", "two_registered_robustness_failures",
               "v2_robustness_rows"),
        "H9": ("NULL_ROBUST", "bh_fail_loo_stable_null", "v1_result"),
    }
    rw_lookup = dict(zip(rw_tab["test_id"], rw_tab["rw_p"]))
    cls_rows = []
    for hid in grid_order:
        if hid in fixed:
            cls, reason, source = fixed[hid]
        else:                                   # H6/H7/H10: RW adjudicates
            if rw_lookup[hid] > 0.10:
                cls = "NULL_FRAGILE"
                reason = "rw_p_gt_0.10"
                source = "v2_robustness_rows"
            else:
                cls = "CONFIRMED_HEADLINE"
                reason = ("bh_sig_q10_sign_ambiguous" if hid == "H6"
                          else "bh_sig_q10_sign_as_declared")
                source = "v1_result"
        cls_rows.append({"test_id": hid, "result_classification": cls,
                         "classification_reason": reason,
                         "classification_source": source})
    cls_df = pd.DataFrame(cls_rows)
    gov = frozen.merge(cls_df, on="test_id", how="left", validate="one_to_one")
    gov = gov.merge(rw_tab[["test_id", "rw_p"]], on="test_id", how="left",
                    validate="one_to_one")
    if gov[["result_classification", "classification_reason",
            "classification_source"]].isna().any().any():
        raise BundleError("classification merge lost a test")
    atomic_write_df(gov.drop(columns="rw_p"),
                    TABLES / "hypothesis_grid_results_v2.csv", index=False)
    print(gov[["test_id", "result_classification", "classification_reason",
               "rw_p"]].to_string(index=False))

    # ---------------- 1.3 MDE null classification ----------------
    print("\n[1.3] MDE null classification")
    mde_tab = null_table(frozen)
    cars = pd.read_csv(TABLES / "event_study_cars.csv")
    ev = cars["car"].to_numpy(dtype=float)
    ev_t = sps.ttest_1samp(ev, 0.0)
    ev_mean = float(np.mean(ev))
    ev_se = abs(ev_mean / float(ev_t.statistic))
    m, ratio, _ab, cls = classify_null(ev_mean, ev_se)
    ev_row = {
        "test_id": "EVENT_CAR_OVERALL", "outcome": "car[-5,+5]",
        "beta_bp": ev_mean * 1e4, "se_bp": ev_se * 1e4,
        "mde80_bp": m * 1e4, "abs_beta_over_half_mde": ratio,
        "classification": cls,
        "basis": (f"v1 event_study_cars.csv (frozen; n={len(ev)}; "
                  f"SE=|mean/t|, t={float(ev_t.statistic):.4f})"),
    }
    mde_tab = pd.concat([mde_tab, pd.DataFrame([ev_row])], ignore_index=True)
    mde_tab = mde_tab.rename(columns={"abs_beta_over_half_mde": "ratio"})
    mde_tab = mde_tab[["test_id", "outcome", "beta_bp", "se_bp", "mde80_bp",
                       "ratio", "classification", "basis"]]
    atomic_write_df(mde_tab, TABLES / "null_classification.csv", index=False)
    print(mde_tab[["test_id", "beta_bp", "mde80_bp", "ratio",
                   "classification"]].to_string(index=False))

    # ---------------- 1.4 DC13 placebo-outcome ----------------
    print("\n[1.4] DC13 placebo-OUTCOME (past |ret|)")
    t0 = time.time()
    outcomes_lag = add_abs_ret_lag1(outcomes)
    panel_lag, _train_lag, _stats_lag, _s, _o = load_panel(
        outcomes_override=outcomes_lag, extra=("abs_ret_lag1",))
    lag_rows = []
    for hid, feat, outcome, _sign in GRID:
        cols = [feat + "_z", "log_volume_z", "market_ret_loo_z"]
        sub = panel_lag.dropna(subset=cols + ["abs_ret_lag1"]).reset_index(drop=True)
        res = fit_driscoll_kraay(sub, "abs_ret_lag1", cols, bandwidth=5)
        b = float(res.params[feat + "_z"])
        p = float(res.pvalues[feat + "_z"])
        lag_rows.append({
            "test_id": hid, "feature": feat, "outcome": "abs_ret_lag1",
            "beta": b, "beta_bp": 1e4 * b,
            "se": float(res.std_errors[feat + "_z"]),
            "t_dk": float(res.tstats[feat + "_z"]), "p_dk": p,
            "n_obs": len(sub),
            "verdict": "PASS" if p > 0.05 else "SPECIFICATION_ERROR_FLAG",
        })
    lag_tab = pd.DataFrame(lag_rows)
    atomic_write_df(lag_tab, TABLES / "placebo_outcome_test.csv", index=False)
    print(lag_tab[["test_id", "beta_bp", "p_dk", "n_obs", "verdict"]]
          .to_string(index=False))
    _tick("DC13", t0)

    # ---------------- 1.5 expanded placebo battery ----------------
    print("\n[1.5] expanded placebo battery")
    f_anom = panel_sorted["anomaly_score_z"].to_numpy(dtype=float)
    f_anom_v1 = panel["anomaly_score_z"].to_numpy(dtype=float)
    sort_order = panel.sort_values(["symbol", "date"]).index.to_numpy(dtype=int)
    f_eod = panel_sorted["end_of_day_concentration_z"].to_numpy(dtype=float)
    symbols = panel_sorted["symbol"].astype(str).to_numpy()

    # (a) 1000 full-panel score permutations (H2/H3)
    print("  (a) 1000 score permutations (H2/H3)")
    t0 = time.time()
    b2 = by_id["H2"]
    eng2 = fp.make_perm_engine(panel_sorted, b2, ["abs_ret_fwd1", "ret_fwd1"])
    validate_c3(eng2, panel_sorted, "anomaly_score_z",
                ["abs_ret_fwd1", "ret_fwd1"], list(V2_SCORE_PERM_SEEDS[:3]))
    cp_score = TABLES / "_checkpoint_score_perm.csv"
    betas_s = np.empty((len(V2_SCORE_PERM_SEEDS), 2))
    p_s = np.empty((len(V2_SCORE_PERM_SEEDS), 2))
    for i, seed in enumerate(V2_SCORE_PERM_SEEDS):
        res_i = fp.perm_fit(eng2, fp.permute_full_v1(f_anom_v1, sort_order, seed))
        betas_s[i] = res_i["beta"]
        p_s[i] = res_i["p"]
        if (i + 1) % 200 == 0:
            pd.DataFrame(betas_s[:i + 1],
                         columns=["H2_abs", "H3_ret"]).to_csv(cp_score, index=False)
            print(f"    {i + 1}/{len(V2_SCORE_PERM_SEEDS)}"
                  f" ({time.time() - t0:.1f}s)")
    # v1 head-of-sequence replication gate
    obs2 = float(frozen.loc[frozen.test_id == "H2", "beta"].iloc[0])
    obs3 = float(frozen.loc[frozen.test_id == "H3", "beta"].iloc[0])
    v1_h2 = float(frozen.loc[frozen.test_id == "H2", "placebo_share"].iloc[0])
    v1_h3 = float(frozen.loc[frozen.test_id == "H3", "placebo_share"].iloc[0])
    head2 = float((betas_s[:200, 0] >= obs2).mean())
    head3 = float((betas_s[:200, 1] <= obs3).mean())
    print(f"    v1 head replication: H2 {head2:.3f} (frozen {v1_h2:.3f}) | "
          f"H3 {head3:.3f} (frozen {v1_h3:.3f})")
    if not (np.isclose(head2, v1_h2, atol=1e-12)
            and np.isclose(head3, v1_h3, atol=1e-12)):
        raise BundleError("first-200 score permutations do NOT reproduce v1 "
                          f"placebo shares ({head2}/{head3} vs {v1_h2}/{v1_h3})")
    _tick("score permutations", t0)

    # (b) 1000 within-symbol 5-session block permutations (H2/H3)
    print("  (b) 1000 within-symbol block permutations (H2/H3)")
    t0 = time.time()
    cp_block = TABLES / "_checkpoint_block_perm.csv"
    betas_b = np.empty((len(V2_BLOCK_PERM_SEEDS), 2))
    p_b = np.empty((len(V2_BLOCK_PERM_SEEDS), 2))
    for i, seed in enumerate(V2_BLOCK_PERM_SEEDS):
        res_i = fp.perm_fit(
            eng2, fp.permute_blocks(f_anom, symbols, seed, block=5))
        betas_b[i] = res_i["beta"]
        p_b[i] = res_i["p"]
        if (i + 1) % 200 == 0:
            pd.DataFrame(betas_b[:i + 1],
                         columns=["H2_abs", "H3_ret"]).to_csv(cp_block, index=False)
            print(f"    {i + 1}/{len(V2_BLOCK_PERM_SEEDS)}"
                  f" ({time.time() - t0:.1f}s)")
    _tick("block permutations", t0)

    # (c) negative-control feature
    print("  (c) negative-control feature (EoD lead-5 + within-block shuffle)")
    t0 = time.time()
    panel_nc = add_negctrl_feature(panel_sorted, stats)
    nc_cols = ["negctrl_eod_lead5_z", "log_volume_z", "market_ret_loo_z"]
    nc_rows = []
    for outcome in ("abs_ret_fwd1", "ret_fwd1"):
        sub = panel_nc.dropna(subset=nc_cols + [outcome]).reset_index(drop=True)
        res = fit_driscoll_kraay(sub, outcome, nc_cols, bandwidth=5)
        b = float(res.params["negctrl_eod_lead5_z"])
        p = float(res.pvalues["negctrl_eod_lead5_z"])
        test_id = "NEGCTRL_LEAD5_ABS" if outcome == "abs_ret_fwd1" \
            else "NEGCTRL_LEAD5_RET"
        nc_rows.append({
            "construction": "negctrl_eod_lead5", "test_id": test_id,
            "feature": "negctrl_eod_lead5", "outcome": outcome,
            "predicted_sign": "pos" if outcome == "abs_ret_fwd1" else "neg",
            "share_type": "dk_p", "n_perm": 1,
            "seed_range": "none", "share": p,
            "share_lo95": np.nan, "share_hi95": np.nan,
            "beta_obs": b, "beta_obs_bp": 1e4 * b,
            "t_dk": float(res.tstats["negctrl_eod_lead5_z"]),
            "n_obs": len(sub),
            "q025_beta": np.nan, "q05_beta": np.nan, "q50_beta": np.nan,
            "q95_beta": np.nan, "q975_beta": np.nan,
            "perm_mean_beta": np.nan, "perm_sd_beta": np.nan,
            "perm_t_mean": np.nan, "perm_p_mean": np.nan,
            "calib_share_p_lt_05": np.nan, "calib_n_p_lt_05": np.nan,
        })
        print(f"    {test_id}: beta={1e4 * b:+.2f} bp p={p:.4f} n={len(sub)}")

    # within-block shuffled EoD (H7/H8 designs)
    b7 = by_id["H7"]
    eng7 = fp.make_perm_engine(panel_sorted, b7, ["abs_ret_fwd1", "ret_fwd1"])
    validate_c3(eng7, panel_sorted, "end_of_day_concentration_z",
                ["abs_ret_fwd1", "ret_fwd1"], list(V2_NEGCTRL_SEEDS[:3]))
    cp_nc = TABLES / "_checkpoint_negctrl_shuffle.csv"
    nc_seeds = list(V2_NEGCTRL_SEEDS[:1000])
    betas_nc = np.empty((len(nc_seeds), 2))
    p_nc = np.empty((len(nc_seeds), 2))
    for i, seed in enumerate(nc_seeds):
        res_i = fp.perm_fit(
            eng7, fp.permute_blocks(f_eod, symbols, seed, block=5))
        betas_nc[i] = res_i["beta"]
        p_nc[i] = res_i["p"]
        if (i + 1) % 200 == 0:
            pd.DataFrame(betas_nc[:i + 1],
                         columns=["H7_abs", "H8_ret"]).to_csv(cp_nc, index=False)
            print(f"    negctrl shuffle {i + 1}/{len(nc_seeds)}"
                  f" ({time.time() - t0:.1f}s)")
    obs7 = float(frozen.loc[frozen.test_id == "H7", "beta"].iloc[0])
    obs8 = float(frozen.loc[frozen.test_id == "H8", "beta"].iloc[0])
    nc_rows += _share_rows("negctrl_eod_blockshuffle", "H7", "end_of_day_concentration",
                           "abs_ret_fwd1", "pos", betas_nc[:, 0], obs7,
                           len(nc_seeds), "829001-829999", pvals=p_nc[:, 0])
    nc_rows += _share_rows("negctrl_eod_blockshuffle", "H8", "end_of_day_concentration",
                           "ret_fwd1", "neg", betas_nc[:, 1], obs8,
                           len(nc_seeds), "829001-829999", pvals=p_nc[:, 1])
    _tick("negative-control block", t0)

    # assemble expanded placebo table
    rows = []
    rows += _share_rows("score_perm", "H2", "anomaly_score", "abs_ret_fwd1",
                        "pos", betas_s[:, 0], obs2, len(V2_SCORE_PERM_SEEDS),
                        "826001-826999", pvals=p_s[:, 0])
    rows += _share_rows("score_perm", "H3", "anomaly_score", "ret_fwd1",
                        "neg", betas_s[:, 1], obs3, len(V2_SCORE_PERM_SEEDS),
                        "826001-826999", pvals=p_s[:, 1])
    rows += _share_rows("block_perm", "H2", "anomaly_score", "abs_ret_fwd1",
                        "pos", betas_b[:, 0], obs2, len(V2_BLOCK_PERM_SEEDS),
                        "828001-828999", pvals=p_b[:, 0])
    rows += _share_rows("block_perm", "H3", "anomaly_score", "ret_fwd1",
                        "neg", betas_b[:, 1], obs3, len(V2_BLOCK_PERM_SEEDS),
                        "828001-828999", pvals=p_b[:, 1])
    placebo = pd.DataFrame(rows + nc_rows)
    for c in ("t_dk", "n_obs"):
        if c not in placebo.columns:
            placebo[c] = np.nan
    placebo = placebo[["construction", "test_id", "feature", "outcome",
                       "predicted_sign", "share_type", "n_perm", "seed_range",
                       "share", "share_lo95", "share_hi95", "beta_obs",
                       "beta_obs_bp", "t_dk", "n_obs", "q025_beta", "q05_beta",
                       "q50_beta", "q95_beta", "q975_beta",
                       "perm_mean_beta", "perm_sd_beta", "perm_t_mean",
                       "perm_p_mean", "calib_share_p_lt_05", "calib_n_p_lt_05"]]
    atomic_write_df(placebo, TABLES / "placebo_distribution_expanded.csv", index=False)
    for cp in (cp_score, cp_block, cp_nc):
        if cp.exists():
            cp.unlink()
    print("\nexpanded placebo summary (share rows):")
    print(placebo.loc[placebo.share_type.isin(["upper", "lower", "two_sided",
                                               "calib_p_lt_05"])]
          [["construction", "test_id", "share_type", "share",
            "calib_share_p_lt_05"]].to_string(index=False))
    print("\nnegative-control lead-5:")
    print(placebo.loc[placebo.construction == "negctrl_eod_lead5",
                      ["test_id", "beta_obs_bp", "share", "n_obs"]]
          .to_string(index=False))

    print(f"\nSTAGE 1 COMPLETE in {time.time() - t_all:.1f}s")
    print("outputs: hypothesis_grid_results_v2.csv, "
          "hypothesis_grid_results_rw.csv, null_classification.csv, "
          "placebo_outcome_test.csv, placebo_distribution_expanded.csv")


if __name__ == "__main__":
    main()
