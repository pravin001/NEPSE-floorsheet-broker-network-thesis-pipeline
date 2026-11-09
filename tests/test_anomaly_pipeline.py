"""Anomaly-scoring pipeline integration test on synthetic features."""
import numpy as np


def test_walk_forward_scores_on_synthetic_two_features(toy_feature_frame):
    from nepsemsc.ml.anomaly_scoring import walk_forward_anomaly_scores

    feats = ["buyer_hhi", "self_loop_ratio"]
    out = walk_forward_anomaly_scores(
        toy_feature_frame, features=feats, n_folds=4,
        purge_gap_sessions=6, n_estimators=50, contamination="auto",
    )
    # all four folds contributed, scores finite, every fold scored its test rows
    assert set(out["fold_id"].unique()) == {0, 1, 2, 3}
    assert np.isfinite(out["anomaly_score"]).all()
    assert out.groupby("fold_id").apply(
        lambda g: g.loc[~g["is_train"], "anomaly_score"].notna().all()).all()

    # reproducibility under identical seeds
    out2 = walk_forward_anomaly_scores(
        toy_feature_frame, features=feats, n_folds=4,
        purge_gap_sessions=6, n_estimators=50, contamination="auto",
    )
    np.testing.assert_allclose(out["anomaly_score"].to_numpy(),
                               out2["anomaly_score"].to_numpy())

    # per-fold train/test disjointness (cross-fold reuse of earlier test dates
    # as later train dates is BY DESIGN in sequential walk-forward)
    for fid, g in out.groupby("fold_id"):
        t_dates = set(g.loc[~g["is_train"], "date"].astype(str))
        r_dates = set(g.loc[g["is_train"], "date"].astype(str))
        assert not (t_dates & r_dates), f"fold {fid} train/test overlap"
