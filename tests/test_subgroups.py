"""v2 Stage-4 pre-declared subgroup tests (plan V2-4)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import pytest

from nepsemsc.analysis.subgroups import assign_subgroups, subgroup_table


def test_assign_subgroups_uses_train_only_ranks():
    syms = [f"S{i}" for i in range(10)]
    dates = pd.date_range("2022-01-03", periods=20, freq="B")
    panel = pd.DataFrame({"fold_id": 0,
                          "symbol": syms,
                          "date": dates[0]})
    train_rows = []
    for i, s in enumerate(syms):
        for d in dates:
            train_rows.append({"fold_id": 0, "symbol": s, "date": d,
                               "amihud": float(i), "log_volume": 1.0})
    train = pd.DataFrame(train_rows)
    ohlcv_rows = []
    for i, s in enumerate(syms):
        for d in dates:
            ohlcv_rows.append({"symbol": s, "date": d,
                               "turnover": float(i + 1)})
    ohlcv = pd.DataFrame(ohlcv_rows)
    a = assign_subgroups(panel, train, ohlcv).set_index("symbol")
    assert a.loc["S9", "turnover_tier"] == "top3"
    assert a.loc["S8", "turnover_tier"] == "top3"
    assert a.loc["S7", "turnover_tier"] == "top3"
    assert a.loc["S6", "turnover_tier"] == "bottom7"
    assert (a["size_group"] == "large").sum() == 5
    assert (a["liquidity_group"] == "illiquid").sum() == 5
    assert a.loc["S0", "size_group"] == "small"
    assert a.loc["S0", "liquidity_group"] == "liquid"


def _subgroup_panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(20261116)
    syms = [f"S{i}" for i in range(10)]
    dates = pd.date_range("2023-01-02", periods=40, freq="B")
    rows = []
    for s in syms:
        for d in dates:
            f = rng.normal()
            rows.append({
                "fold_id": 0, "symbol": s, "date": d,
                "buyer_hhi_z": f, "end_of_day_concentration_z": f,
                "reciprocity_z": f,
                "log_volume_z": rng.normal(), "market_ret_loo_z": rng.normal(),
                "ret_fwd1": 0.01 * f + rng.normal(scale=0.01),
                "abs_ret_fwd1": 0.01 * abs(f) + rng.normal(scale=0.01),
            })
    p = pd.DataFrame(rows)
    for i, s in enumerate(syms):
        m = p.symbol == s
        p.loc[m, "size_group"] = "large" if i >= 5 else "small"
        p.loc[m, "liquidity_group"] = "illiquid" if i >= 5 else "liquid"
        p.loc[m, "turnover_tier"] = "top3" if i >= 7 else "bottom7"
    grid = pd.DataFrame({
        "test_id": ["H4", "H7", "H8", "H10"],
        "feature": ["buyer_hhi", "end_of_day_concentration",
                    "end_of_day_concentration", "reciprocity"],
        "outcome": ["ret_fwd1", "abs_ret_fwd1", "ret_fwd1", "abs_ret_fwd1"],
    })
    return p, grid


def test_subgroup_table_shape_and_not_executed_rows():
    p, grid = _subgroup_panel()
    t = subgroup_table(p, grid)
    assert len(t) == 40
    assert t["row_type"].value_counts().to_dict() == {
        "group": 24, "interaction": 12, "not_executed": 4}
    ne = t[t.row_type == "not_executed"]
    assert (ne["split"] == "circuit_breaker").all()
    assert (ne["status"] == "NOT_EXECUTED").all()
    assert ne["note"].str.contains("no circuit-breaker").all()
    est = t[t.row_type != "not_executed"]
    assert np.isfinite(est["beta_bp"]).all()
    assert est["p_bonf"].between(0, 1).all()
    inter = t[t.row_type == "interaction"]
    assert (inter["bonferroni_family"] == 3).all()
    grp = t[t.row_type == "group"]
    assert (grp["bonferroni_family"] == 6).all()


def test_subgroup_interaction_labels_match_split_direction():
    p, grid = _subgroup_panel()
    t = subgroup_table(p, grid)
    assert set(t.loc[t.row_type == "interaction", "group"]) == {
        "large_vs_small", "illiquid_vs_liquid", "top3_vs_bottom7"}
