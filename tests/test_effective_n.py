"""v2 Stage-4 effective-N tests (plan V2-4)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd

from nepsemsc.analysis.effective_n import add_effective_n, effective_n


def _panel() -> pd.DataFrame:
    rng = np.random.default_rng(20261114)
    rows = []
    for s in range(4):
        for d in range(10):
            rows.append({
                "symbol": f"S{s}",
                "date": pd.Timestamp("2023-01-01") + pd.Timedelta(days=d),
                "x": rng.normal(), "c": rng.normal(), "y": rng.normal(),
            })
    return pd.DataFrame(rows)


def test_effective_n_two_way_fe_formula():
    p = _panel()
    eff = effective_n(p, "y", ["x", "c"])
    assert eff["n_obs"] == 40
    assert eff["n_stocks"] == 4
    assert eff["n_dates"] == 10
    assert eff["n_effective"] == 40 - (4 - 1) - (10 - 1) == 28
    assert eff["n_cross_sections"] == 10


def test_effective_n_fm_guard_skips_rank_deficient_date():
    p = _panel()
    first = p["date"].min()
    p.loc[p["date"] == first, ["x", "c"]] = 1.0
    eff = effective_n(p, "y", ["x", "c"])
    assert eff["n_cross_sections"] == 9


def test_add_effective_n_preserves_grid_columns_and_values():
    p = _panel()
    p["x_z"] = p["x"]
    grid = pd.DataFrame({"test_id": ["T1", "T2"], "feature": ["x", "x"],
                         "outcome": ["y", "y"], "bp": [1.0, 2.0]})
    out = add_effective_n(grid, p, controls=("c",))
    assert list(out.columns[:4]) == ["test_id", "feature", "outcome", "bp"]
    assert out["n_obs"].tolist() == [40, 40]
    assert out["n_effective"].tolist() == [28, 28]
    assert out["bp"].tolist() == [1.0, 2.0]
