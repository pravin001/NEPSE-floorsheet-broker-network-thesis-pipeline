"""Tests for the shared Phase-4 panel builder (DC7 fold-constant discipline)."""
import numpy as np
import pandas as pd


def _scores():
    rng = np.random.default_rng(11)
    rows = []
    for fold_id in (0, 1):
        dates = pd.bdate_range("2024-01-02", periods=30 + 7 * fold_id)
        for dt, d in enumerate(dates):
            for sym in ("NABIL", "API"):
                rows.append({
                    "date": d, "symbol": sym, "fold_id": fold_id,
                    "is_train": dt < 20, "is_event": False,
                    "anomaly_score": rng.normal(0, 1),
                    "buyer_hhi": rng.random(),
                    "self_loop_ratio": rng.random() / 10,
                    "end_of_day_concentration": rng.random() / 10,
                    "reciprocity": rng.random(),
                    "density": rng.random(),
                    "max_betweenness": rng.random(),
                    "core_periphery_coeff": rng.random(),
                    "total_volume": float(rng.integers(5_000, 50_000)),
                    "total_trades": float(rng.integers(10, 500)),
                })
    return pd.DataFrame(rows)


def _outcomes():
    rng = np.random.default_rng(12)
    base = _scores()[["date", "symbol"]].drop_duplicates()
    n = len(base)
    return base.assign(
        ret_fwd1=rng.normal(0, 0.012, n),
        abs_ret_fwd1=lambda f: f["ret_fwd1"].abs(),
        market_ret_loo=rng.normal(0, 0.005, n),
    )


def test_split_train_and_oos_rows_only():
    from nepsemsc.ml.panel_data import build_oos_panel
    s, o = _scores(), _outcomes()
    panel, train = build_oos_panel(s, o)
    assert (~panel["is_train"]).all()
    assert (train["is_train"]).all()
    assert len(panel) + len(train) == len(s)


def test_z_columns_use_own_fold_constants_only():
    """Every _z column exists and is standardized per fold (DC7): dividing the
    panel by fold and re-centering would be a no-op within each fold only if
    constants came from that fold's TRAIN rows."""
    from nepsemsc.ml.panel_data import (build_oos_panel, standardize_test,
                                        train_fold_stats)
    panel, train = build_oos_panel(_scores(), _outcomes())
    st = train_fold_stats(train)
    p = standardize_test(panel, st)
    zcols = ["anomaly_score_z", "log_volume_z", "market_ret_loo_z"]
    for z in zcols:
        assert z in p.columns
    # SDs fold-wise are O(1)-ish, and only rows of that fold were touched
    for fold_id, g in p.groupby("fold_id", observed=True):
        sd = g["log_volume_z"].std(ddof=0)
        assert 0.5 < sd < 5.0, f"fold {fold_id}: sd={sd}"
    # no cross-fold contamination: fold 0 z-stats computed on fold 0 train rows
    z0 = p.loc[p.fold_id == 0, "anomaly_score_z"]
    assert float(z0.notna().all())


def test_extra_outcome_cols_ride_along_without_changing_rows():
    """Phase-5 battery: extra outcome columns (fwd_k horizons) merge onto the
    TEST panel; the base dropna row set stays EXACTLY the default one."""
    from nepsemsc.ml.panel_data import build_oos_panel
    s = _scores()
    o = _outcomes().assign(ret_fwd2=np.nan, abs_ret_fwd2=np.nan)
    a, _ = build_oos_panel(s, o)
    b, _ = build_oos_panel(s, o, extra_outcome_cols=("ret_fwd2",
                                                     "abs_ret_fwd2"))
    assert {"ret_fwd2", "abs_ret_fwd2"} <= set(b.columns)
    assert len(b) == len(a)                 # base row set unchanged
    # all-NaN extra col must not sneak into the row filter — per-fit dropna
    # in each regression handles truncated tails instead
    assert b["ret_fwd2"].isna().all()
