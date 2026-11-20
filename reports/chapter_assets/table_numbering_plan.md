# Table numbering plan — v2.0.2 pre-write, figures refreshed v2.1.0

**Status:** authoritative for thesis table numbers.
**Scope:** Chapters 1–6 and appendices.
**Rule:** numbers are assigned by chapter and order of first citation; existing
slots are preserved wherever they are internally consistent. Panel tables use
`a/b` suffixes. No frozen numeric table is renumbered or rewritten.

**Print assets:** `reports/chapter_assets/print_tables/` (28 CSVs + manifest).
**Figure assets:** `outputs/figures/static/` (F1–F10, 300 dpi PNG + PDF).
**Reference scaffold:** `reports/chapter_assets/ch2_references_scaffold.csv`.

---

## 1. Conflict resolution

Two scaffold files carry local slot lists that disagree with the full chapter
packs. Both are hash-audited in `docs/chapter_artifact_map.md`, so they are
**not edited** in this sprint. Their local lists are superseded by this plan.

### 1.1 Chapter 3

| source | local slot list | canonical decision |
|---|---|---|
| `ch3_methodology_pack.md` | 3.0 design; 3.1 timeline; 3.2 folds; 3.3 features; 3.4 estimator; 3.5 protocol | **canonical** |
| `ch3_walk_forward_diagram.md` | 3.1 folds; 3.2 features | superseded |

The methodology pack covers the whole chapter and is consistent with the
chapter map (`3.3` walk-forward, `3.4` features). The diagram file audits the
figure, not the table numbers. Canonical: **Table 3.2 = folds**, **Table 3.3 =
feature dictionary**. Print files `table_3_2_fold_boundaries.csv` and
`table_3_3_feature_dictionary.csv` use those numbers.

### 1.2 Chapter 4

| source | local slot list | canonical decision |
|---|---|---|
| `ch4_data_engineering_pack.md` | 4.0 timings; 4.1 licence; 4.2 audit; 4.3 reconciliation; 4.4 universe; 4.5 drift | **canonical** |
| `ch4_pipeline_diagram.md` | 4.1 audit; 4.2 reconciliation; 4.3 drift | superseded |

The data pack covers the whole chapter and preserves the `4.0` design-table
convention. Canonical: **4.0 timings**, **4.1 licence**, **4.2 audit**, **4.3
reconciliation**, **4.4 universe**, **4.5 drift**. The diagram's local list
omits the timing and licence tables, so it cannot be the chapter-wide plan.

### 1.3 Chapter 5

The results skeleton already defines `5.1`–`5.5` and refers to “Tables 5.6/5.7”
for the nine v2 checks. This plan preserves those slots:

- **Table 5.6** = inference concordance: multiplicity/dependence, liquidity and
  EGARCH checks (sections 5.6.1–5.6.4).
- **Table 5.7** = distributional, specification and economic checks (sections
  5.6.5–5.6.9), printed as panels **5.7a–5.7e**.

No downstream renumbering is required.

---

## 2. Canonical table inventory

Status vocabulary: `PRINT_READY` = CSV exists in `print_tables/`;
`STUDENT_AUTHORED` = scaffold exists but prose/rows are the student's;
`REUSED` = same table cited in another chapter; `APPENDIX` = full detail, not a
main-text table.

### Chapter 1 — Introduction

| table | title | status | print CSV | primary source |
|---|---|---|---|---|
| 1.1 | Pre-declared hypothesis grid and final classification | PRINT_READY | `table_1_1_hypothesis_grid.csv` | `outputs/tables/hypothesis_grid_results_v2.csv`; `v2_final_headline_set.csv` |
| 1.2 | Canonical headline preview | PRINT_READY | `table_1_2_headline_preview.csv` | `outputs/tables/v2_final_headline_set.csv` |
| 1.3 | Economic magnitude versus the declared cost floor | PRINT_READY | `table_1_3_economic_magnitude.csv` | `outputs/tables/economic_magnitude.csv` |

