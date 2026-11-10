"""Regression: IF train/test score scale consistency (EXP-0004a incident).

The first corpus scoring run produced 0 events across all folds because
train scores used -score_samples while test used -decision_function — under
contamination='auto' the two differ by a constant offset (~+0.5), so every
test score sat below the train-q90 threshold. The sealed behaviour:
- decision_function on BOTH sides. With clearly anomalous rows injected in
the tail chunk, the DC1 scorer MUST fire >= 1 test event.
"""
import numpy as np
import pandas as pd


def _frame(n_sessions: int = 260, symbols: tuple[str, ...] = ("NABIL", "API", "HDL")):
    rng = np.random.default_rng(7)
    dates = pd.bdate_range("2023-01-02", periods=n_sessions)
    rows = []
    for d in dates:
        d_year = d.year
        for sym in symbols:
            anomalous = d_year == 2024  # final ~tail chunk = injected anomaly era
            rows.append({
                "date": d.date(), "symbol": sym,
                "buyer_hhi": 1.0 if anomalous else rng.random(),
                "seller_hhi": 0.9 if anomalous else rng.random(),
                "self_loop_ratio": 0.5 if anomalous else rng.random() * 0.05,
                "end_of_day_concentration": 1.0 if anomalous else rng.random() * 0.1,
                "reciprocity": 0.95 if anomalous else rng.random(),
                "density": 0.8 if anomalous else rng.random(),
                "max_betweenness": 1.0 if anomalous else rng.random(),
                "core_periphery_coeff": 0.99 if anomalous else rng.random(),
            })
    return pd.DataFrame(rows)


def _turnover(frame):
    rng = np.random.default_rng(8)
    return (frame[["date", "symbol"]].drop_duplicates()
            .assign(turnover=rng.random(len(frame[["date", "symbol"]].drop_duplicates()))))


def test_excluded_symbols_never_enter_universe():
    """Phase-5 external cross-section: exclusion applies BEFORE the ranking head."""
    from nepsemsc.ml.anomaly_scoring import select_fold_universe
    rng = np.random.default_rng(3)
    dates = [d.date() for d in pd.bdate_range("2024-01-02", periods=20)]
    rows = []
    for sym, base in (("AAA", 5.0), ("BBB", 4.0), ("CCC", 3.0), ("DDD", 2.0)):
        rows.extend({"date": d, "symbol": sym, "turnover": base + rng.random() * 1e-6}
                    for d in dates)
    turn = pd.DataFrame(rows)
    u_all = select_fold_universe(turn, dates, n_top=3)
    assert u_all == ["AAA", "BBB", "CCC"]
    u_ext = select_fold_universe(turn, dates, n_top=3, excluded={"AAA", "BBB"})
    assert u_ext == ["CCC", "DDD"]
    u_allb = select_fold_universe(turn, dates, n_top=10, excluded=None)
    assert set(u_allb) == {"AAA", "BBB", "CCC", "DDD"}


def test_anomalous_test_chunk_fires_events():
    from nepsemsc.ml.anomaly_scoring import walk_forward_anomaly_scores_dc1
    frame = _frame()
    turn = _turnover(frame)
    scores, summary = walk_forward_anomaly_scores_dc1(
        frame, turn, n_folds=4, purge_gap_sessions=6, n_estimators=30,
        contamination="auto", event_quantile=0.90)
    test = scores.loc[~scores["is_train"]]
    assert len(test) > 0
    n_events = int(test["is_event"].sum())
    assert n_events >= 1, (
        "0 events under train-q90 threshold — scale mixing regression? "
        f"summary:\n{summary}")
    assert n_events < len(test)


def test_train_test_score_scales_overlap():
    from nepsemsc.ml.anomaly_scoring import walk_forward_anomaly_scores_dc1
    frame = _frame()
    scores, _ = walk_forward_anomaly_scores_dc1(
        frame, _turnover(frame), n_folds=4, purge_gap_sessions=6,
        n_estimators=30, contamination="auto", event_quantile=0.90)
    for fold_id, g in scores.groupby("fold_id", observed=True):
        tr = g.loc[g["is_train"], "anomaly_score"]
        te = g.loc[~g["is_train"], "anomaly_score"]
        # decision_function on both sides => the two distributions live on the
        # SAME scale: test max must not exceed the train range by the old
        # +0.5-style offset
        assert te.max() <= tr.max() + 0.5
        assert tr.min() <= te.min() + 0.5
