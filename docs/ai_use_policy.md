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
| `viking303` floorsheet archive (brief's primary) | **NOT FOUND** (websearch, sibling 2026-11-08) | SV1(b) chain engaged |
| `socrateai-official/nepse-open-data` (floorsheet archive) | **ADOPTED — MIT verified** | full MIT text fetched from `raw.githubusercontent.com/socrateai-official/nepse-open-data/main/LICENSE` (2026-11-08); attribution added to README |
| `SamirWagle/Nepse-All-Scraper` (prices proxy) | NO LICENSE file; educational-use disclaimer | internal analytic use with attribution; per-file provenance |
| Kaggle `rohankasichhwa/nepse-daily-stock-data-2012-2025` | **PENDING student UI licence check** | derivative-figure publication RESTRICTED until student confirms; thesis body unaffected |

## (c) Rate-limit / scraping etiquette (for any FUTURE live acquisition)

2 s delays, exponential backoff, session persistence, checkpoint per
stock-month; never scrape the full universe in one run.

## (d) Data licence chain note

Floorsheet derivatives: statistics only (aggregates, network metrics, scores);
row-level data not redistributed (MIT text permits it; conservative choice).
Kaggle OHLCV: secondary controls only; no redistribution of rows in the thesis.
