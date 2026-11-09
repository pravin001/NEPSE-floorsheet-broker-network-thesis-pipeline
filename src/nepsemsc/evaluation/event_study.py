"""Event study (Phase 4 deliverable; scaffold signature + SV3 chain).

Days with anomaly_score above the TRAIN-FOLD 90th percentile (DC7: thresholds
never come from the test fold) form the event set. CAR(t-5..t+5) is computed
against the market model estimated on a 60-day窗口 window of NON-event days.

Fallbacks (SV3), triggered by stated conditions:
  (a) market model, 60-day estimation window            [primary]
  (b) market-adjusted returns (stock NEPSE portfolio return) [fallback 1]
  (c) leave-one-out index for index-constituent stocks  [refinement of (b)]
  (d) raw returns, explicit joint-test caveat           [last resort]
"""
from __future__ import annotations


def event_study_car(*args, **kwargs):  # pragma: no cover — Phase 4
    raise NotImplementedError(
        "event_study_car: implemented in Phase 4 (after anomaly scores exist). "
        "SV3 chain documented in module docstring and configs/project.yaml."
    )
