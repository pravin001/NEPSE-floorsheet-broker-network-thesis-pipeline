"""Trade-size bucket tests (v2 Stage 3, plan V2-3.3).

Runs the production DuckDB SQL against a synthetic in-memory floorsheet:
  * TRAIN-fold-only p10/p90 thresholds (OOS volumes never enter them);
  * correct small/medium/large assignment and buyer-HHI/top-3/EoD arithmetic;
  * `MIN_BUCKET_TRADES` suppression keeps volume/trade counts but NaNs the
    concentration features; the 1-trade sensitivity keeps them;
  * 2023-02-16 sets EoD to NULL while level features survive;
  * the sign-aware large-vs-small success criterion rejects a raw-rule pass
    whose large-bucket sign contradicts the v1 effect.
"""
import duckdb
import numpy as np
import pandas as pd
import pytest

from nepsemsc.features.trade_size import (BUCKET_COLS, DEFECT_DATE,
                                          MIN_BUCKET_TRADES,
                                          bucket_summary,
                                          build_trade_size_features,
                                          pivot_bucket_features,
                                          success_criterion,
                                          thresholds_table)

TRAIN_DATE = "2024-01-02"
TEST_DATE = "2024-01-03"
SMALL_TEST_DATE = "2024-01-04"


def _trade_rows(date, volumes, buyer_ids, contract_start=1, price=100.0):
    return [{
        "date": pd.Timestamp(date).date(),
        "symbol": "AAA",
        "contract_no": contract_start + i,
        "volume": float(v),
        "price": float(price),
        "buyer_broker_id": buyer_ids[i],
        "seller_broker_id": "99",
    } for i, v in enumerate(volumes)]


@pytest.fixture()
def trade_setup():
    rows = []
    # TRAIN: 100 trades, volumes 1..100 -> p10 = 10.9, p90 = 90.1
    rows += _trade_rows(TRAIN_DATE, list(range(1, 101)),
                        [f"{i % 10:02d}" for i in range(100)])
    # TEST 1: six trades per bucket, distinct buyers within each bucket
    rows += _trade_rows(TEST_DATE, [1, 2, 3, 4, 5, 6],
                        ["01", "02", "03", "04", "05", "06"], contract_start=1)
    rows += _trade_rows(TEST_DATE, [40, 50, 60, 70, 80, 85],
                        ["01", "02", "03", "04", "05", "06"], contract_start=7)
    rows += _trade_rows(TEST_DATE, [95, 96, 97, 98, 99, 100],
                        ["01", "02", "03", "04", "05", "06"], contract_start=13)
    # TEST 2: small bucket only 3 trades -> suppressed at min=5
    rows += _trade_rows(SMALL_TEST_DATE, [1, 2, 3],
                        ["01", "02", "03"], contract_start=1)
    rows += _trade_rows(SMALL_TEST_DATE, [50, 55, 60, 65, 70],
                        ["01", "02", "03", "04", "05"], contract_start=4)
    rows += _trade_rows(SMALL_TEST_DATE, [95, 96, 97, 98, 99],
                        ["01", "02", "03", "04", "05"], contract_start=9)
    # DEFECT DAY: level features computable, EoD must be NULL
    rows += _trade_rows(DEFECT_DATE, [40, 50, 60, 70, 80, 85],
                        ["01", "02", "03", "04", "05", "06"])
    trades = pd.DataFrame(rows)

    scores = pd.DataFrame({
        "date": [pd.Timestamp(d).date()
                 for d in (TRAIN_DATE, TEST_DATE, SMALL_TEST_DATE, DEFECT_DATE)],
        "symbol": "AAA",
        "fold_id": 0,
        "is_train": [True, False, False, False],
    })

    con = duckdb.connect()
    con.register("trades_df", trades)
    con.execute("CREATE TABLE floorsheet_dedup AS SELECT * FROM trades_df")
    yield con, scores
    con.close()


def test_train_only_thresholds_ignore_oos_volumes(trade_setup):
    con, scores = trade_setup
    feat = build_trade_size_features(con, scores)
    thr = thresholds_table(feat)
    assert len(thr) == 1
    assert thr.loc[0, "symbol"] == "AAA"
    assert int(thr.loc[0, "n_train_trades"]) == 100
    assert float(thr.loc[0, "p10"]) == pytest.approx(10.9, abs=1e-9)
    assert float(thr.loc[0, "p90"]) == pytest.approx(90.1, abs=1e-9)
    # OOS large trades (volume 100) exist but never enter the thresholds
    assert np.allclose(feat.loc[feat.n_trades == 6, "p90"], 90.1)


