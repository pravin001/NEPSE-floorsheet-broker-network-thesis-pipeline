# AGENTS.md — project state for ANY fresh session

**Read this before doing anything.** Resume point for the whole build.
Sibling project (context only, NOT this repo): `~/research/nepse-kronos-thesis/`
(its data archives are READ-ONLY shared raw inputs).

- Project: `~/research/nepse-floorsheet-microstructure/` (venv `nepse-msc` IN-REPO —
  intentional: venv dir name ≠ package name `nepsemsc`, so no D5-style shadowing;
  pattern anchored `/nepse-msc/` in .gitignore)
- Deadline: 2026-11-27 · Today: 2026-11-14 · Engineering ends 21 Nov (writing 22-27)
- **v2.0 A++ upgrade COMPLETE** (post-`v1.0-freeze`): binding pre-declaration
  `docs/analysis_plan_v2_extension.md` (written before any v2 result). Stages 1–6
  COMPLETE (EXP-0008a–e, EXP-0009a–d, EXP-0010a–c, EXP-0011a–f, EXP-0012,
  EXP-0013); final tag `v2.0-a++-freeze` (2026-11-13).
- **v2.0.1 post-freeze handoff COMPLETE**: verified 67-claim chapter→artefact
  crosswalk, Ch.1–Ch.6 handoff packs, chapter-map integrity guard, derived-only
  deposit archive + preflight (EXP-0014); tag `v2.0.1-handoff`. Frozen
  `v2.0-a++-freeze` tag and all v1/v2 numeric files unchanged.
- **ANALYSIS FROZEN / PRE-WRITE ASSETS COMPLETE** (v2.0.2 pre-write sprint,
  Phases A–F, 2026-11-13 → 2026-11-14): canonical H10 reproduced exactly;
  licences reviewed from live sources; F1–F10 produced as 300-dpi PNG + PDF;
  AI-use policy rewritten; 39 metadata-verified reference candidates; 28
  print-ready table CSVs; full suite **161 passed**; tag `v2.0.2-prewrite`.
  No new regression, test, re-fit, robustness check or specification search
  was run. The statistical layer remains frozen.
- Binding contract: the 19-day brief (hard rules R1-R12, SV1-SV7, DC1-DC20),
  pre-declared constants in `configs/project.yaml` + `docs/analysis_plan.md` (DC20).

## Environment survey — 2026-11-08

| Fact | Value |
|---|---|
| OS | Ubuntu 26.04 (24 cores, 45 Gi RAM, RTX 5070 8 GB — GPU idle: CPU-bound thesis) |
| Python | 3.11.16 via uv-managed toolchain (`uv` 0.13.7 at ~/.local/bin) |
| git | 2.53.0; REPO-LOCAL identity `Prabin Shrestha <itsme_prabin@outlook.com>` set 2026-11-14; all commits and annotated tags rewritten to that identity; global identity intentionally untouched |
| Sys packages | no system-wide pip installs — everything lives in `nepse-msc/` |
| disk | 144G free |

## Data map (Phase-0/1 discovery + Phase-2 corpus — FINAL for the thesis window)

| Source | What | Where | Status |
|---|---|---|---|
| **floorsheet corpus 2021–2023** | Kaggle `viking303/nepse-historical-floorsheet` v14 (CC0, kagglehub cache 1.19 GB): `#,Transact. No.,Symbol,Buyer,Seller,Quantity,Rate,Amount,Date`; 2022 = 242/242 exact | `~/.cache/kagglehub/datasets/viking303/nepse-historical-floorsheet/versions/14/NEPSE_data/` | **ADOPTED 2021-01-03→2023-12-28 (708/710 kaggle sessions; 2 gaps documented)** |
| socrateai daily floorsheets (MIT) | full-market floorsheet per DAY → **PRIMARY for 2024** (232/232 sessions); kaggle-2024 (229 files) = cross-check only | `~/research/nepse-kronos-thesis/data/raw/tier3_floorsheets_socrateai/` | **ADOPTED (SV1(b))** |
| Kaggle OHLCV tier1 (100 scrips, 2012→2025-09) | daily OHLCV + turnover = `ohlcv_source='tier1_kaggle'` | `…/tier1_kaggle/*.csv` | primary OHLCV (EXP-0002d); licence pending student UI check |
| SamirWagle prices tier2 (11 scrips, →2026-11-05) | OHLCV GAP-FILL only | `…/tier2_samirwagle_prices/` | attribution; overlap median Δclose = 0.0000% |
| NEPSE composite index (menaceXnadin, 1997→2026-11-06) | 6,623 rows daily | `data/raw/external/nepse_index_adjusted.csv` | SECONDARY (repo `"license": null` → unstated_in_repo); R8 regime shading/benchmark only; swap-able |
| DuckDB corpus | `floorsheet_raw` 57,927,926 rows (+source col) · `floorsheet_dedup` 57,892,630 · audit tables | `data/duckdb/nepse.duckdb` (gitignored) | EXP-0002b/c — REBUILD: `nepse-msc/bin/python scripts/ingest_corpus.py` then `scripts/audit_corpus.py` (fresh DB); `NEPSEMS_SKIP_LOAD=1` resumes existing DB |
| Processed frontline | `data/processed/nepse_calendar.parquet` (940 sessions; col `session_date`) · `data/processed/daily_ohlcv.parquet` (205,533 rows; 9 canonical cols + ohlcv_source) · `data/metadata/universe_selected.{csv,json}` · `data/metadata/corpus_files_sha256.csv` (1,167 files) · top-12 extracts `data/raw/floorsheet/<SYM>/<YYYY-MM>.csv` (576) | — | |

Key validated facts (treat as REQUIRED reading):
* floorsheet rows are NOT in execution order → ALWAYS sort by contract_no/transaction
  before ordering statistics; contract_no is DAILY-GLOBAL → per-(symbol,date) gaps EXPECTED.
