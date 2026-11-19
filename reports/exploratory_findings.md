# Exploratory findings — v2 Stage 1 (EXP-0008a–e) — v2.1.0 update

Generated 2026-11-11 (NPT) from the frozen v1 artifacts + the Stage-1 v2 runs;
updated 2026-11-19 after the reciprocity correction (EXP-0015). All numbers
below trace to exactly one experiment row: EXP-0008a (this reclassification),
EXP-0008b (Romano–Wolf), EXP-0008c (MDE), EXP-0008d (DC13 placebo-outcome),
EXP-0008e (expanded placebo battery), EXP-0015 (corrected rebuild). No v1 file
was edited; the governance table is `outputs/tables/hypothesis_grid_results_v2.csv`.
The canonical correction record is `reports/reciprocity_correction.md`; v2.0.2
values are preserved in `outputs/tables/superseded_v2_0_2/`.

## 0. Stage-1 disposition (mechanical, pre-declared rules)

| test | v1 BH q=.10 | Stage-1 classification | RW p | reason |
|---|---|---|---|---|
| H1 | no | NULL_ROBUST | .918 | BH fail; LOO-stable null |
| H2 | no | NULL_ROBUST | .918 | BH fail; placebo null; LOO-stable |
| H3 | no | NULL_ROBUST | .959 | BH fail; placebo null; LOO-stable |
| H4 | yes | **EXPLORATORY_POST_HOC** | .152 | opposite sign to pre-declaration |
| H5 | no | NULL_ROBUST | .918 | BH fail; LOO-stable null |
| H6 | yes | **CONFIRMED_HEADLINE** | **.031** | passes RW q=.10 |
| H7 | yes | **NULL_FRAGILE** | .152 | RW demotion (rw p > .10) |
| H8 | yes | **NULL_FRAGILE** | .199 | two registered robustness failures |
| H9 | no | NULL_ROBUST | .918 | BH fail; LOO-stable null |
| H10 | yes | **CONFIRMED_HEADLINE** | **.012** | passes RW q=.10 |

