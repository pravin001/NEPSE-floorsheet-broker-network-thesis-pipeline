# Chapter 5 — Results · skeleton (v2.1.0 reciprocity correction)

**Stage-5 artifact.** Bullet skeleton + one-sentence claim per numbered
subsection; the student writes prose. No thesis paragraphs here.

**Version note (2026-11-19).** Every number below is from the corrected
v2.1.0 rebuild (EXP-0015). The v2.0.2 values are superseded and preserved in
`outputs/tables/superseded_v2_0_2/`; see `reports/reciprocity_correction.md`.
The principal change is that **H6 is now a second headline** and H10's
magnitude roughly doubled; H7/H8/H4 and the nulls keep their v2.0.2
dispositions.

Structure note: the 19-day brief is not present in this repository, so
§5.2/§5.3 of the brief cannot be transcribed literally. The subsection order
below follows `docs/chapter_artifact_map.md` (main regression → placebo →
regime split → event study → robustness) and appends the v2 Stage-1–4
adjudication. Logged as Stage-5 deviation #28.

Path refresh (v2.0.1 handoff): every table path in this skeleton now resolves
to a tracked v2 artefact and is listed in the verified crosswalk
(`docs/chapter_artifact_map.md`), audited by `scripts/audit_chapter_map.py`.
Figures under `outputs/figures/` are real but remain licence-restricted and are
not part of the derived deposit (`reports/limitations.md` L4).

**Units.** `estimated_beta` = basis points per 1 TRAIN-fold standard deviation
of the feature (bp/SD). Raw inference α = .05; BH multiplicity q = .10;
Romano–Wolf FWER q = .10. `n = 7,116` unless stated. Canonical table:
`outputs/tables/v2_final_headline_set.csv`.

---

## 5.1 Sample, folds, and effective N

**Claim (one sentence):** The out-of-sample panel contains 7,116 symbol–date
rows across 12 stocks and 723 dates, with an effective N of 6,383 after
two-way fixed-effect absorption.

- Anchored purged walk-forward, 4 folds, 938 scoring sessions; 7,126 OOS rows;
  666 anomaly events = 9.3% of scored rows (EXP-0004a, EXP-0015).
- 10 rows lost to missing outcome/feature → 7,116 estimable rows (EXP-0004b).
- `n_effective = 7,116 − (12−1) − (723−1) = 6,383` (EXP-0011a).
- FM usable cross-sections: 712–714 depending on feature/outcome slice
  (EXP-0011a).
- 2023-02-16 `contract_no_defect` excluded from ordering-dependent features
  (EoD concentration); level aggregates retain the day (EXP-0002b/c).
- Universe and standardisation constants are TRAIN-fold only (DC1; EXP-0004a).

**Assets.** Table 5.1 = `outputs/tables/hypothesis_grid_results_v2.csv`
(`n_obs`, `n_stocks`, `n_dates`, `n_effective`, `n_cross_sections`).
Design pointers: `docs/analysis_plan.md` §3; `src/nepsemsc/ml/panel_data.py`.

---

## 5.2 Main hypothesis grid

**Claim (one sentence):** Five of ten tests pass BH q = .10 (H4, H6, H7,
H8, H10), but H4 has the opposite sign to its pre-declaration and only H6
and H10 survive Romano–Wolf FWER correction.

- Grid: 10 pre-registered tests; DK(bw=5) primary; BH q = .10 over the family
  of 10 (EXP-0004b, EXP-0015).
- BH-passing adjusted p range: .0136–.0918.
- Point estimates (bp/SD): H1 −1.557 (p .431); H2 −1.494 (.594);
  H3 +0.178 (.953); H4 **+7.510** (.0275); H5 −1.856 (.488);
  H6 **−22.948** (.0048); H7 **+3.952** (.0274); H8 **−4.471** (.0459);
  H9 +1.817 (.459); H10 **+20.642** (.0014).
- Sign vs pre-declaration: H7/H8/H10 agree; H4 opposite (declared negative);
  H6 ambiguous; H1/H2/H3/H5/H9 disagree but are null.
- H4 is the only BH-passing test whose sign contradicts the declared
  direction → Stage-1 label `EXPLORATORY_POST_HOC` (EXP-0008a).

**Assets.** Table 5.2 = `outputs/tables/hypothesis_grid_results.csv` (frozen
v1) and `outputs/tables/hypothesis_grid_results_v2.csv` (governance columns).

