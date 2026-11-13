# Figure 4.1 — Clean-rebuild pipeline (schematic)

**Status:** handoff scaffold, not a result figure. Step order is the ordered
`STEPS` list in `scripts/run_stage6_rebuild.py`; the student redraws it.

```mermaid
flowchart TD
    R["Raw archives<br/>data/raw/ — untouched"] --> U["universe"]
    U --> I["ingest"]
    I --> A["audit"]
    A --> O["ohlcv"]
    O --> V["reconcile"]
    V --> F["daily_features"]
    F --> X["outcomes"]
    X --> P["broker_persistence"]
    P --> S["feature_summary"]
    S --> N["anomaly_scoring"]
    N --> G["panel_regressions"]
    G --> E["regime_split"]
    E --> C["event_study"]
    C --> B["robustness"]
    B --> D["dashboard_cache"]
    D --> Q["engine_validation"]
    Q --> V1["v2_stage1"]
    V1 --> V2["v2_stage2"]
    V2 --> V3["v2_stage3"]
    V3 --> V4["v2_stage4"]
    V4 --> H["final_headline_set"]

    H --> T["outputs/tables/<br/>tables of record"]
    H --> L["outputs/logs/<br/>rebuild log + timings<br/>(local evidence)"]
    H --> Z["data/processed/ + data/duckdb/<br/>rebuildable derivatives"]
```

**Slots.**
- Figure 4.1 = this pipeline schematic (student redraws).
- Table 4.1 = corpus audit summary (`corpus_*` tables; `notebooks/01_data_quality_audit.ipynb`).
- Table 4.2 = volume reconciliation summary (`outputs/tables/volume_reconciliation.csv`).
- Table 4.3 = clean-rebuild drift audit (`outputs/tables/v2_clean_rebuild_audit.csv`).

**Citation keys.** EXP-0002b/c/e/f (corpus + reconciliation), EXP-0013 (clean
rebuild + freeze). Raw archives are provenance anchors and are never deleted by
the driver.
