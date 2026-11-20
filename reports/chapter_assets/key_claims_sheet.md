# Key-claims sheet — v2.1.0 (reciprocity correction)

**Purpose.** A one-stop reference for the claims the corrected analysis
supports, the exact numbers, and the claims it does **not** support. It is a
writing aid, not thesis prose. Replaces the v2.0.2 sheet; the v2.0.2 numbers
remain available for audit in `outputs/tables/superseded_v2_0_2/` and in
`reports/reciprocity_correction.md`.

**Release.** `v2.1.0-reciprocity-correction`. Corrected results are primary.

**Canonical sources**

- `outputs/tables/v2_final_headline_set.csv` — final 10-row classification.
- `outputs/tables/hypothesis_grid_results_v2.csv` — estimates, DK/FM p, BH q,
  MDE, effective N.
- `outputs/tables/se_concordance.csv` — DK/DC-v2/FM/WB/RW concordance.
- `outputs/tables/quantile_tail_summary.csv` — quantile tails.
- `outputs/tables/event_study_upgraded.csv` — event-study inference.
- `outputs/tables/event_study_clustered_inference.csv` — date-clustered
  descriptive inference.
- `outputs/tables/robustness_headline_survival.csv` — robustness variants.
- `outputs/tables/heterogeneity_subgroups.csv` — subgroup grid.
- `outputs/tables/economic_magnitude.csv` — cost floor.
- `reports/reciprocity_correction.md` — defect, code fix, old-vs-new record.
- `reports/chapter_assets/print_tables/` — print projections; the source CSVs
  remain authoritative.

**Rules**

1. Quote the canonical classification; do not re-derive it from a p-value.
2. Name the gate every time: DK, DC-v2, FM, WB, BH, or RW.
3. A BH pass is not a v2 headline; RW q = .10 is the family-wise gate.
4. `survives_liquidity` and `survives_egarch` are declared checks, not new tests.
5. Do not describe an association as causal, a fragile null as a finding, or a
   1-SD effect as tradable.
6. Do not quote v2.0.2 numbers as current. If an old number is shown, label it
   `SUPERSEDED v2.0.2`.

---

## 1. The 10-test grid at a glance

`bp` = basis points per 1 TRAIN-fold standard deviation of the feature. DK is
the primary standard error (Bartlett, bandwidth 5). BH q is the v1 gate over the
family of 10; RW p is the v2 Romano–Wolf family-wise gate (B = 999). WB is the
entity-clustered wild bootstrap (B = 999). FM is Fama–MacBeth.

| H | construct → outcome | β (bp/SD) | DK p | BH q | RW p | WB p | FM p | final classification |
|---|---|---:|---:|---:|---:|---:|---:|---|
| H1 | self-loop ratio → \|return\| | −1.557 | .4306 | .6094 | .918 | .257 | .3404 | `NULL_POWERED` |
| H2 | IF anomaly score → \|return\| | −1.494 | .5945 | .6605 | .918 | .528 | .4976 | `NULL_POWERED` |
| H3 | IF anomaly score → return | +0.178 | .9531 | .9531 | .959 | .960 | .1410 | `NULL_POWERED` |
| H4 | buyer HHI → return | **+7.510** | **.0275** | **.0689** | .152 | **.002** | **.0082** | `EXPLORATORY_POST_HOC` |
| H5 | buyer HHI → \|return\| | −1.856 | .4875 | .6094 | .918 | .357 | .6873 | `NULL_POWERED` |
| H6 | reciprocity → return | **−22.948** | **.0048** | **.0239** | **.031** | **.001** | **.0028** | `HEADLINE_ROBUST` |
| H7 | EoD concentration → \|return\| | **+3.952** | **.0274** | **.0689** | .152 | **.022** | **.0094** | `NULL_FRAGILE` |
| H8 | EoD concentration → return | **−4.471** | **.0459** | **.0918** | .199 | **.095** | **.0587** | `NULL_FRAGILE` |
| H9 | self-loop ratio → return | +1.817 | .4587 | .6094 | .918 | .100 | .3875 | `NULL_POWERED` |
| H10 | reciprocity → \|return\| | **+20.642** | **.0014** | **.0136** | **.012** | **.004** | .4901 | `HEADLINE_MODERATE` |

**Reading the table**

- Five rows pass BH (H4, H6, H7, H8, H10); **two** survive RW q = .10: H6 and
  H10. This is the main change from v2.0.2, where only H10 survived RW.
- H4's BH pass is opposite-signed to its pre-declaration, so it is
  `EXPLORATORY_POST_HOC`, not confirmation.
