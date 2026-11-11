"""Liquidity proxies for the v2 Stage-2 robustness battery (plan V2-2).

Pre-declared constructions (docs/analysis_plan_v2_extension.md, before any
Stage-2 result):

  * Amihud illiquidity = 1e6 * |ret_t| / rupee turnover_t. The floorsheet
    `amount` is not carried on the frozen outcome panel, so the declared
    fallback is used: OHLCV `turnover` (= close x volume), tagged
    `amihud_value_source = ohlcv_turnover`. Zero/NaN turnover -> NaN.
  * Roll implied spread = 2 * sqrt(max(0, -Cov(dp_t, dp_{t-1}))), where
    dp is the first difference of close, 20-session rolling window
    (min_periods=10) within each symbol's own session adjacency. Expressed
    RELATIVE to close (`roll_spread = spread / close`) so that the proxy is
    comparable across price levels; implementation note logged (deviation
    #15). Values clipped at 0 only (negative covariance => no spread).
  * Corwin-Schultz (2012) two-day high/low estimator, computed on the
    TRAILING pair (t-1, t) and averaged over a trailing 20-pair window
    (min_periods=10) so that no future high/low enters a date-t feature;
    negative alpha estimates set to 0.0 as published.
  * Effective tick proxy (Goyenko-Holden-Trzcinka 2009 style) = minimum tick
    / close. The NEPSE tick grid is inferred from the official price bands
    (< Rs 100 -> Rs 0.10; >= Rs 100 -> Rs 1.00) and verified empirically on
    the top-12 floorsheet extracts (all observed trade prices are integer
    rupees; deviation #15 note). Relative tick = tick_size(close)/close.

All features are point-in-time (no future data) and get TRAIN-fold
winsor(1/99)+z standardization downstream via the shared
`train_fold_stats`/`standardize_test` machinery.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LIQUIDITY_COLS = ["amihud", "roll_spread", "corwin_schultz", "effective_tick"]
# effective_tick is a diagnostic/price-discreteness control, not part of the
# three-gamma controlled specification (plan V2-2 names amihud/roll/cs).
LIQUIDITY_GAMMAS = ["amihud", "roll_spread", "corwin_schultz"]

ROLL_WINDOW = 20
ROLL_MIN_PERIODS = 10
CS_WINDOW = 20
CS_MIN_PERIODS = 10
_CS_DEN = 3.0 - 2.0 * np.sqrt(2.0)


def tick_size(price: np.ndarray | pd.Series) -> np.ndarray:
    """NEPSE price-band tick grid (declared): 0.10 below Rs 100, else 1.00.

    Empirically, every trade price in the top-12 floorsheet extracts is an
    integer rupee value (see module docstring), so the >=100 band applies to
    the whole OOS universe.
    """
    p = np.asarray(price, dtype=float)
    return np.where(p < 100.0, 0.1, 1.0)


def amihud_illiquidity(ret: np.ndarray | pd.Series,
                       turnover: np.ndarray | pd.Series,
                       scale: float = 1e6) -> np.ndarray:
    """1e6 * |ret| / turnover; non-positive or missing turnover -> NaN."""
    r = np.asarray(ret, dtype=float)
    v = np.asarray(turnover, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = scale * np.abs(r) / v
    return np.where(np.isfinite(out) & (v > 0), out, np.nan)


def roll_implied_spread(close: np.ndarray | pd.Series,
                        window: int = ROLL_WINDOW,
                        min_periods: int = ROLL_MIN_PERIODS
                        ) -> tuple[np.ndarray, np.ndarray]:
    """(spread, relative_spread) from the Roll (1984) autocovariance.

    `close` must be one symbol's sessions in date order. spread is in price
    units; relative_spread = spread / close. Missing/insufficient history
    yields NaN. Negative autocovariance implies a positive spread; positive
    autocovariance is clipped to 0.
    """
    c = pd.Series(np.asarray(close, dtype=float))
    dp = c.diff()
    cov = dp.rolling(window, min_periods=min_periods).cov(dp.shift(1))
    spread = 2.0 * np.sqrt(np.clip(-cov.to_numpy(), 0.0, None))
    spread = np.where(np.isfinite(spread), spread, np.nan)
    rel = spread / c.to_numpy()
    return spread, rel


def corwin_schultz(high: np.ndarray | pd.Series,
                   low: np.ndarray | pd.Series,
                   window: int = CS_WINDOW,
                   min_periods: int = CS_MIN_PERIODS) -> np.ndarray:
    """Trailing two-day Corwin-Schultz effective spread (as published).

    For date t the pair is (t-1, t): beta uses the squared log high/low
    ranges of both days, gamma the squared log range of the two-day envelope.
    alpha <= 0 -> 0.0 (published convention). The daily series is the trailing
    `window`-pair mean (min_periods) to avoid look-ahead.
    """
    h = pd.Series(np.asarray(high, dtype=float))
    l = pd.Series(np.asarray(low, dtype=float))
    hl = np.log(h / l)
    beta = hl.pow(2) + hl.shift(1).pow(2)
    h_max = h.combine(h.shift(1), max)
    l_min = l.combine(l.shift(1), min)
    env = np.log(h_max / l_min)
    gamma = env.pow(2)
    with np.errstate(invalid="ignore"):
        alpha = ((np.sqrt(2.0 * beta) - np.sqrt(beta)) / _CS_DEN
                 - np.sqrt(gamma / _CS_DEN))
    s = 2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))
    s = s.where(alpha > 0.0, 0.0)
    s = s.where(beta.notna() & gamma.notna(), np.nan)
    s = s.clip(lower=0.0, upper=1.0)
    return s.rolling(window, min_periods=min_periods).mean().to_numpy()


def build_liquidity_features(outcomes: pd.DataFrame,
                             ohlcv: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per (date, symbol) with the four proxies.

    `outcomes` supplies close/ret/turnover; `ohlcv` supplies high/low (and is
    the fallback source of turnover). The function never sorts away the
    caller's keys: output is (date, symbol, amihud, roll_spread,
    corwin_schultz, effective_tick).
    """
    o = outcomes[["date", "symbol", "close", "ret", "turnover"]].copy()
    o["date"] = pd.to_datetime(o["date"]).dt.date
    if ohlcv is not None:
        h = ohlcv[["date", "symbol", "high", "low"]].copy()
        h["date"] = pd.to_datetime(h["date"]).dt.date
        o = o.merge(h, on=["date", "symbol"], how="left")
    else:
        o["high"] = np.nan
        o["low"] = np.nan

    parts = []
    for sym, g in o.groupby("symbol", observed=True, sort=False):
        g = g.sort_values("date")
        close = g["close"].to_numpy(dtype=float)
        _, roll_rel = roll_implied_spread(close)
        cs = corwin_schultz(g["high"].to_numpy(dtype=float),
                            g["low"].to_numpy(dtype=float))
        parts.append(pd.DataFrame({
            "date": g["date"].to_numpy(),
            "symbol": sym,
            "amihud": amihud_illiquidity(g["ret"].to_numpy(dtype=float),
                                         g["turnover"].to_numpy(dtype=float)),
            "roll_spread": roll_rel,
            "corwin_schultz": cs,
            "effective_tick": tick_size(close) / close,
        }))
    out = pd.concat(parts, ignore_index=True)
    return out[["date", "symbol", *LIQUIDITY_COLS]]


def liquidity_row_accounting(panel: pd.DataFrame,
                             cols: list[str] | None = None) -> pd.DataFrame:
    """Coverage of each proxy plus the complete-case count on the panel."""
    cols = LIQUIDITY_COLS if cols is None else cols
    rows = []
    for c in cols:
        rows.append({"item": c, "non_null": int(panel[c].notna().sum()),
                     "rows": len(panel),
                     "share": float(panel[c].notna().mean())})
    complete = panel[cols].notna().all(axis=1)
    rows.append({"item": "complete_cases", "non_null": int(complete.sum()),
                 "rows": len(panel), "share": float(complete.mean())})
    return pd.DataFrame(rows)
