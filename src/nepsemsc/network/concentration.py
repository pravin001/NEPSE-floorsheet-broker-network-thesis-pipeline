"""Concentration metrics — pandas reference implementations.

Production path is the DuckDB SQL in `nepsemsc.data.aggregations` (heavy data
NEVER loads into pandas — brief rule 1). These pure-pandas versions exist so
unit tests can verify the METRIC DEFINITIONS on toy data, and so Phase 3 can
cross-check a sample of the SQL results against a second implementation.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


def hhi_from_volumes(series: pd.Series) -> float:
    """Herfindahl-Hirschman index from integer volume counts: sum of squared
    volume shares. Equal 4 brokers → 0.25; sole broker → 1.0."""
    total = float(series.sum())
    if total <= 0:
        return float("nan")
    shares = series.astype("float64") / total
    return float((shares**2).sum())


def buyer_hhi_by_day(df: pd.DataFrame) -> pd.DataFrame:
    """Per (symbol, date) buyer-side HHI."""
    s = df.groupby(["symbol", "date", "buyer_broker_id"], observed=True)["volume"].sum()
    idx = ["symbol", "date"]
    per = (s.reset_index().groupby(idx, observed=True))
    out = per.apply(lambda g: hhi_from_volumes(g.set_index("buyer_broker_id")["volume"]))
    return out.rename("buyer_hhi").reset_index()


def seller_hhi_by_day(df: pd.DataFrame) -> pd.DataFrame:
    """Per (symbol, date) seller-side HHI."""
    s = df.groupby(["symbol", "date", "seller_broker_id"], observed=True)["volume"].sum()
    per = (s.reset_index().groupby(["symbol", "date"], observed=True))
    out = per.apply(lambda g: hhi_from_volumes(g.set_index("seller_broker_id")["volume"]))
    return out.rename("seller_hhi").reset_index()


def self_loop_volume_ratio(
    df: pd.DataFrame,
    buyer_col: str = "buyer_broker_id",
    seller_col: str = "seller_broker_id",
    volume_col: str = "volume",
    by: list[str] | None = None,
) -> pd.DataFrame | float:
    """Share of volume where buyer broker == seller broker, per day when `by`
    given else scalar. Label regime (R12): this is SELF-LOOP VOLUME — do not
    call it 'wash trading'. Zero-volume daily groups return NaN (guard).
    """
    loop_mask = df[buyer_col] == df[seller_col]

    def _ratio(g: pd.DataFrame) -> float:
        tot = float(g[volume_col].sum())
        if tot <= 0:
            return math.nan
        return float(g.loc[g[buyer_col] == g[seller_col], volume_col].sum() / tot)

    if by is None:
        return _ratio(df)
    return df.groupby(by, observed=True).apply(_ratio).rename("self_loop_volume_ratio").reset_index()


def top_k_share(
    df: pd.DataFrame, id_col: str = "buyer_broker_id", k: int = 3, by=("symbol", "date")
) -> pd.DataFrame:
    """Share of daily volume routed through the k largest brokers on that side."""
    s = df.groupby([*by, id_col], observed=True)["volume"].sum().reset_index()
    rank = s.groupby([*by], observed=True)["volume"].rank(ascending=False)
    s = s.assign(_rk=rank)
    top = s[s["_rk"] <= k].groupby([*by], observed=True)["volume"].sum()
    total = s.groupby([*by], observed=True)["volume"].sum()
    out = (top / total).rename(f"top_{k}_{id_col}_share").reset_index()
    return out


def end_of_day_concentration(
    df: pd.DataFrame,
    contract_col: str = "contract_no",
    top_pct: float = 0.05,
    by=("symbol", "date"),
) -> pd.DataFrame:
    """Share of daily volume in the top `top_pct` of trades BY contract_no.

    Ordering discipline: rows are sorted by contract_no INSIDE this function
    (NEPSE archive file order is not execution order — validated by the
    sibling project). `ceil` keeps at least one trade in the tail for any
    group size.
    """
    def _one(g: pd.DataFrame) -> float:
        s = g.sort_values(contract_col)
        n = len(s)
        if n == 0:
            return math.nan
        k = max(1, math.ceil(top_pct * n))
        tot = float(s["volume"].sum())
        if tot <= 0:
            return math.nan
        return float(s["volume"].tail(k).sum() / tot)

    return df.groupby([*by], observed=True).apply(_one).rename("end_of_day_concentration").reset_index()