RW = Romano–Wolf free step-down, B=999, common row-level Rademacher signs,
recentered t*; p convention (1+#)/(B+1) (deviation #12). The literal
full-family min-p variant is co-reported in
`outputs/tables/hypothesis_grid_results_rw.csv`.

**Net Stage-1 result: two of the five v1 headlines survive a family-wise error
correction at q=.10 — H6 (.031) and H10 (.012).** H7 is demoted, H8 is already
demoted, H4 is exploratory. Both survivors carry the DC13 persistence flag
(§3): reciprocity predicts past |ret| more strongly than forward |ret|. This
tension is the central Stage-1 disclosure. H6 was `NULL_FRAGILE` in v2.0.2;
the corrected feature moves it to `CONFIRMED_HEADLINE` without any change to
the composition rule.

---

## 1. H4 `buyer_hhi → ret_fwd1` — EXPLORATORY_POST_HOC

**(a) Pre-declared direction.** NEGATIVE (`docs/analysis_plan.md`, H4:
buyer concentration → lower forward return).

**(b) Estimate.** +7.51 bp per 1-SD buyer-HHI (DK bw=5, n=7,116), raw
p=.02755, BH-adjusted p=.0689, FM p=.00818 (same sign), LOO sign-stable 12/12
(raw p<.10 in 11/12). The estimate is positive and significant in the
**opposite** direction to the declared hypothesis.

**(c) Why exploratory, not confirmatory.** A directional hypothesis is not
confirmed by a significant estimate of the opposite sign (v1 `sign_agrees =
False`). The result is a real, reproducible pattern in this sample — it
survives the v1 robustness battery and is stronger in the normal era — but it
is post-hoc relative to the pre-declared direction. It is reported as an
exploratory regularity, never as confirmation of H4. Romano–Wolf p=.159
(literal .190) also blocks any FWER-level headline status.

**(d) Candidate explanations (each a candidate, not a claim).**

1. **Illiquidity / size composition** — high buyer concentration may proxy
   for small, illiquid names with a higher required return. *Test:* Stage-2
   liquidity controls (Amihud, Roll, Corwin–Schultz, effective tick) and the
   Stage-4 train-fold size subgroup. Pending.
2. **Price-level / fixed-tick effects** — NEPSE's coarse tick grid can induce
   discreteness in returns that correlates with price level and concentration.
   *Test:* Stage-2 effective-tick control; Stage-3 trade-size buckets. Pending.
3. **Temporary price pressure** — concentrated buying pushes t+1 prices up and
   reverses later. *Test:* EXP-0005b horizons. Executed: H4 grows to
   +12.9 / +14.2 / +13.1 bp at t+2 / t+3 / t+5, so there is **no short-run
   reversal** in the available horizons; this candidate is disfavoured (only
   horizons ≤5 sessions are observable).
4. **DHM-style normal-era phenomenon** — concentration/attention effects
   concentrated in the normal (2023+) era. *Test:* EXP-0004d/0005e. Executed:
   bubble-era β ≈ −0.26 bp vs normal-era +10.49 bp; the effect is a normal-era
   phenomenon in this sample.
5. **Persistent-volatility specification channel** — added because of the
   Stage-1 DC13 result: buyer_hhi predicts *past* |ret| at −9.97 bp
   (p=3.7e-7, §3). The forward estimate may partly inherit persistent
   volatility rather than a clean concentration→return channel. *Test:*
   Stage-2/3 controls that absorb lagged volatility / illiquidity; the
   pre-declared liquidity battery is the first opportunity. Pending.

H4's normal-era, opposite-sign pattern is therefore reported as an
exploratory candidate with at least two live explanations (1/2 vs 5), not as
a confirmed concentration premium.

---

## 2. H8 `end_of_day_concentration → ret_fwd1` — NULL_FRAGILE (regime/threshold artifact)

**(a) Pre-declared direction.** NEGATIVE.

**(b) Estimate.** −4.47 bp per 1-SD EoD concentration, DK p=.04589, BH-adjusted
p=.09176, FM p=.05867 (borderline). MDE₈₀ = 6.27 bp; |β|/MDE = 1.43 → the
null is **underpowered**, not a precise zero (EXP-0008c).

**(c) Two registered robustness failures.**
- EXP-0005c (EoD cutoff): at the top-1% cutoff the estimate collapses to
  −0.60 bp (p=.7634); at 10% it is −4.24 bp (p=.0633). The effect lives in
  the middle of the EoD tail, not the extreme tail.
- EXP-0005e (drop bubble): normal-era estimate −4.44 bp (p=.1703) — it fails.
  The base effect is bubble-era-driven.
- Stage-1 RW p=.203 (also fails the q=.10 rule).

**(d) What H8 is not.** It is not a past-volatility artifact: DC13 passes
(+1.68 bp, p=.2784, §3), and the real EoD beta lies in the tail of the
within-block shuffled-EoD distribution (lower share .006, two-sided .013,
§4). The fragility is specifically **era and threshold** dependence: the
negative EoD→return effect is a bubble-era, mid-tail phenomenon in this
sample, not a stable general relation. H8 is therefore classified
NULL_FRAGILE and must not be quoted as a headline.

---

## 3. DC13 placebo-OUTCOME — the features predict the PAST absolute return

Construction (pre-declared in v1 §3.4, executed now; deviation #13):
`abs_ret_lag1 = |ret(t−1)|` on each symbol's own non-null-return session
adjacency, merged via `build_oos_panel(..., extra_outcome_cols=...)`; same
design/estimator as the grid (feature + log_volume_z + market_ret_loo_z,
DK bw=5). A significant coefficient means the feature predicts the **past**
absolute return — a specification/persistence flag, not a forward result.
All rows n=7,116 (the lag is available for every OOS row; the full outcomes
history precedes the OOS window).

| unique feature | tests | β (bp) | DK p | verdict |
|---|---|---|---|---|
| self_loop_ratio | H1, H9 | −3.94 | .00554 | **SPECIFICATION_ERROR_FLAG** |
| anomaly_score | H2, H3 | −6.55 | .00891 | **SPECIFICATION_ERROR_FLAG** |
| buyer_hhi | H4, H5 | −9.97 | 3.7e-7 | **SPECIFICATION_ERROR_FLAG** |
| reciprocity | H6, H10 | **+44.78** | **8.7e-10** | **SPECIFICATION_ERROR_FLAG** |
| end_of_day_concentration | H7, H8 | +1.68 | .2784 | PASS |

**7 of 10 test rows flag; 5 of 5 unique features except EoD flag.** The
duplicated rows (H2/H3, H4/H5, H6/H10, H1/H9, H7/H8) are the same regression
by construction — the DC13 outcome is feature-specific, not
hypothesis-specific.

**Mechanism check (descriptive, not a new pre-registered test).**
|ret| is persistent: corr(|ret(t−1)|, |ret(t+1)|) = .124. The v2.0.2 feature
autocorrelations were reciprocity .308, anomaly_score .157, buyer_hhi .112,
self_loop .025, EoD .028; correlations with past |ret| were reciprocity +.228,
buyer_hhi −.105, anomaly_score −.094, self_loop −.031, EoD −.017. These are
retained as the v2.0.2 descriptive record; the corrected reciprocity series is
not re-described here. The flag pattern is exactly what persistent features
loading on persistent volatility produce. The lag construction was verified
row-by-row (e.g. ADBL: first available session NaN, next session |−0.002273|,
etc.), and the with/without-controls estimates move in the expected direction.
This is a real persistence channel, not an alignment bug.

**Implication for the headlines.** Both RW survivors are exposed: reciprocity
predicts past |ret| at **+44.78 bp** (p **8.7e-10**) and forward |ret| at
**+20.64 bp** (p **.0014**); the lag association is more than twice the forward
one. The forward H6/H10 estimates may therefore partly inherit a persistent
volatility channel. H7/H8 pass DC13, which is a point in their favour even
though RW/robustness demote them. H4 carries the flag too. No promotion or
demotion is made here beyond the declared Stage-1 rules; this section is a
disclosure that must be carried into Stage 2 (liquidity/volatility controls)
and Stage 5 (final classification rationale + limitations).

---

## 4. Expanded placebo battery (EXP-0008e)

All constructions use the same PANEL and design as the v1 placebo. The
corrected Isolation Forest changes the score draws, so the v2.1.0 shares are
reported below; they are not the v2.0.2 draw set.

**(a) 1000 full-panel anomaly-score shuffles.** H2 upper share **.781** (95% CI
.754–.806), H3 lower share **.521** (.490–.552); two-sided **.430 / .935**.
No forward-return content in the IF anomaly score — the placebo conclusion is
unchanged at 1000 draws.

**(b) 1000 within-symbol 5-session block permutations.** H2 upper **.738**
(.710–.764), H3 lower **.537** (.506–.568); two-sided **.482 / .938**.
Preserving short-range score autocorrelation does not rescue a forward signal.

**(c) Negative-control feature `negctrl_eod_lead5`** (future EoD value
placed at t, z-scaled with the same train constants): abs_ret_fwd1
β=−1.92 bp (p=.2633), ret_fwd1 β=−0.05 bp (p=.9776), n=7,066. No 5-session
lead-lag leakage.

**(d) Negative-control `negctrl_eod_blockshuffle`** (EoD shuffled within
5-session blocks, 1000 draws). The shuffled-feature null is calibrated:
mean placebo β ≈ 0 (−0.02 / +0.05 bp), t(mean) = −0.31 / +0.75, and
4.5% / 3.1% of draws reach p<.05. The **real** EoD beta lies in the tail of
this distribution (H7 upper share .009, H8 lower share .006; two-sided
.024 / .013): the EoD forward effect is not an artifact of within-block score
persistence. This is a favourable block-placebo result for H7/H8, not a
negative-control failure; the negative control itself passes calibration.

---

## 5. What Stage 1 changes for the thesis narrative

- The v1 "5/10 BH-passing headlines" set is **not** the v2 headline set. Under
  RW at q=.10 **H6 and H10** survive; H7 is demoted, H8 is fragile, H4 is
  exploratory.
- The EoD pair is the cleanest on the DC13 persistence check (both pass) even
  though H7 is RW-demoted and H8 is era/threshold-fragile.
- The anomaly-score null (H2/H3) is confirmed at 1000 permutations and under
  block permutations; it remains the strongest negative result in the thesis.
- The DC13 flags are a **design-level caveat**, not a feature-by-feature
  afterthought: five of five unique features predict past absolute returns,
  and the reciprocity survivors have the largest lag association. Stage 2's
  liquidity controls and Stage 5's final classification must address this
  directly.
- v2.0.2's single-survivor narrative is superseded: the corrected metric gives
  two survivors, but they are the same construct predicting two outcomes, not
  independent confirmations.