---

## 5.3 Placebo, anomaly-score nullity, and regime diagnostics

**Claim (one sentence):** The anomaly-score hypotheses fail both the placebo
and multiplicity gates, and no calendar-regime interaction is significant.

- Placebo permutation shares: H2 = **.805**, H3 = **.540** ≈ random
  (EXP-0004c, EXP-0015).
- Expanded placebo: 1,000 full-panel shuffles + within-symbol block shuffles
  confirm the anomaly-score null (EXP-0008e, EXP-0015).
- DC13 placebo-outcome: 7/10 rows flag; the reciprocity pair carries the
  largest past-|ret| association **+44.78 bp** (p 8.7e-10) vs forward effects
  of +20.64 (H10) and −22.95 (H6) → part of both headlines is persistence
  (EXP-0008d, EXP-0015).
- Regime split: bubble 2,737 rows (38.5%) vs normal 4,379 (61.5%); **no
  interaction significant** (min p .1171); H7/H8 same-sign in both eras
  (EXP-0004d).
- Normal-era drop-bubble re-fit: H4/H6/H7/H10 survive BH; H8 fails
  (−4.44 bp, p .1703) → H8 is bubble-era driven (EXP-0005e).

**Assets.** `outputs/tables/placebo_distribution_expanded.csv`,
`outputs/tables/placebo_outcome_test.csv`,
`outputs/tables/regime_split_results.csv`,
`outputs/tables/robustness_drop_bubble_grid.csv`.

---

## 5.4 Event study

**Claim (one sentence):** The 666-event sample shows no economically
meaningful abnormal return — mean CAR +19.33 bp (p .402) — and only the rank
distribution shifts (date-clustered z 2.99, p .0030).

- 666 events on 392 dates; 435 events (65.3%) share a date with another event
  → event-level p-values are upper bounds (EXP-0011e, EXP-0015).
- Reconstruction gate: max |reconstructed CAR − stored CAR| = **0.0**; no
  re-estimation (EXP-0011e).
- Mean CAR **+0.001933** (+19.33 bp), SD .0595, median +.002814
  (+28.14 bp); 53.0% positive (EXP-0011e, EXP-0015).
- Mean CAR t = 0.839 (p .4018); BMP t = 1.339 (p .1809); BMP z = 1.819
  (p .0689); Corrado rank z = **3.481** (p .00050) (EXP-0011e, EXP-0015).
- Date-clustered: mean CAR t = 1.186 (p .2363); rank z = **2.986**
  (p .0030) (EXP-0011e, EXP-0015).
- Uniform market-adjusted mean **−75.21 bp** (p .00050) is mechanical:
  pre-window alpha −0.0962%/day; corr(alpha, CAR−CAR_ma) = −.762
  (EXP-0011e, EXP-0015).
- Illiquid-trigger appendix: n = 16, mean −227.39 bp, BMP z/rank null
  (EXP-0004e/0011e, EXP-0015).

**Assets.** Table 5.4 = `outputs/tables/event_study_upgraded.csv`; date-
clustered table = `outputs/tables/event_study_clustered_inference.csv`;
AR paths = `outputs/tables/event_study_upgraded_ars.csv`.

---

## 5.5 Robustness battery (v1 Phase 5)

**Claim (one sentence):** The five v1 BH-passing estimates are sign-stable
across leave-one-stock-out, horizon, threshold, and era variants, but they do
not replicate below the top-10 tier and H8 fails two registered checks.

- Leave-one-stock-out: all five BH-passing estimates sign-stable 12/12; raw
  p < .10 in 11/12 (H4), 12/12 (H6/H7/H10), 10/12 (H8); H2/H3 stay null 0/12
  (EXP-0005a, EXP-0015). H6 β range −25.411 to −19.766 bp; H10 +18.020 to
  +23.030 bp.
- Horizons: BH pass 0/5 at t+2; 2/5 at t+3 (H6 −40.37 bp, H7 +7.77) and
  2/5 at t+5 (H6 −55.73, H7 +10.22); H10 is not horizon-robust (p .130 /
  .293 / .292); directions identical at every horizon (EXP-0005b, EXP-0015).
- EoD thresholds: H7 +3.72 bp (p .0296) at 1% and +3.78 (p .0387) at 10%;
  H8 **−0.60 bp (p .7634)** at 1%, −4.24 (p .0633) at 10% (EXP-0005c).
