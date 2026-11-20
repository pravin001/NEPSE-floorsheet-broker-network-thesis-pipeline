# reports/ — method notes the student will census-read before writing

- `methodology.md` — pipeline derivation notes (Ch.4 seeds) — filled phases 3-4
- `limitations.md` — every NOT EXECUTED / BLOCKED / FAILED + severity (living v2 copy)
- `provenance.md` — provenance narrative (Ch.3) — filled Phase 2
- `research_progress.md` — milestone log (this file)
- `chapter_assets/` — per-chapter handoff packs, key-claims sheet, print tables

Current state: **v2.1.0-reciprocity-correction** (2026-11-19). Analysis frozen;
writing window 22–27 Nov; deadline 2026-11-27. Authoritative resume point:
`AGENTS.md`.

## Milestone log

| date | milestone | tag / commit | EXP |
|---|---|---|---|
| 2026-11-08 | Phase 0 scaffold + environment survey | — | — |
| 2026-11-09 | Phase 0+1: scaffold, leakage/walk-forward/SE-guard test suite (38 green), NABIL 2024-12 sample, DuckDB init | `3a1f1db` | EXP-0000, EXP-0001a–d |
| 2026-11-09 | Anchored expanding walk-forward declared default (deviation logged before scoring) | `7b808cc` | — |
| 2026-11-09 | Phase 2: full corpus 2021–2024 ingested, audited, reconciled — 938/940 sessions | `02b80e0` | EXP-0002b–f |
| 2026-11-09 | Phase 3: daily (symbol,date) network features, outcomes, broker persistence | `fa328b9` | EXP-0003a–d |
| 2026-11-09 | Phase 4: purged walk-forward IF, hypothesis grid, placebo, regime split, event study | `e04802e` | EXP-0004a–e |
| 2026-11-10 | Phase 5: robustness battery (8 tables + survival master) | `1e5a249` | EXP-0005a–g |
| 2026-11-10 | Phase 6: Dash dashboard, 4 pages, extracts-only | `6855e7b` | EXP-0006 |
| 2026-11-10 | Phase 7: freeze | `v1.0-freeze` (`de27f09`) | EXP-0007 |
| 2026-11-11 | v2 Stage 1: statistical interpretation fixes | `6c0b35d` | EXP-0008a–e |
| 2026-11-11 | v2 Stage 2: liquidity controls, wild cluster bootstrap, SE concordance, VIF audit | `6d3e33e` | EXP-0009a–d |
| 2026-11-12 | v2 Stage 3: quantile panel, EGARCH outcomes, trade-size heterogeneity | `e6a835c`, `8207c8e` | EXP-0010a–c |
| 2026-11-12 | v2 Stage 4: effective-N, broker panel, cost-benefit, subgroups, event-study upgrade | `64705a4` | EXP-0011a–f |
| 2026-11-12 | v2 Stage 5: canonical headline set, chapter skeletons, limitations, chapter map | `31fe5c8` | EXP-0012 |
| 2026-11-13 | v2 Stage 6: clean rebuild, freeze snapshot, deposit prep, register audit | `v2.0-a++-freeze` (`8899c51`) | EXP-0013 |
| 2026-11-13 | v2.0.1 handoff: 67-claim verified crosswalk, Ch.1–6 packs, deposit preflight | `v2.0.1-handoff` (`2b81052`) | EXP-0014 |
| 2026-11-14 | v2.0.2 pre-write sprint: licences, F1–F10 figures, print tables, 39 reference candidates | `v2.0.2-prewrite` (`74606c3`) | — |
| 2026-11-14/15 | Public metadata, author release approval, upstream terms, University disclosure | `55ba473`, `499f8c2`, `4ce43e3`, `3a00dea` | — |
| 2026-11-18 | Viva notes removed from the repository (kept privately) | `730e1f3` | — |
| 2026-11-18 | Reciprocity-volume defect fixed (unordered pairs once; self-loops excluded from numerator) | `e2cc72b` | EXP-0015 |
| 2026-11-19 | v2.1.0: full 21-step rebuild from raw; H6 → `HEADLINE_ROBUST`, H10 stays `HEADLINE_MODERATE`; v2.0.2 tables preserved in `outputs/tables/superseded_v2_0_2/` | `v2.1.0-reciprocity-correction` (`6ec8532`, `b67bea5`) | EXP-0015 |

## Remaining (student-only)

- Write Chapters 1–6 per `chapter_assets/writing_order_memo.md`.
- Review all 39 Chapter 2 references (`ch2_references_scaffold.csv`; all `NOT_REVIEWED` on 2026-11-19).
- Close every `STUDENT` item in `chapter_assets/compliance_checklist.md`, incl. B7 (licence decision), F4 (University AI disclosure), G4 (deposit upload decision).
