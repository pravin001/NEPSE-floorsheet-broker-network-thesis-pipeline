# Analysis deviations (DC20)

Rule: NO entry here = analysis ran exactly as pre-declared in
`docs/analysis_plan.md`. Any deviation requires a timestamped row + reason.

| ts (UTC+5:45) | deviation | reason | registered? |
|---|---|---|---|
| 2026-11-09 (NPT, morning) | walk_forward default fold mode switched `sequential` → `anchored` (expanding). Implemented in `src/nepsemsc/ml/walk_forward.py`; `configs/project.yaml` + `docs/analysis_plan.md` §4 amended in the same commit | The original sequential-pairs reading (8 segments, fold k trains k / tests k+1) scores ONLY the middle segments of the 940-session 2021-01→2024-12 window — the 2021-22 bubble tail and 2024 would never receive out-of-sample scores, contradicting R7's walk-forward intent for a bubble-era sample. Anchored mode keeps purge gap = 6 (horizon 1 + embargo 5) and the identical strict-gap definition (test_start_pos = train_end_pos + gap + 1); only the train-window shape changed. Registered BEFORE any test-fold data was observed or scored (pre-scoring, Phase 2) | yes (DC20) |
