# Limitations (frozen 2026-11-10 — Phase 7, DC20)

Scope: `docs/analysis_plan.md` §1–§8 pre-declarations + the frozen battery
(EXP-0005a–g). Every limitation registered BEFORE or AT freeze; nothing is
post-hoc softened. All numbers [REAL] with their experiment_id.

## 1. Corpus & coverage
- 938/940 window sessions covered (99.79%); gaps **2021-09-01** and
  **2023-11-27** exist in NO verified source (kaggle CC0, socrateai, both
  OHLCV tiers) → non-imputable (EXP-0002b).
- One relabel: kaggle `2021_03_07_floorsheet.csv` ingested AS **2021-03-08**
  (evidence triple; deviation row 2026-11-09; cited EXP-0002b).
- **2023-02-16 `contract_no_defect`**: all 35,043 rows share ONE contract id
  → ordering-dependent features (incl. end-of-day concentration) EXCLUDE the
  day; level aggregates keep it (EXP-0002b/c; page-2 dashboard marks it).
- Dedupe: 752 duplicate (date,symbol,contract_no) keys — 506 exact-drops +
  246 **signature-conflict keys kept NON-merged** (deterministic full-
  signature pick; deviation row; EXP-0002c) — conflicts are 0.006% of rows.
- Junk scrape rows (19 pairs + 4 empty-symbol rows) stay in raw with NULL
  volume; no aggregate touches them (post-SV7 filter, EXP-0003a).

## 2. Source/licence policy (D6/D8)
- 2021-2023 = kaggle viking303 **CC0**; 2024 = socrateai **MIT** (primary;
  SV1(b) adoption), kaggle-2024 = cross-check only (232/232 socrateai).
- OHLCV: tier1_kaggle primary — **licence PENDING student UI check; figures
  RESTRICTED until confirmed** (EXP-0002d); tier2 SamirWagle = gap-fill
  only (overlap median Δclose 0.0000% on 28,908 non-null pairs).
- NEPSE composite index: repo licence **unstated_in_repo** → SECONDARY
  (regime shading/benchmark only; R8; swap-able).

## 3. Floorsheet-structure constraints
- Rows are **NOT tx-ordered** → all ordering statistics sort by
  `contract_no`; contract_no is DAILY-GLOBAL → per-(symbol,date) id gaps
  are expected, not defects (sibling-validated).
- Volume counts the BUY side (EXP-0002e reconciliation, top-12 ratio
  median 1.0000, 94.7% of pairs in [0.98, 1.02]).
- Full-market OHLCV covers 100/530 scrips (tier1) → corpus-wide fs/OHLCV
  volume ≈ 2× is a **coverage/scope artifact, not a finding** (limiation
  logged at EXP-0002e).

## 4. Design, folds, estimators (DC1–DC20; D7/D9)
- Universe = per-fold top-10 by TRAIN-only mean turnover (≥90% coverage).
  Default fold mode = **anchored expanding** (D7 deviation, pre-scoring);
  sequential retained as variant only — it scores JUST the middle segments
  (2021-07→2023-06; no 2024/bubble-tail coverage), pooled Spearman vs
  anchored +0.87 on 2,731 overlapping OOS rows (EXP-0005g).
- §3.2 purge rule operationalized as max-VIF on the FULLY STANDARDIZED
  design (incl. the market control): κ(std) = 3.3 → no purge fired; VIF
  ≤ 2.38 (deviation row; EXP-0004b).
- Fama-MacBeth uses ONLY estimable date cross-sections (n ≥ 1+#regressors
  AND full-rank, else skipped) — FM is concordance evidence, not headline
  (EXP-0004b; guard deviation row).
- DK (bw=5) is primary; BH q=0.10 over the family of 10; the placebo
  conjunction applies ONLY to placebo-scoped rows (H2/H3) — a constraint
  never applied is NOT a failure (deviation row; EXP-0004c).

## 5. Findings-level limitations (what the result does NOT establish)
- **The IF anomaly score has NO out-of-sample forward-return content**:
  placebo permutation shares H2 = 0.800 / H3 = 0.640 ≈ random; ALL-events
  CAR +0.13% (p .569); null survives LOO, eras, thresholds (EXP-0004c,
  EXP-0004e, EXP-0005a/e).
- Headline signals are **tier-localized**: ranks 11-15 external
  replication passes 0/5 (raw p ≥ .23; directions preserved, magnitudes
  shrink 2–4×) → likely a liquidity/attention-tier phenomenon, NOT a
  market-wide regularity (EXP-0005f).
- Specificity of the horizon: BH passes die at t+2/t+3 (raw H7 p .0185 /
  H4 .0321); at t+5 only H7 survives (p .0061); signs stable, magnitudes
  grow with k → short-horizon effect family (EXP-0005b).
- **H8 is fragile twice**: loses significance at the top-1% EoD cutoff
  (−0.60 bp, p .76) and in the normal era (−4.44 bp, p .17) → H8 is a
  bubble-era, mid-tail effect (EXP-0005c/e).
- **H4 shows the OPPOSITE sign** to the declared negative (+7.51 bp base;
  +10.49 bp normal era — a concentration *premium* in daily forward
  returns), FM p .0082 concordant → interpretive care; effect is normal-era
  driven (EXP-0004b/d, EXP-0005e).
- H6/H10: DK-primary only (FM p .5403 / .2896) — DK sample-dependent SE
  family; treat as suggestive (EXP-0004b).
- Regime split: NO interaction significant (min p .1171) → era statements
  rest on magnitude comparisons, not identified interactions (EXP-0004d).
- Illiquid-trigger event subsample: −2.45%, p .0018 but **n = 16** —
  small-n caveat, not headline (EXP-0004e).
- Alternative-scorer leg is rank-correlation ONLY (SV5): diag-z²-sum
  (+.95) vs full Mahalanobis (+.83) confirm a shared quadratic class but
  score LEVELS/tails stay method-dependent (EXP-0005d).
- Alternative-EoD leg is threshold sensitivity (raw p + concordance, no
  fresh BH family — declared); fwd_k horizons use within-window closes
  only (coverage 99.9/99.7/99.4%; declared) (EXP-0005b/c).

## 6. Presentation (Phase 6)
- Dashboard is EXTRACTS-ONLY: top-12-symbol extracts + register tables; it
  computes no statistics beyond labeled descriptive aggregates (R11) and
  serves no full-corpus data (EXP-0006).

## 7. What would change the conclusions
- Any amendment to `configs/project.yaml` (frozen fingerprint
  `9a60208f…b012f`; enforced by `tests/test_freeze.py`), a failed headline
  number (headline set H4/H6/H7/H8/H10, bh_sig_q10 + sign directions
  pinned by tests), or a source/licence upgrade (tier1, index) must be
  registered as a NEW experiment row — never a silent edit.
