"""Leakage tests (R1/R5/DC7): standardiser must NEVER see non-train stats,
and fold masks must be disjoint."""
import numpy as np
import pandas as pd
import pytest

pandas = pd  # fixture-style alias


def test_standardizer_uses_train_stats_only():
    from nepsemsc.ml.standardize import LeakSafeStandardizer
    train = pandas.DataFrame({"x": np.arange(10.0)})
    test = pandas.DataFrame({"x": [5.0, 100.0, 110.0]})
    sc = LeakSafeStandardizer(["x"], winsor=(0.01, 0.99))
    sc.fit(train, fold_label="fold0_train")
    out = sc.transform(test, fold_label="fold0_test")
    # semantics per analysis_plan §7: stats computed on WINSORISED train values
    q01, q99 = float(train["x"].quantile(0.01)), float(train["x"].quantile(0.99))
    clipped = train["x"].clip(q01, q99)
    mu, sd = float(clipped.mean()), float(clipped.std(ddof=0))
    expected = (np.clip(np.array([5.0, 100.0, 110.0]), q01, q99) - mu) / sd
    assert np.allclose(out["x"].to_numpy(), expected)
    assert sc.fitted_on == "fold0_train"
    assert out["x"].iloc[1] == pytest.approx(out["x"].iloc[2])
    # the FULL-series stats would differ — assert we did NOT use them
    full_clipped_clip_hi = float(pandas.concat([train, test])["x"].quantile(0.99))
    assert q99 != full_clipped_clip_hi


def test_winsorization_bounds_come_from_train():
    from nepsemsc.ml.standardize import LeakSafeStandardizer
    train = pandas.DataFrame({"x": np.arange(1.0, 11.0)})     # max 10.0
    test = pandas.DataFrame({"x": [50.0, -50.0]})
    sc = LeakSafeStandardizer(["x"])
    sc.fit(train)
    z = sc.transform(test)
    q01, q99 = float(train["x"].quantile(0.01)), float(train["x"].quantile(0.99))
    clipped = train["x"].clip(q01, q99)
    mu, sd = float(clipped.mean()), float(clipped.std(ddof=0))
    expected = np.array([(q99 - mu) / sd, (q01 - mu) / sd])  # 50→clip hi, -50→clip lo
    assert np.allclose(z["x"].to_numpy(), expected)
    # the bound is the TRAIN quantile, not the test max
    assert abs(q99 - float(test["x"].max())) > 30


def test_refit_changes_stats():
    from nepsemsc.ml.standardize import LeakSafeStandardizer
    a = pandas.DataFrame({"x": np.arange(10.0)})
    b = pandas.DataFrame({"x": np.arange(1000.0, 1010.0)})
    sc = LeakSafeStandardizer(["x"]).fit(a)
    mu_a = float(sc.stats_["mu"]["x"])
    sc.fit(b, fold_label="fold1_train")
    mu_b = float(sc.stats_["mu"]["x"])
    assert abs(mu_a - mu_b) > 10


def test_fold_masks_disjoint(toy_feature_frame):
    from nepsemsc.ml.walk_forward import purged_folds, assert_no_fold_overlap
    folds = purged_folds(toy_feature_frame["date"].unique(), n_folds=4, purge_gap_sessions=6)
    assert_no_fold_overlap(folds)   # per-fold train/test disjoint (R5, both modes)
    # NOTE: whole-frame union disjointness is NOT assertable in either
    # walk-forward mode — later folds legitimately train on earlier test
    # segments (sequential pairs reuse segment k+1; anchored expands through
    # all prior chunks).
