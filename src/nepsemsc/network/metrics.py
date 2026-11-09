"""Daily graph metrics (density, reciprocity, degree/strength, betweenness)."""
from __future__ import annotations

import networkx as nx


def density(G: nx.DiGraph) -> float:
    return nx.density(G)


def reciprocity_volume(G: nx.DiGraph) -> float:
    """Share of directed edge VOLUME that flows on bidirectional pairs.

    Defined as 2 * sum(min(w_ij, w_ji)) / sum(all weights): the minimum is the
    matched bidirectional flow, doubled so a perfectly symmetric pair counts
    exactly once per direction beaten. Unweighted reciprocity (nx.reciprocity)
    is reported separately by `metrics_frame` for reference.
    """
    tot = sum(d.get("weight", 1.0) for _, _, d in G.edges(data=True))
    if tot <= 0:
        return 0.0
    matched = 0.0
    for u, v, d in G.edges(data=True):
        w_ij = d.get("weight", 1.0)
        if G.has_edge(v, u):
            matched += min(w_ij, G[v][u].get("weight", 1.0))
    return 2.0 * matched / tot


def degree_extremes(G: nx.DiGraph) -> dict:
    """Max in/out degree (counts) and max in/out STRENGTH (volume)."""
    if G.number_of_nodes() == 0:
        return {"max_in_degree": 0, "max_out_degree": 0, "max_in_strength": 0.0,
                "max_out_strength": 0.0}
    pins = dict(G.in_degree())
    pout = dict(G.out_degree())
    sins = dict(G.in_degree(weight="weight"))
    sout = dict(G.out_degree(weight="weight"))
    any_in = max(pins.values()) if pins else 0
    any_out = max(pout.values()) if pout else 0
    return {"max_in_degree": int(any_in), "max_out_degree": int(any_out),
            "max_in_strength": float(max(sins.values(), default=0.0)),
            "max_out_strength": float(max(sout.values(), default=0.0))}


def max_betweenness(G: nx.DiGraph, unweighted: bool = True, precision_k: int | None = None) -> float:
    """Max betweenness centrality; computed on the SMALL daily aggregated
    graph only. If the node count exceeds `precision_k`, k-sample approximation
    (seed fixed) is used, mirroring SV4 fallback (b).
    """
    if G.number_of_nodes() < 3:
        return 0.0
    import random  # lazy; the seed policy read happens at call time

    from nepsemsc.utils.seeds import GLOBAL_SEED

    if precision_k is not None and G.number_of_nodes() > precision_k:
        rng = random.Random(GLOBAL_SEED)
        bc = nx.betweenness_centrality(G, k=precision_k, seed=rng.randint(0, 2**32 - 1),
                                       normalized=True, weight=None if unweighted else "weight")
        return float(max(bc.values()))
    bc = nx.betweenness_centrality(G, normalized=True,
                                   weight=None if unweighted else "weight")
    return float(max(bc.values()))


def metrics_frame(G: nx.DiGraph) -> dict:
    """One (symbol, date) → dict of structural metrics."""
    m = dict(density=density(G),
             reciprocity_volume=reciprocity_volume(G))
    m.update(degree_extremes(G))
    m["max_betweenness"] = max_betweenness(G)
    m["n_nodes"] = G.number_of_nodes()
    m["n_edges"] = G.number_of_edges()
    return m