### Chapter 2 — Literature

| table | title | status | print CSV | primary source |
|---|---|---|---|---|
| 2.1 | Literature matrix by stream | STUDENT_AUTHORED | — | `reports/chapter_assets/ch2_literature_matrix.csv` |
| 2.2 | Comparison with the closest studies | STUDENT_AUTHORED | — | `reports/chapter_assets/ch2_comparison_table.csv` |

No print CSV is generated for 2.1/2.2 because their rows are deliberately
unresolved (`TODO(student)`, `CMP-TODO-*`). The 39 metadata-verified records in
`ch2_references_scaffold.csv` support the student's reading, but the matrix
requires the student's own content judgements. The scaffold records
`content_review_status = NOT_REVIEWED`; metadata verification is not a claim
that the student has read the paper.

### Chapter 3 — Methodology

| table | title | status | print CSV | primary source |
|---|---|---|---|---|
| 3.0 | Design summary | PRINT_READY | `table_3_0_design_summary.csv` | `docs/analysis_plan.md`; v2 extension |
| 3.1 | Pre-declaration and freeze timeline | PRINT_READY | `table_3_1_predeclaration_timeline.csv` | plan headers; experiment register |
| 3.2 | Anchored walk-forward folds and OOS counts | PRINT_READY | `table_3_2_fold_boundaries.csv` | `outputs/tables/anomaly_scoring_summary.csv` |
| 3.3 | Feature and outcome dictionary | PRINT_READY | `table_3_3_feature_dictionary.csv` | `reports/chapter_assets/ch3_feature_dictionary.csv` |
| 3.4 | Estimator and inference matrix | PRINT_READY | `table_3_4_estimator_matrix.csv` | frozen plans; register |
| 3.5 | Event-study and robustness protocol matrix | PRINT_READY | `table_3_5_protocol_matrix.csv` | frozen plans; register |

Table 3.3 is a content-identical copy of the audited scaffold with one
malformed CSV field correctly quoted. See §5.

### Chapter 4 — Data engineering

| table | title | status | print CSV | primary source |
|---|---|---|---|---|
| 4.0 | Stage-6 clean-rebuild steps and timings | PRINT_READY | `table_4_0_pipeline_timings.csv` | `outputs/logs/v2_stage6_rebuild_timings.csv` |
| 4.1 | Source and licence matrix | PRINT_READY | `table_4_1_licence_matrix.csv` | `reports/licence_review.md`; `LICENSE` |
| 4.2 | Corpus quality audit summary | PRINT_READY | `table_4_2_corpus_audit.csv` | Ch.4 pack; `corpus_*` tables |
| 4.3 | Volume reconciliation summary | PRINT_READY | `table_4_3_volume_reconciliation.csv` | `outputs/tables/volume_reconciliation.csv` |
| 4.4a | Universe selection ranking | PRINT_READY | `table_4_4a_universe_selection.csv` | `outputs/tables/universe_selected_top10.csv` |
| 4.4b | Universe exclusions | PRINT_READY | `table_4_4b_universe_exclusions.csv` | `outputs/tables/universe_exclusions.csv` |
| 4.5a | Clean-rebuild drift summary | PRINT_READY | `table_4_5a_drift_summary.csv` | `outputs/tables/v2_clean_rebuild_audit.csv` |
| 4.5b | Clean-rebuild drift, artifact detail | APPENDIX | `table_4_5b_drift_detail.csv` | same |

Table 4.1 supersedes the “tier1 pending” wording in the Ch.4 pack and
`reports/limitations.md` L4. The live Kaggle metadata declares MIT; upstream
NEPSE Alpha remains `UNCERTAIN`. The provenance manifest stays authoritative per
file. See `reports/licence_review.md`.

Table 4.0's source log is local and gitignored; the print CSV is the tracked
projection. It records 21/21 exit-0 steps and a 4,209.8 s total. No step was
re-run to make the table.

### Chapter 5 — Results

