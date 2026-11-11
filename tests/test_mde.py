"""v2 Stage-1 MDE null-classification tests (plan V2-1.3)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import pytest

from nepsemsc.evaluation.mde import (MDE_Z, classify_null, mde_80,
                                     null_table)


def test_mde_formula():
    assert MDE_Z == pytest.approx(2.80)
    assert mde_80(1.0) == pytest.approx(2.80)
    assert mde_80(0.25) == pytest.approx(0.70)


def test_classify_powered_underpowered_and_boundary():
    m, ratio, ab, cls = classify_null(0.5, 1.0)
    assert m == pytest.approx(2.8)
    assert ratio == pytest.approx(0.5 / 1.4)
    assert ab == pytest.approx(0.5)
    assert cls == "NULL_POWERED"

    # exact tie resolves to the honest (underpowered) side
    _, _, _, cls = classify_null(1.4, 1.0)
    assert cls == "NULL_UNDERPOWERED"

    _, _, _, cls = classify_null(1.4 - 1e-9, 1.0)
    assert cls == "NULL_POWERED"

    # absolute value drives the rule
    _, _, _, cls = classify_null(-2.0, 1.0)
    assert cls == "NULL_UNDERPOWERED"


def test_classify_zero_se_is_underpowered_by_tie_rule():
    m, ratio, _ab, cls = classify_null(0.1, 0.0)
    assert m == 0.0
    assert pd.isna(ratio)
    assert cls == "NULL_UNDERPOWERED"


def _tiny_grid() -> pd.DataFrame:
    # `bp` in basis points, `se` in RETURNS (the frozen-grid convention).
    rows = [
        ("H1", "self_loop_ratio", "abs_ret_fwd1", -1.55, 1.97e-4),
        ("H2", "anomaly_score", "abs_ret_fwd1", -1.49, 2.66e-4),
        ("H3", "anomaly_score", "ret_fwd1", 0.96, 3.00e-4),
        ("H4", "buyer_hhi", "ret_fwd1", 7.51, 3.41e-4),
        ("H5", "buyer_hhi", "abs_ret_fwd1", -1.86, 2.67e-4),
        ("H7", "end_of_day_concentration", "abs_ret_fwd1", 3.95, 1.79e-4),
        ("H8", "end_of_day_concentration", "ret_fwd1", -4.47, 2.24e-4),
        ("H9", "self_loop_ratio", "ret_fwd1", 1.82, 2.45e-4),
        ("H10", "reciprocity", "abs_ret_fwd1", 9.49, 3.85e-4),
    ]
    return pd.DataFrame(rows, columns=["test_id", "feature", "outcome",
                                       "bp", "se"])


def test_null_table_selects_declared_rows_only():
    tab = null_table(_tiny_grid())
    assert list(tab["test_id"]) == ["H1", "H2", "H3", "H5", "H8", "H9"]
    assert set(tab["classification"]) == {"NULL_POWERED", "NULL_UNDERPOWERED"}
    h8 = tab.loc[tab["test_id"] == "H8"].iloc[0]
    assert h8["classification"] == "NULL_UNDERPOWERED"
    assert h8["mde80_bp"] == pytest.approx(2.8 * 2.24)


def test_null_table_event_summary_row_optional():
    grid = _tiny_grid()
    ev = pd.DataFrame([{"mean_car": 0.0013, "t_stat": 0.57}])
    tab = null_table(grid, event_summary=ev)
    assert "EVENT_CAR_OVERALL" in set(tab["test_id"])
    row = tab.loc[tab["test_id"] == "EVENT_CAR_OVERALL"].iloc[0]
    assert row["classification"] == "NULL_POWERED"
