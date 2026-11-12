"""v2 Stage-4 H7 specification-curve tests (plan V2-4)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import pytest

from nepsemsc.analysis.specification_curve import (curve_summary, fit_spec,
                                                   spec_grid,
                                                   subsample_panel)


def test_spec_grid_is_declared_144_factorial():
    g = spec_grid()
    assert len(g) == 144
    assert g["spec_id"].nunique() == 144
    assert g["se_family"].value_counts().to_dict() == {
        "DK": 36, "DC": 36, "FM": 36, "WB": 36}
    assert set(g["outcome_label"]) == {"abs_ret", "ret"}
    assert set(g["controls"]) == {"base", "gamma_all"}
    assert set(g["subsample"]) == {"full", "bubble", "normal"}
    assert set(g["cutoff"]) == {"5pct", "1pct", "10pct"}
    assert (g.loc[g["cutoff"] == "5pct", "cutoff_col"]
            == "end_of_day_concentration_z").all()
    assert (g.loc[g["cutoff"] == "1pct", "cutoff_col"] == "eod_01_z").all()
    assert (g.loc[g["cutoff"] == "10pct", "cutoff_col"] == "eod_10_z").all()


def test_subsample_panel_uses_calendar_regime_definition():
    p = pd.DataFrame({
        "date": pd.to_datetime(["2021-06-01", "2022-12-31",
                                "2023-01-01", "2024-12-31"]),
        "x": [1, 2, 3, 4],
    })
    assert subsample_panel(p, "bubble")["x"].tolist() == [1, 2]
    assert subsample_panel(p, "normal")["x"].tolist() == [3, 4]
    assert subsample_panel(p, "full")["x"].tolist() == [1, 2, 3, 4]
    with pytest.raises(ValueError):
        subsample_panel(p, "nope")


def test_curve_summary_metrics_are_auditable():
    c = pd.DataFrame({
        "beta_bp": [1.0, 2.0, 4.0, -1.0, -3.0, -5.0],
        "ci_excludes_0": [True, False, True, False, True, False],
        "p_lt_05": [True, False, True, False, True, False],
        "outcome_label": ["abs_ret"] * 3 + ["ret"] * 3,
    })
    s = curve_summary(c).set_index("group")
    a = s.loc["outcome=abs_ret"]
    assert a["n_specs"] == 3
    assert a["median_bp"] == pytest.approx(2.0)
    assert a["range_bp"] == pytest.approx(3.0)
    assert a["robustness_ratio"] == pytest.approx(1.5)
    assert a["share_ci_excludes_0"] == pytest.approx(2 / 3)
    assert a["share_positive"] == 1.0
    r = s.loc["outcome=ret"]
    assert r["robustness_ratio_abs"] == pytest.approx(4.0 / 3.0)


def _fit_panel() -> pd.DataFrame:
    rng = np.random.default_rng(20261115)
    rows = []
    for s in range(8):
        for d in range(40):
            f = rng.normal()
            c1, c2 = rng.normal(size=2)
            g1, g2, g3 = rng.normal(size=3)
            rows.append({
                "symbol": f"S{s}",
                "date": pd.Timestamp("2023-01-01") + pd.Timedelta(days=d),
                "end_of_day_concentration_z": f,
                "eod_01_z": rng.normal(), "eod_10_z": rng.normal(),
                "log_volume_z": c1, "market_ret_loo_z": c2,
                "amihud_z": g1, "roll_spread_z": g2,
                "corwin_schultz_z": g3,
                "abs_ret_fwd1": 0.01 * f + rng.normal(scale=0.01),
                "ret_fwd1": 0.01 * f + rng.normal(scale=0.01),
            })
    return pd.DataFrame(rows)


def test_fit_spec_dk_and_fm_execute_and_return_bp_scale():
    p = _fit_panel()
    grid = spec_grid()
    for fam in ("DK", "FM"):
        spec = grid[(grid.se_family == fam) & (grid.outcome_label == "abs_ret")
                    & (grid.controls == "base") & (grid.subsample == "full")
                    & (grid.cutoff == "5pct")].iloc[0]
        r = fit_spec(p, spec)
        assert np.isfinite(r["beta_bp"]) and np.isfinite(r["p"])
        assert r["n_obs"] == 320
        assert r["ci_lo_bp"] < r["beta_bp"] < r["ci_hi_bp"]
        assert r["ci_method"] == "normal"


def test_fit_spec_wb_branch_runs_with_declared_engine():
    p = _fit_panel()
    grid = spec_grid()
    spec = grid[(grid.se_family == "WB") & (grid.outcome_label == "abs_ret")
                & (grid.controls == "base") & (grid.subsample == "full")
                & (grid.cutoff == "5pct")].iloc[0]
    r = fit_spec(p, spec, seeds=[833_001 + i for i in range(20)])
    assert np.isfinite(r["beta_bp"]) and np.isfinite(r["p"])
    assert 0.0 <= r["p"] <= 1.0
    assert r["ci_method"] == "wb_percentile"
    assert r["ci_lo_bp"] <= r["ci_hi_bp"]
