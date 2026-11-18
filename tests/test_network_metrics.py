"""Reciprocity-volume tests — regression guard for the v2.1.0 correction.

The documented definition is

    2 * sum_{unordered i<j} min(w_ij, w_ji) / sum(all edge weights)

Each unordered pair is counted once; self-loops stay in the denominator but
never enter the numerator. See ``reports/reciprocity_correction.md``.
"""
import networkx as nx
import pytest


def _g(edges):
    g = nx.DiGraph()
    for u, v, w in edges:
        g.add_edge(u, v, weight=float(w))
    return g


def test_symmetric_two_broker_pair_is_one():
    """The bug returned 2.0 for a perfectly symmetric pair."""
    from nepsemsc.network.metrics import reciprocity_volume
    g = _g([("A", "B", 1.0), ("B", "A", 1.0)])
    assert reciprocity_volume(g) == pytest.approx(1.0)


def test_asymmetric_pair_uses_twice_the_minimum():
    """2 * min(3, 1) / (3 + 1) = 0.5."""
    from nepsemsc.network.metrics import reciprocity_volume
    g = _g([("A", "B", 3.0), ("B", "A", 1.0)])
    assert reciprocity_volume(g) == pytest.approx(0.5)


def test_self_loop_only_is_zero():
    """A broker trading with itself is not reciprocal inter-broker volume."""
    from nepsemsc.network.metrics import reciprocity_volume
    g = _g([("A", "A", 1.0)])
    assert reciprocity_volume(g) == pytest.approx(0.0)


def test_self_loop_stays_in_denominator_only():
    """A<->B (1 each) plus C->C (1): 2 * 1 / 3 = 2/3."""
    from nepsemsc.network.metrics import reciprocity_volume
    g = _g([("A", "B", 1.0), ("B", "A", 1.0), ("C", "C", 1.0)])
    assert reciprocity_volume(g) == pytest.approx(2.0 / 3.0)


def test_one_way_edges_do_not_count():
    """A->B and B->C, but no reverse edges: zero reciprocal volume."""
    from nepsemsc.network.metrics import reciprocity_volume
    g = _g([("A", "B", 2.0), ("B", "C", 3.0)])
    assert reciprocity_volume(g) == pytest.approx(0.0)


def test_mixed_graph_matches_documented_formula():
    """A<->B (2,1), B->C (1), C->C (1): 2 * min(2,1) / 5 = 0.4."""
    from nepsemsc.network.metrics import reciprocity_volume
    g = _g([("A", "B", 2.0), ("B", "A", 1.0),
            ("B", "C", 1.0), ("C", "C", 1.0)])
    assert reciprocity_volume(g) == pytest.approx(0.4)


def test_empty_graph_is_zero():
    from nepsemsc.network.metrics import reciprocity_volume
    assert reciprocity_volume(nx.DiGraph()) == pytest.approx(0.0)


def test_zero_weight_graph_is_zero():
    from nepsemsc.network.metrics import reciprocity_volume
    g = _g([("A", "B", 0.0), ("B", "A", 0.0)])
    assert reciprocity_volume(g) == pytest.approx(0.0)


def test_reciprocity_never_exceeds_one():
    """For any directed graph, 2*sum(min) <= total edge weight."""
    from nepsemsc.network.metrics import reciprocity_volume
    g = _g([
        ("A", "B", 2.0), ("B", "A", 1.0),
        ("B", "C", 3.0), ("C", "B", 3.0),
        ("C", "A", 1.0), ("A", "C", 4.0),
        ("A", "A", 5.0), ("D", "D", 2.0),
        ("D", "A", 1.0),
    ])
    value = reciprocity_volume(g)
    assert 0.0 <= value <= 1.0


def test_metrics_frame_uses_corrected_value():
    from nepsemsc.network.metrics import metrics_frame
    g = _g([("A", "B", 1.0), ("B", "A", 1.0), ("C", "C", 1.0)])
    frame = metrics_frame(g)
    assert frame["reciprocity_volume"] == pytest.approx(2.0 / 3.0)
