"""v2 Stage-2 liquidity-proxy tests (plan V2-2).

Pins the pre-declared constructions AND the no-look-ahead property: every
proxy at date t may use only information up to and including t.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import pytest

from nepsemsc.features.liquidity import (LIQUIDITY_COLS, amihud_illiquidity,
                                         build_liquidity_features,
                                         corwin_schultz,
                                         liquidity_row_accounting,
                                         roll_implied_spread, tick_size)


def test_tick_size_price_bands():
    p = np.array([99.99, 100.0, 100.01, 1042.0])
    assert tick_size(p).tolist() == [0.1, 1.0, 1.0, 1.0]
    # scalar-shaped Series also accepted
    assert tick_size(pd.Series([50.0, 500.0])).tolist() == [0.1, 1.0]


def test_amihud_formula_and_invalid_turnover():
    ret = np.array([0.01, -0.02, 0.0, 0.03, 0.01])
    turn = np.array([1e6, 2e6, 1e6, 0.0, np.nan])
    out = amihud_illiquidity(ret, turn)
    assert out[0] == pytest.approx(1e6 * 0.01 / 1e6)
    assert out[1] == pytest.approx(1e6 * 0.02 / 2e6)
    assert out[2] == 0.0
    assert np.isnan(out[3]) and np.isnan(out[4])


def test_roll_spread_flat_prices_zero_and_relative_definition():
    close = np.full(40, 250.0)
    spread, rel = roll_implied_spread(close)
    assert np.nanmax(np.abs(spread)) == 0.0
    assert np.nanmax(np.abs(rel)) == 0.0

    rng = np.random.default_rng(3)
    close = 250.0 + np.cumsum(rng.normal(size=80))
    spread, rel = roll_implied_spread(close)
    ok = np.isfinite(spread)
    assert (spread[ok] >= 0).all()
    assert rel[ok] == pytest.approx(spread[ok] / close[ok])


def test_roll_spread_has_no_lookahead():
    rng = np.random.default_rng(4)
    close = 300.0 + np.cumsum(rng.normal(size=90))
    _, rel = roll_implied_spread(close)
    changed = close.copy()
    changed[-20:] += 25.0  # perturb only the FUTURE tail
    _, rel2 = roll_implied_spread(changed)
    assert np.allclose(rel[:-20], rel2[:-20], equal_nan=True)


def test_corwin_schultz_flat_prices_zero_and_range():
    n = 50
    flat = np.full(n, 300.0)
    cs = corwin_schultz(flat, flat)
    assert np.nanmax(np.abs(cs)) == 0.0

    rng = np.random.default_rng(5)
    mid = 300.0 + np.cumsum(rng.normal(scale=2.0, size=n))
    high = mid + rng.uniform(0.5, 3.0, size=n)
    low = mid - rng.uniform(0.5, 3.0, size=n)
    cs = corwin_schultz(high, low)
    ok = np.isfinite(cs)
    assert ok.sum() > 0
    assert (cs[ok] >= 0).all() and (cs[ok] <= 1).all()


def test_corwin_schultz_has_no_lookahead():
    n = 70
    rng = np.random.default_rng(6)
    mid = 400.0 + np.cumsum(rng.normal(size=n))
    high = mid + 1.0
    low = mid - 1.0
    cs = corwin_schultz(high, low)
    high2, low2 = high.copy(), low.copy()
    high2[-25:] += 10.0
    low2[-25:] -= 10.0
    cs2 = corwin_schultz(high2, low2)
    assert np.allclose(cs[:-25], cs2[:-25], equal_nan=True)


def test_build_liquidity_features_keys_and_columns():
    rng = np.random.default_rng(7)
    rows = []
    for sym, base in (("AAA", 250.0), ("BBB", 1200.0)):
        close = base + np.cumsum(rng.normal(scale=2.0, size=40))
        for i, c in enumerate(close):
            rows.append({
                "date": pd.Timestamp("2022-01-01") + pd.Timedelta(days=i),
                "symbol": sym, "close": c,
                "ret": rng.normal(scale=0.01),
                "turnover": float(rng.uniform(1e5, 1e7)),
                "high": c + rng.uniform(0.5, 2.0),
                "low": c - rng.uniform(0.5, 2.0),
            })
    out_df = pd.DataFrame(rows)
    liq = build_liquidity_features(out_df)
    assert list(liq.columns) == ["date", "symbol", *LIQUIDITY_COLS]
    assert len(liq) == len(out_df)
    assert set(liq["symbol"]) == {"AAA", "BBB"}
    # effective tick is exact by construction
    left = out_df[["date", "symbol", "close"]].copy()
    left["date"] = pd.to_datetime(left["date"]).dt.date
    m = liq.merge(left, on=["date", "symbol"])
    assert m["effective_tick"].to_numpy() == pytest.approx(
        tick_size(m["close"].to_numpy()) / m["close"].to_numpy())
    # high/low absent -> CS is entirely NaN (no silent fabrication)
    assert liq["corwin_schultz"].isna().all()


def test_liquidity_row_accounting_counts():
    p = pd.DataFrame({
        "amihud": [1.0, np.nan, 2.0, 3.0],
        "roll_spread": [1.0, 2.0, np.nan, 3.0],
        "corwin_schultz": [1.0, 2.0, 3.0, 4.0],
        "effective_tick": [1.0, 2.0, 3.0, np.nan],
    })
    t = liquidity_row_accounting(p).set_index("item")
    assert t.loc["amihud", "non_null"] == 3
    assert t.loc["roll_spread", "non_null"] == 3
    assert t.loc["corwin_schultz", "non_null"] == 4
    assert t.loc["complete_cases", "non_null"] == 1
    assert (t["rows"] == 4).all()
