"""Core-periphery coefficient — Borgatti-Everett pattern matching.

Discrete BE criterion (Borgatti & Everett 1999, Social Networks 21): for a
candidate partition, the ideal pattern is M_ij = 1 if both i,j are CORE;
M_ij = f if exactly one is core; M_ij = 0 if all-periphery pairs. Given a
partition, f* has the closed form mean(A) over cross pairs, clipped to [0,1].

We search partitions by Perron-vector order + threshold sweep:
  1. W = max-normalised symmetric weight matrix (both directions summed),
  2. v = leading eigenvector of the symmetric matrix (deterministic eigh —
     power iteration is NOT safe here: a bipartite star has eigenvalues
     ±λ of equal magnitude and oscillates),
  3. sweep m = 1..n over "core = top-m nodes by v",
  4. CP = 1 - SSE(f*, partition) / SSE(all-periphery null), in [0, 1].

Interpretation guard (R12): CP is a STRUCTURE description; high CP is
consistent with core-periphery organisation and with some manipulation-type
topologies, but is not evidence of manipulation by itself.
"""
from __future__ import annotations

import numpy as np
import networkx as nx


def _symmetric_weight_matrix(G: nx.DiGraph, nodes: list) -> np.ndarray | None:
    n = len(nodes)
    idx = {nd: i for i, nd in enumerate(nodes)}
    W = np.zeros((n, n), dtype="float64")
    for u, v, d in G.edges(data=True):
        w = float(d.get("weight", 1.0))
        W[idx[u], idx[v]] += w
        W[idx[v], idx[u]] += w  # symmetrise (buy-side and sell-side of a pair)
    W = np.clip(W, 0.0, None)
    wmax = W.max()
    if not np.isfinite(wmax) or wmax <= 0:
        return None
    return W / wmax


def _leading_eigenvector(W: np.ndarray) -> np.ndarray:
    """Deterministic leading eigenvector of a symmetric matrix.

    np.linalg.eigh is used (stable + reproducible). Power iteration was
    abandoned deliberately: symmetric matrices with spectrum symmetric about
    zero (stars/bipartite tops are common in broker networks) oscillate
    between ±v and never converge.
    """
    vals, vecs = np.linalg.eigh(W)
    v = vecs[:, int(np.argmax(vals))]
    return np.abs(v)


def borgatti_everett_score(G: nx.DiGraph, return_core: bool = False):
    """(core_periphery_coefficient in [0,1], optimal core node list, best m)."""
    nodes = list(G.nodes())
    n = len(nodes)
    if n == 0:
        return (0.0, [], 0) if return_core else 0.0
    W = _symmetric_weight_matrix(G, nodes)
    if W is None:
        return (0.0, [], 0) if return_core else 0.0
    A = W.copy()
    np.fill_diagonal(A, 0.0)

    sse_null = float((A**2).sum())
    if sse_null <= 0:
        return (0.0, [], 0) if return_core else 0.0

    v = _leading_eigenvector(A)
    order = list(np.lexsort((np.arange(n), -v)))  # stable descending sort

    best_sse, best_f, best_m, best_core = float("inf"), 0.0, 0, []
    iu0, iu1 = np.triu_indices(n, 1)
    a_flat = A[iu0, iu1]
    for m in range(1, n + 1):
        in_core = np.zeros(n, dtype=bool)
        in_core[order[:m]] = True
        core_i = in_core[iu0]
        core_j = in_core[iu1]
        cross = (core_i & ~core_j) | (~core_i & core_j)
        both = core_i & core_j
        n_cross = int(cross.sum())
        f = float(np.clip(a_flat[cross].mean() if n_cross else 0.0, 0.0, 1.0))
        sse = (float(((a_flat[both] - 1.0) ** 2).sum())
               + float(((a_flat[cross] - f) ** 2).sum())
               + float((a_flat[~both & ~cross] ** 2).sum()))
        if sse < best_sse - 1e-15:
            best_sse, best_f, best_m = sse, f, m
            best_core = [nodes[i] for i in order[:m]]

    cp = max(0.0, min(1.0, 1.0 - best_sse / sse_null))
    if return_core:
        return float(cp), best_core, int(best_m)
    return float(cp)
