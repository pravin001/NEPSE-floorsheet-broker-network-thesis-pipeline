"""Core-periphery metric behaviour tests (star = pure core-periphery)."""
import networkx as nx
import pytest


def _star_directed() -> nx.DiGraph:
    G = nx.DiGraph()
    for i in range(1, 6):
        G.add_edge("C", f"L{i}", weight=1.0)
        G.add_edge(f"L{i}", "C", weight=1.0)
    return G


def _ring_directed() -> nx.DiGraph:
    G = nx.DiGraph()
    nodes = [f"n{i}" for i in range(8)]
    for a, b in zip(nodes, nodes[1:] + nodes[:1]):
        G.add_edge(a, b, weight=1.0)
        G.add_edge(b, a, weight=1.0)
    return G


def test_star_is_perfect_core_periphery():
    from nepsemsc.network.core_periphery import borgatti_everett_score
    cp, core, m = borgatti_everett_score(_star_directed(), return_core=True)
    assert cp > 0.95
    assert "C" in core
    assert m == 1


def test_ring_is_not_a_core_periphery_structure():
    from nepsemsc.network.core_periphery import borgatti_everett_score
    cp_star = borgatti_everett_score(_star_directed())
    cp_ring = borgatti_everett_score(_ring_directed())
    assert cp_ring < cp_star - 0.3
    assert cp_ring < 0.75


def test_empty_and_single_node_safe():
    from nepsemsc.network.core_periphery import borgatti_everett_score
    assert borgatti_everett_score(nx.DiGraph()) == 0.0
    G = nx.DiGraph()
    G.add_edge("a", "b", weight=1.0)
    G.add_edge("b", "a", weight=1.0)
    assert isinstance(borgatti_everett_score(G), float)
