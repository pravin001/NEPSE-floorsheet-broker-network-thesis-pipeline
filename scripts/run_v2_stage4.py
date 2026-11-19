"""Stage 4 master runner — effective-N, H7 specification curve, broker panel,
pre-declared subgroups, event-study BMP/rank upgrade (v2 plan V2-4).

Sections, in order:
  4.0  gates: panel shape, EoD rows/days, frozen H7 spec reproduction;
  4.1  effective-N columns on the v2 grid + Romano-Wolf table;
  4.2  H7 specification curve (144 declared factorial specs; the plan's
       "= 72" is an arithmetic slip, deviation #20) + figure;
  4.3  broker-level monthly panel + network snapshots (DESCRIPTIVE, R11);
  4.4  pre-declared subgroup heterogeneity (size / liquidity / turnover tier;
       circuit-breaker NOT_EXECUTED);
  4.5  event-study BMP + Corrado-style rank tests on the frozen v1 windows;
  4.6  cost-benefit arithmetic table.

Pre-run gates (abort, never silently continue):
  * Stage-4 panel = 7,116 rows / 723 dates / 12 symbols;
  * EoD SQL = 233,454 rows / 937 days (938 - defect);
  * base DK H7 spec reproduces the frozen +3.952373 bp / p .027432;
  * DC-v2, FM and WB base specs reproduce Stage-2/frozen references;
  * event CAR reconstruction max |diff| <= 1e-12;
  * broker buy/sell totals reconcile exactly and HHI is in [0, 1].
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from nepsemsc.analysis.effective_n import add_effective_n
from nepsemsc.analysis.event_study_upgrade import (
    clustered_inference as event_clustered)
from nepsemsc.analysis.event_study_upgrade import upgrade as event_upgrade
from nepsemsc.analysis.specification_curve import (curve_summary,
                                                   run_spec_curve)
from nepsemsc.analysis.subgroups import (assign_subgroups,
                                         subgroup_table)
from nepsemsc.broker.monthly_panel import (add_core_flags,
                                           build_broker_panel,
                                           snapshot_figure)
from nepsemsc.data.duckdb_loader import get_conn
from nepsemsc.features.liquidity import (LIQUIDITY_COLS,
                                         build_liquidity_features)
from nepsemsc.ml.panel_data import (Z_SOURCE_COLS, build_oos_panel,
                                    standardize_test, train_fold_stats)
from nepsemsc.ml.panel_regression import fit_driscoll_kraay
from nepsemsc.utils.io import atomic_write_df

TABLES = ROOT / "outputs/tables"
FIGURES = ROOT / "outputs/figures"
DEFECT = "2023-02-16"
BASE_CONTROLS = ("log_volume_z", "market_ret_loo_z")
EOD_SQL = """
WITH fs AS (
    SELECT date, symbol, contract_no, volume
    FROM floorsheet_dedup
    WHERE volume IS NOT NULL AND volume > 0
      AND price > 0
      AND COALESCE(buyer_broker_id, '') <> ''
      AND COALESCE(seller_broker_id, '') <> ''
      AND COALESCE(symbol, '') <> ''
),
ranked AS (
    SELECT date, symbol, volume,
           ROW_NUMBER() OVER (PARTITION BY date, symbol
                              ORDER BY contract_no DESC) AS rn_desc,
           COUNT(*) OVER (PARTITION BY date, symbol) AS n_t
    FROM fs
    WHERE CAST(date AS VARCHAR) <> '{DEFECT}'
)
SELECT date, symbol,
       SUM(CASE WHEN rn_desc <= CAST(ceil(0.01 * n_t) AS BIGINT)
                THEN volume ELSE 0 END) / SUM(volume) AS eod_01,
       SUM(CASE WHEN rn_desc <= CAST(ceil(0.10 * n_t) AS BIGINT)
                THEN volume ELSE 0 END) / SUM(volume) AS eod_10
