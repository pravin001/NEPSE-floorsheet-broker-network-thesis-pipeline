# Block log (R10 / engineering rule 7 / SV triggers)

Every BLOCKED/FAILED item gets a row: timestamp, trigger condition observed,
decision taken, degraded artefact impact. NO scope reduction here — drops are
scope changes, distinct from blocks, and appear in limitations instead.

## 2026-11-08 — inherited + re-verified intelligence (Phase 0/1)

| ts (UTC+5:45) | item | trigger | decision | evidence |
|---|---|---|---|---|
| 2026-11-08 ~23:00 | nepalstock.com direct scraping | HTTP 000 ×3 today (curl, 20 s timeout); ALSO network-blocked per sibling project D9 on 2026-11-08 | Never attempt direct scrape of nepalstock.com in this project. Adopt SV1(b): pre-scraped archive `socrateai-official/nepse-open-data` (MIT licence text verified by sibling project 2026-11-08; local 650-file archive present) | this log + `docs/experiment_register.md` EXP-0001 |
| 2026-11-08 ~23:00 | `viking303` floorsheet archive per brief | NOT FOUND (websearch by sibling project 2026-11-08; not re-searched today — treat as unavailable) | SV1 primary source replaced by socrateai archive; documented as substitution, NOT a scope drop | above row |
| 2026-11-08 ~23:30 | floorsheets for 2021–2023 (bubble era) | No daily floorsheet file in local archive (covers 2024-01→2026-11); no known public archive | OPEN — bounded Phase-2 search (~2 h) precedes the scope fork; fork trigger: if unverified by 2026-11-12, adopt 2024–2026 window and re-derive R8 regimes from OHLCV drawdown/momentum (analysis_plan §5). NOT silent: decision will be logged as a DECISION row, everything proceeds | `docs/analysis_plan.md` |
| 2026-11-08 ~23:35 | Kaggle OHLCV licence | kagglehub metadata carried no machine-readable licence (sibling D9) | PENDING user UI check; thesis text unaffected; derivative publication RESTRICTED till checked | `docs/ai_use_policy.md` |