* **Volume counts buyer-side** (EXP-0002e: top-12 median fs/OHLCV ratio 1.0000; CGH day-check 910=910). Full-market ~2x ratio = scope artifact (tier1 OHLCV covers 100/530 scrips) — limitation, not finding.
* **2023-02-16 = `contract_no_defect`**: ALL 35,043 rows share ONE transaction id (source-side; only day corpus-wide with id-share < 0.5). Ordering-dependent features MUST exclude this day; level aggregates keep it.
* **Junk scrape rows**: 19 (symbol,date) pairs + 4 empty-symbol rows with all numerics empty stay in raw with NULL volume → no aggregate touches them.
* Broker ids: purely numeric → lpad 2 (`08`); alphanumeric dealer codes (`D01`, 35,941 rows) pass through verbatim uppercase (BROKER_ID_SQL). No zeros/float forms in corpus.
* One relabel: kaggle `2021_03_07_floorsheet.csv` ingested AS 2021-03-08 (evidence triple: absent-day (a); CGH rate band [635,665]==OHLC (b); CGH qty 910==volume (c)) — analysis_deviations row.
* Kaggle sessions vs DC3 calendar: 940 window sessions ↔ 938 corpus days; gaps 2021-09-01, 2023-11-27 (no source anywhere; non-imputable).

## Decisions log

- **D1 (2026-11-08)** Repo at `~/research/nepse-floorsheet-microstructure`; venv `nepse-msc` in-repo.
- **D2 (2026-11-08)** Provenance registers, audit tables, figures, manifests, notebook + docs are TRACKED; raw archives and heavy parquets ignored.
- **D3 (2026-11-08)** Data acquisition route: socrateai archive (SV1(b) adoption; nepalstock-direct BLOCKED — FS-000 evidence in block_log); the brief's "viking303 scraper" was later FOUND as a Kaggle DATASET (not a scraper) and adopted for 2021–2023.
- **D4 (2026-11-08)** Scope fork for 2021-2023 floorsheets → RESOLVED POSITIVELY 2026-11-09 (kaggle CC0 corpus verified + ingested; no fork needed).
- **D5 (2026-11-08)** Seeds + hypothesis grid + SE family + fold structure pre-declared BEFORE scoring anything (DC14/DC20): see seeds.py + analysis_plan.md.
- **D6 (2026-11-09)** Corpus source assignment: 2021–2023 = kaggle viking303 (CC0); 2024 = socrateai PRIMARY (MIT); kaggle-2024 cross-check only. One documented relabel (2021-03-07→03-08, evidence triple). D01 dealer codes verbatim. Evidence: EXP-0002b.
- **D7 (2026-11-09)** Walk-forward DEFAULT fold mode = **anchored expanding** (deviation row 2026-11-09 BEFORE any test-fold data observed; commit `26ad798`): sequential could not score past 2023-06-14. Sequential kept as Phase-5 variant.
- **D8 (2026-11-09)** OHLCV policy: tier1 primary + tier2 gap-fill (every row carries `ohlcv_source`); NEPSE index = secondary shading input (licence unstated → non-headline; user may swap source).
- **D9 (2026-11-09)** Phase-4 estimator conventions (deviation rows cited in EXP-0004b/c): ALL regressors incl. the market control z-standardized with TRAIN-fold constants via the shared builder `src/nepsemsc/ml/panel_data.py` (κ on a fully standardized design; §3.2 purge = max-VIF metric); IF scores use **-decision_function on BOTH sides** (scale incident + regression tests); FM slices skipped unless row-count and full-rank feasible; headline conjunction: placebo constraint applies ONLY to placebo-scoped rows (H2/H3), sign agreement REPORTED not gated.

## Phase plan (19-day, per brief)

| Phase | Window | Status |
|---|---|---|
| 1 | 8-9 Nov: env + sample data + DuckDB + pytest smoke | EXECUTED 2026-11-08 (STATUS REPORT below; mandatory stop honoured) |
| 2 | 9-12 Nov: top-10 selection + full window acquisition/audit + reconciliation + provenance | **EXECUTED 2026-11-09 (STATUS REPORT below)** — 6 days ahead of the 12-Nov mark |
| 3 | 12-15 Nov: daily network features + core-periphery + broker persistence | **EXECUTED 2026-11-09 (`a1fc845`) — 6 days ahead (STATUS REPORT below)** |
| 4 | 15-18 Nov: purged walk-forward IF + placebo + economic signature + regime split + event study | **EXECUTED 2026-11-09 — MANDATORY R10 STOP honoured; user review passed ("continue")** |
| 5 | 18-20 Nov: robustness battery (+ optional GPU/IF sklearnex) | **EXECUTED 2026-11-10 (STATUS REPORT below) — 8+ days ahead** |
| 6 | 20-21 Nov: Dash dashboard (4 pages, extracts-only) | **EXECUTED 2026-11-10 (STATUS REPORT below) — 10 days ahead** |
| 7 | 21 Nov: freeze artefacts + experiment register + limitations | **EXECUTED 2026-11-10 (STATUS REPORT below) — MANDATORY R10 STOP honoured (user authorisation "Do what is required"); tag `v1.0-freeze`** |
| 8 | 22-27 Nov: chapter asset bundles + narrative skeleton (student writes prose) | **HANDOFF COMPLETE 2026-11-13** — Ch.1–Ch.6 packs/skeletons, verified crosswalk, deposit preflight; student writing window |

## v2.0 A++ upgrade — post-freeze program (started 2026-11-10, after `v1.0-freeze`)

Binding pre-declaration: `docs/analysis_plan_v2_extension.md` (V2-0..V2-6),
written BEFORE any v2 computation. Governance: frozen v1 numeric files are
NEVER edited; v2 adds new result files + governance columns + deviation rows.
Every stage ends with a printed STATUS REPORT + commit; final tag
`v2.0-a++-freeze`. Detailed deviation rows #10–#30 are in
`docs/analysis_deviations.md` (post-freeze #31–#32 record the chapter-map
defect and v2.0.1 handoff); experiment rows EXP-0008a–e, EXP-0009a–d,
EXP-0010a–c, EXP-0011a–f, EXP-0012, EXP-0013 and EXP-0014 are in the register.

