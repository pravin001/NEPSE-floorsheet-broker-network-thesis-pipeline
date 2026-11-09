"""Graph-builder tests (aggregation + the tuple/subset regression)."""
import pandas as pd


def _edges():
    return pd.DataFrame({
        "date": ["2024-01-01"] * 4,
        "symbol": ["NABIL"] * 4,
        "buyer_broker_id": ["08", "08", "10", "12"],
        "seller_broker_id": ["10", "10", "08", "12"],
        "pair_volume": [100.0, 50.0, 30.0, 7.0],
    })


def test_agg_sums_duplicate_pairs():
    from nepsemsc.network.graph_builder import build_directed_weighted_graph
    G = build_directed_weighted_graph(_edges())
    assert G["08"]["10"]["weight"] == 150.0          # duplicate pair aggregated
    assert G["10"]["08"]["weight"] == 30.0
    assert G.number_of_nodes() == 3
    selfloops = [(u, v) for u, v in G.edges() if u == v]
    assert selfloops == [("12", "12")]


def test_multi_column_subset_check_does_not_crash():
    """Regression: aggregate branch compared tuple <= set (TypeError)."""
    from nepsemsc.network.graph_builder import build_directed_weighted_graph
    G = build_directed_weighted_graph(_edges())      # runs with aggregate=True
    assert G.number_of_edges() == 3