- H7/H8 pass BH but fail RW; they are `NULL_FRAGILE`, not headlines.
- H6 now passes all four estimators; its SE concordance is `STRONG` (4/4).
- H10 passes DK, DC-v2 and WB but not FM; its SE concordance is `MODERATE`
  (3/4), so the composition rule caps it at `HEADLINE_MODERATE`.
- H9's WB p is exactly `.100`; the strict `< .10` counting rule does not count
  it.
- H2/H3 remain null. Their estimates moved slightly because the Isolation
  Forest score was rebuilt from the corrected feature set.

---

## 2. H6 — the robust headline

**What is supported**

- Construct: reciprocity → signed next-session return.
- Effect: **−22.948 bp per 1 TRAIN-SD** of reciprocity (raw β
  `−0.002294764231134801`).
- DK p **.0048**; DC-v2 p **6.71e-6**; WB p **.001**; FM p **.0028**; RW p
  **.031**; BH q **.0239**.
- SE concordance **STRONG** (DK, DC-v2, FM, WB all significant at p < .10).
- Liquidity-controlled β **−23.182 bp**, p **.0043**, a **−1.02%** change from
  the base estimate. The three controls are Amihud, Roll and Corwin–Schultz;
  they are proxies, not quoted spreads.
- EGARCH primary outcome: p **.0016**, sign matches the base. The model is the
  declared symmetric EGARCH(1,1); it is not an asymmetric extension.
- Quantile tails: τ = .10 **−21.865 bp** (p `1.63e-45`); τ = .25 **−15.103**;
  τ = .50 **−9.324**; τ = .75 **−8.311**; τ = .90 **−3.628** (p **.0299**);
  τ90/τ10 ratio **0.166**; `BOTH_TAILS (INCREASING)`.
- Robustness: sign-stable in **12/12** leave-one-symbol-out refits; BH-pass at
  t+3 (−40.372 bp, p .0167) and t+5 (−55.730 bp, p .0126); survives drop-bubble
  (−31.979 bp, p .0045).
- Pre-declared direction is **ambiguous**, so the negative sign is not an
  opposite-sign failure.

**What must be disclosed**

- H6 fails the t+2 horizon BH gate (0/5 headlines pass), and the external tier
  is not significant (−13.298 bp, raw p .1758, 0/5 BH).
- H6 and H10 are the **same feature** predicting two outcomes. They are not
  independent evidence.
- Reciprocity predicts past \|return\| at **+44.780 bp** (p **8.71e-10**), more
  than twice its forward association. Part of H6 is a volatility-persistence
  channel, not a clean forward-looking signal.
- Corrected reciprocity correlates **.833** with `n_edges` and **.765** with
  `n_nodes`. The design controls log volume, market return, symbol and date, not
  network size. Do not read H6 as a network-size-free reciprocity effect.
- H6 does **not** survive every later robustness variant. `HEADLINE_ROBUST` is
  the output of the pre-declared Stage-1/2/3 composition rule, not a universal
  robustness claim.

**Do not write**

- “H6 is causal.”
- “Reciprocity predicts returns market-wide.”
- “H6 proves a reversal strategy.”
- “H6 and H10 independently confirm the same effect.”

---

## 3. H10 — the moderate headline

**What is supported**

- Construct: reciprocity → absolute next-session return.
- Effect: **+20.642 bp per 1 TRAIN-SD** of reciprocity (raw β
  `0.0020641998360399066`).
- DK p **.0014**; DC-v2 p **1.00e-5**; WB p **.004**; FM p **.4901**; RW p
  **.012**; BH q **.0136**.
- SE concordance **MODERATE** (DK, DC-v2, WB significant at p < .10; FM not).
- Liquidity-controlled β **+19.658 bp**, p **.0021**, a **−4.77%** change from
  the base estimate.
- EGARCH primary outcome: p **.0497**, sign matches the base.
- Quantile tails: τ = .10 **+4.838 bp** (p `2.00e-6`); τ = .25 **+5.935**;
  τ = .50 **+8.929**; τ = .75 **+15.435**; τ = .90 **+34.643** (p
  `8.58e-118`); τ90/τ10 ratio **7.161**; `BOTH_TAILS (INCREASING)`.
- Drop-bubble: **+23.467 bp**, p **.0096**, BH pass. Leave-one-symbol-out:
  sign-stable 12/12.
- Pre-declared subgroup grid: size-small **+26.791 bp** (p_bonf **.0473**);
  turnover bottom-7 **+22.715 bp** (p_bonf **.0183**). These are descriptive
  cells, not new headlines; the interactions are null (size p .319; turnover
  p .152).
