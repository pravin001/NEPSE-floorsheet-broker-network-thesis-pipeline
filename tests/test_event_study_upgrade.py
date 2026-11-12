"""v2 Stage-4 event-study BMP/rank upgrade tests (plan V2-4)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm
from scipy import stats as sps

from nepsemsc.analysis.event_study_upgrade import (bmp_test, clustered_inference,
                                                   corrado_rank, reconstruct)


def test_bmp_test_matches_cross_sectional_t():
    scar = np.array([1.0, -1.0, 2.0, -2.0, 0.5, -0.5])
    out = bmp_test(scar)
    t = scar.mean() / (scar.std(ddof=1) / np.sqrt(len(scar)))
    assert out["t"] == pytest.approx(t)
    assert out["p"] == pytest.approx(2 * sps.t.sf(abs(t), len(scar) - 1))
    assert out["z"] == pytest.approx(scar.mean() * np.sqrt(len(scar)))


def test_corrado_rank_centres_on_expected_rank_sum():
    rank_sum = np.array([10.0, 12.0, 14.0])
    n_est = np.array([20.0, 20.0, 20.0])
    n_win = np.array([5.0, 5.0, 5.0])
    out = corrado_rank(rank_sum, n_est, n_win)
    expected = 5 * (20 + 5 + 1) / 2
    centered = rank_sum - expected
    z = centered.mean() / (centered.std(ddof=1) / np.sqrt(3))
    assert out["z"] == pytest.approx(z)
    assert out["n"] == 3


def _fixture(method: str = "market_model"):
    rng = np.random.default_rng(20261117)
    dates = pd.date_range("2021-01-04", periods=80, freq="B")
    ret = rng.normal(scale=0.01, size=80)
    mkt = rng.normal(scale=0.008, size=80)
    px = pd.DataFrame({"date": dates.date, "symbol": "AAA",
                       "ret": ret, "market_ret_loo": mkt})
    scores = pd.DataFrame({"date": [dates[70].date()], "symbol": ["AAA"],
                           "is_train": [False], "is_event": [True]})
    # replicate the v1 estimation rule: 60 non-event sessions before t0-5
    est_idx = list(range(5, 65))
    est = px.iloc[est_idx]
    if method == "market_model":
        X = sm.add_constant(est["market_ret_loo"].to_numpy(float),
                            has_constant="add")
        fit = sm.OLS(est["ret"].to_numpy(float), X).fit()
        alpha, beta = float(fit.params[0]), float(fit.params[1])
        ar = (px.iloc[65:76]["ret"].to_numpy(float)
              - alpha - beta * px.iloc[65:76]["market_ret_loo"].to_numpy(float))
    else:
        alpha = beta = np.nan
        ar = (px.iloc[65:76]["ret"].to_numpy(float)
              - px.iloc[65:76]["market_ret_loo"].to_numpy(float))
    cars = pd.DataFrame([{
        "date": dates[70].date(), "symbol": "AAA", "fold_id": 0,
        "method": method, "alpha_est": alpha, "beta_est": beta,
        "r2_est": 0.5, "n_est": 60, "n_window": 11,
        "car": float(np.nansum(ar)),
    }])
    return cars, px, scores


@pytest.mark.parametrize("method", ["market_model", "market_adjusted"])
def test_reconstruct_reproduces_stored_car_exactly(method):
    cars, px, scores = _fixture(method)
    aug, payload, ar_long = reconstruct(cars, px, scores)
    assert aug.iloc[0]["car_abs_diff"] == pytest.approx(0.0, abs=1e-14)
    assert np.isfinite(aug.iloc[0]["scar"])
    assert np.isfinite(aug.iloc[0]["rank_sum"])
    assert len(ar_long) == 11
    assert sorted(ar_long["lag"]) == list(range(-5, 6))


def test_clustered_inference_aggregates_to_dates():
    per_event = pd.DataFrame({
        "date": ["2021-01-04", "2021-01-04", "2021-01-05", "2021-01-06"],
        "car": [0.01, 0.03, -0.02, 0.00],
        "rank_sum": [10.0, 14.0, 8.0, 11.0],
        "rank_sum_ma": [9.0, 13.0, 7.0, 10.0],
        "n_est": [60.0] * 4,
        "n_window": [11.0] * 4,
    })
    out = clustered_inference(per_event)
    row = out.loc[out["statistic"] == "mean_car"].iloc[0]
    d = pd.Series([0.02, -0.02, 0.00])
    expected_t = d.mean() / (d.std(ddof=1) / np.sqrt(3))
    assert row["n_dates"] == 3
    assert row["mean"] == pytest.approx(d.mean())
    assert row["t"] == pytest.approx(expected_t)
    assert set(out["statistic"]) == {
        "mean_car", "corrado_rank_centered", "corrado_rank_centered_ma"}