| table | title | status | print CSV | primary source |
|---|---|---|---|---|
| 5.1 | Sample, folds and effective N | PRINT_READY | `table_5_1_sample_effective_n.csv` | `hypothesis_grid_results_v2.csv` |
| 5.2 | Main hypothesis grid | PRINT_READY | `table_5_2_main_grid.csv` | `hypothesis_grid_results_v2.csv` |
| 5.3 | Canonical final headline set | PRINT_READY | `table_5_3_canonical_headline_set.csv` | `v2_final_headline_set.csv` |
| 5.4 | Event-study inference | PRINT_READY | `table_5_4_event_study.csv` | `event_study_upgraded.csv` |
| 5.5 | Robustness battery survival | PRINT_READY | `table_5_5_robustness_survival.csv` | `robustness_headline_survival.csv` |
| 5.6 | Inference concordance across v2 checks | PRINT_READY | `table_5_6_inference_concordance.csv` | grid + SE concordance + liquidity + EGARCH |
| 5.7a | Quantile tail estimates | PRINT_READY | `table_5_7a_quantile_tails.csv` | `quantile_tail_summary.csv` |
| 5.7b | Trade-size heterogeneity, primary | PRINT_READY | `table_5_7b_trade_size.csv` | `trade_size_heterogeneity.csv` |
| 5.7c | H7 specification-curve summary | PRINT_READY | `table_5_7c_specification_curve.csv` | `specification_curve_h7_summary.csv` |
| 5.7d | Subgroup heterogeneity grid | PRINT_READY | `table_5_7d_subgroups.csv` | `heterogeneity_subgroups.csv` |
| 5.7e | Economic magnitude versus cost floor | PRINT_READY | `table_5_7e_cost_floor.csv` | `economic_magnitude.csv` |

Table 5.3 is the full 11-column canonical set. Table 1.2 is the eight-column
preview of the same frozen rows; cite 1.2 in the introduction and 5.3 in the
results. Table 5.7e repeats Table 1.3's values with the source `note` column;
cite 1.3 for the preview and 5.7e for the full result.

### Chapter 6 — Discussion

| table | title | status | print CSV | primary source |
|---|---|---|---|---|
| — | No new numbered main-text table | REUSED | — | Table 5.3; F9; F10 |

Chapter 6 reuses Table 5.3 and Figures 5.6/6.1. The limitations register remains
`reports/limitations.md`; if the student wants it as a table, place it in
Appendix C as **Table C.1** rather than creating a Ch.6 numeric slot. The broker
panel descriptives belong in Appendix B (**Table B.1**), next to F10, because
they are descriptive and monthly-aggregated.

---

## 3. Appendix table plan

| appendix table | contents | source |
|---|---|---|
| B.1 | Broker panel and core–periphery descriptives | `outputs/tables/broker_panel_summary.csv`; `broker_core_definition_sensitivity.csv`; `broker_core_transitions.csv` |
| C.1 | Limitations register L1–L26 | `reports/limitations.md` |
| D.1 | Full clean-rebuild drift audit (73 rows) | `table_4_5b_drift_detail.csv` |
| D.2 | Full H7 specification curve (144 rows) | `outputs/tables/specification_curve_h7.csv` |
| D.3 | Full trade-size sensitivity (36 extra rows) | `outputs/tables/trade_size_heterogeneity.csv` |
| D.4 | Full subgroup grid (40 rows) | `table_5_7d_subgroups.csv` |

Appendix tables are numbered by appendix letter and are not part of the
chapter table sequence.

---

## 4. Figure cross-reference (advisory)

The Phase-C static figures are the numbered thesis figures. This mapping
supersedes the legacy dynamic-figure slots in `ch5_results_skeleton.md`; those
source PNGs remain available for the dashboard and are not the print set.

