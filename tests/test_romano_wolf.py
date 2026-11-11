"""v2 Stage-1 Romano-Wolf step-down tests (plan V2-1.2)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import pytest

from nepsemsc.evaluation._panel_boot import (build_bundle, pseudo_draws,
                                             slow_pseudo_refit)
from nepsemsc.evaluation.romano_wolf import (bootstrap_family, stepdown,
                                             wild_pvalue)


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    rng = np.random.default_rng(20261112)
    rows = []
    for s in range(8):
        for d in range(30):
            rows.append({"symbol": f"S{s:02d}",
                         "date": pd.Timestamp("2022-01-01") + pd.Timedelta(days=d),
                         "x": rng.normal(), "c1": rng.normal(), "c2": rng.normal()})
    p = pd.DataFrame(rows)
    p["y1"] = 0.3 * p["x"] - 0.2 * p["c1"] + rng.normal(size=len(p))
    p["y2"] = -0.1 * p["x"] + 0.4 * p["c2"] + rng.normal(size=len(p))
    return p.sort_values(["symbol", "date"]).reset_index(drop=True)


def test_stepdown_hand_computed_example():
    p_obs = np.array([0.01, 0.04, 0.03])
    p_boot = np.array([
        [0.005, 0.20, 0.10],
        [0.020, 0.01, 0.50],
        [0.500, 0.50, 0.005],
        [0.900, 0.90, 0.90],
    ])
    out = stepdown(p_obs, p_boot)
    assert out["order_ascending_p"].tolist() == [1, 3, 2]
    assert out["rw_p"].to_numpy() == pytest.approx([0.8, 0.8, 0.8])
    assert out["rw_p_literal_minp_fullset"].to_numpy() == pytest.approx(
        [0.8, 0.8, 0.8])
    assert (out["rw_p"].to_numpy() >= p_obs).all()


def test_stepdown_is_monotone_in_ascending_raw_p():
    rng = np.random.default_rng(7)
    p_obs = np.sort(rng.uniform(size=10))
    p_boot = rng.uniform(size=(200, 10))
    out = stepdown(p_obs, p_boot)
    order = np.argsort(p_obs)
    assert np.all(np.diff(out["rw_p"].to_numpy()[order]) >= -1e-15)
    assert out["rw_p"].between(0.0, 1.0).all()


def test_stepdown_known_null_is_not_significant():
    rng = np.random.default_rng(11)
    p_obs = np.full(5, 0.52)
    p_boot = rng.uniform(0.01, 0.99, size=(300, 5))
    out = stepdown(p_obs, p_boot)
    assert (out["rw_p"] > 0.10).all()


def test_wild_pvalue_convention():
    t_boot = np.array([-1.0, 0.0, 1.0])
    assert wild_pvalue(t_boot, 0.5) == pytest.approx(3.0 / 4.0)  # 2 hits
    assert wild_pvalue(t_boot, 2.0) == pytest.approx(1.0 / 4.0)  # no hits
    assert wild_pvalue(t_boot, 0.0) == pytest.approx(1.0)        # all 3


def test_bootstrap_family_shapes_and_checkpoint(panel, tmp_path):
    b1, _ = build_bundle(panel, "y1", ["x", "c1", "c2"],
                         test_id="T1", feature="x")
    b2, _ = build_bundle(panel, "y2", ["x", "c1", "c2"],
                         test_id="T2", feature="x")
    cp = tmp_path / "rw_checkpoint.csv"
    seeds = [910_001 + i for i in range(30)]
    out = bootstrap_family([b1, b2], seeds, chunk_size=10,
                           checkpoint_path=cp)
    assert out["t_boot"].shape == (30, 2)
    assert out["p_boot"].shape == (30, 2)
    assert np.isfinite(out["t_boot"]).all()
    assert np.isfinite(out["p_boot"]).all()
    assert cp.is_file()
    assert np.allclose(out["t_obs"], [b1.t_obs[0], b2.t_obs[0]])
    stepped = stepdown(out["p_obs"], out["p_boot"])
    assert stepped["rw_p"].between(0.0, 1.0).all()


def test_engine_pseudo_draws_match_full_refits(panel):
    b, _ = build_bundle(panel, "y1", ["x", "c1", "c2"],
                        test_id="T1", feature="x")
    rng = np.random.default_rng(321)
    eta = (rng.integers(0, 2, size=(2, len(panel))) * 2 - 1).astype(np.int8)
    draws = pseudo_draws(b, eta)
    for d in range(2):
        ref = slow_pseudo_refit(panel, b, eta[d].astype(float) * b.e_w)
        for j, col in enumerate(b.col_names):
            assert b.beta[j] + draws["delta"][d, j] == pytest.approx(
                float(ref.params[col]), rel=1e-8)
            assert draws["se"][d, j] == pytest.approx(
                float(ref.std_errors[col]), rel=1e-8)
