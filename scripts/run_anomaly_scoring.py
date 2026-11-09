"""EXP-0004a — PURGED ANCHORED WALK-FORWARD IF SCORING (DC1 universe).

Pre-declared execution (plan §2/§4 + fold-mode deviation 2026-11-09):
  * scoring set = EXP-0003a features, universe candidates = tier1 OHLCV
    symbols, rows=一 2023-02-16 EXCLUDED (eod undefined; 252 defect pairs;
    declared in deviations);
  * anchored folds (gap 6, warm-up chunk 0) over the 938 scoring sessions;
  * per fold TOP-10 by TRAIN-date mean tier1 turnover + DC2 >=90% coverage
    (deterministic tie-break) → universe re-selected per fold (DC1);
  * LeakSafeStandardizer (winsor 1/99) + IsolationForest(200, auto,
    if_seed(k)) fit TRAIN; test scored OOS (-decision_function);
  * event = test score >= TRAIN-fold q90 threshold; per-fold summary saved.
Output: data/processed/anomaly_scores.parquet
        outputs/tables/anomaly_scoring_summary.csv (+ preview csv).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from nepsemsc.ml.anomaly_scoring import walk_forward_anomaly_scores_dc1
from nepsemsc.utils.io import atomic_write_df, sha256_file
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.tz import utc_iso

DEFECT_DATE = "2023-02-16"


def main() -> None:
    feat = pd.read_parquet(ROOT / "data/processed/daily_features.parquet")
    # canonical scoring names (FEATURES_DEFAULT) <- module column names
    feat = feat.rename(columns={
        "self_loop_volume_ratio": "self_loop_ratio",
        "reciprocity_volume": "reciprocity",
    })
    feat["date"] = pd.to_datetime(feat["date"]).dt.date
    n0 = len(feat)
    feat = feat[feat["date"].astype(str) != DEFECT_DATE].copy()   # declared
    print(f"scoring rows: {n0:,} → {len(feat):,} (2023-02-16 excluded)")

    # candidates turnover = tier1 outcome panel  (symbol, date, turnover)
    px = pd.read_parquet(ROOT / "data/processed/daily_outcomes.parquet")
    px["date"] = pd.to_datetime(px["date"]).dt.date
    turnover = px[["symbol", "date", "turnover"]].dropna()
    print(f"turnover panel: {len(turnover):,} rows "
          f"({turnover.symbol.nunique()} symbols)")

    scores, summary = walk_forward_anomaly_scores_dc1(
        feat, turnover, n_folds=4, purge_gap_sessions=6,
        n_estimators=200, contamination="auto", mode="anchored",
        n_top=10, min_coverage=0.90, event_quantile=0.90,
    )
    print(summary[["fold_id", "universe", "n_train_complete", "n_test_complete",
                   "score_threshold_q90_train", "n_test_events",
                   "event_share_test"]].to_string(index=False))
    atomic_write_df(scores, ROOT / "data/processed/anomaly_scores.parquet")
    atomic_write_df(summary, ROOT / "outputs/tables/anomaly_scoring_summary.csv",
                    index=False)
    test_only = scores.loc[~scores["is_train"]]
    pv = test_only[["date", "symbol", "fold_id", "is_event", "anomaly_score",
                    "buyer_hhi", "self_loop_ratio", "reciprocity"]]
    atomic_write_df(pv.head(200), ROOT / "outputs/tables/anomaly_scores_preview.csv",
                    index=False)
    print(f"test rows scored OOS: {len(test_only):,} | event rows: "
          f"{int(test_only.is_event.sum()):,}")

    prov.record({
        "ts_utc": utc_iso(),
        "artifact": "data/processed/anomaly_scores.parquet",
        "kind": "walk_forward_scoring_exp0004a",
        "source_path": "daily_features.parquet (EXP-0003a) + daily_outcomes.turnover",
        "source_url": "derived", "sha256":
            sha256_file(ROOT / "data/processed/anomaly_scores.parquet"),
        "bytes": (ROOT / "data/processed/anomaly_scores.parquet").stat().st_size,
        "rows_sampled": len(scores), "rows_total": len(scores),
        "licence": "derived",
        "evidence": "; ".join(
            f"f{r.fold_id}:uni={r.universe}|thr={r.score_threshold_q90_train:.4f}"
            f"|events={r.n_test_events}" for r in summary.itertuples()),
    })
    print("SCORING_DONE")


if __name__ == "__main__":
    main()