- Alternative scorers: mean OOS Spearman vs IF — Mahalanobis +.86 (range
  .78–.92), diag-z² +.95 (.93–.96), LOF +.63 (.48–.79), OC-SVM +.54
  (.44–.66) (rank-correlation only; SV5) (EXP-0005d, EXP-0015).
- External top-5 (ranks 11–15): 3,409 estimable OOS rows / 256 events;
  **0/5 BH pass** (smallest raw p .0539, H10); magnitudes attenuate, and H10
  falls to 80% of base while remaining non-significant (EXP-0005f, EXP-0015).
- Sequential fold mode: pooled Spearman +.87 vs anchored on 2,731 overlapping
  rows; coverage limited to 2021-07→2023-06 (EXP-0005g).

**Assets.** Table 5.5 = `outputs/tables/robustness_headline_survival.csv`
(46 variant×headline rows) + `robustness_*` tables.

---

## 5.6 v2 statistical reclassification

**Claim (one sentence):** After multiplicity, dependence, liquidity,
distributional, and specification checks, H6 is a robust headline and H10 a
moderate headline; H7/H8 are fragile, H4 is exploratory, and H1/H2/H3/H5/H9
are powered nulls.

### 5.6.1 Multiplicity — Romano–Wolf

- B = 999, common row-level Rademacher signs, recentred t*; p = (1+#)/(B+1)
  (EXP-0008b).
- RW p: H6 **.031** and H10 **.012** (q = .10 survivors); H4 .152; H7 .152;
  H8 .199; H1/H2/H3/H5/H9 .918–.959 (EXP-0008b, EXP-0015).
- H7 loses raw significance under FWER; H8 never survives; H4 is already
  exploratory (EXP-0008b).

### 5.6.2 Dependence — wild cluster bootstrap and SE concordance

- WB (CGM-2008 ReBWB, cluster = symbol, B = 999; 12-cluster small-G caveat):
  H4 .002; H6 **.001**; H7 .022; H8 .095; H9 .100; H10 **.004**
  (EXP-0009c, EXP-0015).
- Four-SE concordance (DK / DC-v2 / FM / WB, each p < .10):
  STRONG H4/H6/H7/H8; MODERATE H10; NULL other five (EXP-0009d, EXP-0015).
- True DC-v2 p: H4 .0053; H6 **6.71e-6**; H7 .0086; H8 .0574; H10
  **1.00e-5**; v1 `p_dc` was a silent time-kernel fallback equal to DK
  (EXP-0009d, EXP-0015).
- FM p: H4 .0082; H6 **.0028**; H7 .0094; H8 .0587; H10 **.4901**
  (EXP-0004b/0009d, EXP-0015).

### 5.6.3 Liquidity controls

- Three γ controls (Amihud, Roll, Corwin–Schultz), identical 7,116 rows, all
  complete cases (EXP-0009a/b).
- Every BH-passing estimate moves **< 6%** and keeps its sign; H10
  **+19.658 bp (p .0021)** vs base +20.642 (.0014), −4.8%; H6 **−23.182**
  (p .0043), −1.0%; H7 −5.80%; H4 −2.04%; H8 −1.44% (EXP-0009b, EXP-0015).
- Null estimates: H1 +37.1%, H2 +18.2%, H3 −40.2%, H5 +0.8%, H9 +5.2%; all
  remain null (EXP-0009b, EXP-0015).
- VIF max **2.049** (`anomaly_score_z`); |r| max .637; no collinearity flag
  (EXP-0009d, EXP-0015).

### 5.6.4 EGARCH-standardised outcomes

- EGARCH(1,1) symmetric (`o = 0`), TRAIN-fold fits; 40 fits (37 converged,
  4 degenerate); 6,819/7,116 usable z rows (EXP-0010a).
- H10 **+547.22 z (p .0497)**; H6 **−1048.08 (.0016)**; H7 +149.15 (.0638);
  H8 −157.91 (.0745); H4 +256.86 (.0544); all five sign-match the base beta
  and pass at α = .10 (EXP-0010a, EXP-0015).
- Exclusion sensitivities: H4 fails both (p .1410 / .1182); H7 fails the
  degenerate-exclusion (p .1157) and passes the non-converged exclusion
  (p .0536); H6/H8/H10 remain < .10 (EXP-0010a, EXP-0015).
- `survives_egarch` in the final table = sign match AND p < .10.

### 5.6.5 Quantile tails

- Quantile panel: 50/50 fits converged; 7,116 × 737 two-way design
  (EXP-0010b).
- H10 **BOTH_TAILS / INCREASING**: τ = .10 +4.84 bp; τ = .50 +8.93;
  τ = .90 **+34.64**; ratio 7.16 (EXP-0010b, EXP-0015).
- H4 BOTH_TAILS / INCREASING: +2.12 → +9.61 bp (ratio 4.53) (EXP-0010b).
- H6 **BOTH_TAILS / INCREASING**: −21.87 bp at τ = .10, −9.32 at τ = .50,
  −3.63 at τ = .90; ratio 0.166 (the effect weakens toward the upper tail)
  (EXP-0010b, EXP-0015). H8 LOWER_TAIL / U_SHAPE: −3.17 → −0.47
  (EXP-0010b).
- H7 NONE / HUMP: +0.71 (p .117) → +1.21 (p .062); median +2.20
  (EXP-0010b).
- Null tail labels are unadjusted descriptive only (EXP-0010b, EXP-0015).

### 5.6.6 Trade-size heterogeneity

- TRAIN-fold p10/p90 per (fold, symbol); small < p10, medium p10–p90,
  large > p90; minimum-5-trades guard (EXP-0010c).
- H7 large-ticket **+4.519 bp (p .0356)** (sign-aware pass); small-ticket
  bucket unusable (0.35% of volume) (EXP-0010c).
- H8 medium-ticket −5.266 bp (p .0056); not a large-ticket effect
  (EXP-0010c).

### 5.6.7 H7 specification curve

- 144 executed specifications / **72 unique design betas** (plan says “72”;
  arithmetic is 4×2×2×3×3 = 144; deviation #20) (EXP-0011b).
- Outcome `abs_ret`: **72/72 positive**, median +3.952 bp, CI-excluding-0
  share .583, p < .05 share .542 (EXP-0011b).
- Subsample: full-sample CI-exclusion .958 vs bubble .292; H7 is bubble-
  fragile (EXP-0011b).
- Outcome `ret`: 66/72 negative, median −4.289; 1% EoD cutoff median −0.601
  with **zero** CI exclusions (EXP-0011b).

### 5.6.8 Subgroup heterogeneity

- 36 estimated rows (24 group cells + 12 interactions) + 4 `NOT_EXECUTED`
  circuit-breaker rows (EXP-0011d, EXP-0015).
- **Two H10 subgroup cells survive Bonferroni** (descriptive cells in a
  separate family): turnover bottom-7 **+22.715 bp** (p_bonf **.0183**) and
  size-small **+26.791 bp** (p_bonf **.0473**) (EXP-0011d, EXP-0015).
- **No interaction survives**: H10×turnover −10.686 bp (p **.1524**);
  H7 small-size +7.020 (p_bonf .1629); H7×size −5.557 (p_bonf .1932)
  (EXP-0011d, EXP-0015).
- Circuit-breaker split unavailable: no limit-hit flag in the corpus or
  verified archives (EXP-0011d).

### 5.6.9 Economic magnitude vs cost floor

- Declared explicit round-trip cost floor **30–50 bp**; excludes brokerage,
  spread, CNS carry (EXP-0011f).
- H10 +20.642 bp/SD is **1.45–2.42× below** the floor; H7 +3.952 is
  **7.59–12.65× below**; H4 +7.510 is **3.99–6.66× below** (EXP-0011f,
  EXP-0015).
- At 1 SD engagement, none is standalone tradable; conditional/stacked
  tradability remains speculative (EXP-0011f).

**Assets.** Tables 5.6/5.7:
`outputs/tables/se_concordance.csv`,
`outputs/tables/wild_cluster_bootstrap.csv`,
`outputs/tables/headline_with_liquidity_controls.csv`,
`outputs/tables/headline_with_egarch_outcome.csv`,
`outputs/tables/quantile_tail_summary.csv`,
`outputs/tables/trade_size_heterogeneity.csv`,
`outputs/tables/specification_curve_h7.csv`,
`outputs/tables/heterogeneity_subgroups.csv`,
`outputs/tables/economic_magnitude.csv`. Figures:
`outputs/figures/specification_curve_h7.png` (Figure 5.1),
`outputs/figures/quantile_H10.png` (Figure 5.2),
`outputs/figures/trade_size_heterogeneity.png` (Figure 5.3),
`outputs/figures/quantile_all_tests.png` (Figure 5.4),
`outputs/figures/egarch_outcomes.png` (Figure 5.5),
`outputs/figures/feature_correlation.png` (Figure 5.6). EXP-0008a–0011f.

---

## 5.7 Canonical headline set and final classification

**Claim (one sentence):** The canonical v2.1.0 set contains one robust
headline (H6), one moderate headline (H10), one exploratory post-hoc result
(H4), two fragile nulls (H7/H8), and five powered nulls (H1/H2/H3/H5/H9).

- Composition rule: final = Stage-1 classification ∩ Stage-2 concordance ∩
  Stage-3 checks; every demotion is citable to a Stage-1–3 artifact (EXP-0012,
  EXP-0015).
- H6 → `HEADLINE_ROBUST`: Stage-1 `CONFIRMED_HEADLINE` (RW .031), Stage-2
  `STRONG` 4/4, liquidity pass (−1.0%), EGARCH pass (p .0016), both tails
  increasing (EXP-0012, EXP-0015).
- H10 → `HEADLINE_MODERATE`: Stage-1 `CONFIRMED_HEADLINE` (RW .012), Stage-2
  headline True, liquidity pass (−4.8%), EGARCH pass (p .0497), both tails
  increasing; FM p .4901 and MODERATE (not STRONG) concordance block
  `HEADLINE_ROBUST` (EXP-0012, EXP-0015).
- H4 → `EXPLORATORY_POST_HOC`: opposite sign to pre-declaration; RW p .152
  (EXP-0012).
- H7/H8 → `NULL_FRAGILE`: BH pass but RW p .152/.199; H8 also
  MDE-underpowered (`|β|/(MDE₈₀/2) = 1.426`) (EXP-0012).
- H1/H2/H3/H5/H9 → `NULL_POWERED`: Stage-1 `NULL_ROBUST` + MDE
  `NULL_POWERED`; Stage-1 label maps to the brief's NULL_POWERED taxonomy
  (EXP-0012).
- Column semantics: `survives_liquidity` = remains significant at α = .10
  under the three γ controls (null rows are False by construction, not
  because the estimate changed); `survives_egarch` = sign match AND p < .10.

**Assets.** Table 5.3 = `outputs/tables/v2_final_headline_set.csv`.
Companion: `reports/limitations.md`; `docs/experiment_register.md` EXP-0012.

---

## Chapter asset checklist

| asset | file | used in |
|---|---|---|
| canonical headline set | `outputs/tables/v2_final_headline_set.csv` | §5.7, Table 5.3 |
| main grid | `outputs/tables/hypothesis_grid_results.csv` | §5.2, Table 5.2 |
| governance grid | `outputs/tables/hypothesis_grid_results_v2.csv` | §5.1/§5.7 |
| RW p-values | `outputs/tables/hypothesis_grid_results_rw.csv` | §5.6.1 |
| SE concordance | `outputs/tables/se_concordance.csv` | §5.6.2 |
| WB p-values | `outputs/tables/wild_cluster_bootstrap.csv` | §5.6.2 |
| liquidity controls | `outputs/tables/headline_with_liquidity_controls.csv` | §5.6.3 |
| EGARCH outcomes | `outputs/tables/headline_with_egarch_outcome.csv` | §5.6.4 |
| quantile tails | `outputs/tables/quantile_tail_summary.csv` | §5.6.5 |
| trade size | `outputs/tables/trade_size_heterogeneity.csv` | §5.6.6 |
| H7 spec curve | `outputs/tables/specification_curve_h7.csv` | §5.6.7 |
| subgroups | `outputs/tables/heterogeneity_subgroups.csv` | §5.6.8 |
| cost-benefit | `outputs/tables/economic_magnitude.csv` | §5.6.9 |
| event study | `outputs/tables/event_study_upgraded.csv` | §5.4 |
| robustness | `outputs/tables/robustness_headline_survival.csv` | §5.5 |
| verified crosswalk | `docs/chapter_artifact_map.md` | all sections |
| audit guard | `tests/test_chapter_map_integrity.py` | build check |
