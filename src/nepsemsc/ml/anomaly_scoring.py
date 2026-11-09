"""Anomaly scoring under purged walk-forward (Module 2 — R1/R7 discipline).

Per fold k:
  * rows with (date in fold.train)  → winsorised + standardised with
    TRAIN constants, IsolationForest fitted there (seed = if_seed(k));
  * rows with (date in fold.test)   → scored by THAT fitted model
    (-decision_function ⇒ higher = more anomalous);
  * train rows also receive an IN-SAMPLE score labelled is_train=True —
    used for EDA only, never pooled with test scores in regressions.

No fold's statistics touch another fold. Violation = invalid result, not a
fallback (DC7).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from nepsemsc.ml.standardize import LeakSafeStandardizer
from nepsemsc.ml.walk_forward import purged_folds
from nepsemsc.utils.seeds import if_seed

FEATURES_DEFAULT = [
    "buyer_hhi",
    "seller_hhi",
    "self_loop_ratio",
    "end_of_day_concentration",
    "reciprocity",
    "density",
    "max_betweenness",
    "core_periphery_coeff",
]


def walk_forward_anomaly_scores(
    feature_frame: pd.DataFrame,
    features: list[str] | None = None,
    n_folds: int = 4,
    purge_gap_sessions: int = 6,
    n_estimators: int = 200,
    contamination: str | float = "auto",
    winsor: tuple[float, float] = (0.01, 0.99),
    date_col: str = "date",
    mode: str = "anchored",
) -> pd.DataFrame:
    """Returns a frame: [date, features..., anomaly_score, fold_id, is_train]."""
    features = features or FEATURES_DEFAULT
    folds = purged_folds(feature_frame[date_col], n_folds=n_folds,
                         purge_gap_sessions=purge_gap_sessions, mode=mode)
    out_rows: list[pd.DataFrame] = []
    for fold in folds:
        frame = feature_frame
        X_all = frame[features].astype("float64")
        complete = ~X_all.isna().any(axis=1).to_numpy()
        train_mask = frame[date_col].isin(fold.train_dates).to_numpy() & complete
        test_mask = frame[date_col].isin(fold.test_dates).to_numpy() & complete

        scaler = LeakSafeStandardizer(feature_cols=features, winsor=winsor)
        X_train_std = scaler.fit_transform(frame.loc[train_mask], fold_label=f"fold{fold.fold_id}_train")

        model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=if_seed(fold.fold_id),
        )
        model.fit(X_train_std.to_numpy())

        train_out = frame.loc[train_mask, [date_col]].copy()
        train_out["anomaly_score"] = -model.score_samples(X_train_std.to_numpy())
        train_out["fold_id"] = fold.fold_id
        train_out["is_train"] = True

        X_test_std = scaler.transform(frame.loc[test_mask], fold_label=f"fold{fold.fold_id}_test")
        test_out = frame.loc[test_mask, [date_col]].copy()
        test_out["anomaly_score"] = -model.decision_function(X_test_std.to_numpy())
        test_out["fold_id"] = fold.fold_id
        test_out["is_train"] = False

        # carry the features through for downstream merges
        for chunk in (train_out, test_out):
            chunk[features] = frame.loc[chunk.index, features]

        out_rows.append(train_out)
        out_rows.append(test_out)

    res = (pd.concat(out_rows, ignore_index=True)
             .sort_values(["date", "is_train", "fold_id"], ascending=[True, False, True])
             .reset_index(drop=True))
    return res