| thesis figure | Phase-C file | chapter/section | title |
|---|---|---|---|
| 3.1 | `ch3_walk_forward_diagram.md` | Ch.3 §3.3 | Anchored purged walk-forward schematic |
| 3.2 | `f3_feature_small_multiples.png` | Ch.3 §3.4 | Daily network-feature trajectories |
| 4.1 | `ch4_pipeline_diagram.md` | Ch.4 §4.1 | Clean-rebuild pipeline schematic |
| 4.2 | `f1_corpus_coverage.png` | Ch.4 §4.3 | Corpus coverage by year and source |
| 4.3 | `f2_audit_panel.png` | Ch.4 §4.3 | Corpus and feature-build audit |
| 5.1 | `f7_placebo_quantile_summary.png` | Ch.5 §5.3 | Placebo null intervals versus observed effects |
| 5.2 | `f6_event_study_path.png` | Ch.5 §5.4 | Event-study abnormal-return path |
| 5.3 | `f8_tier_locality.png` | Ch.5 §5.5/§5.6.8 | H10 tier locality |
| 5.4 | `f4_h10_quantile_curve.png` | Ch.5 §5.6.5 | H10 quantile curve |
| 5.5 | `f5_h7_specification_curve.png` | Ch.5 §5.6.7 | H7 specification curve |
| 5.6 | `f9_cost_benefit.png` | Ch.5 §5.6.9 | Headline effects versus cost floor |
| 6.1 | `f10_broker_snapshots.png` | Ch.6 §6.4 | Broker-network snapshots |

All Phase-C files are 300 dpi PNG + PDF with the footer
`EXP-id · data <12-hex> · v2.1.0`. Provenance and blank-check results are in
`outputs/figures/static/figure_manifest.csv`.

---

## 5. Known source quirks and print-copy handling

| source | quirk | handling |
|---|---|---|
| `reports/chapter_assets/ch3_feature_dictionary.csv` | Line 4 has an unquoted comma in the final `notes` field; `pandas.read_csv` raises `ParserError` | Source untouched (audited hash). Print copy quotes only that field; content identical. |
| `outputs/logs/v2_stage6_rebuild_timings.csv` | Local and gitignored | Print CSV is the tracked evidence projection; source SHA-256 recorded in the manifest. |
| `outputs/tables/se_concordance.csv` | Contains literal `NULL (0/4)` labels; pandas' default NA list can misread `NULL` | Read with `keep_default_na=False`; numeric count column `n_sig_p_lt_10` retained. |
| `outputs/tables/v2_clean_rebuild_audit.csv` | Documents a 2.03e-12 relative drift in `broker_id_defect_sensitivity.csv`, while the prose summary's 3.55e-14 refers to the regression-table subset | Footnote in Table 4.5a states both figures; no value is changed. |
| `outputs/tables/economic_magnitude.csv` | H4 is opposite-sign post hoc | Every cost table flags H4; no table presents it as a tradable directional signal. |

---

## 6. Citation rules for the student

1. Cite a table by its canonical number and panel letter, e.g. “Table 5.7d”,
   never by CSV filename in the thesis body.
2. Every numeric sentence must resolve to an EXP key in the chapter pack or
   experiment register. The table number alone is not a citation.
3. Do not quote a rounded value from a print CSV as if it were more precise than
   the source. The manifest records the rounding rule.
4. Do not add a table between existing numbers. Add it as the next free number
   in the chapter, or as an appendix table, and update this plan.
5. Table 2.1/2.2 remain student-authored. Do not paste `TODO(student)` or
   `CMP-TODO-*` rows into the thesis.

---

## 7. Verification status

- 28 print CSVs generated; all parse with `pandas.read_csv`.
- Every print CSV has a source hash, output hash, transform, rounding rule and
  footnote in `print_tables/table_manifest.csv`.
- No print table introduces a new estimate, test, model fit or robustness check.
- The 39 Ch.2 records have Crossref HTTP 200 metadata and DOI HTTP 302
  resolution; content review remains `NOT_REVIEWED`.
- Frozen result tables and audited scaffold hashes are unchanged.
