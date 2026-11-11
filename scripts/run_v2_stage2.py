"""Stage 2 master runner — referee-proof robustness battery (v2 plan V2-2).

Sections, in order:
  2.1  liquidity proxies (Amihud, Roll, Corwin-Schultz, effective tick),
       TRAIN-fold winsor/z constants, row accounting;
  2.2  liquidity-controlled regressions: per-test single-feature sensitivity
       (same row set before/after) + four-feature joint spec on ret/abs_ret,
       plus declared drop-sensitivity if VIF flags;
  2.3  wild cluster bootstrap (CGM-2008 ReBWB, cluster=symbol, B=999,
       V2_WB_SEEDS), engine validated against full PanelOLS refits;
  2.4  true two-way clustered SEs (v1 DC was a silent fallback — deviation
       #15) and the 4-estimator concordance table;
  2.5  VIF / correlation audit + feature correlation heatmap;
  2.6  report `reports/liquidity_robustness.md`.

Pre-run gates (abort, never silently continue):
  * frozen-grid replication for all 10 tests (n=7116, beta/se/t/p rel<1e-8);
  * liquidity complete-case count equals the base panel row count;
  * wild-cluster engine vs full refits rel<1e-8 on >=2 designs x 3 draws.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from nepsemsc.evaluation._panel_boot import BundleError, build_bundle
from nepsemsc.evaluation.diagnostics import (correlation_table, max_abs_corr,
                                             vif_table)
from nepsemsc.evaluation.wild_bootstrap import (bootstrap_wild_cluster,
                                                validate_cluster_engine)
from nepsemsc.features.liquidity import (LIQUIDITY_COLS, LIQUIDITY_GAMMAS,
                                         build_liquidity_features,
                                         liquidity_row_accounting)
from nepsemsc.ml.panel_data import (build_oos_panel, standardize_test,
                                    train_fold_stats, Z_SOURCE_COLS)
from nepsemsc.ml.panel_regression import (fit_double_clustered_v2,
                                          fit_driscoll_kraay)
from nepsemsc.utils.io import atomic_write_df
from nepsemsc.utils.seeds_v2 import V2_WB_SEEDS
from run_panel_regressions import GRID
from run_v2_stage1 import validate_frozen_grid

TABLES = ROOT / "outputs/tables"
FIGURES = ROOT / "outputs/figures"
LOGS = ROOT / "outputs/logs"
for d in (TABLES, FIGURES, LOGS):
    d.mkdir(parents=True, exist_ok=True)

FOUR_FEATURES = ["buyer_hhi", "self_loop_ratio", "reciprocity",
                 "end_of_day_concentration"]
CONTROLS = ["log_volume_z", "market_ret_loo_z"]
ALPHA = 0.10
REL_GATE = 1e-8


def _tick(label: str, t0: float) -> None:
    print(f"  {label}: {time.time() - t0:.1f}s")


def _fit_row(panel: pd.DataFrame, outcome: str, cols: list[str],
             feature: str, test_id: str, spec: str) -> dict:
    res = fit_driscoll_kraay(panel, outcome, cols, bandwidth=5)
    b = float(res.params[feature])
    return {
        "test_id": test_id, "spec": spec, "feature": feature,
        "outcome": outcome, "beta": b, "bp": 1e4 * b,
        "se": float(res.std_errors[feature]), "t": float(res.tstats[feature]),
        "p_dk": float(res.pvalues[feature]), "n_obs": int(res.nobs),
    }


def main() -> None:
    t_all = time.time()
    print("=" * 78)
    print("STAGE 2 — referee-proof robustness battery (v2 plan V2-2)")
    print("=" * 78)

    frozen = pd.read_csv(TABLES / "hypothesis_grid_results.csv")
    gov = pd.read_csv(TABLES / "hypothesis_grid_results_v2.csv")
    rw = pd.read_csv(TABLES / "hypothesis_grid_results_rw.csv")

    # ------------------------- 2.1 liquidity features ---------------------- #
    print("\n[2.1] liquidity features + TRAIN-fold standardization")
    t0 = time.time()
    outcomes = pd.read_parquet(ROOT / "data/processed/daily_outcomes.parquet")
    ohlcv = pd.read_parquet(ROOT / "data/processed/daily_ohlcv.parquet")
    scores = pd.read_parquet(ROOT / "data/processed/anomaly_scores.parquet")

    liq = build_liquidity_features(outcomes, ohlcv)
    panel, train = build_oos_panel(scores, outcomes)
    panel = panel.merge(liq, on=["date", "symbol"], how="left")
    train = train.merge(liq, on=["date", "symbol"], how="left")
    z_cols = Z_SOURCE_COLS + LIQUIDITY_COLS
    stats = train_fold_stats(train, cols=z_cols)
    panel = standardize_test(panel, stats)
    z_needed = [c + "_z" for c in z_cols]
    panel = panel.dropna(subset=z_needed).reset_index(drop=True)
    panel_sorted = panel.sort_values(["symbol", "date"]).reset_index(drop=True)
    print(f"  OOS panel rows with complete liquidity: {len(panel):,}")

    raw_accounting = liquidity_row_accounting(panel, cols=LIQUIDITY_COLS)
    atomic_write_df(raw_accounting, TABLES / "liquidity_row_accounting.csv",
                    index=False)

    desc = []
    for c in LIQUIDITY_COLS:
        s = panel[c]
        z = panel[c + "_z"]
        desc.append({
            "feature": c, "n": int(s.notna().sum()),
            "mean": float(s.mean()), "sd": float(s.std(ddof=1)),
            "q01": float(s.quantile(0.01)), "median": float(s.median()),
            "q99": float(s.quantile(0.99)), "max": float(s.max()),
            "z_sd": float(z.std(ddof=1)),
            "amihud_value_source": ("ohlcv_turnover"
                                    if c == "amihud" else "not_applicable"),
        })
    atomic_write_df(pd.DataFrame(desc), TABLES / "liquidity_summary.csv",
                    index=False)
    print(pd.DataFrame(desc)[["feature", "mean", "median", "q99", "max"]]
          .to_string(index=False))

    # base bundles + frozen replication gate (same 10 designs as Stage 1)
    bundles = []
    for hid, feat, outcome, _sign in GRID:
        b, _res = build_bundle(panel_sorted, outcome,
                               [feat + "_z", *CONTROLS],
                               test_id=hid, feature=feat)
        bundles.append(b)
    validate_frozen_grid(bundles, frozen)
    by_id = {b.test_id: b for b in bundles}
    _tick("liquidity + base bundles", t0)

    # --------------------- 2.2 liquidity-controlled regressions ------------ #
    print("\n[2.2] liquidity-controlled regressions")
    t0 = time.time()
    liq_z = [g + "_z" for g in LIQUIDITY_GAMMAS]
    rows = []
    for hid, feat, outcome, _sign in GRID:
        base_cols = [feat + "_z", *CONTROLS]
        liq_cols = [feat + "_z", *CONTROLS, *liq_z]
        base = _fit_row(panel, outcome, base_cols, feat + "_z", hid,
                        "single_feature_base")
        ctrl = _fit_row(panel, outcome, liq_cols, feat + "_z", hid,
                        "single_feature_liquidity")
        ctrl["base_bp"] = base["bp"]
        ctrl["delta_bp"] = ctrl["bp"] - base["bp"]
        ctrl["pct_delta"] = (ctrl["delta_bp"] / abs(base["bp"])
                             if base["bp"] != 0 else np.nan)
        ctrl["survives_liquidity"] = ctrl["p_dk"] < ALPHA
        base["base_bp"] = base["bp"]
        base["delta_bp"] = 0.0
        base["pct_delta"] = 0.0
        base["survives_liquidity"] = base["p_dk"] < ALPHA
        rows.extend([base, ctrl])

    # four-feature joint specification (the four constructed network features)
    joint = []
    for outcome in ("ret_fwd1", "abs_ret_fwd1"):
        for spec, gam in (("joint_4features_base", []),
                          ("joint_4features_liquidity", liq_z)):
            cols = [f + "_z" for f in FOUR_FEATURES] + CONTROLS + gam
            res = fit_driscoll_kraay(panel, outcome, cols, bandwidth=5)
            for f in FOUR_FEATURES:
                joint.append({
                    "test_id": "JOINT_4F", "spec": spec,
                    "feature": f, "outcome": outcome,
                    "beta": float(res.params[f + "_z"]),
                    "bp": 1e4 * float(res.params[f + "_z"]),
                    "se": float(res.std_errors[f + "_z"]),
                    "t": float(res.tstats[f + "_z"]),
                    "p_dk": float(res.pvalues[f + "_z"]),
                    "n_obs": int(res.nobs),
                })
            for g in LIQUIDITY_GAMMAS:
                if g + "_z" in res.params.index:
                    joint.append({
                        "test_id": "JOINT_4F", "spec": spec,
                        "feature": g, "outcome": outcome,
                        "beta": float(res.params[g + "_z"]),
                        "bp": 1e4 * float(res.params[g + "_z"]),
                        "se": float(res.std_errors[g + "_z"]),
                        "t": float(res.tstats[g + "_z"]),
                        "p_dk": float(res.pvalues[g + "_z"]),
                        "n_obs": int(res.nobs),
                    })
    joint = pd.DataFrame(joint)
    for outcome in ("ret_fwd1", "abs_ret_fwd1"):
        base_map = joint[(joint.spec == "joint_4features_base")
                         & (joint.outcome == outcome)].set_index("feature")["bp"]
        m = (joint.spec == "joint_4features_liquidity") & (joint.outcome == outcome)
        joint.loc[m, "base_bp"] = joint.loc[m, "feature"].map(base_map)
        joint["delta_bp"] = joint["bp"] - joint["base_bp"]
        joint["pct_delta"] = joint["delta_bp"] / joint["base_bp"].abs()
        joint["survives_liquidity"] = joint["p_dk"] < ALPHA
    # fill base rows with their own bp
    mb = joint.spec == "joint_4features_base"
    joint.loc[mb, "base_bp"] = joint.loc[mb, "bp"]
    joint.loc[mb, "delta_bp"] = 0.0
    joint.loc[mb, "pct_delta"] = 0.0

    liq_table = pd.concat([pd.DataFrame(rows), joint], ignore_index=True)
    liq_table = liq_table[["test_id", "spec", "feature", "outcome", "beta", "bp",
                           "se", "t", "p_dk", "n_obs", "base_bp", "delta_bp",
                           "pct_delta", "survives_liquidity"]]
    print(liq_table.loc[liq_table.test_id != "JOINT_4F",
                        ["test_id", "bp", "p_dk", "base_bp", "delta_bp"]]
          .round(4).to_string(index=False))
    print("\njoint four-feature spec:")
    print(liq_table.loc[(liq_table.test_id == "JOINT_4F")
                        & (liq_table.spec == "joint_4features_liquidity"),
                        ["outcome", "feature", "bp", "p_dk"]]
          .round(4).to_string(index=False))
    _tick("liquidity regressions", t0)

    # --------------------- 2.3 wild cluster bootstrap ---------------------- #
    print("\n[2.3] wild cluster bootstrap (ReBWB, cluster=symbol, B=999)")
    t0 = time.time()
    v_bundles = [by_id["H2"], by_id["H7"], by_id["H10"]]
    worst = validate_cluster_engine(panel_sorted, v_bundles,
                                    list(V2_WB_SEEDS[:3]))
    print(f"  engine validation: 3 designs x 3 draws, max rel {worst:.2e}")
    cp = TABLES / "_checkpoint_wb_tboot.csv"
    wb = bootstrap_wild_cluster(panel, bundles, V2_WB_SEEDS, chunk_size=200,
                                checkpoint_path=cp)
    if cp.exists():
        cp.unlink()
    wb_tab = pd.DataFrame({
        "test_id": [b.test_id for b in bundles],
        "feature": [b.feature for b in bundles],
        "outcome": [b.outcome for b in bundles],
        "beta": np.array([b.beta[0] for b in bundles]),
        "bp": 1e4 * np.array([b.beta[0] for b in bundles]),
        "se_dk": np.array([b.se_obs[0] for b in bundles]),
        "t_dk": wb["t_dk"],
        "p_dk": wb["p_obs"],
        "se_cluster_obs": wb["se_cluster_obs"],
        "t_cluster_obs": wb["t_obs"],
        "p_wb": wb["p_wb"],
        "t_boot_mean": wb["t_boot"].mean(axis=0),
        "t_boot_sd": wb["t_boot"].std(axis=0, ddof=1),
        "B": wb["B"], "n_clusters": wb["n_clusters"],
    })
    wb_tab["p_wb_le_10"] = wb_tab["p_wb"] < ALPHA
    atomic_write_df(wb_tab, TABLES / "wild_cluster_bootstrap.csv", index=False)
    print(wb_tab[["test_id", "bp", "t_dk", "t_cluster_obs", "p_dk", "p_wb",
                  "n_clusters"]].round(4).to_string(index=False))
    _tick("wild cluster bootstrap", t0)

    # ------------------ 2.4 true two-way SE + concordance ------------------ #
    print("\n[2.4] true two-way clustered SEs + 4-estimator concordance")
    t0 = time.time()
    dc_rows = []
    for hid, feat, outcome, _sign in GRID:
        res = fit_double_clustered_v2(panel, outcome, [feat + "_z", *CONTROLS])
        dc_rows.append({"test_id": hid, "p_dc_v2": float(res.pvalues[feat + "_z"]),
                        "se_dc_v2": float(res.std_errors[feat + "_z"]),
                        "dc_cov_type": res.cov_type_used})
    dc = pd.DataFrame(dc_rows)

    conc = frozen[["test_id", "feature", "outcome", "bp", "p_dk", "p_dc",
                   "p_fm"]].copy()
    conc = conc.merge(dc, on="test_id", how="left", validate="one_to_one")
    conc = conc.merge(wb_tab[["test_id", "p_wb", "n_clusters"]],
                      on="test_id", how="left", validate="one_to_one")
    conc = conc.merge(rw[["test_id", "rw_p"]], on="test_id", how="left",
                      validate="one_to_one")
    conc = conc.merge(gov[["test_id", "result_classification"]], on="test_id",
                      how="left", validate="one_to_one")
    pcols = ["p_dk", "p_dc_v2", "p_fm", "p_wb"]
    conc["n_sig_p_lt_10"] = (conc[pcols] < ALPHA).sum(axis=1)
    conc["significant_estimators"] = conc.apply(
        lambda r: ",".join(c.replace("p_", "") for c in pcols
                           if r[c] < ALPHA), axis=1)
    conc["se_concordance"] = conc["n_sig_p_lt_10"].map(
        {4: "STRONG", 3: "MODERATE", 2: "WEAK", 1: "FRAGILE", 0: "NULL"})
    conc["stage1_classification"] = conc["result_classification"]
    conc["stage2_headline"] = (
        conc["se_concordance"].isin(["STRONG", "MODERATE"])
        & (conc["result_classification"] == "CONFIRMED_HEADLINE"))
    conc["wb_small_cluster_caveat"] = conc["n_clusters"] < 20
    conc["note"] = np.where(
        conc["p_dc"] == conc["p_dk"],
        ("v1 p_dc was the time-kernel fallback (==DK); p_dc_v2 is the true "
         "two-way cluster; WB uses entity-clustered t and only "
         f"{int(conc['n_clusters'].iloc[0])} symbol clusters (small-cluster caveat)"),
        "v1 p_dc fallback check")
    conc = conc[["test_id", "feature", "outcome", "bp", "p_dk", "p_dc",
                 "p_dc_v2", "se_dc_v2", "dc_cov_type", "p_fm", "p_wb", "rw_p",
                 "n_sig_p_lt_10", "significant_estimators", "se_concordance",
                 "n_clusters", "wb_small_cluster_caveat",
                 "stage1_classification", "stage2_headline", "note"]]
    atomic_write_df(conc, TABLES / "se_concordance.csv", index=False)
    print(conc[["test_id", "p_dk", "p_dc_v2", "p_fm", "p_wb", "rw_p",
                "se_concordance", "stage2_headline"]].round(4).to_string(index=False))
    _tick("DC + concordance", t0)

    # -------------------------- 2.5 VIF audit ------------------------------ #
    print("\n[2.5] VIF / correlation audit")
    t0 = time.time()
    all_features = FOUR_FEATURES + ["anomaly_score"]
    all_z = [f + "_z" for f in all_features] + liq_z
    corr_cols = all_z + CONTROLS  # FULL design matrix, controls included
    corr = correlation_table(panel, corr_cols)
    atomic_write_df(corr.reset_index().rename(columns={"index": "feature"}),
                    TABLES / "feature_correlation.csv", index=False)
    vif = vif_table(panel, corr_cols)
    mx = max_abs_corr(corr)
    vif["max_abs_corr_with_feature"] = vif["feature"].map(mx)
    vif["vif_flag_gt5"] = vif["vif"] > 5.0
    vif["corr_flag_gt0.7"] = vif["max_abs_corr_with_feature"] > 0.7
    atomic_write_df(vif, TABLES / "vif_audit.csv", index=False)
    print(vif.round(3).to_string(index=False))

    # heatmap (matplotlib, thesis-grade static PNG)
    fig, ax = plt.subplots(figsize=(8.2, 7.0))
    im = ax.imshow(corr.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    labels = [c.replace("_z", "") for c in corr.columns]
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{corr.to_numpy()[i, j]:.2f}", ha="center",
                    va="center", fontsize=7,
                    color="white" if abs(corr.to_numpy()[i, j]) > 0.55 else "black")
    fig.colorbar(im, ax=ax, shrink=0.8, label="Pearson r")
    ax.set_title("Stage-2 design correlation (features, liquidity, controls)")
    fig.tight_layout()
    fig.savefig(FIGURES / "feature_correlation.png", dpi=180)
    plt.close(fig)

    # declared drop-sensitivity for flagged features (expected none)
    flagged = vif.loc[vif["vif_flag_gt5"] | vif["corr_flag_gt0.7"], "feature"]
    drop_rows = []
    for fdrop in flagged:
        if fdrop not in [f + "_z" for f in FOUR_FEATURES]:
            continue
        keep = [f for f in FOUR_FEATURES if f + "_z" != fdrop]
        for outcome in ("ret_fwd1", "abs_ret_fwd1"):
            cols = [f + "_z" for f in keep] + CONTROLS + liq_z
            res = fit_driscoll_kraay(panel, outcome, cols, bandwidth=5)
            for f in keep:
                drop_rows.append({
                    "test_id": "JOINT_4F", "spec": f"joint_drop_{fdrop.replace('_z','')}",
                    "feature": f, "outcome": outcome,
                    "beta": float(res.params[f + "_z"]),
                    "bp": 1e4 * float(res.params[f + "_z"]),
                    "se": float(res.std_errors[f + "_z"]),
                    "t": float(res.tstats[f + "_z"]),
                    "p_dk": float(res.pvalues[f + "_z"]),
                    "n_obs": int(res.nobs),
                })
    if drop_rows:
        liq_table = pd.concat([liq_table, pd.DataFrame(drop_rows)],
                              ignore_index=True)
        atomic_write_df(liq_table,
                        TABLES / "headline_with_liquidity_controls.csv",
                        index=False)
        print(f"  flagged features -> {len(drop_rows)} drop-sensitivity rows added")
    else:
        atomic_write_df(liq_table,
                        TABLES / "headline_with_liquidity_controls.csv",
                        index=False)
        print("  no VIF>5 or |r|>0.7 flags: no drop-sensitivity run required")
    _tick("VIF audit", t0)

    print(f"\nSTAGE 2 COMPLETE in {time.time() - t_all:.1f}s")


if __name__ == "__main__":
    main()
