# AGENTS.md — project state for ANY fresh session

**Read this before doing anything.** Resume point for the whole build.
Sibling project (context only, NOT this repo): `~/research/nepse-kronos-thesis/`
(its data archives are READ-ONLY shared raw inputs).

- Project: `~/research/nepse-floorsheet-microstructure/` (venv `nepse-msc` IN-REPO —
  intentional: venv dir name ≠ package name `nepsemsc`, so no D5-style shadowing;
  pattern anchored `/nepse-msc/` in .gitignore)
- Deadline: 2026-11-27 · Today: 2026-11-08 · Engineering ends 21 Nov (writing 22-27)
- Binding contract: the 19-day brief (hard rules R1-R12, SV1-SV7, DC1-DC20),
  pre-declared constants in `configs/project.yaml` + `docs/analysis_plan.md` (DC20).

## Environment survey — 2026-11-08

| Fact | Value |
|---|---|
| OS | Ubuntu 26.04 (24 cores, 45 Gi RAM, RTX 5070 8 GB — GPU idle: CPU-bound thesis) |
| Python | 3.11.16 via uv-managed toolchain (`uv` 0.13.7 at ~/.local/bin) |
| git | 2.53.0; REPO-LOCAL identity only — global identity intentionally untouched (sibling D-note); replace placeholder in Phase 7 |
| Sys packages | no system-wide pip installs — everything lives in `nepse-msc/` |

## Data map (the decisive Phase-0/1 discovery)

| Source | What | Where | Status |
|---|---|---|---|
| socrateai daily floorsheets (MIT, verified) | full-market floorsheet per DAY: `transaction,symbol,buyer,seller,quantity,rate,amount,date` · 650 files · 2024-01-01→2026-11-02 · 2.9 GB local | `~/research/nepse-kronos-thesis/data/raw/tier3_floorsheets_socrateai/` | **ADOPTED (SV1(b))** |
| Kaggle OHLCV 2012→2025-09 (101 symbols) | daily OHLCV + turnover | `…/tier1_kaggle/*.csv` | secondary controls; licence pending user UI check |
| SamirWagle prices →2026-02 | OHLCV override/extend | `…/tier2_samirwagle_prices/` | attribution |
| SampirWagle floorsheet index (2026 only) | 176 files 2026-02→2026-11 | `…/data/metadata/samirwagle_floorsheet_index.json` | cross-check only |
| **floorsheets 2021–2023** | NOT FOUND locally; socrateai/SamirWagle don't have them | — | **OPEN**: bounded Phase-2 search; scope fork rule in analysis_plan §1 |

Key validated facts from sibling project (treat as REQUIRED reading):
* floorsheet rows are NOT in execution order (reverse-pair rate 0.79–0.86 in
  2024) → ALWAYS `sort_values("transaction")` before any ordering statistic;
* contract_no is daily-global → per-(symbol,date) gaps ARE EXPECTED; assert
  monotonic-after-sort, document gaps (SV6 adapted — row-order fallback is
  INVALID for this archive).

## Decisions log