- Cost floor: **20.642 bp** is **1.45–2.42× below** the 30–50 bp round-trip
  explicit-cost floor; not standalone tradable at 1 SD.

**What must be disclosed**

- FM p **.4901** and `MODERATE` concordance mean this is not `HEADLINE_ROBUST`.
- The t+2, t+3 and t+5 variants all fail BH (0/5 at each horizon); the effect
  remains positive but is not horizon-robust.
- The external tier is **+16.437 bp**, raw p **.0539**, **0/5 BH pass**. The
  point estimate attenuates only ~20%, but it is not significant after the
  family correction.
- The DC13 placebo-outcome check found a past-\|return\| association of
  **+44.780 bp**, larger than the forward **+20.642 bp**; part of H10 is a
  persistence/volatility channel.
- The 12-symbol panel is the per-fold top-10 universe, not the 530-symbol
  market.

**Do not write**

- “H10 is robust / strong / confirmed.”
- “Reciprocity predicts returns market-wide.”
- “H10 is a tradable signal.”
- “H10 is causal.”
- “The subgroup survivors confirm a size or liquidity story.”

---

## 4. H4 — exploratory, opposite sign

- Construct: buyer HHI → next-session return.
- Pre-declared direction: **negative**. Estimated: **+7.510 bp/SD**, the
  opposite sign.
- DK p **.0275**; BH q **.0689**; RW p **.152**; WB p **.002**; FM p **.0082**;
  DC-v2 p **.0053**.
- Survives the three liquidity controls (β **+7.357 bp**, p **.0306**, −2.04%
  change) and the EGARCH primary outcome (p **.0544**, sign match).
- Quantile tails: τ = .10 **+2.121 bp**; τ = .90 **+9.610 bp**; ratio **4.532**;
  `BOTH_TAILS (INCREASING)`.
- Cost floor: **7.510 bp** is **3.99–6.66× below** the floor; opposite-sign
  post hoc; not standalone tradable.
- Drop-bubble: **+10.489 bp**, p **.0094**, BH pass. External tier: **+0.288
  bp**, p **.9416**, 0/5 BH.

**Classification:** `EXPLORATORY_POST_HOC`. It is a post-hoc, opposite-sign
association. It may motivate future work; it does not confirm the pre-declared
hypothesis.

**Do not write:** “buyer HHI negatively predicts returns” (the estimate is
positive) or “H4 confirms the concentration story.”

---

## 5. H7 and H8 — fragile, not headlines

### H7 — end-of-day concentration → \|return\|

- β **+3.952 bp/SD**; DK p **.0274**; BH q **.0689**; RW p **.152**; WB p
  **.022**; FM p **.0094**.
- Specification curve: **144** executed specifications / **72** unique design
  betas. For `abs_ret`: **72/72 positive**, median **+3.952 bp**, CI excludes
  0 in **.583** of specs, p < .05 in **.542**. For `ret`: **66/72 negative**,
  median **−4.289 bp**. Full-sample CI-exclusion **.958** vs bubble **.292**;
  the 1% EoD cutoff collapses the CI-exclusion share to **0**. Overall curve
  median **+1.235 bp**; **39.6%** of all specs have a CI excluding zero.
- Trade-size: EoD large-ticket **+4.519 bp**, p **.0356**, the only sign-aware
  pass; the small bucket is **0.35%** of volume. This does not rescue H7 from
  the RW/specification-curve failures.
- Quantile tails: `NONE (HUMP)`; τ = .10 **+0.706 bp** (p .1169); τ = .50
  **+2.202** (p .0024); τ = .90 **+1.212** (p .0623).
- `NULL_FRAGILE`. The supported statement is a volatility/absolute-return
  association, not a directional-return effect.

### H8 — end-of-day concentration → return

- β **−4.471 bp/SD**; DK p **.0459**; BH q **.0918**; RW p **.199**; WB p
  **.095**; FM p **.0587**.
- Registered robustness failures: top-1% cutoff **−0.601 bp** (p **.7634**);
  normal era **−4.442 bp** (p **.1703**). MDE₈₀ **6.269 bp**;
  \|β\| / (MDE₈₀/2) = **1.426** → `NULL_UNDERPOWERED` in the MDE table, but the
  final label is `NULL_FRAGILE` because the registered failures are the
  specific demotion.
- Trade-size: medium-ticket **−5.266 bp** (p **.0056**); not a large-ticket
  effect.
- `NULL_FRAGILE`.

**Do not write:** “H7/H8 are headline findings,” or “H8 is a precise zero”
(it is underpowered as well as fragile).

---

## 6. The five powered nulls