FROM ranked
GROUP BY 1, 2
""".replace("{DEFECT}", DEFECT)


def _tick(label: str, t0: float) -> None:
    print(f"  {label}: {time.time() - t0:.1f}s", flush=True)


def build_stage4_panel():
    """Rebuild the Stage-2 panel + EoD 1%/10% columns (same 7,116 rows)."""
    scores = pd.read_parquet(ROOT / "data/processed/anomaly_scores.parquet")
    outcomes = pd.read_parquet(ROOT / "data/processed/daily_outcomes.parquet")
    ohlcv = pd.read_parquet(ROOT / "data/processed/daily_ohlcv.parquet")

    liq = build_liquidity_features(outcomes, ohlcv)
    panel, train = build_oos_panel(scores, outcomes)
    panel = panel.merge(liq, on=["date", "symbol"], how="left")
    train = train.merge(liq, on=["date", "symbol"], how="left")

    con = get_conn()
    eod = con.execute(EOD_SQL).df()
    con.close()
    eod["date"] = pd.to_datetime(eod["date"]).dt.date
    panel["date"] = pd.to_datetime(panel["date"]).dt.date
    train["date"] = pd.to_datetime(train["date"]).dt.date
    panel = panel.merge(eod, on=["date", "symbol"], how="left")
    train = train.merge(eod, on=["date", "symbol"], how="left")

    z_cols = Z_SOURCE_COLS + LIQUIDITY_COLS + ["eod_01", "eod_10"]
    stats = train_fold_stats(train, cols=z_cols)
    panel = standardize_test(panel, stats)
    panel = panel.dropna(subset=[c + "_z" for c in z_cols]).reset_index(drop=True)

    eod_accounting = {
        "eod_rows": int(len(eod)),
        "eod_days": int(eod["date"].nunique()),
        "panel_rows": int(len(panel)),
        "panel_dates": int(panel["date"].nunique()),
        "panel_symbols": int(panel["symbol"].nunique()),
    }
    print(f"  EoD SQL rows {len(eod):,} / days {eod['date'].nunique()}",
          flush=True)
    print(f"  Stage-4 panel {len(panel):,} rows / {panel['date'].nunique()} "
          f"dates / {panel['symbol'].nunique()} symbols", flush=True)
    assert len(panel) == 7116, len(panel)
    assert panel["date"].nunique() == 723
    assert panel["symbol"].nunique() == 12
    assert len(eod) == 233_454 and eod["date"].nunique() == 937
    return panel, train, ohlcv, eod_accounting


def sec_effective_n(panel: pd.DataFrame) -> pd.DataFrame:
    print("\n[4.1] effective-N columns", flush=True)
    frozen = pd.read_csv(TABLES / "hypothesis_grid_results.csv").set_index(
        "test_id")
    for name in ("hypothesis_grid_results_v2.csv",
                 "hypothesis_grid_results_rw.csv"):
        grid = pd.read_csv(TABLES / name)
        aug = add_effective_n(grid, panel)
        joined = aug.set_index("test_id").join(
            frozen[["n_obs"]], how="left", rsuffix="_frozen")
        if not (joined["n_obs"] == joined["n_obs_frozen"]).all():
            raise AssertionError(f"{name}: n_obs mismatch vs frozen grid")
        atomic_write_df(aug, TABLES / name)
        print(f"  {name}: {len(aug)} rows, n_obs == frozen for all tests",
              flush=True)
    return pd.read_csv(TABLES / "hypothesis_grid_results_v2.csv")


def fig_spec_curve(curve: pd.DataFrame, path: Path) -> None:
    d = curve.sort_values("beta_bp").reset_index(drop=True)
    colors = {"DK": "#1f77b4", "DC": "#ff7f0e", "FM": "#2ca02c",
              "WB": "#d62728"}
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 9),
        gridspec_kw={"height_ratios": [2.4, 1.25]})
    for fam, g in d.groupby("se_family", observed=True):
        ax1.errorbar(g.index, g["beta_bp"],
                     yerr=[g["beta_bp"] - g["ci_lo_bp"],
                           g["ci_hi_bp"] - g["beta_bp"]],
                     fmt="o", ms=2.5, lw=0.7, capsize=0,
                     color=colors[fam], label=fam, alpha=0.85)
    ax1.axhline(0.0, color="k", lw=0.8)
    ax1.set_ylabel("H7 beta (bp per SD)")
    ax1.set_xlabel("specification rank (sorted by beta)")
    ax1.set_title("H7 specification curve — 144 declared specifications")
    ax1.legend(title="SE family", fontsize=8, title_fontsize=8)

    y, ticks, labels = 0.0, [], []
    factor_cols = (("SE", "se_family"), ("Outcome", "outcome_label"),
                   ("Controls", "controls"), ("Sample", "subsample"),
                   ("EoD", "cutoff"))
    for fname, col in factor_cols:
        for lev in sorted(d[col].dropna().unique()):
            m = d[col] == lev
            share = float(d.loc[m, "ci_excludes_0"].mean())
            ax2.barh(y, share, color="#7f8c8d", height=0.62)
            ax2.text(share + 0.01, y, f"{share:.2f} (n={int(m.sum())})",
                     va="center", fontsize=7)
            ticks.append(y)
            labels.append(f"{fname}: {lev}")
            y += 1.0
        y += 0.4
    ax2.set_yticks(ticks)
    ax2.set_yticklabels(labels, fontsize=7)
    ax2.invert_yaxis()
    ax2.set_xlim(0, 1.18)
    ax2.set_xlabel("share of 95% CIs excluding zero (by factor level)")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def sec_spec_curve(panel: pd.DataFrame):
    print("\n[4.2] H7 specification curve (144 declared specs)", flush=True)
    t0 = time.time()
    curve = run_spec_curve(panel)
    if len(curve) != 144:
        raise AssertionError(f"spec curve has {len(curve)} rows")
    if not np.isfinite(curve["beta_bp"]).all():
        raise AssertionError("non-finite spec-curve beta")
    atomic_write_df(curve, TABLES / "specification_curve_h7.csv")
    summary = curve_summary(curve)
    atomic_write_df(summary, TABLES / "specification_curve_h7_summary.csv")
    fig_spec_curve(curve, FIGURES / "specification_curve_h7.png")

    frozen = pd.read_csv(TABLES / "hypothesis_grid_results.csv").set_index(
        "test_id").loc["H7"]
    base = curve.loc[curve["spec_id"] == "DK|abs_ret|base|full|5pct"].iloc[0]
    rel = abs(base["beta_bp"] - frozen["bp"]) / abs(frozen["bp"])
    if rel > 1e-8 or abs(base["p"] - frozen["p_dk"]) > 1e-8:
        raise AssertionError(f"frozen H7 reproduction failed rel={rel:.2e}")
    wb = curve.loc[curve["spec_id"] == "WB|abs_ret|base|full|5pct"].iloc[0]
    wb_ref = pd.read_csv(TABLES / "wild_cluster_bootstrap.csv").set_index(
        "test_id").loc["H7"]
    if abs(float(wb["p"]) - float(wb_ref["p_wb"])) > 1e-12:
        raise AssertionError(f"WB reproduction failed {wb['p']} vs "
                             f"{wb_ref['p_wb']}")
    dc = curve.loc[curve["spec_id"] == "DC|abs_ret|base|full|5pct"].iloc[0]
    dc_ref = pd.read_csv(TABLES / "se_concordance.csv").set_index(
        "test_id").loc["H7"]
    if abs(float(dc["p"]) - float(dc_ref["p_dc_v2"])) > 1e-9:
        raise AssertionError(f"DC-v2 reproduction failed {dc['p']} vs "
                             f"{dc_ref['p_dc_v2']}")
    fm = curve.loc[curve["spec_id"] == "FM|abs_ret|base|full|5pct"].iloc[0]
    if abs(float(fm["p"]) - float(frozen["p_fm"])) > 1e-8:
        raise AssertionError(f"FM reproduction failed {fm['p']} vs "
                             f"{frozen['p_fm']}")
    _tick("specification curve", t0)
    print(f"  gate: base DK {base['beta_bp']:+.6f} bp p {base['p']:.6f} "
          f"(frozen {frozen['bp']:+.6f} / {frozen['p_dk']:.6f}); "
          f"DC p {dc['p']:.4f}; FM p {fm['p']:.4f}; WB p {wb['p']:.4f}",
          flush=True)
    return curve, summary


def sec_broker():
    print("\n[4.3] broker-level monthly panel (descriptive, R11)", flush=True)
    t0 = time.time()
    con = get_conn()
    panel, edges, jac, trans, n_trades = build_broker_panel(con)
    con.close()

    total_buy = int(panel["buy_paisa"].sum())
    total_sell = int(panel["sell_paisa"].sum())
    if total_buy != total_sell:
        raise AssertionError(f"broker buy/sell totals do not reconcile: "
                             f"{total_buy} vs {total_sell}")
    if not panel["hhi"].between(0.0, 1.0).all():
        raise AssertionError("HHI outside [0,1]")
    if panel["month"].nunique() != 48:
        raise AssertionError(f"unexpected month count {panel.month.nunique()}")

    keep = ["month", "broker", "buy_paisa", "sell_paisa", "buy_value_npr",
            "sell_value_npr", "total_value_npr", "net_position_npr",
            "n_buy_trades", "n_sell_trades", "n_trades", "n_buy_symbols",
            "n_sell_symbols", "breadth", "n_symbols", "hhi",
            "top_symbol_share", "betweenness", "eigenvector", "degree",
            "weighted_degree", "n_active_brokers", "betweenness_rank",
            "core_month", "n_core_months_12", "persistent_core", "core"]
    atomic_write_df(panel[keep], TABLES / "broker_level_panel.csv")
    atomic_write_df(jac, TABLES / "broker_top50_persistence.csv")
    atomic_write_df(trans, TABLES / "broker_core_transitions.csv")

    active_gt50 = jac.loc[jac["n_active"] > 50, "jaccard"].dropna()
    summary = pd.DataFrame([
        {"item": "valid_trades", "value": n_trades},
        {"item": "months", "value": int(panel["month"].nunique())},
        {"item": "brokers", "value": int(panel["broker"].nunique())},
        {"item": "broker_months", "value": int(len(panel))},
        {"item": "active_min", "value": int(panel.groupby("month").size().min())},
        {"item": "active_max", "value": int(panel.groupby("month").size().max())},
        {"item": "hhi_median", "value": float(panel["hhi"].median())},
        {"item": "hhi_p99", "value": float(panel["hhi"].quantile(0.99))},
        {"item": "hhi_max", "value": float(panel["hhi"].max())},
        {"item": "breadth_median", "value": float(panel["breadth"].median())},
        {"item": "core_brokers", "value": int(panel.loc[panel["core"],
                                                       "broker"].nunique())},
        {"item": "core_broker_months", "value": int(panel["core"].sum())},
        {"item": "jaccard_top50_mean", "value": float(jac["jaccard"].mean())},
        {"item": "jaccard_top50_mean_active_gt50",
         "value": float(active_gt50.mean())},
        {"item": "core_to_core", "value": int(trans["core_to_core"].sum())},
        {"item": "core_to_periphery",
         "value": int(trans["core_to_periphery"].sum())},
        {"item": "periphery_to_core",
         "value": int(trans["periphery_to_core"].sum())},
        {"item": "entries", "value": int(trans["entries"].sum())},
        {"item": "exits", "value": int(trans["exits"].sum())},
    ])
    atomic_write_df(summary, TABLES / "broker_panel_summary.csv")

    # Core-definition sensitivity: the declared betweenness rule degenerates
    # when the monthly graph is complete (betweenness identically zero), so the
    # same persistence rule is also run on eigenvector and on raw value.
    sens = []
    base_set = set(map(tuple, panel.loc[panel["core"], ["month", "broker"]]
                       .to_numpy()))
    for metric in ("betweenness", "eigenvector", "total_value_paisa"):
        alt = add_core_flags(panel, rank_col=metric)
        alt_set = set(map(tuple, alt.loc[alt["core"], ["month", "broker"]]
                           .to_numpy()))
        inter = len(base_set & alt_set)
        union = len(base_set | alt_set)
        sens.append({
            "rank_variable": metric,
            "core_brokers": int(alt.loc[alt["core"], "broker"].nunique()),
            "core_broker_months": int(alt["core"].sum()),
            "jaccard_vs_declared": inter / union if union else np.nan,
            "n_core_only_here": len(alt_set - base_set),
            "n_core_only_declared": len(base_set - alt_set),
        })
    sens = pd.DataFrame(sens)
    atomic_write_df(sens, TABLES / "broker_core_definition_sensitivity.csv")

    snap = []
    for month, fname in (("2021-10", "broker_network_bubble.png"),
                         ("2023-06", "broker_network_normal.png")):
        info = snapshot_figure(panel, edges, month, FIGURES / fname)
        snap.append({"month": month, **info})
    atomic_write_df(pd.DataFrame(snap), TABLES / "broker_snapshot_summary.csv")
    _tick("broker panel", t0)
    print(f"  {n_trades:,} valid trades; {len(panel):,} broker-months; "
          f"{panel['broker'].nunique()} brokers; "
          f"core broker-months {int(panel['core'].sum())}", flush=True)
    print(summary.to_string(index=False), flush=True)
    print("  core-definition sensitivity:", flush=True)
    print(sens.to_string(index=False), flush=True)
    return panel, jac, trans, summary, pd.DataFrame(snap), sens


def sec_broker_id_defect(panel: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    """Leave-defect-rows-out sensitivity for the dotted broker-id vintage.

    The corpus contains broker ids rendered as floats (`58.0`) on 15 days.
    The daily network features treat them as distinct nodes, so the affected
    (date, symbol) rows carry a measurement defect.  The Stage-4 broker panel
    canonicalises the ids; this sensitivity re-fits each test without the
    affected OOS rows so the thesis can quote the size of the defect's
    influence on the frozen grid.
    """
    print("\n[4.4b] broker-id source-format defect sensitivity", flush=True)
    t0 = time.time()
    con = get_conn()
    aff = con.execute("""
        SELECT DISTINCT CAST(date AS DATE) AS date, symbol
        FROM floorsheet_dedup
        WHERE buyer_broker_id LIKE '%.0' OR seller_broker_id LIKE '%.0'
    """).df()
    con.close()
    aff["date"] = pd.to_datetime(aff["date"]).dt.date
    panel = panel.copy()
    panel["_broker_id_defect"] = (panel.merge(
        aff.assign(_aff=True), on=["date", "symbol"], how="left"
    )["_aff"].fillna(False).astype(bool).to_numpy())
    n_aff = int(panel["_broker_id_defect"].sum())
    if n_aff != 37:
        raise AssertionError(f"expected 37 affected OOS rows, got {n_aff}")
    if n_aff / len(panel) > 0.01:
        raise AssertionError("broker-id defect touches >1% of the OOS panel")

    g = grid.set_index("test_id")
    rows = []
    for test_id, r in g.iterrows():
        feat = str(r["feature"]) + "_z"
        outcome = str(r["outcome"])
        cols = [feat, *BASE_CONTROLS]
        full = fit_driscoll_kraay(panel, outcome, cols, bandwidth=5)
        clean = fit_driscoll_kraay(panel.loc[~panel["_broker_id_defect"]],
                                   outcome, cols, bandwidth=5)
        b_full = float(full.params[feat])
        b_clean = float(clean.params[feat])
        rows.append({
            "test_id": test_id, "feature": r["feature"], "outcome": outcome,
            "n_full": int(full.nobs), "n_excl_affected": int(clean.nobs),
            "n_affected": n_aff,
            "beta_full_bp": 1e4 * b_full,
            "beta_excl_affected_bp": 1e4 * b_clean,
            "p_full_dk": float(full.pvalues[feat]),
            "p_excl_affected_dk": float(clean.pvalues[feat]),
            "pct_change_beta": ((b_clean - b_full) / abs(b_full)
                                if b_full != 0 else np.nan),
            "sign_same": bool(np.sign(b_full) == np.sign(b_clean)),
        })
    out = pd.DataFrame(rows)
    atomic_write_df(out, TABLES / "broker_id_defect_sensitivity.csv")
    _tick("broker-id sensitivity", t0)
    print(out[["test_id", "beta_full_bp", "beta_excl_affected_bp",
               "p_full_dk", "p_excl_affected_dk", "pct_change_beta",
               "sign_same"]].to_string(index=False), flush=True)
    return out


def sec_subgroups(panel: pd.DataFrame, train: pd.DataFrame,
                  ohlcv: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    print("\n[4.4] pre-declared subgroup heterogeneity", flush=True)
    t0 = time.time()
    assign = assign_subgroups(panel, train, ohlcv)
    for split in ("size_group", "liquidity_group", "turnover_tier"):
        counts = assign.groupby("fold_id")[split].nunique()
        if not (counts == 2).all():
            raise AssertionError(f"{split}: a fold has one group only")
    if not (assign.groupby("fold_id")["turnover_tier"]
            .apply(lambda s: (s == "top3").sum() == 3).all()):
        raise AssertionError("turnover tier is not 3 per fold")
    atomic_write_df(assign, TABLES / "subgroup_assignments.csv")
    panel = panel.merge(
        assign[["fold_id", "symbol", "size_group", "liquidity_group",
                "turnover_tier"]],
        on=["fold_id", "symbol"], how="left", validate="many_to_one")
    if panel[["size_group", "liquidity_group", "turnover_tier"]].isna().any().any():
        raise AssertionError("subgroup assignment failed to cover the panel")
    table = subgroup_table(panel, grid)
    atomic_write_df(table, TABLES / "heterogeneity_subgroups.csv")
    _tick("subgroups", t0)
    est = table[table["row_type"].isin(("group", "interaction"))]
    print(f"  {len(est)} estimated rows + "
          f"{int((table['row_type'] == 'not_executed').sum())} "
          f"NOT_EXECUTED row(s)", flush=True)
    print(est[["test_id", "split", "group", "row_type", "beta_bp", "t",
               "p_dk", "p_bonf"]].to_string(index=False), flush=True)
    return table


def sec_event_study():
    print("\n[4.5] event-study BMP + rank upgrade", flush=True)
    t0 = time.time()
    cars = pd.read_csv(TABLES / "event_study_cars.csv")
    outcomes = pd.read_parquet(ROOT / "data/processed/daily_outcomes.parquet")
    scores = pd.read_parquet(ROOT / "data/processed/anomaly_scores.parquet")
    summary, per_event, ar_long, gate = event_upgrade(cars, outcomes, scores)
    clustered = event_clustered(per_event)
    # The v2.0.2 gates asserted the fixed counts 686 and 16.  Those counts are
    # consequences of the Isolation Forest event definition, and the v2.1.0
    # reciprocity correction changes the scores.  The invariant is coverage:
    # every v1 event row is upgraded exactly once, and the appendix partition
    # matches the source `method` split.  Counts are reported, not asserted.
    if gate["n_events"] != len(cars):
        raise AssertionError(
            f"upgraded {gate['n_events']} events for {len(cars)} cars rows")
    if len(per_event) != len(cars):
        raise AssertionError(
            f"per-event table has {len(per_event)} rows for {len(cars)} events")
    if not per_event["event_idx"].is_unique:
        raise AssertionError("per-event table has duplicate event_idx values")
    if gate["max_car_abs_diff"] > 1e-12:
        raise AssertionError(f"CAR reconstruction diff "
                             f"{gate['max_car_abs_diff']}")
    n_appendix = int(per_event["illiquid_appendix"].sum())
    n_appendix_source = int((cars["method"] == "market_adjusted").sum())
    if n_appendix != n_appendix_source:
        raise AssertionError(
            f"appendix split {n_appendix} != source method split "
            f"{n_appendix_source}")
    atomic_write_df(summary, TABLES / "event_study_upgraded.csv")
    atomic_write_df(per_event, TABLES / "event_study_upgraded_events.csv")
    atomic_write_df(ar_long, TABLES / "event_study_upgraded_ars.csv")
    atomic_write_df(pd.DataFrame([gate]), TABLES / "event_study_upgrade_gate.csv")
    atomic_write_df(clustered, TABLES / "event_study_clustered_inference.csv")
    _tick("event study", t0)
    print(f"  gate: {gate['n_events']} events, max |CAR diff| "
          f"{gate['max_car_abs_diff']:.2e}, appendix {n_appendix}", flush=True)
    print(summary.to_string(index=False), flush=True)
    print("  date-clustered descriptive inference:", flush=True)
    print(clustered.to_string(index=False), flush=True)
    return summary, gate


def sec_cost_benefit() -> pd.DataFrame:
    print("\n[4.6] cost-benefit arithmetic", flush=True)
    # Read the effects from the rebuilt base grid rather than hardcoding v2.0.2
    # constants: the v2.1.0 reciprocity correction changes H6/H10 (and the
    # Isolation Forest scores behind H2/H3), so a constant here would silently
    # reproduce the superseded estimate.
    base = pd.read_csv(TABLES / "hypothesis_grid_results.csv").set_index("test_id")
    rows = [
        {"test_id": "H7", "effect_bp_per_sd": float(base.loc["H7", "bp"]),
         "direction": "positive", "cost_low_bp": 30.0, "cost_high_bp": 50.0},
        {"test_id": "H10", "effect_bp_per_sd": float(base.loc["H10", "bp"]),
         "direction": "positive", "cost_low_bp": 30.0, "cost_high_bp": 50.0},
        {"test_id": "H4", "effect_bp_per_sd": float(base.loc["H4", "bp"]),
         "direction": "opposite_sign_post_hoc", "cost_low_bp": 30.0,
         "cost_high_bp": 50.0},
    ]
    df = pd.DataFrame(rows)
    df["cost_multiple_low"] = df["cost_low_bp"] / df["effect_bp_per_sd"]
    df["cost_multiple_high"] = df["cost_high_bp"] / df["effect_bp_per_sd"]
    df["standalone_tradable_at_1sd"] = False
    df["note"] = ("declared round-trip explicit-cost range; excludes "
                  "brokerage, spread and CNS carry, so the hurdle is a floor")
    atomic_write_df(df, TABLES / "economic_magnitude.csv")
    print(df[["test_id", "effect_bp_per_sd", "cost_low_bp", "cost_high_bp",
              "cost_multiple_low", "cost_multiple_high"]]
          .to_string(index=False), flush=True)
    return df


def main() -> None:
    t_all = time.time()
    print("=" * 78)
    print("STAGE 4 — effective-N, specification curve, broker panel, "
          "subgroups, event-study upgrade (v2 plan V2-4)")
    print("=" * 78)

    print("\n[4.0] panel + gates", flush=True)
    t0 = time.time()
    panel, train, ohlcv, eod_accounting = build_stage4_panel()
    _tick("panel", t0)

    grid = sec_effective_n(panel)
    curve, curve_summary_df = sec_spec_curve(panel)
    (broker_panel, jac, trans, broker_summary, snap,
     core_sens) = sec_broker()
    defect_sens = sec_broker_id_defect(panel, grid)
    subgroups = sec_subgroups(panel, train, ohlcv, grid)
    events, event_gate = sec_event_study()
    econ = sec_cost_benefit()

    print("\n[4.7] headline numbers of record", flush=True)
    print(f"  specification curve: {len(curve)} specs; "
          f"median {curve['beta_bp'].median():+.3f} bp; "
          f"CI-excluding-0 share {curve['ci_excludes_0'].mean():.3f}",
          flush=True)
    print(curve_summary_df.to_string(index=False), flush=True)
    print(f"\nStage 4 total wall: {time.time() - t_all:.1f}s", flush=True)
    print("STAGE4_DONE", flush=True)


if __name__ == "__main__":
    main()
