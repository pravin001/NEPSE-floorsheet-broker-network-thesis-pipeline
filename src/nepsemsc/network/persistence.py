"""Broker-pair persistence (R11 PhD-seed appendix) — DESCRIPTIVE ONLY.

Top-k brokers per (symbol, date) by combined buy+sell volume; day-over-day
Jaccard overlap of the top-k sets. DC1 note: for any FORMAL use these must be
computed on training-fold days; the thesis artefact is descriptive across the
full window and labelled as such.
"""
from __future__ import annotations

import pandas as pd


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    un = a | b
    if not un:
        return 0.0
    return len(a & b) / len(un)


def daily_topk_brokers(edges: pd.DataFrame, k: int = 10,
                       buyer_col: str = "buyer_broker_id",
                       seller_col: str = "seller_broker_id",
                       volume_col: str = "pair_volume") -> dict:
    """{date: set(top-k broker ids)} from aggregated broker-pair edges."""
    buy = edges.groupby("date", observed=True)[buyer_col].apply(list).to_dict()
    sell = edges.groupby("date", observed=True)[seller_col].apply(list).to_dict()
    out: dict = {}
    for date in sorted(set(buy) | set(sell)):
        g = edges[edges["date"] == date]
        vol = {}
        for _, r in g.iterrows():
            vol[r[buyer_col]] = vol.get(r[buyer_col], 0.0) + float(r[volume_col])
            vol[r[seller_col]] = vol.get(r[seller_col], 0.0) + float(r[volume_col])
        top = sorted(vol.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
        out[date] = {b for b, _ in top}
    return out


def broker_persistence(edges: pd.DataFrame, k: int = 10) -> pd.DataFrame:
    """Day-over-day Jaccard of the top-k broker sets."""
    tops = daily_topk_brokers(edges, k=k)
    dates = [d for d in sorted(tops)]
    rows = []
    for prev, cur in zip(dates[:-1], dates[1:]):
        rows.append({"date": cur, "jaccard_topk": jaccard(tops[prev], tops[cur])})
    return pd.DataFrame(rows)


def broker_persistence_summary(edges: pd.DataFrame, k: int = 10) -> dict:
    s = broker_persistence(edges, k=k)
    if s.empty:
        return {"n_day_pairs": 0, "mean_jaccard_topk": float("nan")}
    return {"n_day_pairs": int(len(s)),
            "mean_jaccard_topk": float(s["jaccard_topk"].mean())}
