"""v2 Stage-2 wild-cluster-bootstrap and clustered-SE tests (plan V2-2).

Pins:
  * the (1+#)/(B+1) two-sided p convention;
  * Rademacher cluster weights: one sign per SYMBOL per draw, deterministic;
  * the hard engine gate against FULL entity-clustered PanelOLS refits;
  * the observed t uses the same entity-clustered estimator as the draws;
  * the v1 `fit_double_clustered` fallback is preserved bit-for-bit (the
    frozen v1 `p_dc` column equals DK; deviation #15), while the v2 wrapper
    executes a genuine two-way cluster.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import pytest

from nepsemsc.evaluation._panel_boot import build_bundle
from nepsemsc.evaluation.wild_bootstrap import (bootstrap_wild_cluster,
                                                cluster_weights,
                                                validate_cluster_engine,
                                                wild_cluster_p)
from nepsemsc.ml.panel_regression import (fit_cluster_entity,
                                          fit_double_clustered,
                                          fit_double_clustered_v2,
                                          fit_driscoll_kraay)


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    rng = np.random.default_rng(20261113)
    rows = []
    entity_effect = {f"S{s:02d}": rng.normal(scale=0.5) for s in range(8)}
    for s in range(8):
        sym = f"S{s:02d}"
        for d in range(36):
            rows.append({"symbol": sym,
                         "date": pd.Timestamp("2022-01-01") + pd.Timedelta(days=d),
                         "x": rng.normal(), "c1": rng.normal(), "c2": rng.normal()})
    p = pd.DataFrame(rows)
    p["y1"] = (0.30 * p["x"] - 0.20 * p["c1"]
               + p["symbol"].map(entity_effect) + rng.normal(size=len(p)))
    p["y2"] = (0.10 * p["x"] + 0.40 * p["c2"]
               + p["symbol"].map(entity_effect) + rng.normal(size=len(p)))
    return p.sort_values(["symbol", "date"]).reset_index(drop=True)


@pytest.fixture(scope="module")
def bundles(panel):
    b1, _ = build_bundle(panel, "y1", ["x", "c1", "c2"], test_id="T1", feature="x")
    b2, _ = build_bundle(panel, "y2", ["x", "c1", "c2"], test_id="T2", feature="x")
    return [b1, b2]


def test_wild_cluster_p_convention():
    t = np.array([-1.0, 0.0, 1.0])
    assert wild_cluster_p(t, 0.5) == pytest.approx(3.0 / 4.0)   # 2 hits
    assert wild_cluster_p(t, 2.0) == pytest.approx(1.0 / 4.0)   # 0 hits
    assert wild_cluster_p(t, 0.0) == pytest.approx(1.0)         # all hit
    assert wild_cluster_p(t, -2.0) == pytest.approx(1.0 / 4.0)  # two-sided


def test_cluster_weights_one_rademacher_sign_per_symbol():
    seeds = [833_001, 833_002, 833_003]
    eta = cluster_weights(seeds, 12)
    assert eta.shape == (3, 12)
    assert set(np.unique(eta)).issubset({-1, 1})
    assert np.array_equal(eta, cluster_weights(seeds, 12))  # deterministic
    assert not np.array_equal(eta[0], eta[1])


def test_engine_gate_against_full_entity_clustered_refits(panel, bundles):
    worst = validate_cluster_engine(panel, bundles, [833_001, 833_002, 833_003])
    assert worst < 1e-8


def test_bootstrap_uses_entity_clustered_observed_statistic(panel, bundles):
    seeds = [833_001 + i for i in range(19)]
    out = bootstrap_wild_cluster(panel, bundles, seeds)
    assert out["B"] == 19
    assert out["n_clusters"] == 8
    assert out["t_boot"].shape == (19, 2)
    assert np.all(out["p_wb"] >= 1.0 / 20.0)
    assert np.all(out["p_wb"] <= 1.0)
    ref = fit_cluster_entity(panel, "y1", ["x", "c1", "c2"])
    assert out["t_obs"][0] == pytest.approx(float(ref.tstats["x"]))
    assert out["se_cluster_obs"][0] == pytest.approx(float(ref.std_errors["x"]))


def test_v1_double_cluster_wrapper_fallback_pinned(panel):
    cols = ["x", "c1", "c2"]
    dk = fit_driscoll_kraay(panel, "y1", cols, bandwidth=5)
    v1 = fit_double_clustered(panel, "y1", cols)
    assert v1.cov_type_used == "double_clustered_fallback_time_kernel"
    assert float(v1.pvalues["x"]) == pytest.approx(float(dk.pvalues["x"]),
                                                   rel=1e-12)


def test_v2_double_cluster_executes_two_way_and_differs_from_dk(panel):
    cols = ["x", "c1", "c2"]
    v2 = fit_double_clustered_v2(panel, "y1", cols)
    dk = fit_driscoll_kraay(panel, "y1", cols, bandwidth=5)
    assert v2.cov_type_used == "double_clustered_two_way_v2"
    assert np.isfinite(float(v2.pvalues["x"]))
    # with entity dependence the two-way SE must not silently equal the
    # time-kernel fallback (the exact v1 defect)
    assert float(v2.std_errors["x"]) != pytest.approx(
        float(dk.std_errors["x"]), rel=1e-9)
