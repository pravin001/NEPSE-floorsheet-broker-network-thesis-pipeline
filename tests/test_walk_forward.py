"""Purged walk-forward fold construction tests (R7)."""
import pandas as pd
import pytest

from nepsemsc.ml.walk_forward import purged_folds


def test_purge_gap_is_strict(toy_feature_frame):
    dates = toy_feature_frame["date"].unique()
    folds = purged_folds(dates, n_folds=4, purge_gap_sessions=6)
    u = sorted(set(dates))
    for f in folds:
        # sessions STRICTLY between train_end and test_start equal purge_gap
        train_end_pos, test_start_pos = f.train_pos[1] - 1, f.test_pos[0]
        assert test_start_pos - train_end_pos == f.purge_gap_sessions + 1
        assert str(u[f.train_pos[1] - 1]) not in {str(d) for d in f.test_dates}
        # and no dropped session appears in either side
        dropped = {u[i] for i in range(f.train_pos[1], f.test_pos[0])}
        assert len(dropped) == f.purge_gap_sessions
        assert not (dropped & set(f.train_dates))
        assert not (dropped & set(f.test_dates))


def test_four_folds_chronological(toy_feature_frame):
    dates = toy_feature_frame["date"].unique()
    folds = purged_folds(dates, n_folds=4, purge_gap_sessions=6)
    assert len(folds) == 4
    for a, b in zip(folds, folds[1:]):
        assert a.train_dates[0] < b.train_dates[0]
    for f in folds:
        assert len(f.train_dates) > 0 and len(f.test_dates) > 0


def test_gap_consumes_segment_raises():
    with pytest.raises(ValueError):
        purged_folds(list(range(12)), n_folds=4, purge_gap_sessions=6)


def test_sequential_mode_protects_labelling(toy_feature_frame):
    """DC7 restated: fold ids must not shuffle between runs."""
    dates = toy_feature_frame["date"].unique()
    f1 = purged_folds(dates, n_folds=4, purge_gap_sessions=6)
    f2 = purged_folds(dates, n_folds=4, purge_gap_sessions=6)
    for a, b in zip(f1, f2):
        assert a.train_dates == b.train_dates and a.test_dates == b.test_dates
