"""SE specification guard tests (R3): forbidden SEs raise; the allowed
Driscoll-Kraay path runs on a synthetic panel; double-cluster path returns."""
import numpy as np
import pandas as pd
import pytest

linearmodels = pytest.importorskip("linearmodels")
pandas = pd


@pytest.fixture
def synth_panel():
    rng = np.random.default_rng(3)
    ents = [f"S{i:02d}" for i in range(12)]
    times = list(pd.bdate_range("2023-01-02", periods=48).date)
    frames = []
    for e in ents:
        f = pd.DataFrame({"symbol": e, "date": times})
        f["x"] = rng.normal(0, 1, len(times))
        e_eff = rng.normal(0, 0.3)
        f["y"] = 0.5 * f["x"] + e_eff + 0.01 * np.arange(len(times)) + rng.normal(0, 0.5, len(times))
        frames.append(f)
    return pandas.concat(frames, ignore_index=True)


def test_forbidden_se_raises():
    from nepsemsc.ml.panel_regression import ensure_valid_se
    for bad in ("robust", "hc1", "hc0", "unadjusted", "plain"):
        with pytest.raises(ValueError):
            ensure_valid_se(bad)
    assert ensure_valid_se("driscoll_kraay") == "driscoll_kraay"


def test_driscoll_kraay_runs(synth_panel):
    from nepsemsc.ml.panel_regression import fit_driscoll_kraay
    res = fit_driscoll_kraay(synth_panel, outcome="y", feature_cols=["x"],
                             bandwidth=5, entity_effects=True, time_effects=True)
    params = {str(i) for i in res.params.index}
    assert "x" in params
    assert abs(float(res.params.loc["x"]) - 0.5) < 0.15
    assert getattr(res, "cov_type_used") == "driscoll_kraay"


def test_double_clustered_runs(synth_panel):
    from nepsemsc.ml.panel_regression import fit_double_clustered
    res = fit_double_clustered(synth_panel, outcome="y", feature_cols=["x"])
    assert "x" in {str(i) for i in res.params.index}
    assert res.cov_type_used.startswith("double_clustered")


def test_fama_macbeth_recovers_beta(synth_panel):
    from nepsemsc.ml.panel_regression import fit_fama_macbeth
    out = fit_fama_macbeth(synth_panel, outcome="y", feature_cols=["x"])
    st = out["coef_stats"]["x"]
    assert abs(st["beta"] - 0.5) < 0.15
    assert st["se"] > 0