| H | construct → outcome | β (bp/SD) | DK p | MDE₈₀ (bp) | what is supported |
|---|---|---:|---:|---:|---|
| H1 | self-loop ratio → \|return\| | −1.557 | .4306 | 5.530 | no detectable association at the declared gates |
| H2 | IF anomaly score → \|return\| | −1.494 | .5945 | 7.859 | anomaly-score null; placebo share .805 |
| H3 | IF anomaly score → return | +0.178 | .9531 | 8.473 | anomaly-score null; placebo share .540 |
| H5 | buyer HHI → \|return\| | −1.856 | .4875 | 7.485 | no detectable association |
| H9 | self-loop ratio → return | +1.817 | .4587 | 6.868 | no detectable association; WB p .100 exactly |

All are `NULL_POWERED`. “Powered null” does **not** mean “proven zero”; it means
the design could detect an effect of the stated MDE and did not. The IF
anomaly-score channel (H2/H3) is the clearest negative result: placebo shares
`.805` and `.540` are close to random.

**Do not write:** “there is no effect” without the MDE caveat; “the anomaly
score is irrelevant” as a universal claim; “self-loop volume is wash trading.”

---

## 7. Event study — no economically meaningful mean effect

- Sample: **666 events** on **392 dates**; **435** events (**65.3%**) share a
  date with another event (161 shared dates; max 9 events on one date), so
  event-level p-values are upper bounds.
- Reconstruction gate: max \|reconstructed CAR − stored CAR\| = **0.0**; no
  re-estimation.
- Mean CAR **+19.326 bp**; SD **594.54 bp**; median **+28.14 bp**; 53.0%
  positive.
- Mean CAR t **0.839** (p **.4018**); BMP t **1.339** (p **.1809**); BMP z
  **1.819** (p **.0689**); Corrado rank z **3.481** (p **.000499**).
- Date-clustered: mean CAR t **1.186** (p **.2363**); rank z **2.986** (p
  **.0030**); market-adjusted rank z **3.249** (p **.0013**).
- The uniform market-adjusted mean **−75.21 bp** (p **.000499**) is a
  pre-window-alpha artefact, not an event effect. The market-model subset
  (650 events) has mean **+25.40 bp**; the 16 illiquid events use the
  market-adjusted method.
- The 16-event illiquid appendix (mean **−227.39 bp**, p **.0033**) is
  appendix-only and not a headline.

**Supported statement:** the mean abnormal return is not distinguishable from
zero; only the rank distribution shifts, and that shift is weaker under date
clustering.

**Do not write:** “the event study shows positive abnormal returns” or “the
market-adjusted CAR is negative, so the event is harmful.”

---

## 8. Economic magnitude — below the cost floor

| H | effect at 1 SD (bp) | multiple below 30 bp | multiple below 50 bp | standalone tradable? |
|---|---:|---:|---:|---|
| H7 | 3.952 | 7.59× | 12.65× | no |
| H10 | 20.642 | 1.45× | 2.42× | no |
| H4 | 7.510 | 3.99× | 6.66× | no; opposite-sign post hoc |

The floor is **30–50 bp round-trip explicit cost** and excludes brokerage,
bid–ask spread and CNS carry. True all-in costs are higher, so the comparison
is conservative in the direction of making the effects look larger than they
are.

**Do not write:** “H10 is profitable,” “the strategy earns 20.6 bp per trade,”
or “transaction costs are covered.”

---

## 9. Design and sample claims

- Corpus: **57,927,926** raw floorsheet rows → **57,892,630** after
  deduplication (**35,296** drops); **1,167** day files; **530** symbols;
  **938/940** calendar sessions. Gaps: 2021-09-01 and 2023-11-27. **752**
  duplicate keys (**506** exact, **246** signature-conflict); **19**
  missing-broker pairs; **114,167** low-activity symbol-days (<100 trades).
- Headline panel: **12 symbols**, **723 dates**, **7,116** estimable rows;
  **7,126** OOS rows minus **10** missing outcome/feature rows; effective N
  **6,383** = 7,116 − 11 − 722. FM cross-sections **712–714**.
- Validation: **4** anchored expanding folds; **6-session** purge; **938**
  scoring sessions; **666** anomaly events (**9.3%** of scored rows). Warm-up
  chunk is never tested; winsorisation, standardisation, Isolation Forest and
  the q90 threshold are TRAIN-only.
- 2023-02-16: **35,043** rows share one contract ID; ordering-dependent
  features exclude the day; level aggregates keep it.
- Broker-ID defect: **275,590** dotted-ID rows on **15** days; **37/7,116**
  OOS rows (**0.52%**) affected; leave-defect-rows-out signs unchanged, H8 raw
  p **.0563**.