def test_bucket_assignment_and_feature_arithmetic(trade_setup):
    con, scores = trade_setup
    feat = build_trade_size_features(con, scores)
    d = pd.Timestamp(TEST_DATE).date()

    buckets = feat[feat.date == d].set_index("bucket")
    assert set(buckets.index) == {"small", "medium", "large"}
    assert int(buckets.loc["small", "n_trades"]) == 6
    assert int(buckets.loc["large", "n_trades"]) == 6

    med = buckets.loc["medium"]
    vols = np.array([40, 50, 60, 70, 80, 85], dtype=float)
    expected_hhi = float(((vols / vols.sum()) ** 2).sum())
    assert float(med["buyer_hhi"]) == pytest.approx(expected_hhi)
    assert float(med["top3_buyer_share"]) == pytest.approx(235.0 / 385.0)
    # EoD = last ceil(0.05*6)=1 contracted trade by contract_no DESC = 85
    assert float(med["eod_concentration"]) == pytest.approx(85.0 / 385.0)


def test_min_trades_suppression_nans_features_but_keeps_volume(trade_setup):
    con, scores = trade_setup
    feat = build_trade_size_features(con, scores)
    d = pd.Timestamp(SMALL_TEST_DATE).date()
    small = feat[(feat.date == d) & (feat.bucket == "small")].iloc[0]
    assert int(small["n_trades"]) == 3
    assert bool(small["suppressed_min_trades"]) is True
    assert float(small["bucket_volume"]) == pytest.approx(6.0)
    assert np.isnan(small["buyer_hhi"])
    assert np.isnan(small["top3_buyer_share"])
    assert np.isnan(small["eod_concentration"])
    assert MIN_BUCKET_TRADES == 5

    # the 1-trade sensitivity keeps the 3-trade bucket's features
    feat1 = build_trade_size_features(con, scores, min_trades=1)
    small1 = feat1[(feat1.date == d) & (feat1.bucket == "small")].iloc[0]
    assert bool(small1["suppressed_min_trades"]) is False
    assert np.isfinite(small1["buyer_hhi"])


def test_defect_day_eod_null_but_level_features_survive(trade_setup):
    con, scores = trade_setup
    feat = build_trade_size_features(con, scores)
    d = pd.Timestamp(DEFECT_DATE).date()
    row = feat[(feat.date == d) & (feat.bucket == "medium")].iloc[0]
    assert np.isnan(row["eod_concentration"])
    assert np.isfinite(row["buyer_hhi"])
    assert np.isfinite(row["top3_buyer_share"])


def test_pivot_and_bucket_summary(trade_setup):
    con, scores = trade_setup
    feat = build_trade_size_features(con, scores)
    wide = pivot_bucket_features(feat)
    assert len(wide) == 4
    assert list(wide.columns[:3]) == ["fold_id", "date", "symbol"]
    assert set(BUCKET_COLS).issubset(wide.columns)

    summ = bucket_summary(feat, min_trades=5).set_index("bucket")
    assert int(summ.loc["small", "suppressed_days"]) == 1
    assert int(summ.loc["small", "used_days"]) == 2
    assert int(summ.loc["medium", "suppressed_days"]) == 0
    assert float(summ["volume_share"].sum()) == pytest.approx(1.0)

    feat1 = build_trade_size_features(con, scores, min_trades=1)
    summ1 = bucket_summary(feat1, min_trades=1).set_index("bucket")
    assert int(summ1.loc["small", "suppressed_days"]) == 0
    assert int(summ1.loc["small", "used_days"]) == 3


def test_sign_aware_success_criterion_rejects_wrong_signed_large_bucket():
    ts = pd.DataFrame([
        {"test_id": "H7", "metric": "eod_concentration", "bucket": "small",
         "spec": "primary", "beta_bp": -1.3595, "p_dk": 0.6497},
        {"test_id": "H7", "metric": "eod_concentration", "bucket": "large",
         "spec": "primary", "beta_bp": 4.5190, "p_dk": 0.0356},
        {"test_id": "H8", "metric": "top3_buyer_share", "bucket": "small",
         "spec": "primary", "beta_bp": 5.6048, "p_dk": 0.4011},
        {"test_id": "H8", "metric": "top3_buyer_share", "bucket": "large",
         "spec": "primary", "beta_bp": 5.8421, "p_dk": 0.0272},
    ])
    base = {"H7": 3.9524, "H8": -4.4709}
    crit = success_criterion(ts, base)

    h7 = crit[(crit.test_id == "H7") &
              (crit.metric == "eod_concentration")].iloc[0]
    assert bool(h7["success_criterion"]) is True
    assert bool(h7["success_criterion_sign_aware"]) is True
    assert bool(h7["sign_large_matches_v1"]) is True

    h8 = crit[(crit.test_id == "H8") &
              (crit.metric == "top3_buyer_share")].iloc[0]
    # raw rule passes (|large| >= |small| AND p_large <= p_small) ...
    assert bool(h8["success_criterion"]) is True
    # ... but the large-bucket sign contradicts v1, so the honest rule fails
    assert bool(h8["sign_large_matches_v1"]) is False
    assert bool(h8["success_criterion_sign_aware"]) is False

    expected_cols = ["test_id", "metric", "beta_large_bp", "p_large",
                     "beta_small_bp", "p_small", "sign_large_matches_v1",
                     "sign_small_matches_v1", "magnitude_large_ge_small",
                     "p_large_le_small", "success_criterion",
                     "success_criterion_sign_aware"]
    assert list(crit.columns) == expected_cols
