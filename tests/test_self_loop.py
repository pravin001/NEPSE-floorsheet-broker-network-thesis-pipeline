"""Self-loop detection tests (R12: metric = self-loop VOLUME, not 'wash trading')."""
import numpy as np
import pytest

pandas = pytest.importorskip("pandas")


def test_self_loop_basic_ratio():
    from nepsemsc.network.concentration import self_loop_volume_ratio
    df = pandas.DataFrame({
        "buyer_broker_id": ["01", "01", "02", "02"],
        "seller_broker_id": ["01", "02", "03", "02"],
        "volume": [10.0, 30.0, 10.0, 50.0],
    })
    # self-loop volume = 10 (row0) + 50 (row3) = 60 of 100
    assert self_loop_volume_ratio(df) == pytest.approx(0.6)


def test_self_loop_by_day_matches_per_symbol(toy_floorsheet):
    from nepsemsc.network.concentration import self_loop_volume_ratio
    out = self_loop_volume_ratio(toy_floorsheet, by=["symbol", "date"])
    for sym in toy_floorsheet["symbol"].unique():
        g = toy_floorsheet[(toy_floorsheet["date"] == "2024-01-03") &
                           (toy_floorsheet["symbol"] == sym)]
        expected = float(
            g.loc[g["buyer_broker_id"] == g["seller_broker_id"], "volume"].sum()
            / g["volume"].sum())
        row = out[(out["date"] == "2024-01-03") & (out["symbol"] == sym)]
        assert float(row["self_loop_volume_ratio"].iloc[0]) == pytest.approx(expected)


def test_self_loop_zero_volume_nan():
    from nepsemsc.network.concentration import self_loop_volume_ratio
    df = pandas.DataFrame({
        "buyer_broker_id": ["01"], "seller_broker_id": ["02"], "volume": [0.0],
    })
    assert np.isnan(self_loop_volume_ratio(df))