| Stage | Status | Headline outcome |
|---|---|---|
| 1 · statistical interpretation fixes | **COMPLETE 2026-11-11** (`Stage 1: statistical interpretation fixes (v2.0-stage1)`) | Romano–Wolf B=999: **only H10 survives q=.10 (rw_p .081)**; H6 .120 / H7 .159 demoted NULL_FRAGILE; H4 EXPLORATORY_POST_HOC; H8 NULL_FRAGILE; H1/H2/H3/H5/H9 NULL_ROBUST. DC13: 7/10 rows flag (5/5 unique features except EoD); H10 (sole survivor) carries the largest past-\|ret\| association (+19.69 vs +9.49 bp forward). Expanded placebo (1000 draws + blocks): anomaly score null confirmed; EoD block-placebo tail .009/.006; negctrl lead-5 null. MDE: H8 NULL_UNDERPOWERED, others NULL_POWERED. pytest 89 passed |
| 2 · referee-proof robustness | **COMPLETE 2026-11-11** (`Stage 2: liquidity controls, wild cluster bootstrap, SE concordance, VIF audit (v2.0-stage2)`) | Liquidity controls on identical 7,116 rows move no v1 BH-passing estimate >6% or sign; **H10 +9.586 bp p .0117 vs base +9.492 p .0138**. WB corrected to entity-clustered covariance on both draws and observed t (engine 5.11e-13; 12-cluster small-G caveat): p_WB H4 .002 / H6 .002 / H7 .022 / H8 .095 / H9 .100 / H10 .009. v1 `p_dc` disclosed as silent time-kernel fallback (==DK); true DC-v2 p H4 .0053 / H6 .0021 / H7 .0086 / H8 .0574 / H10 .0028. 4-SE concordance STRONG H4/H7/H8, MODERATE H6/H10, NULL other five; **Stage-2 headline = {H10} only** (intersection with Stage-1 CONFIRMED_HEADLINE). VIF max 2.538, \|r\| max .635, no flags. pytest **103 passed** |
| 3 · panel/outcome upgrades | **COMPLETE 2026-11-11** (`Stage 3: quantile panel, EGARCH outcomes, trade-size heterogeneity (v2.0-stage3)`) | EGARCH(1,1)-standardized outcomes (declared arch 8.0.0 call = symmetric `o=0`): 40 fits (37 converged, 4 degenerate), 6,819/7,116 usable z rows; all five BH-passing signs match v1, standardized-effect ratios 0.86–1.17 — H10 +412.40 z p .0383, H6 −511.87 p .0204, H7 +149.15 p .0638, H8 −157.91 p .0745, H4 +256.86 p .0544; H4/H7 fragile in exclusion sensitivities; nulls stay null. Quantile panel (50/50 converged, 7,116×737 two-way design): **H10 BOTH_TAILS INCREASING +3.08/+4.89/+18.70 bp at τ=.10/.50/.90 (ratio 6.06)**; H4 BOTH_TAILS; H6/H8 LOWER_TAIL; H7 NONE/HUMP; null tail labels unadjusted descriptive only. Trade-size (TRAIN-only p10/p90; min-5 guard): **H7 EoD large-bucket +4.519 bp p .0356** (sign-aware pass), H8 medium-bucket −5.266 p .0056 (not large-ticket); small bucket 0.35% volume/unusable. H7 specification curve deferred to V2-4/Stage 4 per binding plan. All Stage-3 tables byte-identical across reruns. pytest **120 passed** |
| 4 · effective-N, broker panel, cost-benefit, subgroups | **COMPLETE 2026-11-12** (`Stage 4: effective-N, broker panel, cost-benefit, subgroups, event-study upgrade (v2.0-stage4)`) | Effective N: **6,383** (7,116 − 11 − 722), FM cross-sections 712–714; frozen β/p unchanged. H7 spec curve: **144 specs / 72 unique design betas** (plan arithmetic slip logged): 72/72 `abs_ret` positive, median +3.952 bp, CI-excl .583, p<.05 .542; full .958 vs bubble .292; `ret` 66/72 negative and 1% cutoff collapses; H7 stays NULL_FRAGILE. Broker panel: 57.9M trades, **91 canonical brokers, 3,026 broker-months**, active 50–90; core 11/219; transitions 183/28/36; 18/48 complete-graph months; source-format defect 275,590 rows/15 days, 37/7,126 OOS rows, leave-out signs unchanged (H8 p .0563). Subgroups: **no Bonferroni survivor** (min p_bonf .1434); circuit-breaker `NOT_EXECUTED`. Event study: reconstruction exact (max ΔCAR 0.0); mean CAR +12.86 bp p .569; BMP p .240; rank z 3.158 (date-clustered 2.522, p .012); market-adjusted −73.41 bp is a pre-window-alpha artifact. Cost-benefit: H7 7.59–12.65× / H10 3.16–5.27× / H4 3.99–6.66× **below** the 30–50 bp floor; not tradable at 1 SD. 22 artifacts byte-identical across consecutive runs; pytest **143 passed** |
| 5 · final headline set + chapter skeletons | **COMPLETE 2026-11-12** (`Stage 5: canonical headline set, chapter skeletons, limitations (v2.0-stage5)`) | Canonical set 10 rows × exact brief columns; **H10 HEADLINE_MODERATE** sole headline (RW .081, WB .009, MODERATE concordance, liquidity+EGARCH pass, both tails increasing); H4 EXPLORATORY_POST_HOC (opposite sign, RW .159); H6/H7/H8 NULL_FRAGILE (RW .120/.159/.203; H8 also MDE-underpowered, ratio 1.426); H1/H2/H3/H5/H9 NULL_POWERED (RW .915; MDE powered). Composition/taxonomy in deviation #27, brief-structure fallback #28. Ch.5/Ch.6 bullet skeletons in `reports/chapter_assets/`; `reports/limitations.md` 24 rows L1–L24 (CRITICAL/MAJOR/MINOR); `chapter_section` column added to the register; EXP-0012; manifest +6 rows; canonical table byte-identical across two builds; pytest **149 passed** |
| 6 · freeze v2.0 | **COMPLETE 2026-11-13** (`Stage 6: clean rebuild, freeze, deposit prep, final audit`) | Clean rebuild 21/21 steps exit 0 in 3,749.9 s (62.5 min); `data/raw/` unchanged (577 files / 611,881,127 bytes); 73 table artefacts: 40 identical, 25 ≤3.55e-14, 4 reorder-only, 2 QuantReg drift 7.44e-7, 1 float aggregation ±1 unit, 1 descriptive sequential-fold threshold flip (146→141; anchored 686 unchanged); classifications identical. 7-file `configs/v2_freeze/` snapshot; lock 153 pins incl. `arch==8.0.0`; 629-row hash backfill; final register audit 697 checks = 695 OK + manifest self-reference + EXP-0000 historical lock; pytest 154 passed; deposit README/CITATION/LICENSE prepared (not uploaded); tag `v2.0-a++-freeze` |

