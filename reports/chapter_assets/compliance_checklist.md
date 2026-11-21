# Pre-submission compliance checklist — v2.1.0 reciprocity correction

**Purpose.** A single sign-off list for the student before the thesis is
submitted or deposited. It separates what the release already verified
(`DONE`) from what only the student can verify (`STUDENT`) and what depends on
the deposit decision (`CONDITIONAL`).

**Version note (2026-11-19).** v2.1.0 corrects `reciprocity_volume` and
rebuilds every dependent result (EXP-0015; deviation #45). The v2.0.2 values
are superseded and preserved in `outputs/tables/superseded_v2_0_2/`.

**Rule.** A checked box is not proof of correctness. The evidence column names
the file or command that must be inspected. If an item cannot be evidenced, it
stays unchecked.

**Status vocabulary**

| status | meaning |
|---|---|
| `DONE` | Verified in the v2.1.0 release; evidence path exists. |
| `STUDENT` | Requires the student's reading, writing, or institutional decision. |
| `CONDITIONAL` | Depends on whether and where the thesis is deposited. |
| `PENDING` | Phase-F action still to be completed at the time this file was written. |

---

## 1. Frozen-analysis and repository integrity

| ID | check | evidence | status |
|---|---|---|---|
| A1 | v2.1.0 is a registered bug-fix release: no new hypothesis, regression, robustness variant, specification search or prediction model was added. | `docs/experiment_register.md` EXP-0015; `docs/analysis_deviations.md` #45; `reports/reciprocity_correction.md` | DONE |
| A2 | The canonical headline set is the corrected v2.1.0 set: H6 `HEADLINE_ROBUST` and H10 `HEADLINE_MODERATE`; H4 `EXPLORATORY_POST_HOC`; H7/H8 `NULL_FRAGILE`; H1/H2/H3/H5/H9 `NULL_POWERED`. | `outputs/tables/v2_final_headline_set.csv`; `reports/chapter_assets/print_tables/table_5_3_canonical_headline_set.csv` | DONE |
| A3 | H10 reproduces exactly from the corrected inputs: β `+20.641998360399068 bp`, DK p `0.001362135102402554`, n `7,116`, n_eff `6,383`. | `outputs/tables/verification_h10_recompute.csv`; `docs/analysis_deviations.md`; `scripts/verify_h10_independent.py` | DONE |
| A4 | Spot checks reproduce: H7 `+3.9523733421516263 bp`; H10 RW p `.012`; event-study CAR `+19.32624055663073 bp`, p `.4018346125607248`. | `outputs/tables/verification_spot_checks.csv` | DONE |
| A5 | No pre-fix result is silently lost: the v2.0.2 tables are preserved byte-for-byte and checksummed; the corrected tables are the new primary record. | `outputs/tables/superseded_v2_0_2/` (43 CSVs + `MANIFEST.sha256`); `reports/reciprocity_correction.md`; `git diff` shows the dependent live tables updated | DONE |
| A6 | Full test suite passes and the result is logged. | `nepse-msc/bin/pytest tests notebooks/*_*.ipynb --nbmake -q` — **177 passed, 0 failed** (unit/leakage/SE-spec/freeze/chapter-map + 2 notebooks) on 2026-11-19 | DONE |
| A7 | The release commit and tag exist and point at the tested tree. | `git log -1`; `git tag --points-at HEAD` (tag `v2.1.0-reciprocity-correction`) | DONE |

---

## 2. Data and licence

| ID | check | evidence | status |
|---|---|---|---|
| B1 | The licence position is stated in two layers: the dataset grant as quoted, and upstream clarity. | `reports/licence_review.md`; `reports/chapter_assets/print_tables/table_4_1_licence_matrix.csv` | DONE |
| B2 | Tier1 Kaggle metadata is quoted as `MIT`; the description's “educational and research purposes” wording and “scraped from NEPSE Alpha” are disclosed. | `reports/licence_review.md` §1; Table 4.1 | DONE |
| B3 | Upstream NEPSE Alpha rights remain `UNCERTAIN`; no permission is inferred from silence. | `reports/licence_review.md`; `reports/limitations.md` L4 (note: L4's “pending” wording is superseded by Table 4.1; the hash-audited L4 is not edited) | DONE |
| B4 | `viking303` floorsheets are quoted as `CC0: Public Domain`; `socrateai` 2024 floorsheets are quoted as MIT-style with notice; `SamirWagle` and `menaceXnadin` are `license:null` with educational/unofficial-mirror caveats. | `reports/licence_review.md`; Table 4.1 | DONE |
| B5 | The thesis does not redistribute raw floorsheets or raw OHLCV. | `docs/deposit_preflight.md`; `.gitignore`; `docs/deposit_readme.md` | CONDITIONAL |
| B6 | The deposit contains derived tables only, with the code licence and source notices preserved. | `dist/nepse-floorsheet-microstructure-v2.1.0-derived.tar.gz`; `docs/deposit_preflight.md` records the SHA-256 | CONDITIONAL |
| B7 | The student has decided whether Kaggle-declared MIT plus the education/research statement is sufficient for the University, or whether upstream NEPSE Alpha permission is required. | `reports/licence_review.md` §conclusions; `docs/ai_use_policy.md` §7.2 | STUDENT |
| B8 | No public upload, push, DOI registration or Zenodo/OSF/GitHub action was performed by the agent. | `git remote -v`; session record; `docs/ai_use_policy.md` §5 | DONE |
| B9 | If depositing after v2.1.0, rebuild the derived archive from the tagged commit rather than reusing the v2.0.2 archive. | `scripts/build_deposit_archive.py`; `docs/deposit_preflight.md` | CONDITIONAL |

---

## 3. Statistical reporting and interpretation

| ID | check | evidence | status |
|---|---|---|---|
| C1 | Every numeric sentence resolves to an `EXP-*` key and a canonical table or figure. | `docs/experiment_register.md`; chapter packs; `reports/chapter_assets/key_claims_sheet.md` | STUDENT |
| C2 | The final classification is quoted from the canonical table, not re-derived from a p-value. | `outputs/tables/v2_final_headline_set.csv`; Table 5.3 | STUDENT |
| C3 | H10 is described as `HEADLINE_MODERATE`, not “robust” or “strong”. DK p `.0014`, RW p `.012`, WB p `.004`, FM p `.4901`, SE concordance `MODERATE`. | Table 5.3; `outputs/tables/se_concordance.csv`; `reports/limitations.md` L9 | STUDENT |
| C4 | H4 is described as `EXPLORATORY_POST_HOC` with the opposite sign to the pre-declaration. It is not presented as confirmation. | `outputs/tables/hypothesis_grid_results_v2.csv`; `reports/limitations.md`; key-claims sheet | STUDENT |
| C5 | H7/H8 are described as `NULL_FRAGILE`; their DK p-values are not presented as headline discoveries. H6 is `HEADLINE_ROBUST` (not fragile) and must not be lumped with them. | `outputs/tables/v2_final_headline_set.csv`; `reports/limitations.md` L8/L16 | STUDENT |
| C6 | H1/H2/H3/H5/H9 are described as `NULL_POWERED`, with MDE caveats where relevant. | `outputs/tables/hypothesis_grid_results_v2.csv`; `reports/limitations.md` | STUDENT |
| C7 | The IF anomaly-score channel is described as null; H2/H3 placebo shares `.805`/`.540` are reported. | `outputs/tables/hypothesis_grid_results_v2.csv`; key-claims sheet | STUDENT |
| C8 | `self_loop_ratio` is called a self-loop volume share, **not** wash trading or manipulation. | `reports/limitations.md` L10; `reports/chapter_assets/ch3_feature_dictionary.csv` | STUDENT |
| C9 | All estimates are described as predictive/associational, not causal. No instrument, exogenous shock or event timing identifies a causal effect. | `reports/limitations.md` L1 | STUDENT |
| C10 | The external replication tier is reported as a failure: 0/5 BH pass, smallest raw p `.0539`, magnitudes attenuate. No market-wide claim. | `outputs/tables/robustness_top5_external_grid.csv`; `outputs/tables/robustness_headline_survival.csv`; `reports/limitations.md` L2 | STUDENT |
| C11 | The event-study overlap is disclosed: 666 events on 392 dates; 435 events (65.3%) share a date; event-level p-values are upper bounds. | `outputs/tables/event_study_upgraded.csv`; `reports/limitations.md` L13 | STUDENT |
| C12 | The market-adjusted event-study variant is not quoted as an event effect; its negative mean is a pre-window-alpha artefact. | `reports/heterogeneity_event_study.md`; `reports/limitations.md` L13 | STUDENT |
| C13 | Quantile tail labels for null hypotheses are described as unadjusted/descriptive, not as new findings. | `outputs/tables/quantile_tail_summary.csv`; `docs/analysis_deviations.md` #18 | STUDENT |
| C14 | The cost-floor comparison is reported: H10 `20.642 bp/SD` is 1.45–2.42× below the 30–50 bp floor; H10 is the absolute-return association, while H6 is a signed-return association with an ambiguous pre-declared direction and is not costed as a directional strategy; H7 and H4 are also below; none is standalone tradable at 1 SD. | `outputs/tables/economic_magnitude.csv`; Table 5.7e; `reports/limitations.md` | STUDENT |
| C15 | The wild-cluster-bootstrap caveat is stated: only 12 symbol clusters; WB is a concordance signal, not a replacement primary. | `reports/liquidity_robustness.md`; `docs/analysis_deviations.md` #16 | STUDENT |
| C16 | The broker-ID defect sensitivity is disclosed where relevant: 37/7,116 OOS rows (0.52%); H8 loses raw 5% (p .0563), other signs unchanged. | `outputs/tables/broker_id_defect_sensitivity.csv`; `reports/limitations.md` L20 | STUDENT |
| C17 | The 2023-02-16 contract-number defect is disclosed: ordering-dependent features exclude the day; level aggregates keep it. | `reports/limitations.md` L7; `outputs/tables/corpus_duplicate_keys.csv` | STUDENT |
| C18 | No p-value is described as “significant” without naming the gate (DK, BH, RW, WB, FM) and the family/multiplicity rule. | `reports/chapter_assets/key_claims_sheet.md`; Table 5.6 | STUDENT |

---

## 4. Tables and figures

| ID | check | evidence | status |
|---|---|---|---|
| D1 | Table numbers follow `reports/chapter_assets/table_numbering_plan.md`; no ad hoc renumbering. | `reports/chapter_assets/table_numbering_plan.md` | DONE |
| D2 | Print CSVs are used as projections, not hand-edited; the source remains authoritative. | `reports/chapter_assets/print_tables/README.md`; `table_manifest.csv` | DONE |
| D3 | Table 3.3's malformed source field is handled by the print copy only; the audited source is untouched. | `table_manifest.csv`; `reports/chapter_assets/ch3_feature_dictionary.csv` | DONE |
| D4 | Table 4.1 and L4 state the same current two-layer licence position: Kaggle tier1 metadata declares MIT, while upstream NEPSE Alpha clearance is `UNCERTAIN`. The provenance manifest remains authoritative per file. | `reports/licence_review.md`; `reports/limitations.md` L4; `reports/chapter_assets/print_tables/table_4_1_licence_matrix.csv` | DONE |
| D5 | Figures F1–F10 are 300 dpi PNG + PDF, regenerated from the corrected v2.1.0 tables, with the footer `EXP-id · data <12-hex> · v2.1.0`, and every PNG passed the blank check (10/10 PASS). | `outputs/figures/static/figure_manifest.csv`; `outputs/figures/static/*.png/.pdf` | DONE |
| D6 | F7's panel note discloses that it plots the frozen permutation quantiles, not the 1,000 draw-level values. | `outputs/figures/static/figure_manifest.csv`; `docs/analysis_deviations.md` #33 | DONE |
| D7 | F10's note discloses that it composites the two frozen network renders rather than rebuilding edge lists. | `outputs/figures/static/figure_manifest.csv`; `docs/analysis_deviations.md` #34 | DONE |
| D8 | Figure numbers follow the advisory Phase-C mapping, not the legacy dynamic-figure slots. | `reports/chapter_assets/table_numbering_plan.md` §4 (F1–F10 slots 4.1–6.1) | STUDENT |
| D9 | Every figure caption is written by the student, matches the plotted data, and names the source/EXP key. | `outputs/figures/static/figure_manifest.csv` caption scaffolds; student's final captions | STUDENT |
| D10 | No figure plots a raw OHLCV series or a licence-restricted index: F1/F8 and the other static figures read derived tables only, and the NEPSE index is a secondary regime-shading input, not a plotted series. | `outputs/figures/static/figure_manifest.csv` `input_artifacts`; `reports/licence_review.md` §3 | DONE |

---

## 5. References and literature

| ID | check | evidence | status |
|---|---|---|---|
| E1 | Every reference in the thesis has a real, retrieved DOI/URL and a timestamp. | `reports/chapter_assets/ch2_references_scaffold.csv`; `ch2_reference_retrieval_log.csv` | DONE |
| E2 | The 39 scaffold records are Crossref HTTP 200 and DOI HTTP 302; no reference was generated from memory. | `ch2_reference_retrieval_log.csv` | DONE |
| E3 | `content_review_status` is changed from `NOT_REVIEWED` only after the student has read the paper and confirmed the cited claim. | `ch2_references_scaffold.csv`; `ch2_reference_verification.md` §2 | STUDENT |
| E4 | The SSRN record `10.2139/ssrn.2793509` is labelled as posted content/working paper, not a final journal article. | `ch2_references_scaffold.csv`; `ch2_reference_verification.md` §4 | STUDENT |
| E5 | No `TODO(student)` or `CMP-TODO-*` row appears in the thesis. | `ch2_literature_matrix.csv`; `ch2_comparison_table.csv`; final thesis | STUDENT |
| E6 | The comparison table is filled with verified studies and the student's own reading, not AI-invented rows. | `reports/chapter_assets/ch2_comparison_table.csv` | STUDENT |
| E7 | Citation style, page ranges, volume/issue and year are checked against the publisher's version. | `ch2_references_scaffold.csv`; publisher pages via DOI | STUDENT |
| E8 | No quotation is attributed to a paper unless the student has the exact passage. | student's reference notes | STUDENT |
| E9 | The literature review is the student's prose; the scaffold and matrix are not pasted in as text. | `docs/ai_use_policy.md` §4; final thesis | STUDENT |

---

## 6. AI-use and disclosure

| ID | check | evidence | status |
|---|---|---|---|
| F1 | `docs/ai_use_policy.md` records OpenCode+GLM, OpenCode+DeepSeek, and this sprint's `DeepSeek V4.1 Flash Free`. | `docs/ai_use_policy.md` §2 | DONE |
| F2 | The policy states the permitted and prohibited roles, approval gates, provenance controls and model limitations. | `docs/ai_use_policy.md` §3–§9 | DONE |
| F3 | The policy states that no thesis prose was AI-drafted. | `docs/ai_use_policy.md` §4, §11.1 | DONE |
| F4 | The student completes the University disclosure with the institutional wording (kept private), tools, dates and sign-off. | `docs/ai_use_policy.md` §11 | STUDENT |
| F5 | The student can defend every claim and has read every chapter; a green suite is not a substitute for understanding. | `docs/ai_use_policy.md` §5 | STUDENT |
| F6 | If the model/provider changes after 2026-11-14, the policy table and University disclosure are updated. | `docs/ai_use_policy.md` §2, §12 | STUDENT |
| F7 | No AI-generated citation, result, table cell or figure value is submitted without a traceable source. | `docs/ai_use_policy.md` §6–§7; all manifests | STUDENT |

---

## 7. Deposit and submission

| ID | check | evidence | status |
|---|---|---|---|
| G1 | The deposit archive is derived-only and excludes raw data, DuckDB, processed parquet, logs and licence-restricted figures. | `docs/deposit_preflight.md`; `docs/deposit_readme.md` | CONDITIONAL |
| G2 | The archive checksum matches the recorded SHA-256. | `dist/nepse-floorsheet-microstructure-v2.1.0-derived.tar.gz`; `docs/deposit_preflight.md` | CONDITIONAL |
| G3 | The deposit README names the author, licence, data sources and exclusions. | `docs/deposit_readme.md` | STUDENT |
| G4 | The student has decided whether to upload to a repository; no upload is performed by the agent. | `docs/ai_use_policy.md` §5 | STUDENT |
| G5 | The final PDF has been checked for formatting, cross-references, table/figure numbering, word count and appendices. | final thesis PDF | STUDENT |
| G6 | The final PDF has been checked for accidental `TODO`, `NOT_REVIEWED`, `UNCERTAIN` (where not intended), placeholder rows and broken links. | final thesis PDF | STUDENT |
| G7 | The viva/defence notes do not introduce claims that are absent from the frozen analysis. | `reports/chapter_assets/key_claims_sheet.md` | STUDENT |

---

## 8. Final sign-off

| role | name | date | signature |
|---|---|---|---|
| Student | ______________________________ | __________ | ______________________________ |
| Supervisor (if required) | ______________________________ | __________ | ______________________________ |

**Submission rule.** If any `STUDENT` item is unchecked, the thesis is not ready
to submit. If any `CONDITIONAL` item is unresolved, do not deposit publicly.
