"""HHI metric definition tests (toy data)."""
import math

import numpy as np
import pytest

pandas = pytest.importorskip("pandas")


def test_hhi_equal_brokers_is_one_over_n():
    from nepsemsc.network.concentration import hhi_from_volumes
    assert hhi_from_volumes(pandas.Series([100, 100, 100, 100])) == pytest.approx(0.25)


def test_hhi_single_broker_is_one():
    from nepsemsc.network.concentration import hhi_from_volumes
    assert hhi_from_volumes(pandas.Series([500])) == pytest.approx(1.0)


def test_hhi_two_brokers_3_7():
    from nepsemsc.network.concentration import hhi_from_volumes
    # shares 0.3 and 0.7 → 0.09 + 0.49 = 0.58
    assert hhi_from_volumes(pandas.Series([3, 7])) == pytest.approx(0.58)


def test_hhi_zero_volume_is_nan():
    from nepsemsc.network.concentration import hhi_from_volumes
    assert math.isnan(hhi_from_volumes(pandas.Series([0, 0])))


def test_daily_buyer_hhi_matches_handcalc(toy_floorsheet):
    """One (symbol, date) group recomputed by hand vs function output."""
    from nepsemsc.network.concentration import buyer_hhi_by_day
    out = buyer_hhi_by_day(toy_floorsheet)
    g = toy_floorsheet[(toy_floorsheet["symbol"] == "NABIL") &
                       (toy_floorsheet["date"] == "2024-01-02")]
    per_buyer = g.groupby("buyer_broker_id")["volume"].sum()
    shares = per_buyer / per_buyer.sum()
    expected = float((shares**2).sum())
    row = out[(out["symbol"] == "NABIL") & (out["date"] == "2024-01-02")]
    assert float(row["buyer_hhi"].iloc[0]) == pytest.approx(expected)


def test_top3_share_geq_hhi_sanity(toy_floorsheet):
    from nepsemsc.network.concentration import top_k_share, seller_hhi_by_day
    t3 = top_k_share(toy_floorsheet, id_col="seller_broker_id", k=3)
    shl = seller_hhi_by_day(toy_floorsheet)
    m = t3.merge(shl, on=["symbol", "date"])
    # top-3 share must exceed the HHI for any grouping (HHI ≤ Σtopk share² ≤ topk share)
    assert (m["top_3_seller_broker_id_share"].to_numpy() >
            m["seller_hhi"].to_numpy() - 1e-9).all()
