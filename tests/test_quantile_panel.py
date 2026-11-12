"""Quantile panel tests (v2 Stage 3, plan V2-3.1).

Pins the declared two-way dummy design, recovery of a known quantile slope,
per-(test,tau) checkpoint resume, and the pre-declared tail labels/shape fields.
"""
import numpy as np
import pandas as pd
import pytest

from nepsemsc.models import quantile_panel as qp
from nepsemsc.models.quantile_panel import (TAUS, build_quantile_design,
                                            fit_quantile, run_quantile_grid,
                                            tail_summary)


def _toy_panel(n_dates: int = 12, n_symbols: int = 20, seed: int = 7):
    rng = np.random.default_rng(seed)
    rows = []
    for d in pd.bdate_range("2024-01-02", periods=n_dates):
        for s in range(n_symbols):
            x = rng.normal(0.0, 1.0)
            rows.append({
                "date": d,
                "symbol": f"S{s:02d}",
                "reciprocity_z": x,
                "log_volume_z": rng.normal(0.0, 1.0),
                "market_ret_loo_z": rng.normal(0.0, 1.0),
                "y": 1.5 * x + rng.normal(0.0, 1.0),
            })
    return pd.DataFrame(rows)


def test_design_shape_and_columns():
    panel = _toy_panel(n_dates=3, n_symbols=2)
    X = build_quantile_design(panel, "reciprocity_z")
    # const + feature + 2 controls + (2-1) symbol dummies + (3-1) date dummies
    assert X.shape == (6, 7)
    assert list(X.columns[:3]) == ["const", "reciprocity_z",
                                   "log_volume_z"]
    assert sum(c.startswith("sym_") for c in X.columns) == 1
    assert sum(c.startswith("d_") for c in X.columns) == 2
    assert np.isfinite(X.to_numpy(dtype=float)).all()


def test_known_median_slope_is_recovered():
    panel = _toy_panel()
    rec = fit_quantile(panel, "y", "reciprocity_z", tau=0.50)
    assert rec["beta"] == pytest.approx(1.5, abs=0.20)
    assert rec["n_obs"] == len(panel)
    assert rec["converged"] is True
    assert rec["ci_lo_bp"] < rec["beta_bp"] < rec["ci_hi_bp"]


def test_checkpoint_resume_does_not_refit(monkeypatch, tmp_path):
    panel = _toy_panel(n_dates=3, n_symbols=4)
    calls = []

    def fake_fit(panel, outcome, feature_col, tau, controls=(), **kwargs):
        calls.append(float(tau))
        return {
            "tau": float(tau), "beta": 0.001 * tau, "beta_bp": 10.0 * tau,
            "se_bp": 1.0, "p_robust": 0.05, "ci_lo_bp": 10.0 * tau - 2.0,
            "ci_hi_bp": 10.0 * tau + 2.0, "n_obs": len(panel),
            "pseudo_r2": 0.1, "iterations": 3, "converged": True,
            "fit_seconds": 0.0,
        }

    monkeypatch.setattr(qp, "fit_quantile", fake_fit)
    ckpt = tmp_path / "checkpoint.csv"
    grid = [("H10", "reciprocity", "abs_ret_fwd1", "pos")]
    first = run_quantile_grid(panel, grid, ckpt, taus=(0.25, 0.75))
    assert len(calls) == 2 and len(first) == 2

    second = run_quantile_grid(panel, grid, ckpt, taus=(0.25, 0.75))
    assert len(calls) == 2  # both rows replayed from the checkpoint
    pd.testing.assert_frame_equal(first, second)


def _q_rows(test_id, b10, b50, b90, lo10, hi10, lo90, hi90):
    rows = []
    for tau, val, lo, hi in (
        (0.10, b10, lo10, hi10),
        (0.25, b50, b50 - 1.0, b50 + 1.0),
        (0.50, b50, b50 - 1.0, b50 + 1.0),
        (0.75, b90, b90 - 1.0, b90 + 1.0),
        (0.90, b90, lo90, hi90),
    ):
        rows.append({
            "test_id": test_id, "tau": tau, "beta_bp": val,
            "ci_lo_bp": lo, "ci_hi_bp": hi, "p_robust": 0.01,
        })
    return rows


def test_tail_labels_use_ci_and_v1_reference_sign():
    q = pd.DataFrame(
        _q_rows("BOTH", 2.0, 4.0, 8.0, 1.0, 3.0, 7.0, 9.0)
        + _q_rows("LOWER", -2.0, -1.0, 1.0, -3.0, -1.0, -1.0, 2.0)
        + _q_rows("UPPER", 1.0, 3.0, 5.0, -1.0, 2.0, 4.0, 6.0)
        + _q_rows("NONE", 1.0, 2.0, 3.0, -1.0, 2.0, -1.0, 5.0)
        + _q_rows("MIXED", -2.0, 0.0, 1.0, -3.0, -1.0, -1.0, 2.0)
        + _q_rows("HUMP", 1.0, 3.0, 2.0, 0.5, 1.5, 1.5, 2.5)
    )
    base = {"BOTH": 10.0, "LOWER": -10.0, "UPPER": 10.0,
            "NONE": 10.0, "MIXED": 10.0, "HUMP": 10.0}
    t = tail_summary(q, base).set_index("test_id")

    assert t.loc["BOTH", "tail_classification"] == "BOTH_TAILS"
    assert t.loc["LOWER", "tail_classification"] == "LOWER_TAIL"
    assert t.loc["UPPER", "tail_classification"] == "UPPER_TAIL"
    assert t.loc["NONE", "tail_classification"] == "NONE"
    assert t.loc["MIXED", "tail_classification"] == "TAIL_MIXED"

    assert t.loc["BOTH", "tail_shape"] == "INCREASING"
    assert t.loc["HUMP", "tail_shape"] == "HUMP"
    assert t.loc["BOTH", "beta_ratio_90_10"] == pytest.approx(4.0)
    assert bool(t.loc["BOTH", "lower_ci_excludes_0"]) is True
    assert bool(t.loc["BOTH", "upper_ci_excludes_0"]) is True
    assert bool(t.loc["LOWER", "lower_ci_excludes_0"]) is True
    assert bool(t.loc["LOWER", "upper_ci_excludes_0"]) is False
    assert t.loc["BOTH", "base_bp_v1"] == pytest.approx(10.0)
    assert set(TAUS) == {0.10, 0.25, 0.50, 0.75, 0.90}
