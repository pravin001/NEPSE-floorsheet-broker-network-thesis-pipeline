# Figure 3.1 — Anchored purged walk-forward (schematic)

**Status:** handoff scaffold, not a result figure. Redrawn from the frozen
`docs/analysis_plan.md` §4; the student renders the final figure. Event count
updated to the corrected v2.1.0 sample (666 events; EXP-0015).

```mermaid
flowchart LR
    A["940 DC3 calendar sessions<br/>938 with corpus coverage"] --> B["5 equal chunks<br/>linspace(0, n, 6)"]
    B --> C["Chunk 0<br/>warm-up train only"]
    B --> D["Fold 1 test chunk"]
    B --> E["Fold 2 test chunk"]
    B --> F["Fold 3 test chunk"]
    B --> G["Fold 4 test chunk"]

    C --> H["Fold f training set:<br/>all sessions strictly before test chunk"]
    D --> H
    E --> H
    F --> H
    G --> H

    H --> I["Purge gap = 6 sessions<br/>horizon 1 + embargo 5<br/>test_start = train_end + gap + 1"]
    I --> J["TRAIN-only winsorise + standardise<br/>TRAIN-only IsolationForest (200 trees)<br/>TRAIN-only q90 event threshold"]
    J --> K["Score test chunk<br/>-decision_function on both sides"]
    K --> L["OOS rows: 7,126<br/>events: 666 (9.3%)"]
```

**Slots.**
- Figure 3.1 = this schematic (student redraws in the thesis tool).
- Table 3.1 = fold boundaries / train-test counts (from `outputs/tables/hypothesis_grid_results_v2.csv` and the fold diagnostics table).
- Table 3.2 = feature dictionary (`ch3_feature_dictionary.csv`).

**Citation keys.** EXP-0004a (scoring), EXP-0011a (effective N), EXP-0013 (freeze).