## v2.0.1 post-freeze handoff (2026-11-13)

Trigger: the Stage-5 chapter map named six artefacts that never existed
(`main_regression.csv`, `placebo_distribution.csv`, `regime_split.csv`,
`event_study_car.csv`, `robustness_matrix.csv`, `broker_persistence.csv`).
Diagnosis: latent documentation drift, **not a v2 regression**; the Stage-6
register audit only resolved experiment-row paths, so the chapter surface was
outside its input. Logged as deviations #31 (defect + audit gap) and #32
(handoff repair).

| item | value |
|---|---|
| crosswalk | `docs/chapter_artifact_map.md` — 67 claims / 6 chapters / 50 distinct artefacts; columns chapter, section, claim_id, artifact_path, exp_id, sha256, claim_version, status |
| claim versions | `v1` frozen results remain citable (e.g. H7 v1 p=.0274) even when v2 reclassifies (`NULL_FRAGILE`); `v2` = governance/robustness or handoff scaffold |
| audit | `scripts/audit_chapter_map.py` → `outputs/tables/v2_chapter_map_audit.csv`; 67/67 OK, 0 FAIL, stable SHA-256 |
| guard | `tests/test_chapter_map_integrity.py` — 7 tests; suite now **161 passed** |
| packs | `reports/chapter_assets/ch1_introduction_pack.md` … `ch4_data_engineering_pack.md`; Ch.5/Ch.6 skeletons path-refreshed; Ch.2 is an empty literature/gap/comparison scaffold with **no invented citations** |
| deposit | `dist/nepse-floorsheet-microstructure-v2.0.1-derived.tar.gz` (gitignored, deterministic) + `docs/deposit_preflight.md`; derived tables/code/docs only; raw/duckdb/processed/figures/logs excluded; 76/76 tables hash-aligned |
| TODOs | tier1 OHLCV upstream verification (public-repo caveat accepted 2026-11-14); derived-only vs licensed-subset deposit scope (author identity resolved 2026-11-14) |

`git tag v2.0-a++-freeze` remains on `51c7d89`; the handoff is a new commit and
tag `v2.0.1-handoff`. No frozen v1 numeric file, binding freeze file, final
classification, or existing tag was moved.

## v2.0.2 pre-write sprint (2026-11-13 → 2026-11-14)

**State: ANALYSIS FROZEN / PRE-WRITE ASSETS COMPLETE.** Phases A–F executed
under the pre-write contract: no new analyses, regressions, tests, re-fits or
robustness checks; no thesis prose; no invented citations; no uploads.

| item | value |
|---|---|
| canonical verification | H10 exact: β `+9.492266420621041 bp`, DK p `.013754510527417598`, n `7,116`, n_eff `6,383`; secondary liquidity-controlled β `+9.585688569659226 bp`, p `.011719355980632`; 3/3 spot checks (H7 `+3.9523733421516263 bp`, H10 RW p `.081`, event-study CAR `+12.860877654854391 bp`, p `.5689998994`) |
| licence review | live, verbatim two-layer finding: tier1 Kaggle declares `MIT` + “educational and research purposes” + “scraped from NEPSE Alpha”; upstream NEPSE Alpha rights `UNCERTAIN`; viking303 `CC0`; socrateai MIT-style/`NOASSERTION`; SamirWagle `license:null`/Educational; menaceXnadin `license:null`/unofficial mirror |
| figures | F1–F10 in `outputs/figures/static/`; 300 dpi PNG + PDF; footer `EXP-id · data <12-hex> · v2.0.1`; `figure_manifest.csv`; 10/10 blank-check PASS |
| AI policy | `docs/ai_use_policy.md` v2.0.2-prewrite: OpenCode+GLM, OpenCode+DeepSeek, `DeepSeek V4.1 Flash Free`; permitted/prohibited roles; approval gates; provenance/citation/licence controls; University disclosure TODO |
| references | 39 Crossref-verified candidates (11 NET, 10 LIQ, 6 MAN, 7 EM, 5 NP); all Crossref 200 / DOI 302 on 2026-11-14; `content_review_status = NOT_REVIEWED` on every row; one SSRN `POSTED_CONTENT_NOT_FINAL` |
| print tables | 28 CSVs + `table_manifest.csv` in `reports/chapter_assets/print_tables/`; all hashes/rows/columns validated; canonical numbering in `table_numbering_plan.md` |
| chapter map | 67/67 OK, 50 distinct artefacts; `docs/ai_use_policy.md` reclassified `v2/VERIFIED` after the Phase-D rewrite; provenance manifest append-only |
| suite | **161 passed** (159 tests + 2 notebooks); `outputs/tables/v2_chapter_map_audit.csv` 67/67 OK |
| deviations | #33–#40 (figure representations, Phase-A verification, licence finding, static-figure conventions, metadata-only references, table numbering, chapter-map hash repair) |
| public metadata | legal author identity `Prabin Shrestha <itsme_prabin@outlook.com>` in `CITATION.cff`, `LICENSE`, `pyproject.toml` and deposit docs; v2.0.2 release date 2026-11-14; full public push incl. figures authorised 2026-11-14 with the upstream caveat accepted; push awaits GitHub authentication |
| tag | `v2.0.2-prewrite` on the metadata-finalisation commit |

