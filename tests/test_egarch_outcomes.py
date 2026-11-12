"""EGARCH-standardized outcome tests (v2 Stage 3, plan V2-3.2).

Pins the numerical contract of `src/nepsemsc/models/egarch_outcomes.py`:
  * the manual variance recursion matches a hand-computed path (and, on a real
    synthetic fit, arch's own conditional-volatility path);
  * the underflow and extreme-z guards stop the forward filter and return NaN
    for the failure point and every later draw;
  * the parameter fit uses TRAIN-fold returns only (perturbing OOS returns
    leaves the fit diagnostics bit-identical while changing the z outcomes);
  * `abs_z_fwd1 = |z_fwd1|` and the `<60 train obs` exclusion is explicit.
"""
import numpy as np
import pandas as pd
import pytest

from nepsemsc.models.egarch_outcomes import (MIN_TRAIN_OBS, Z_NUMERIC_MAX,
                                             build_egarch_outcomes, fit_egarch,
                                             filter_forward,
                                             validate_recursion)


class _FakeRes:
    def __init__(self, sigma, resid):
        self.conditional_volatility = np.asarray(sigma, dtype=float)
        self.resid = np.asarray(resid, dtype=float)


def _synthetic_panel(seed: int = 7, n_train: int = 80, n_test: int = 20):
    rng = np.random.default_rng(seed)
    n = n_train + n_test
    ret = rng.normal(0.0, 0.01, n)
    dates = pd.bdate_range("2024-01-02", periods=n)
    scores = pd.DataFrame({
        "date": dates, "symbol": "AAA", "fold_id": 0,
        "is_train": [True] * n_train + [False] * n_test,
    })
    outcomes = pd.DataFrame({"date": dates, "symbol": "AAA", "ret": ret})
    return scores, outcomes


def test_filter_forward_matches_hand_recursion_and_return_scale():
    sig_last = 0.02
    z_last = 0.4
    res = _FakeRes(
        sigma=[0.01, 0.015, sig_last],
        resid=[0.0, 0.0, z_last * sig_last],
    )
    params = {"mu": 0.0, "omega": -0.05, "alpha": 0.12,
              "gamma": 0.03, "beta": 0.90}
    # raw returns ~1-2 bp against ~2 bp conditional sigma keep |z| < 20
    fwd = np.array([0.0001, -0.00005, 0.0002])
    got = filter_forward(res, params, fwd)

    log_s2 = np.log(sig_last ** 2)
    z = z_last
    expected = []
    e_abs = np.sqrt(2.0 / np.pi)
    for r in fwd:
        log_s2 = (params["omega"]
                  + params["alpha"] * (abs(z) - e_abs)
                  + params["gamma"] * z
                  + params["beta"] * log_s2)
        sigma = np.exp(0.5 * log_s2)          # in x100 return units
        expected.append(sigma / 100.0)        # returned in raw return units
        z = (r * 100.0 - params["mu"]) / sigma
    np.testing.assert_allclose(got, expected, rtol=1e-12, atol=0.0)


def test_sigma_underflow_stops_and_nans_all_later_draws():
    res = _FakeRes(sigma=[0.01, 0.01, 0.02], resid=[0.0, 0.0, 0.0])
    # omega so negative that the first recursion underflows exp() to 0.0
    params = {"mu": 0.0, "omega": -4000.0, "alpha": 0.0,
              "gamma": 0.0, "beta": 1.0}
    sig, info = filter_forward(res, params, np.array([0.0, 0.0, 0.0]),
                               return_info=True)
    assert info["stop_reason"] == "sigma_underflow"
    assert info["stop_index"] == 0
    assert np.isnan(sig).all()


def test_extreme_z_stops_and_nans_all_later_draws():
    res = _FakeRes(sigma=[0.01, 0.01, 0.02], resid=[0.0, 0.0, 0.0])
    params = {"mu": 0.0, "omega": -0.1, "alpha": 0.0,
              "gamma": 0.0, "beta": 0.9}
    # a +100% raw return against ~0.03% conditional sigma is >20 SD
    sig, info = filter_forward(res, params, np.array([1.0, 0.0]),
                               return_info=True)
    assert info["stop_reason"] == "extreme_z"
    assert info["stop_index"] == 0
    assert np.isnan(sig).all()
    assert Z_NUMERIC_MAX == 20.0


def test_fit_egarch_recursion_matches_arch_path():
    rng = np.random.default_rng(7)
    ret = rng.normal(0.0, 0.01, 100)
    res, params = fit_egarch(ret[:80])
    assert np.isfinite(list(params.values())).all()
    assert params["gamma"] == 0.0  # declared o=0 (symmetric EGARCH)
    rel = validate_recursion(res, params, ret[:80])
    assert rel < 1e-8


def test_build_outcomes_abs_mapping_and_boundary_accounting():
    scores, outcomes = _synthetic_panel(seed=7)
    z, log = build_egarch_outcomes(scores, outcomes)
    assert len(log) == 1
    assert int(log.loc[0, "n_train"]) == 80
    # the last OOS session has no next session -> its z cannot be formed
    assert int(log.loc[0, "n_usable_oos"]) == 19
    assert int(log.loc[0, "n_oos_excluded"]) == 1
    assert len(z) == 19
    np.testing.assert_allclose(z["abs_z_fwd1"], z["z_fwd1"].abs())
    assert z["z_fwd1"].notna().all()


def test_fit_is_train_only_perturbing_oos_returns_leaves_fit_diagnostics():
    scores, outcomes = _synthetic_panel(seed=7)
    z_a, log_a = build_egarch_outcomes(scores, outcomes)

    perturbed = outcomes.copy()
    mask = perturbed["date"] > outcomes.loc[79, "date"]
    perturbed.loc[mask, "ret"] = perturbed.loc[mask, "ret"] * 1.05
    z_b, log_b = build_egarch_outcomes(scores, perturbed)

    for col in ("n_train", "converged", "recursion_max_rel", "status",
                "n_oos", "n_usable_oos", "n_oos_excluded"):
        assert log_a.loc[0, col] == log_b.loc[0, col], col

    za = z_a.set_index("date")["z_fwd1"]
    zb = z_b.set_index("date")["z_fwd1"]
    common = za.index.intersection(zb.index)
    assert len(common) > 0
    assert not np.allclose(za.loc[common], zb.loc[common])


def test_fewer_than_min_train_observations_is_explicitly_counted():
    scores, outcomes = _synthetic_panel(seed=11, n_train=MIN_TRAIN_OBS - 1,
                                        n_test=10)
    z, log = build_egarch_outcomes(scores, outcomes)
    assert log.loc[0, "status"] == "fewer_than_min_train"
    assert int(log.loc[0, "n_train"]) == MIN_TRAIN_OBS - 1
    assert bool(log.loc[0, "flag_degenerate"]) is True
    assert z.empty
