"""Purged walk-forward fold construction tests (R7) — anchored + sequential."""
import pytest

from nepsemsc.ml.walk_forward import purged_folds, assert_no_fold_overlap

MODES = ["anchored", "sequential"]


def _assert_strict_gap(dates, folds):
    """Generic strict-gap invariant (holds in BOTH modes)."""
    u = sorted(set(dates))
    for f in folds:
        train_end_pos, test_start_pos = f.train_pos[1] - 1, f.test_pos[0]
        assert test_start_pos - train_end_pos == f.purge_gap_sessions + 1
        assert str(u[train_end_pos]) not in {str(d) for d in f.test_dates}
        dropped = {u[i] for i in range(f.train_pos[1], f.test_pos[0])}
        assert len(dropped) == f.purge_gap_sessions
        assert not (dropped & set(f.train_dates))
        assert not (dropped & set(f.test_dates))


@pytest.mark.parametrize("mode", MODES)
def test_purge_gap_is_strict(mode, toy_feature_frame):
    dates = toy_feature_frame["date"].unique()
    folds = purged_folds(dates, n_folds=4, purge_gap_sessions=6, mode=mode)
    _assert_strict_gap(dates, folds)


@pytest.mark.parametrize("mode", MODES)
def test_fold_train_test_disjoint(mode, toy_feature_frame):
    dates = toy_feature_frame["date"].unique()
    folds = purged_folds(dates, n_folds=4, purge_gap_sessions=6, mode=mode)
    assert_no_fold_overlap(folds)   # raises on any per-fold train/test overlap (R5)
    assert len(folds) == 4
    for f in folds:
        assert len(f.train_dates) > 0 and len(f.test_dates) > 0


@pytest.mark.parametrize("mode", MODES)
def test_folds_deterministic(mode, toy_feature_frame):
    """DC7 restated: fold ids must not shuffle between runs (both modes)."""
    dates = toy_feature_frame["date"].unique()
    f1 = purged_folds(dates, n_folds=4, purge_gap_sessions=6, mode=mode)
    f2 = purged_folds(dates, n_folds=4, purge_gap_sessions=6, mode=mode)
    for a, b in zip(f1, f2):
        assert a.train_dates == b.train_dates and a.test_dates == b.test_dates


def test_default_mode_is_anchored(toy_feature_frame):
    dates = toy_feature_frame["date"].unique()
    default = purged_folds(dates, n_folds=4, purge_gap_sessions=6)
    explicit = purged_folds(dates, n_folds=4, purge_gap_sessions=6, mode="anchored")
    for a, b in zip(default, explicit):
        assert a.mode == b.mode == "anchored"
        assert a.train_dates == b.train_dates and a.test_dates == b.test_dates


def test_anchored_train_window_expands(toy_feature_frame):
    dates = toy_feature_frame["date"].unique()
    folds = purged_folds(dates, n_folds=4, purge_gap_sessions=6, mode="anchored")
    # same chronological origin for every fold (anchored) ...
    assert len({f.train_dates[0] for f in folds}) == 1
    # ... and the training set STRICTLY expands fold over fold
    for a, b in zip(folds, folds[1:]):
        assert set(a.train_dates) < set(b.train_dates)
        assert b.test_dates[0] > a.test_dates[-1]      # test blocks advance
    assert folds[-1].train_dates[-1] > folds[0].train_dates[-1]


def test_anchored_test_blocks_tile_timeline(toy_feature_frame):
    """After the warm-up chunk, every session is in exactly one test block
    or exactly one purge gap — nothing beyond the warm-up is silently dropped."""
    dates = toy_feature_frame["date"].unique()
    u = sorted(set(dates))
    folds = purged_folds(dates, n_folds=4, purge_gap_sessions=6, mode="anchored")
    covered: set[str] = set()
    for f in folds:
        covered |= {str(d) for d in u[f.test_pos[0]: f.test_pos[1]]}          # test
        covered |= {str(d) for d in u[f.train_pos[1]: f.test_pos[0]]}         # purge gap
    tail = {str(d) for d in u[folds[0].train_pos[1]:]}   # from first purged session on
    assert covered == tail                       # exact tiling
    assert str(u[-1]) in {str(d) for d in folds[-1].test_dates}               # 2024 tail IS scored


def test_sequential_chronological_train_starts(toy_feature_frame):
    """Rolling pairs: each fold trains on a LATER segment than the previous."""
    dates = toy_feature_frame["date"].unique()
    folds = purged_folds(dates, n_folds=4, purge_gap_sessions=6, mode="sequential")
    for a, b in zip(folds, folds[1:]):
        assert a.train_dates[0] < b.train_dates[0]


def test_gap_consumes_segment_raises():
    # 12 sessions / 4 sequential folds = 3-session segments < gap 6
    with pytest.raises(ValueError):
        purged_folds(list(range(12)), n_folds=4, purge_gap_sessions=6)


def test_anchored_purge_gap_consumes_chunk_raises():
    # 32 sessions → anchored chunks of 6/6/7/6/7; fold 0 test = [6+6, 12) → empty
    with pytest.raises(ValueError):
        purged_folds(list(range(32)), n_folds=4, purge_gap_sessions=6)


def test_not_enough_sessions_raises():
    with pytest.raises(ValueError):
        purged_folds(list(range(4)), n_folds=4, purge_gap_sessions=1)


def test_unknown_mode_raises(toy_feature_frame):
    dates = toy_feature_frame["date"].unique()
    with pytest.raises(ValueError, match="unknown fold mode"):
        purged_folds(dates, n_folds=4, purge_gap_sessions=6, mode="nope")
