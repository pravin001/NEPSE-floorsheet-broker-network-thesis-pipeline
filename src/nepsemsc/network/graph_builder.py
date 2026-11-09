"""Daily directed weighted broker graph from AGGREGATED edge lists only."""
from __future__ import annotations

import pandas as pd
import networkx as nx


def build_directed_weighted_graph(
    edges: pd.DataFrame,
    source_col: str = "buyer_broker_id",
    target_col: str = "seller_broker_id",
    weight_col: str = "pair_volume",
    aggregate: bool = True,
) -> nx.DiGraph:
    """Buyer → seller directed graph, edge weight = summed broker-pair volume.

    `edges` must ALREADY be an aggregated pair-level table (Module 1 SQL) —
    raw trade rows are never passed here (performance rule). Self-loops
    (broker trading with itself) are legal edges in the network object and
    are also tracked separately in the feature table.
    """
    if (aggregate and {source_col, target_col} <= set(edges.columns)
            and len(edges) > 1):
        agg_cols = [source_col, target_col]
        edges = edges.groupby(agg_cols, observed=True)[weight_col].sum().reset_index()
    G = nx.DiGraph()
    for src, tgt, w in zip(edges[source_col], edges[target_col], edges[weight_col]):
        if G.has_edge(src, tgt):
            G[src][tgt]["weight"] += float(w)
        else:
            G.add_edge(src, tgt, weight=float(w))
    return G


def edges_from_frame(frame: pd.DataFrame, date, symbol: str | None = None) -> pd.DataFrame:
    """Filter the broker-pair daily table to ONE (symbol, date) slice."""
    m = frame["date"] == date
    if symbol is not None:
        m &= frame["symbol"] == symbol
    return frame.loc[m]
