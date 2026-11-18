"""Daily graph metrics (density, reciprocity, degree/strength, betweenness)."""
from __future__ import annotations

import networkx as nx


def density(G: nx.DiGraph) -> float:
    return nx.density(G)


def reciprocity_volume(G: nx.DiGraph) -> float:
    """Share of directed edge VOLUME that flows on bidirectional pairs.

    Definition (feature dictionary / analysis plan):
        2 * sum_{unordered i<j} min(w_ij, w_ji) / sum(all edge weights)

    The minimum is the matched bidirectional flow for one unordered pair,
    doubled so a perfectly symmetric pair counts exactly once per direction.
    Self-loops (broker i trading with itself) are NOT bidirectional broker
    pairs: they remain in the denominator (total volume) but are excluded from
    the numerator. Each unordered pair is counted once.

    Correction note (v2.1.0): the previous implementation iterated over both
    directed edges, added the minimum twice, then multiplied by two again —
    returning 4*min/total and up to 2.0 for a perfectly symmetric two-broker
    graph. It also counted self-loops as reciprocal pairs. See
    `reports/reciprocity_correction.md`.
    """
    tot = sum(d.get("weight", 1.0) for _, _, d in G.edges(data=True))
    if tot <= 0:
        return 0.0
    matched = 0.0
    seen: set[tuple] = set()
    for u, v, d in G.edges(data=True):
        if u == v:
            continue  # self-loop: denominator only, never a reciprocal pair
        if (v, u) in seen:
            continue  # this unordered pair was already counted
        seen.add((u, v))
        if G.has_edge(v, u):
            matched += min(d.get("weight", 1.0),
                           G[v][u].get("weight", 1.0))
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