**Next:** the student writes Chapters 1–6 in the 22–27 Nov window using
`reports/chapter_assets/writing_order_memo.md` (Ch.4 → Ch.3 → Ch.5 → Ch.6 →
Ch.1, with Ch.2 reading in parallel) and `key_claims_sheet.md`. Every chapter is
student prose. No new analysis is permitted.

**Remaining student TODOs:** (1) upstream NEPSE Alpha permission remains
unverified; the author accepted the caveat for the public repository on
2026-11-14, so this is a thesis/deposit-clearance item rather than a blocker for
the public code repo; (2) complete the University disclosure wording/sign-off;
(3) decide whether and where to deposit the derived-only archive (no archive
upload has been performed).

## R10 gate status

Phase 1 stop honoured (2026-11-08). Phase 2 auto-proceeded (50 passed). Phase 3 auto-proceeded
(52 passed). Phase 4 HARD GATE passed (user review 2026-11-09 → "continue"). Phase 5
auto-proceeded (58 passed). Phase 6 auto-proceeded (62 passed). **Phase 7 freeze EXECUTED
2026-11-10 after explicit user authorisation (mandatory R10 stop honoured): requirements-lock
regenerated WITH kagglehub==1.0.3 (144 pins, zero version bumps), config fingerprint FROZEN
`9a60208f…b012f` (enforced by tests/test_freeze.py), docs/limitations.md written, EXP-0007
registered, repo-local git identity set (global untouched), tag `v1.0-freeze`.
ENGINEERING IS COMPLETE — Phase 7 is the LAST engineering phase; any post-freeze change
requires a NEW registered experiment row (DC20).** Phase 8 (22-27 Nov) = chapter asset
bundles + narrative skeleton; the student writes prose.

**v2.0 A++ freeze (2026-11-13):** Stage 6 clean rebuild + freeze completed; EXP-0013
registered, 7-file `configs/v2_freeze/` snapshot, 153-pin lock, final register audit
695/695 hash-aligned artefacts (2 documented exemptions), tag `v2.0-a++-freeze`.
Any post-v2 change now requires a new registered experiment row.

## Gotchas to remember (inherited + Phase-2)

- floorsheets not tx-ordered → sort by contract_no ALWAYS.
- `^` in DuckDB SQL is NOT power — use `pow(x, 2)`.
- Python 3.11 only for this venv (brief).
- pandas 3.x installed — run the SE-spec test FIRST after any dependency change.
- The kronos project's raw archives are shared READ-ONLY inputs: never modify or write into `~/research/nepse-kronos-thesis/`.
- venv sits IN-REPO under `/nepse-msc/` (anchored ignore) — do not rename.
- **DuckDB glob CSV readers**: use `filename = 'filename'` (string alias) on multi-file reads; kaggle dates come from FILENAMES (underscored `2021_03_07`) — relabel keys must be underscore-form (`_iso2fn` in duckdb_loader). INSERT ... SELECT needs the explicit `SELECT` (was missing once — caught by ParserException).
- **nbmake CLI**: notebooks must be passed as args WITH `--nbmake`; wrong-arg collection aborts the run with 0 collected. Invocation: `pytest tests notebooks/*_*.ipynb --nbmake`.
- **calendar parquet column is `session_date`** — CAST to `date` before `USING (date)` joins in DuckDB SQL.
- `heredoc`-inline python with parens/quotes produced 3 syntax traps today — prefer writing patch scripts to `/tmp/opencode/*.py` and running them.
- pytest with an explicit bad arg aborts before collecting `tests/` ("collected 0 items") — fix the arg, not the tests.
- **IF scoring scale**: ALWAYS `-model.decision_function(...)` on BOTH train and test sides. Mixing `-score_samples` (train) with `-decision_function` (test) adds a ~+0.5 offset under contamination='auto' and silently zeroes all events vs a train-q90 threshold (EXP-0004a incident; pinned by tests/test_anomaly_scale.py).
- **FM fallback slices**: any per-date cross-section must clear BOTH `n >= 1 + #regressors` AND full-rank X, else statsmodels silently returns pinv-determined arbitrary betas (SingularMatrixWarning) — guard lives in `fit_fama_macbeth` (deviation row).
- **Conjunction semantics**: a placebo constraint that was never applied to a test is NOT a failure for it — Phase-4 gate uses `placebo_share.fillna(0.0) <= alpha` (missing = not applicable; deviation row).
- **Deterministic re-score trick**: carrying bookkeeping columns (total_volume) through the scoring parquet must NOT change scores — verify with a max|Δ|=0 null diff (ET convention).

## Phase 1 STATUS REPORT (2026-11-08 — filled post-execution)

