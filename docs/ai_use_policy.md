# AI-Use & ToS/Licence Policy (R9)

## (a) AI usage in this thesis

* AI (OpenCode/GLM) is used for: engineering — pipeline code, tests, notebooks,
  docs scaffolding, execution, verification. It does NOT write thesis prose;
  the student writes every prose chapter (Phase 8 prepares asset bundles + a
  narrative skeleton the student expands).
* AI-assisted code does not fabricate results: every number in this repo
  originates from executed code on real data, labelled [REAL], or from
  synthetic test fixtures labelled [SYNTHETIC].

## (b) ToS / licence evidence register (inherited from sibling project, 2026-11-08)

| Source | Status | Evidence |
|---|---|---|
| nepalstock.com direct | **BLOCKED at network level** (HTTP 000 ×2 on 2026-11-08, sibling D9; re-verified this project today) | no ToS page reachable → nothing was ever direct-scraped; the question does not arise |
| `viking303/nepse-historical-floorsheet` (brief's primary — floorsheets 2014→2026) | **FOUND + ADOPTED for 2021–2023 — CC0 verified** (2026-11-09; supersedes the sibling 2026-11-08 "NOT FOUND" note: no *scraper* existed, but the *Kaggle dataset* does) | Kaggle dataset-card licence "CC0 Public Domain" at kaggle.com/datasets/viking303/nepse-historical-floorsheet (v14); kagglehub download 1.19 GB installed at `~/.cache/kagglehub/...` (outside repo); 1,167 day files sha256-stamped in `data/metadata/corpus_files_sha256.csv`; provenance rows under EXP-0002b |
| `socrateai-official/nepse-open-data` (floorsheet archive) | **ADOPTED — MIT verified — 2024 slice is PRIMARY for 2024** (232/232 sessions) | full MIT text fetched from `raw.githubusercontent.com/socrateai-official/nepse-open-data/main/LICENSE` (2026-11-08); attribution added to README |
| SamirWagle OHLCV (`tier2`, gap-fill only, 11 scrips) | attribution (educational disclaimer, no LICENSE file) | overlap median abs(Δclose)/close = 0.0000% vs tier1 (EXP-0002d) → same upstream, low substitution risk |
| rohankasichhwa OHLCV (`tier1_kaggle`, 100 scrips) | **PENDING student UI licence check** | derivative-figure publication RESTRICTED until student confirms; thesis body unaffected |
| menaceXnadin/nepse-historical-market-data-csv (NEPSE composite index daily) | **SECONDARY input — licence UNSTATED in repo** (GitHub API `"license": null`, checked 2026-11-09) | non-headline use only: R8 regime shading / benchmark series; limitation note logged (-registers); swap-able by user if a licensed index series is preferred |

## (c) Rate-limit / scraping etiquette (for any FUTURE live acquisition)

2 s delays, exponential backoff, session persistence, checkpoint per
stock-month; never scrape the full universe in one run.

## (d) Data licence chain note

Floorsheet derivatives: statistics only (aggregates, network metrics, scores);
row-level data not redistributed (MIT text permits it; conservative choice).
Kaggle CC0 floorsheets (viking303): CC0 permits redistribution; conservative
policy unchanged — statistics only. Kaggle OHLCV (rohankasichhwa): secondary
controls only; no redistribution of rows in the thesis. menaceXnadin NEPSE
index: regime-shading figures only; series not redistributed; licence status
must be re-checked if the index becomes headline evidence.