- **D1 (2026-11-08)** Repo at `~/research/nepse-floorsheet-microstructure`; venv `nepse-msc` in-repo.
- **D2 (2026-11-08)** Provenance registers, audit tables, figures, manifests, notebook + docs are TRACKED; raw archives and heavy parquets ignored.
- **D3 (2026-11-08)** Data acquisition route: socrateai archive (SV1(b) adoption; nepalstock-direct BLOCKED, viking303 NOT FOUND — inherited evidence + today's HTTP-000 re-check). Sample-route contract honoured via the same archive (one stock × one month, local).
- **D4 (2026-11-08)** Scope fork for 2021-2023 floorsheets: bounded search in Phase 2 (trigger: nothing verified by 2026-11-12 → adopt 2024-01→2026-11 window and re-derive R8 regimes from OHLCV drawdown/momentum; decision row lands in block_log + analysis_deviations, NEVER silent).
- **D5 (2026-11-08)** Seeds + hypothesis grid + SE family + fold structure pre-declared 2026-11-08 BEFORE scoring anything (DC14/DC20): see seeds.py + analysis_plan.md.

## Phase plan (19-day, per brief)

| Phase | Window | Status |
|---|---|---|
| 1 | 8-9 Nov: env + sample data + DuckDB + pytest smoke | EXECUTED 2026-11-08 (STATUS REPORT below; MANDATORY STOP after) |
| 2 | 9-12 Nov: top-10 selection + full window acquisition/audit + reconciliation + provenance | NOT EXECUTED (2021-23 archive search FIRST, then per-fold universe) |
| 3 | 12-15 Nov: daily network features + core-periphery + broker persistence | NOT EXECUTED |
| 4 | 15-18 Nov: purged walk-forward IF + placebo + economic signature + regime split + event study | NOT EXECUTED (STOP after for user review) |
| 5 | 18-20 Nov: robustness battery (+ optional GPU/IF sklearnex) | NOT EXECUTED |
| 6 | 20-21 Nov: Dash dashboard (4 pages, extracts-only) | NOT EXECUTED |
| 7 | 21 Nov: freeze artefacts + experiment register + limitations | NOT EXECUTED (STOP) |
| 8 | 22-27 Nov: chapter asset bundles + narrative skeleton (student writes prose) | NOT EXECUTED |

## R10 gate status

Phase 1 pytest suite green (report below) → STOP as mandated. NEXT: user says
"continue" → Phase 2 begins with the 2021-2023 archive search (bounded 2h),
then top-10 selection from tier1_kaggle turnover (DC1/DC2), backfill of any
missing 2024-2026 socrateai dates, quality audit, reconciliation.

## Gotchas to remember (inherited)

- floorsheets not tx-ordered → sort by contract_no ALWAYS (above).
- `^` in DuckDB SQL is NOT power — use `pow(x, 2)` (already done in aggregations.py).
- Python 3.11 only for this venv (brief).
- pandas 3.x installed — run the SE-spec test FIRST after any dependency change.
- The kronos project's raw archives are shared READ-ONLY inputs: never modify
  or write into `~/research/nepse-kronos-thesis/`.
- venv sits IN-REPO under `/nepse-msc/` (anchored ignore) — do not rename.

## Phase 1 STATUS REPORT (2026-11-08 — filled post-execution)

| item | value |
|---|---|
| env | python 3.11.16 (uv venv `nepse-msc`); duckdb 2.0.0 · pandas 3.1.1 · numpy 2.4.6 · networkx 3.6.1 · sklearn 1.9.1 · linearmodels 7.1 · statsmodels 0.15.0 · plotly 7.1.0 · dash 4.5.0 · sklearnex 2199.9.9 (optional accel) |
| pytest | **38 passed, 0 failed** (+ nbmake notebook test 1 passed) — R10 gate GREEN |
| sample data | NABIL 2024-12 from LOCAL socrateai archive (MIT, SV1(b) adoption): 13,099 rows, 20 daily files sha256-stamped, schema validation PASS, missing broker ids 0 |
| DuckDB | data/duckdb/nepse.duckdb · floorsheet_raw loaded · brief query executed (587–839 trades/day; 48–66 unique buyers/sellers) |
| HHI/self-loop table | outputs/tables/sample_hhi_selfloop.csv: buyer_hhi mean 0.056 (max 0.153); self_loop_volume_ratio mean ~2.4%, standout day 2024-12-18 = 33.65% [REAL, uninterpreted] |
| config fingerprint | 29a43e8c12c26260fea5cfbb0349b9a003696bcf60972e9a25ade8c91acff459 |
| blockers | none active; two OPEN decisions documented (2021-23 archive search + Kaggle licence check) |
| note | adaptation declared: brief's "viking303 scraper" route cannot exist (not found + nepalstock network-blocked); socrateai archive is the pre-scraped archive of SV1(b) — documented in block_log + ai_use_policy |
| [] STOP | mandatory R10 stop after Phase 1 — awaiting user "continue" for Phase 2 |