| item | value |
|---|---|
| env | python 3.11.16 (uv venv `nepse-msc`); duckdb 2.0.0 · pandas 3.1.1 · numpy 2.4.6 · networkx 3.6.1 · sklearn 1.9.1 · linearmodels 7.1 · statsmodels 0.15.0 · plotly 7.1.0 · dash 4.5.0 · sklearnex 2199.9.9 (optional accel) |
| pytest | **38 passed, 0 failed** (+ nbmake notebook test 1 passed) — R10 gate GREEN |
| sample data | NABIL 2024-12 from LOCAL socrateai archive (MIT, SV1(b) adoption): 13,099 rows, 20 daily files sha256-stamped, schema validation PASS, missing broker ids 0 |
| DuckDB | data/duckdb/nepse.duckdb · floorsheet_raw loaded · brief query executed (587–839 trades/day; 48–66 unique buyers/sellers) |
| HHI/self-loop table | outputs/tables/sample_hhi_selfloop.csv: buyer_hhi mean 0.056 (max 0.153); self_loop_volume_ratio mean ~2.4%, standout day 2024-12-18 = 33.65% [REAL, uninterpreted] |
| config fingerprint | 29a43e8c12c26260fea5cfbb0349b9a003696bcf60972e9a25ade8c91acff459 (yaml since amended in fold-mode commit) |
| blockers | none active |
| note | adaptation declared: brief's "viking303 scraper" could not exist as a scraper (nepalstock network-blocked); then RESOLVED by finding the Kaggle dataset (D3/D4/D6) |

## Phase 2 STATUS REPORT (2026-11-09 — filled post-execution)

| item | value |
|---|---|
| universe | TOP-10 by window turnover (≥90% coverage, TRAIN-only re-selection rule untouched): SHIVM API HDL AHPC NRIC NABIL NICA UPPER NLIC AKPL; buffer NHPC HIDCL [REAL, EXP-0002a] |
| corpus sources | 2021–2023 kaggle viking303 CC0 (935 files, 3 yrs) + 2024 socrateai MIT (232 files) [REAL]; kaggle-2024 (229 files) cross-check only; all 1,167 day files sha256-stamped |
| calendar | 940 DC3 sessions 2021-01-01→2024-12-31; corpus covers **938/940 (99.79%)**; gaps: 2021-09-01, 2023-11-27 (no source in ANY verified archive; non-imputable, documented) |
| floorsheet headcount | **57,927,926 raw rows** = 36,706,934 kaggle + 21,220,992 socrateai → dedupe (date,symbol,contract_no) drops 35,296 page-splits → **57,892,630 dedup**; 752 dup keys (506 exact, 246 signature-conflicts documented NON-merged); 530 symbols [EXP-0002b/c] |
| relabel | kaggle `2021_03_07_floorsheet.csv` AS 2021-03-08 — evidence triple [REAL] (day-absent both OHLCV sources; CGH rate band [635,665]==OHLC band; CGH qty 910==tier1 volume 910, re-verified live in notebook EXP-0002f) |
| audit | missing-broker junk pairs 19 (+4 empty-symbol rows, NULL volume by construction); low-activity (<100 trades) pairs 114,167 (min 1); dealer-code rows 35,941; negative volume 0 / negative amount 0; non-positive price 8 + null contract_no 2 (inside junk/defect classes); **2023-02-16: ALL 35,043 rows share one contract id → `contract_no_defect`, ordering-features exclude, level aggregates keep** |
| OHLCV | daily_ohlcv.parquet 205,533 rows (tier1 201,115 + 4,418 tier2-only rows); tiers overlap on 28,915 (symbol,date) keys and median Δclose = **0.0000%** computed on the 28,908 non-null-close pairs (same upstream) [EXP-0002d] |
| reconciliation | top-12: pairs 10,909 both-sides; volume_ratio median **1.0000**; 96.6% in [0.95,1.25]; 94.7% in [0.98,1.02] → buyer-side counting; full-market ~2x = tier1-coverage scope artifact (100/530 scrips) — limitation logged [EXP-0002e] |
| index | NEPSE composite 1997→2026-11-06 (6,623 rows) fetched as SECONDARY shading input; repo licence `null` → unstated_in_repo; limitation + swap note in ai_use_policy |
| pytest | **50 passed, 0 failed** (48 unit + 2 notebooks nbmake) — R10 gate GREEN |
| provenance | manifest 30 entries; register EXP-0002a–f EXECUTED; deviations: fold-mode + relabel + defect rows; ai_use_policy licence table rewritten (viking303 FOUND/CC0 supersedes NOT-FOUND note) |
| open items | tier1 OHLCV licence = PENDING student UI check (figures RESTRICTED until confirmed); kagglehub not yet in requirements-lock (regen before Phase-7 freeze) |
| gate | auto-proceed to Phase 3 per R10 (pytest green, 0 BLOCKED). Phase-3 MUST honour: 2023-02-16 ordering exclusion, junk/NULL-volume filtering, `source` propagation, DC1 per-fold universe re-selection |

## Phase 3 STATUS REPORT (2026-11-09 — filled post-execution)

| item | value |
|---|---|
| features | **233,706 (symbol,date) pairs** from 57,892,602 post-SV7 rows (28 junk dropped; volume kept 99.999996%) |
| graph stage | 37,165,013 aggregated pair edges → 529 symbols × 938 days in 46 min (24-way parallel); graphs exact (< 200 nodes); fixed tuple<=set glyph bug + regression test |
| outcomes | 80,610 rows × 99 tier1 symbols × 940 days; ret_fwd1/abs_ret/parkinson/market_loo coverage ≥ 99.9% |
| persistence | 233,177 transitions; mean J 0.2339 — DESCRIPTIVE (R11); promoter-only scrips uninterpreted |
| regimes | calendar regime medians — descriptive only (EXP-0003d) |
| pytest | 52 passed |

## Phase 4 STATUS REPORT (2026-11-09 — filled post-execution; R10 GATE: results presented for user review)

