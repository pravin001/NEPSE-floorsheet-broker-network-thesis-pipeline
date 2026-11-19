# Chapter 4 — Data engineering · handoff pack (v2.0.1)

**Status:** skeleton + verified asset manifest. **No thesis prose.** The student
writes the data-engineering chapter; this pack supplies section slots, verified
sources and EXP keys.

**Reproducibility references:** `docs/reproducibility.md`; Stage-6 rebuild
driver `scripts/run_stage6_rebuild.py`.

---

## 4.1 Pipeline architecture

**Claim slot.** A 21-step ordered pipeline rebuilds every derived artefact from
the raw archives; the Stage-6 driver deletes only `data/processed/` and
`data/duckdb/`, asserts `data/raw/` is unchanged, and aborts on any non-zero
step.

- Figure 4.1 slot: pipeline schematic
  (`reports/chapter_assets/ch4_pipeline_diagram.md`).
- Table 4.0 slot: step order and timings (from
  `outputs/logs/v2_stage6_rebuild_timings.csv`, local evidence; summary in
  `docs/reproducibility.md`).
- Source: `scripts/run_stage6_rebuild.py`.

**Citation keys:** EXP-0013.

## 4.2 Provenance and licensing

**Claim slot.** Every raw file and derived table carries a SHA-256 provenance
row; the code is MIT, the 2021–2023 floorsheets are CC0, the 2024 floorsheets
are MIT with attribution, and the tier1 OHLCV licence remains pending.

- Table 4.1 slot: source/licence matrix.
- Sources: `data/metadata/provenance_manifest.csv` (authoritative, self-
  referential); `data/metadata/corpus_files_sha256.csv`;
  `docs/ai_use_policy.md`.
- Boundary: `reports/limitations.md` L4 (figures restricted until tier1 licence
  confirmed).

**Citation keys:** EXP-0002b, EXP-0002d, EXP-0007.

## 4.3 Corpus quality audit

**Claim slot.** The corpus contains 57,927,926 raw rows → 57,892,630 after
deduplication (35,296 page-split drops), 1,167 day files, 530 symbols and
938/940 calendar sessions; 752 duplicate keys (506 exact, 246 signature-
conflict non-merged), 19 junk (symbol,date) pairs plus 4 empty-symbol rows, and
the 2023-02-16 `contract_no_defect` (35,043 rows, one transaction id).

- Table 4.2 slot: audit summary.
- Sources: `notebooks/01_data_quality_audit.ipynb`;
  `outputs/tables/corpus_daily_summary.csv`;
  `outputs/tables/corpus_duplicate_keys.csv`;
  `outputs/tables/corpus_missing_broker_ids.csv`;
  `outputs/tables/corpus_low_activity_days.csv`;
  `outputs/tables/corpus_symbol_coverage.csv`.

**Citation keys:** EXP-0002b, EXP-0002c, EXP-0002f.

## 4.4 Volume reconciliation

**Claim slot.** Floorsheet volume counts the buyer side: top-12 median
floorsheet/OHLCV volume ratio 1.0000, 96.6% of pairs in [0.95,1.25] and 94.7% in
[0.98,1.02]; the full-market ~2× ratio is a tier1-coverage artifact, not a
finding.

- Table 4.3 slot: reconciliation summary.
- Source: `outputs/tables/volume_reconciliation.csv`.
- Boundary: `reports/limitations.md` L12.

**Citation keys:** EXP-0002e.

## 4.5 Universe, OHLCV and feature/outcome construction

**Claim slot.** The top-10 universe is selected on TRAIN-fold turnover with a
≥90% coverage rule; OHLCV uses tier1 primary plus tier2 gap-fill with
`ohlcv_source` propagated; features and outcomes are built per the frozen plan.

- Table 4.4 slot: universe and exclusion counts.
- Sources: `outputs/tables/universe_selected_top10.csv`;
  `outputs/tables/universe_exclusions.csv`;
  `docs/analysis_plan.md` §1/§2.
- Builders: `scripts/select_top10.py`, `scripts/build_ohlcv.py`,
  `scripts/build_daily_features.py`, `scripts/build_outcomes.py`.

**Citation keys:** EXP-0002a, EXP-0002d, EXP-0003a/b.

## 4.6 Clean rebuild and drift audit

**Claim slot.** The v2.1.0 correction rebuild completed 21/21 steps with exit
0 in 4,209.8 s (70.2 min), reading only the untouched raw archives, and rebuilt
every dependent table from source. The pre-fix v2.0.2 Stage-6 audit had shown
the pipeline itself was deterministic (73 tracked tables: 40 byte-identical,
25 at ≤3.55e-14 relative, 4 reorder-only, 2 QuantReg optimizer drifts 7.44e-7,
1 float-aggregation difference, 1 descriptive sequential-fold threshold flip).
v2.1.0 keeps the v2.0.2 tables byte-for-byte in
`outputs/tables/superseded_v2_0_2/` and records the old-vs-new identity
`old = 2 × (corrected + self_loop_share)` on all 233,706 rows.

- Table 4.5 slot: drift audit (historical v2.0.2:
  `outputs/tables/v2_clean_rebuild_audit.csv`); v2.1.0 rebuild log
  `outputs/logs/v2_stage6_rebuild.log`.
- Source: `docs/reproducibility.md`; `configs/v2_freeze/freeze_manifest.csv`;
  `reports/reciprocity_correction.md`.

**Citation keys:** EXP-0013 (v2.0.2 freeze), EXP-0015 (v2.1.0 correction).

---

## Verified asset manifest

Machine-readable: `reports/chapter_assets/ch4_asset_manifest.csv`.

| asset | role | version | EXP keys |
|---|---|---|---|
| `scripts/run_stage6_rebuild.py` | 21-step driver | v2 | EXP-0013 |
| `data/metadata/corpus_files_sha256.csv` | per-file provenance | v1 | EXP-0002b |
| `docs/ai_use_policy.md` | licence register | v2 | EXP-0002d |
| `notebooks/01_data_quality_audit.ipynb` | executable audit | v1 | EXP-0002f |
| `outputs/tables/volume_reconciliation.csv` | volume check | v1 | EXP-0002e |
| `outputs/tables/v2_clean_rebuild_audit.csv` | drift evidence | v2 | EXP-0013 |
| `docs/reproducibility.md` | rebuild record | v2 | EXP-0013 |
| `reports/chapter_assets/ch4_pipeline_diagram.md` | Figure 4.1 scaffold | v2 handoff | EXP-0013 |

**Note.** The licence register was rewritten in the v2.0.2 pre-write sprint
(Phase D), so its crosswalk row is now `v2 | VERIFIED`. The v1 file remains in
git history and its old hash remains in the append-only provenance manifest;
no numeric result changed.
