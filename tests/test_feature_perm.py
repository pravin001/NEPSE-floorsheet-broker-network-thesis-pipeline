"""v2 Stage-1 feature-permutation engine tests (C3 + permutation schemes)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import pytest

from nepsemsc.evaluation import feature_perm as fp
from nepsemsc.evaluation._panel_boot import build_bundle
from nepsemsc.ml.panel_regression import fit_driscoll_kraay


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    rng = np.random.default_rng(20261111)
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


def test_permute_full_v1_reorders_the_v1_order_shuffle():
    arr = np.arange(12.0)
    order = np.array([4, 0, 11, 2, 7, 1, 9, 3, 10, 5, 8, 6])
    got = fp.permute_full_v1(arr, order, 12345)
    rng = np.random.default_rng(12345)
    expected = rng.permutation(arr)[order]
    assert np.array_equal(got, expected)
    assert sorted(got) == sorted(arr)


def test_permute_blocks_never_crosses_symbols_and_keeps_blocks():
    f = np.arange(17.0)
    symbols = np.array(["A"] * 10 + ["B"] * 7)
    out = fp.permute_blocks(f, symbols, 999, block=5)
    assert sorted(out) == sorted(f)
    a = out[:10]
    b = out[10:]
    assert (np.array_equal(a, np.arange(10))
            or np.array_equal(a, np.r_[np.arange(5, 10), np.arange(0, 5)]))
    assert (np.array_equal(b, np.arange(10, 17))
            or np.array_equal(b, np.r_[np.arange(15, 17), np.arange(10, 15)]))


def test_shares_are_sided_and_two_sided():
    pb = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    sh = fp.shares(pb, 1.0, "pos")
    assert sh["upper"] == pytest.approx(0.4)       # >= 1.0
    assert sh["lower"] == pytest.approx(0.8)       # <= 1.0
    assert sh["two_sided"] == pytest.approx(0.8)   # |b| >= 1.0
    assert sh["sided"] == pytest.approx(0.4)
    assert fp.shares(pb, 1.0, "neg")["sided"] == pytest.approx(0.8)


def test_wilson_ci_contains_share():
    lo, hi = fp.wilson_ci(25, 100)
    assert 0.0 <= lo < 0.25 < hi <= 1.0
    lo0, hi0 = fp.wilson_ci(0, 100)
    assert lo0 == pytest.approx(0.0, abs=1e-12)
    lo100, hi100 = fp.wilson_ci(100, 100)
    assert hi100 == pytest.approx(1.0, abs=1e-12)
    assert np.isnan(fp.wilson_ci(0, 0)[0])


def test_c3_engine_matches_full_refits(panel):
    b, _ = build_bundle(panel, "y1", ["x", "c1", "c2"],
                        test_id="T1", feature="x")
    eng = fp.make_perm_engine(panel, b, ["y1", "y2"])
    for seed in (101, 102):
        fperm = fp.permute_full(panel["x"].to_numpy(), seed)
        fast = fp.perm_fit(eng, fperm)
        base = panel.copy()
        base["x"] = fperm
        for j, outcome in enumerate(("y1", "y2")):
            res = fit_driscoll_kraay(base, outcome, ["x", "c1", "c2"],
                                     bandwidth=5)
            assert fast["beta"][j] == pytest.approx(
                float(res.params["x"]), rel=1e-8)
            assert fast["se"][j] == pytest.approx(
                float(res.std_errors["x"]), rel=1e-8)
            assert fast["t"][j] == pytest.approx(
                float(res.tstats["x"]), rel=1e-8)