| item | value |
|---|---|
| scoring (EXP-0004a) | anchored purge-gap-6 walk-forward, DC1 per-fold top-10 universes (fold0 NBL / f1–2 NHPC / f3 SHIVM + 9 common); IF(200,'auto') train-only; **7,126 OOS rows / 686 events (9.6%)**; thresholds train-q90 (0.023–0.033); train rows 17,822 EDA-only; re-score after carrying volume cols reproduced scores bit-exactly |
| grid (EXP-0004b) | n=7,116; κ(std) 3.3 → NO §3.2 purge; VIF ≤ 2.38; IPS mean-ADF ≤ −4.29; DK(bw=5) primary + DC + full-rank-guarded FM (SV2); BH q=0.10 |
| headlines | **5/10 BH-passing: H4 H6 H7 H8 H10** (adj p 0.0689–0.0918); DG — H7 EoD→abs_ret +3.95 bp/SD (FM .0094 concordant), H8 EoD→ret −4.47 bp/SD (FM .0587 borderline), H10 reciprocity→abs_ret +9.49 bp/SD (FM .2896 DK-only), H4 buyer_hhi→ret +7.51 bp/SD (**opposite-sign** vs declared negative; FM .0082 normal-era driven), H6 reciprocity→ret −10.94 bp/SD (amb sign, FM .5403 DK-only) |
| placebo (EXP-0004c) | H2 share 0.800, H3 0.640 (≈ random) → **anomaly score has NO forward-return content in the OOS design** (H2/H3 rejected twice: placebo + BH); conjunction semantics fixed pre-numbers-of-record (deviation row) |
| regime split (EXP-0004d) | bubble 38.5% / normal 61.5%; **no interaction significant** (min p 0.1171) — headline signals do not calendar-switch; H7/H8 same-sign betas in both eras |
| event study (EXP-0004e) | 686 events; 670 market-model + 16 illiquid-trigger market-adjusted; **overall CAR +0.13% p .569 (null)**; market-model +0.19% p .409; illiquid subsample −2.45% p .0018 (n=16 caveat); no post-event daily drift |
| register/manifest | EXP-0004a–e EXECUTED; deviation rows: κ/control standardization, FM full-rank guard, conjunction semantics; provenance manifest 42+ entries |
| pytest | **56 passed, 0 failed** (54 unit incl. panel_data ×2 + anomaly-scale ×2, + notebooks 00/01) |
| [] STOP | **mandatory R10 stop after Phase 4 — results above presented for user review before Phase 5 (robustness battery)** |

## Phase 5 STATUS REPORT (2026-11-10 — filled post-execution; NOT an R10 stop → auto-proceed)

| item | value |
|---|---|
| battery | `scripts/run_robustness.py` sections a–g per plan §7 pre-declarations; ONE consolidated provenance row (`robustness_battery_exp0005a_g`; manifest 43 entries); 3 runs executed, **numbers of record = first complete run**; engineering-incident row added to analysis_deviations (fwd_k leading-shift fix + panel ride-along + full-feature input frame + diag-z² sign — all BEFORE numbers of record; regression test added to test_panel_data) |
| (a) LOO (EXP-0005a) | 12 symbol-drops × 10 tests = 110 DK refits; **all five headlines sign-stable 12/12**; raw p<.10 in 11/12 (H4), 12/12 (H6/H7/H10), 10/12 (H8); β spreads (bp) H4 +6.57..+9.35, H6 −12.74..−8.92, H7 +2.95..+4.66, H8 −6.15..−3.36, H10 +7.97..+10.71; H2/H3 stay null (0/12) — **placebo null LOO-robust** [REAL] |
| (b) horizons (EXP-0005b) | coverage 99.9/99.7/99.4% (within-window closes); BH(heads): t+2 0/5, t+3 0/5 (raw H7 p .0185 dies under BH), **t+5 1/5: H7 +10.22 bp p .0061**; directions IDENTICAL at every horizon (H7/H8/H10 same-sign; H4 opposite-sign); magnitudes GROW with k — t+1 stays the primary pre-declared object; horizon sensitivity = descriptive [REAL] |
| (c) EoD thresholds (EXP-0005c) | descriptive sensitivity (raw DK p + concordance vs base 5%, no fresh BH family — pre-declared): **H7 threshold-robust** 1% +3.72 bp (p .0296) / 10% +3.78 (p .0387) vs base +3.95; **H8 collapses at 1%** −0.60 bp (p .7634), concordant at 10% −4.24 (p .0633) ⇒ H8's return effect = mid-tail EoD mass; SQL rows 233,454 / 937 days = 938 − defect ✓ |
| (d) alt scorers (EXP-0005d) | per-fold OOS Spearman vs IF: Mahalanobis +.83 (.70–.92), diag-z² +.95 (.94–.96), LOF +.60 (.41–.78), OC-SVM +.54 (.45–.66) ⇒ IF OOS ordering = strong instance of a broader quadratic-anomaly class, not one-algorithm artifact; noise-floor nuance: OC-SVM/LOF share ~half the ordering — score levels/tails stay method-dependent (SV5: correlation only, no inference) [REAL] |
| (e) drop-bubble (EXP-0005e) | normal era (2023+, n=4,379; folds/constants unchanged): **H4/H6/H7/H10 survive BH (adj .0611/.0611/.0765/.0611), magnitudes ≥ base** (H4 +10.49 bp opposite-sign ⇒ normal-era phenomenon re-confirmed); **H8 FAILS (−4.44 bp p .1703)** ⇒ H8 bubble-era-driven; H2/H3 null — no era rescues the anomaly score [REAL] |
| (f) top-5 external (EXP-0005f) | ranks 11–15 per fold (base top-10 excluded BEFORE the head; universes printed in register; fresh IF(200)/constants): 3,414 OOS rows / 264 events (7.7%); **0/5 BH-pass (raw p ≥ .23)**; directions agree (H7 +2.14, H8 −0.70, H10 +5.40 bp) but magnitudes shrink ~2–4× ⇒ **concentration signals are tier-specific (liquidity/attention), not market-wide — the battery's primary honest limitation** [REAL] |
| (g) sequential (EXP-0005g) | D7 coverage limitation confirmed (test = middle segments 2021-07→2023-06 only; NO 2024, no bubble tail); n_oos 1,068–1,092/fold; event shares 7.6–13.5%; pooled Spearman vs anchored on 2,731 overlapping OOS rows = **+0.87 (p < 1e-300)** ⇒ fold mode changes coverage/levels, not the anomaly ranking; anchored choice not the driver of EXP-0004's pattern [REAL] |
| verdict | headlines survive LOO + thresholds + normal-era drop; degrade ONLY below the traded tier (f) and inflect at longer horizons (b, sign-stable, size grows); H8 fragile twice (1% cutoff + bubble era); IF anomaly score OOS nullity re-confirmed wherever re-checkable — thesis narrative: broker-network concentration effects are REAL but LOCALIZED to the most-traded tier; the IF event-based story is NULL |
| tables | 8 CSVs outputs/tables/robustness_* (master headline-survival = 46 variant×test rows) |
| pytest | pytest 58 = 56 unit + 2 notebooks (two new tests this phase: anomaly-scale excluded-symbols ×1 + panel ride-along ×1, so 55-unit checkpoint estimate was off by one) — all green |
| [] NEXT | Phase 7 freeze = HARD STOP: lock regen w/ kagglehub, fingerprint, limitations doc, register finalization, identity — presented and executed only after user authorisation |

