"""Data-quality audit primitives (pre-results, per DATA STRATEGY).

Rules fixed ONCE (SV7 pre-decision, configs/project.yaml):
  * missing broker ids  → rows are DROPPED for network analyses (unbiased,
    loses volume) and flagged; policy never switches mid-analysis.
  * duplicates          → keyed on (date, symbol, contract_no), first kept.
  * contract_no         → monotonicity ASSERTED per (symbol, date) after
    sorting; gaps documented (they do NOT break percentile-based ordering,
    but are reported per day because the EoD proxy depends on order).
  * low-activity days   → <100 trades flagged; inclusion rule decided
    pre-results (default: flag, include — decision recorded before Phase 4).
"""
from __future__ import annotations

import pandas as pd

DUPLICATE_KEYS = ["date", "symbol", "contract_no"]


def drop_duplicates_contract(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Dedupe on (date, symbol, contract_no); return (clean_frame, n_duplicates)."""
    before = len(df)
    clean = df.drop_duplicates(subset=DUPLICATE_KEYS, keep="first").copy()
    return clean, before - len(clean)


def missing_id_report(df: pd.DataFrame) -> dict:
    """Share of rows with missing buyer/seller broker id (overall + by date)."""
    n = len(df)
    out = {"n_rows": n}
    for col, key in (("buyer_broker_id", "missing_buyer_id"),
                     ("seller_broker_id", "missing_seller_id")):
        if col in df.columns:
            miss_id = (df[col].isna()) | (df[col] == "")
            n_miss = int(miss_id.sum())
            out[key] = {"n": n_miss, "share": (n_miss / n) if n else 0.0}
            by_date = df.assign(_miss=miss_id).groupby("date", observed=True)["_miss"].mean()
            out[key + "_by_date_max"] = float(by_date.max()) if len(by_date) else 0.0
    return out


def drop_missing_broker_ids(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """SV7 policy application: drop rows missing either broker id."""
    id_cols = [c for c in ("buyer_broker_id", "seller_broker_id") if c in df.columns]
    mask = pd.Series(False, index=df.index)
    for c in id_cols:
        mask |= df[c].isna() | (df[c] == "")
    clean = df.loc[~mask].copy()
    return clean, int(mask.sum())


def contract_monotonicity_report(df: pd.DataFrame) -> pd.DataFrame:
    """Per (symbol, date): is contract_no strictly increasing when SORTED,
    how many session gaps exist, and the max single gap.

    Gaps per (symbol, date) are expected (contract ids are daily-global, not
    per-symbol); we DOCUMENT them: the end-of-day proxy needs ordering after
    sort, not global continuity.
    """
    def _one(g: pd.DataFrame) -> pd.Series:
        s = g["contract_no"].sort_values()
        s = s.dropna().astype("int64")
        if len(s) < 2:
            return pd.Series({"n_trades": len(s), "strictly_increasing": True,
                              "n_gaps": 0, "n_decreases": 0, "max_gap": 0})
        d = s.diff().dropna()
        n_gaps = int((d > 1).sum())
        n_decr = int((d <= 0).sum())
        return pd.Series({"n_trades": len(s), "strictly_increasing": n_decr == 0,
                          "n_gaps": n_gaps, "n_decreases": n_decr,
                          "max_gap": int(d.max()) if len(d) else 0})

    return (df.groupby(["symbol", "date"], observed=True)
              .apply(_one)
              .reset_index())


def low_activity_days(df: pd.DataFrame, min_trades: int = 100) -> pd.DataFrame:
    """(symbol, date) combos with fewer than `min_trades` trades."""
    counts = df.groupby(["symbol", "date"], observed=True).size().rename("n_trades")
    low = counts[counts < min_trades].reset_index()
    return low


def ohlc_violation_report(ohlcv: pd.DataFrame) -> dict:
    """DC5-rate audit per tier: high >= max(open, close), low <= min(open,close)."""
    oh = ohlcv["high"].astype("float64")
    lo = ohlcv["low"].astype("float64")
    op = ohlcv["open"].astype("float64")
    cl = ohlcv["close"].astype("float64")
    n = len(ohlcv)
    viol_hi = int((oh < pd.concat([op, cl], axis=1).max(axis=1) - 1e-9).sum())
    viol_lo = int((lo > pd.concat([op, cl], axis=1).min(axis=1) + 1e-9).sum())
    return {"n_rows": n, "high_violations": viol_hi, "low_violations": viol_lo}
