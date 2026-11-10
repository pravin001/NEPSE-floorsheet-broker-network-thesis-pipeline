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
        # decision_function on BOTH sides: -decision_function = -score_samples
        # + offset; score_samples/decision_function mixing puts train/test on
        # different scales (offset ~ +0.5 under contamination='auto') and
        # silently kills every event when thresholding train-q90 vs test.
        train_out["anomaly_score"] = -model.decision_function(X_train_std.to_numpy())
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


# ---------------------------------------------------------------------------
# DC1 panel scorer: per-fold universe re-selection from TRAIN-FOLD data only.
# ---------------------------------------------------------------------------

def select_fold_universe(
    turnover: pd.DataFrame,
    train_dates: list,
    n_top: int = 10,
    min_coverage: float = 0.90,
    symbol_col: str = "symbol",
    date_col: str = "date",
    turnover_col: str = "turnover",
    excluded: set[str] | frozenset[str] | None = None,
) -> list[str]:
    """TOP-`n_top` symbols by MEAN DAILY TURNOVER over the fold's TRAIN dates
    only (analysis_plan §1 DC1), with the DC2 coverage rule (>= min_coverage
    of train sessions present). Deterministic tie-break on symbol id so fold
    universes never depend on groupby order (DC7). `excluded` symbols are
    removed BEFORE the ranking head (Phase-5 external cross-section: ranks
    11+ of the same train-only ranking)."""
    n_sessions = len(set(train_dates))
    g = turnover[turnover[date_col].isin(train_dates)]
    if excluded:
        g = g.loc[~g[symbol_col].isin(excluded)]
    stats = g.groupby(symbol_col, observed=True)[turnover_col].agg(
        mean_turnover="mean", n_days="size")
    stats = stats[stats["n_days"] >= min_coverage * n_sessions]
    stats = stats.sort_values(["mean_turnover", symbol_col],
                              ascending=[False, True])
    return stats.head(n_top).index.tolist()


def walk_forward_anomaly_scores_dc1(
    feature_frame: pd.DataFrame,
    turnover: pd.DataFrame,
    features: list[str] | None = None,
    n_folds: int = 4,
    purge_gap_sessions: int = 6,
    n_estimators: int = 200,
    contamination: str | float = "auto",
    winsor: tuple[float, float] = (0.01, 0.99),
    date_col: str = "date",
    mode: str = "anchored",
    n_top: int = 10,
    min_coverage: float = 0.90,
    event_quantile: float = 0.90,
    per_fold_exclude=None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Purged walk-forward scoring WITH per-fold DC1 universe.

    Per fold: universe = top-`n_top` by train-date mean turnover (+DC2
    coverage). Standardizer + IsolationForest fit on TRAIN rows of that
    universe ONLY; test rows = SAME universe, later dates. Event flag =
    test-row score >= `event_quantile` of the TRAIN-fold score distribution
    of that same fold (never pooled/test). `per_fold_exclude`: optional
    callable(fold) -> iterable of symbol ids removed before the ranking head
    (Phase-5 external cross-section). Returns (scores_frame, summary frame
    with the fold universe + diagnostics). TRAIN scores are in-sample
    (is_train) — EDA only, never pooled with test rows in regressions.
    """
    features = features or FEATURES_DEFAULT
    folds = purged_folds(feature_frame[date_col], n_folds=n_folds,
                         purge_gap_sessions=purge_gap_sessions, mode=mode)
    out_rows, summary_rows = [], []
    for fold in folds:
        universe = select_fold_universe(
            turnover, fold.train_dates, n_top=n_top, min_coverage=min_coverage,
            excluded=set(per_fold_exclude(fold)) if per_fold_exclude else None)
        ff = feature_frame[
            feature_frame[date_col].isin(fold.train_dates + fold.test_dates)
            & feature_frame["symbol"].isin(universe)]
        frame = ff
        X_all = frame[features].astype("float64")
        complete = ~X_all.isna().any(axis=1).to_numpy()
        train_mask = frame[date_col].isin(fold.train_dates).to_numpy() & complete
        test_mask = frame[date_col].isin(fold.test_dates).to_numpy() & complete

        scaler = LeakSafeStandardizer(feature_cols=features, winsor=winsor)
        X_train_std = scaler.fit_transform(
            frame.loc[train_mask], fold_label=f"fold{fold.fold_id}_train")

        model = IsolationForest(
            n_estimators=n_estimators, contamination=contamination,
            random_state=if_seed(fold.fold_id))
        model.fit(X_train_std.to_numpy())

        train_out = frame.loc[train_mask, [date_col, "symbol"]].copy()
        # -decision_function on BOTH sides (scale-consistent; see generic
        # scorer note): ranking unchanged, offset accounted.
        train_out["anomaly_score"] = -model.decision_function(X_train_std.to_numpy())
        train_out["fold_id"] = fold.fold_id
        train_out["is_train"] = True

        X_test_std = scaler.transform(frame.loc[test_mask],
                                      fold_label=f"fold{fold.fold_id}_test")
        test_out = frame.loc[test_mask, [date_col, "symbol"]].copy()
        test_out["anomaly_score"] = -model.decision_function(X_test_std.to_numpy())
        train_scores = train_out["anomaly_score"].to_numpy()
        threshold = float(np.quantile(train_scores, event_quantile)) \
            if len(train_scores) else float("nan")
        test_out["is_event"] = (test_out["anomaly_score"].to_numpy() >= threshold)
        test_out["fold_id"] = fold.fold_id
        test_out["is_train"] = False

        # carry features through for panel merges, + control bookkeeping cols
        # (total_volume needed by regression runners for log-volume control;
        # NOT model inputs — identical scores under the same seeds)
        for col in ("total_volume", "total_trades"):
            if col in frame.columns:
                for chunk in (train_out, test_out):
                    chunk[col] = frame.loc[chunk.index, col]
        for chunk in (train_out, test_out):
            chunk[features] = frame.loc[chunk.index, features]

        summary_rows.append({
            "fold_id": fold.fold_id, "mode": mode,
            "universe": ",".join(sorted(universe)), "n_universe": len(universe),
            "n_train_complete": int(train_mask.sum()),
            "n_test_complete": int(test_mask.sum()),
            "score_threshold_q90_train": threshold,
            "n_test_events": int(test_out["is_event"].sum()),
            "event_share_test": float(test_out["is_event"].mean())
                if len(test_out) else float("nan"),
            "train_dates": f"{fold.train_dates[0]}..{fold.train_dates[-1]}",
            "test_dates": f"{fold.test_dates[0]}..{fold.test_dates[-1]}",
        })
        out_rows.append(train_out)
        out_rows.append(test_out)

    res = (pd.concat(out_rows, ignore_index=True)
             .sort_values(["date", "is_train", "fold_id"],
                          ascending=[True, False, True])
             .reset_index(drop=True))
    return res, pd.DataFrame(summary_rows)