## Phase 7 STATUS REPORT (2026-11-10 — frozen; tag `v1.0-freeze`)

| item | value |
|---|---|
| freeze (EXP-0007) | user authorised ("Do what is required") after the Phase-5/6 results were presented; NOTHING frozen pre-authorisation |
| requirements-lock | regenerated from live venv via `uv pip freeze`: **144 pins** (was 141): +kagglehub==1.0.3, +kagglesdk, +protobuf; **ZERO version bumps / removals** — SE-spec test run FIRST (4 passed) then full suite |
| fingerprint (DC20) | configs/project.yaml: initial `29a43e8c…` (2026-11-08) → frozen **`9a60208f16040c8246108f79060fa81b69f0fa5609a4a365c4c898898d6b012f`** (only amendment ever = pre-declared fold-mode change, commit `26ad798`); `tests/test_freeze.py::test_config_fingerprint_is_frozen` fails loudly on ANY byte change |
| freeze audit tests | `tests/test_freeze.py` (6 tests): fingerprint bite, 9 battery tables + 46 survival rows + 10-grid + 4 folds, register EXP-0000–0007 completeness, manifest ≥46 with battery+cache kinds (47 actual), limitations/lock presence incl. kagglehub pinned, headline set + SIGN DIRECTIONS pinned (H7/H10+, H8−, H4+ opposite, H6−, H2/H3 null) |
| limitations | docs/limitations.md — 7 sections: corpus gaps/relabel/defect, licences (tier1 RESTRICTED pending, index unstated), floorsheet structure (buyer-side volume, scope artifact), D7/D9 conventions, findings-level limits (score nullity, tier-locality, horizon, H8×2 fragility, H4 opposite-sign normal-era, H6/H10 DK-only, no era interactions, n=16 illiquid caveat), presentation scope, falsification conditions — all with EXP citations |
| identity | repo-local `Prabin Shrestha <itsme_prabin@outlook.com>` (set 2026-11-14; all 17 commits and annotated tags rewritten; GLOBAL git identity untouched per sibling D-note) |
| pytest | **68 passed, 0 failed** (66 unit incl. 6 freeze-audit + SE-spec, 2 notebooks) |
| [] STATE | ENGINEERING COMPLETE (all of R1–R12, SV1–SV7, DC1–DC20 satisfied or documented). Phase 8: chapter asset bundles (figures/table packs per chapter) + narrative skeleton — the student writes 22–27 Nov; aid on request. ANY change now = new EXP row |

## Phase 6 STATUS REPORT (2026-11-10 — filled post-execution; NOT an R10 stop → auto-proceed to Phase 7 freeze)

| item | value |
|---|---|
| contract | 4 pages, EXTRACTS-ONLY: runtime serves `data/processed/dashboard_cache/*.csv` (compact snapshots) + `outputs/tables/*.csv` (register artifacts of record) ONLY — `test_layout_builds_without_duckdb` literally imports duckdb-blocked to prove it; no full-corpus reads, no DuckDB connection in the app process; exp0006 cache provenance rows ×4 in manifest (46 entries total) |
| pages | 1 · Corpus & Provenance (/) — 938/940 calendar strip + per-source daily load + licence table + top-12 extract load (log-scaled); 2 · Daily Network Features (/features) — 12-symbol × 9-metric explorer w/ bubble shading + defect-day marker + descriptive stats card (R11 only); 3 · Anomaly Events & CARs (/anomaly) — 686/7,126 KPIs, score histogram w/ event overlay, per-day event bars, ES table + method CAR bars, fold diagnostics table; 4 · Inference & Robustness (/inference) — 10-row grid table (DK/FM/BH/placebo/sign/headline), variant×headline survival heatmap (9 variants), LOO β-range funnel, base-vs-eras-vs-top5 magnitude bars, regime-interaction table |
| build | `scripts/build_dashboard_cache.py` (idempotent re-run appends prov rows — documented in evidence) → `scripts/dashboard_app.py` + `scripts/dashboard_pages/` (Dash 4.5 Pages, dbc CDN stylesheet) — run `nepse-msc/bin/python scripts/dashboard_app.py` → 127.0.0.1:8050 |
| honesty | every plotted number pre-computed in the register artifacts [REAL]; the app computes ONLY descriptive aggregates on page 2 (labeled); no inference, no re-scoring, no new experiment |
| pytest | **62 passed, 0 failed** (60 unit incl. 4 dashboard tests + 2 notebooks) |
| [] NEXT | **Phase 7 freeze = HARD STOP (R10)** — presented and EXECUTED post-authorisation (EXP-0007 report below) |
