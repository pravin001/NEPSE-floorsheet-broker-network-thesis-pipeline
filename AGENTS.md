# AGENTS.md — project state for ANY fresh session

**Read this before doing anything.** Resume point for the whole build.
Sibling project (context only, NOT this repo): `~/research/nepse-kronos-thesis/`
(its data archives are READ-ONLY shared raw inputs).

- Project: `~/research/nepse-floorsheet-microstructure/` (venv `nepse-msc` IN-REPO —
  intentional: venv dir name ≠ package name `nepsemsc`, so no D5-style shadowing;
  pattern anchored `/nepse-msc/` in .gitignore)
- Deadline: 2026-11-27 · Today: 2026-11-09 · Engineering ends 21 Nov (writing 22-27)
- Binding contract: the 19-day brief (hard rules R1-R12, SV1-SV7, DC1-DC20),
  pre-declared constants in `configs/project.yaml` + `docs/analysis_plan.md` (DC20).

## Environment survey — 2026-11-08

| Fact | Value |
|---|---|
| OS | Ubuntu 26.04 (24 cores, 45 Gi RAM, RTX 5070 8 GB — GPU idle: CPU-bound thesis) |
| Python | 3.11.16 via uv-managed toolchain (`uv` 0.13.7 at ~/.local/bin) |
| git | 2.53.0; REPO-LOCAL identity only — global identity intentionally untouched (sibling D-note); replace placeholder in Phase 7 |
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

## Phase plan (19-day, per brief)

| Phase | Window | Status |
|---|---|---|
| 1 | 8-9 Nov: env + sample data + DuckDB + pytest smoke | EXECUTED 2026-11-08 (STATUS REPORT below; mandatory stop honoured) |
| 2 | 9-12 Nov: top-10 selection + full window acquisition/audit + reconciliation + provenance | **EXECUTED 2026-11-09 (STATUS REPORT below)** — 6 days ahead of the 12-Nov mark |
| 3 | 12-15 Nov: daily network features + core-periphery + broker persistence | IN PROGRESS (auto-proceed per R10; honour gates in Phase-2 report §7) |
| 4 | 15-18 Nov: purged walk-forward IF + placebo + economic signature + regime split + event study | NOT EXECUTED (STOP after for user review) |
| 5 | 18-20 Nov: robustness battery (+ optional GPU/IF sklearnex) | NOT EXECUTED |
| 6 | 20-21 Nov: Dash dashboard (4 pages, extracts-only) | NOT EXECUTED |
| 7 | 21 Nov: freeze artefacts + experiment register + limitations | NOT EXECUTED (STOP) |
| 8 | 22-27 Nov: chapter asset bundles + narrative skeleton (student writes prose) | NOT EXECUTED |

## R10 gate status

Phase 1 stop honoured (2026-11-08). Phase 2 complete with pytest **50 passed / 0 failed**
(48 unit + notebooks 00+01 under nbmake) and zero BLOCKED items → auto-proceed to
Phase 3. NEXT STOP: after Phase-4 results (user review), then Phase-7 freeze.

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