**Do not write:** “the sample is the whole market” (it is the top-10/top-12
tier); “the panel is balanced” (it is not); “the folds are random” (they are
anchored and purged).

---

## 10. External replication and locality

- External tier = ranks **11–15** of the same TRAIN turnover ranking:
  **3,414** OOS rows, **3,409** estimable, **256** events (**7.5%**).
- **0/5** BH pass. H10 **+16.437 bp** (raw p **.0539**, BH q **.539**); H7
  **+2.138** (p **.3532**); H8 **−0.701** (p **.8106**); H4 **+0.288** (p
  **.9416**); H6 **−13.298** (p **.1758**).
- Point estimates attenuate for H4 (3.8% of base), H8 (16%), H7 (54%) and H6
  (58%); H10 attenuates only to 80% of base but remains non-significant. The
  tier-locality statement rests on the 0/5 BH result, not on a uniform
  magnitude ratio.
- Headline-panel turnover split: bottom-7 H10 **+22.715 bp** (p_bonf
  **.0183**); top-3 **+10.315** (p_bonf **1.000**); interaction **−10.686**
  (p **.1524**). The bottom-7 cell survives Bonferroni; the interaction does
  not, so the tier-locality pattern is directional, not statistically
  established.

**Do not write:** “the effect is market-wide” or “the strategy scales to other
stocks.”

---

## 11. Do-not-claim list

| do not claim | use instead |
|---|---|
| H6 or H10 is universally robust | H6 `HEADLINE_ROBUST` on the declared Stage-1/2/3 gates but mixed in later variants; H10 `HEADLINE_MODERATE`, FM p .4901 |
| H6 and H10 are independent confirmations | same feature, two outcomes: signed return and absolute return |
| H4 confirms the pre-declared negative relation | `EXPLORATORY_POST_HOC`; estimate is positive, opposite sign |
| H7/H8 are headline findings | `NULL_FRAGILE`; BH pass but RW fail |
| The nulls prove no effect | `NULL_POWERED` with the reported MDE; not a precise zero |
| Self-loop volume is wash trading/manipulation | it is a self-loop volume share; no manipulation ground truth |
| The result is market-wide | external ranks 11–15: 0/5 BH pass |
| The effect is tradable alpha | all 1-SD effects are below the 30–50 bp cost floor |
| The event study shows positive abnormal returns | mean CAR p .4018; only the rank distribution shifts |
| The IF anomaly score predicts returns | H2/H3 null; placebo shares .805/.540 |
| Any estimate is causal | predictive/associational only; no instrument or exogenous shock |
| Reciprocity is network-size-free | corrected feature correlates .833 with `n_edges` and .765 with `n_nodes` |
| The 39 references are a literature review | metadata-verified candidates; content review is `NOT_REVIEWED` |
| F7 is a histogram of 1,000 draws | frozen permutation quantile summary; draw-level values were not persisted |
| F10 is a fresh network recomputation | composite of two frozen network renders |
| v2.0.2 numbers are current | v2.0.2 is a superseded record in `outputs/tables/superseded_v2_0_2/` |

---

## 12. Where to find the exact value

| need | file |
|---|---|
| final classification and RW/WB p | `outputs/tables/v2_final_headline_set.csv` |
| DK/FM p, BH q, MDE, effective N | `outputs/tables/hypothesis_grid_results_v2.csv` |
| four-estimator concordance | `outputs/tables/se_concordance.csv` |
| quantile tails | `outputs/tables/quantile_tail_summary.csv` |
| event study | `outputs/tables/event_study_upgraded.csv` |
| date-clustered event inference | `outputs/tables/event_study_clustered_inference.csv` |
| robustness variants | `outputs/tables/robustness_headline_survival.csv` |
| external tier | `outputs/tables/robustness_top5_external_grid.csv` |
| subgroups/tier locality | `outputs/tables/heterogeneity_subgroups.csv` |
| trade size | `outputs/tables/trade_size_heterogeneity.csv` |
| specification curve | `outputs/tables/specification_curve_h7_summary.csv` |
| cost floor | `outputs/tables/economic_magnitude.csv` |
| placebo outcome | `outputs/tables/placebo_outcome_test.csv` |
| correction record | `reports/reciprocity_correction.md` |
| superseded v2.0.2 tables | `outputs/tables/superseded_v2_0_2/` |
| corpus/sample counts | `outputs/tables/corpus_daily_summary.csv`; `hypothesis_grid_results_v2.csv` |
| print-ready versions | `reports/chapter_assets/print_tables/` |
