"""v2 Stage-4 broker monthly panel tests (descriptive, R11)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import pytest
import duckdb

from nepsemsc.broker.monthly_panel import (add_core_flags, canonical_broker_id,
                                           create_broker_macro,
                                           exact_concentration,
                                           monthly_centrality,
                                           top50_persistence,
                                           transition_counts)


def test_exact_concentration_uses_integer_paisa():
    bs = pd.DataFrame({
        "month": [pd.Timestamp("2023-01-01")] * 3,
        "broker": ["B1"] * 3,
        "symbol": ["A", "B", "C"],
        "value_paisa": [1, 1, 2],
    })
    c = exact_concentration(bs).iloc[0]
    assert c["n_symbols"] == 3
    assert c["hhi"] == pytest.approx(6 / 16)
    assert c["top_symbol_share"] == pytest.approx(0.5)


def test_exact_concentration_single_symbol_is_one():
    bs = pd.DataFrame({"month": [pd.Timestamp("2023-01-01")],
                       "broker": ["B1"], "symbol": ["A"],
                       "value_paisa": [123456789]})
    assert exact_concentration(bs).iloc[0]["hhi"] == pytest.approx(1.0)


def _core_panel() -> pd.DataFrame:
    months = pd.date_range("2021-01-01", periods=12, freq="MS")
    rows = []
    for bi in range(10):
        b = f"B{bi}"
        for mi, m in enumerate(months):
            if b == "B0":
                bt = 20.0 if mi >= 5 else 10.0
            elif b == "B1":
                bt = 11.0 if mi < 6 else 0.0
            elif b == "B2":
                bt = 12.0 if mi < 5 else 0.0
            else:
                bt = 0.0
            rows.append({"month": m, "broker": b, "betweenness": bt,
                         "total_value_paisa": 1000 - bi,
                         "n_buy_trades": 1, "n_sell_trades": 1})
    return pd.DataFrame(rows)


def test_core_requires_top_decile_and_six_of_trailing_twelve():
    p = add_core_flags(_core_panel())
    b0 = p[p.broker == "B0"].set_index("month")
    b1 = p[p.broker == "B1"].set_index("month")
    b2 = p[p.broker == "B2"].set_index("month")
    months = sorted(p.month.unique())
    # B0 first becomes top decile in month 5; six top months only at month 10
    assert not b0.loc[months[9], "core"]
    assert b0.loc[months[10], "core"]
    assert b0.loc[months[10], "n_core_months_12"] == 6
    # B1/B2 reach only five top-decile months -> never core
    assert not b1["core"].any()
    assert not b2["core"].any()
    assert b2.loc[months[4], "core_month"]
    assert not b2.loc[months[4], "core"]


def _value_panel() -> pd.DataFrame:
    rows = []
    for m, offset in ((pd.Timestamp("2023-01-01"), 0),
                      (pd.Timestamp("2023-02-01"), 1)):
        for i in range(60):
            rows.append({"month": m, "broker": f"B{i}",
                         "total_value_paisa": 10_000 - i,
                         "core": False})
    # month 2: B49 drops below B50 but stays active
    idx = (pd.DataFrame(rows).month == pd.Timestamp("2023-02-01")) & \
          (pd.DataFrame(rows).broker == "B49")
    rows[int(np.where(idx)[0][0])]["total_value_paisa"] = 1
    return pd.DataFrame(rows)


def test_top50_jaccard_counts_set_overlap():
    j = top50_persistence(_value_panel())
    row = j[j.month == pd.Timestamp("2023-02-01")].iloc[0]
    assert row["n_active"] == 60
    assert row["overlap"] == 49
    assert row["jaccard"] == pytest.approx(49 / 51)


def test_transition_counts_core_swap():
    m1 = pd.Timestamp("2023-01-01")
    m2 = pd.Timestamp("2023-02-01")
    p = pd.DataFrame({
        "month": [m1, m1, m1, m1, m2, m2, m2, m2],
        "broker": ["A", "B", "C", "D"] * 2,
        "core": [True, False, False, False, False, True, False, False],
    })
    t = transition_counts(p).iloc[0]
    assert t["core_to_core"] == 0
    assert t["core_to_periphery"] == 1
    assert t["periphery_to_core"] == 1
    assert t["periphery_to_periphery"] == 2
    assert t["entries"] == 0 and t["exits"] == 0


def test_monthly_centrality_star_graph():
    edges = pd.DataFrame({
        "month": [pd.Timestamp("2023-01-01")] * 3,
        "buyer": ["C", "C", "C"], "seller": ["L1", "L2", "L3"],
        "value_paisa": [10, 20, 30], "n_trades": [1, 1, 1],
    })
    c = monthly_centrality(edges).set_index("broker")
    assert c.loc["C", "betweenness"] == pytest.approx(1.0)
    assert c.loc["L1", "betweenness"] == pytest.approx(0.0)
    assert c.loc["C", "eigenvector"] > c.loc["L1", "eigenvector"]
    assert c.loc["C", "degree"] == 3


def test_broker_id_canonicalisation_merges_float_vintage():
    assert canonical_broker_id("58.0") == "58"
    assert canonical_broker_id("1.0") == "01"
    assert canonical_broker_id("08") == "08"
    assert canonical_broker_id("D01") == "D01"
    con = duckdb.connect()
    create_broker_macro(con)
    got = con.execute(
        "SELECT canon_broker('1.0'), canon_broker('58.0'), "
        "canon_broker('08'), canon_broker('D01')").fetchone()
    con.close()
    assert got == ("01", "58", "08", "D01")
