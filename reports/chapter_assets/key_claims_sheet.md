# Key-claims sheet — v2.0.2 pre-write

**Purpose.** A one-stop reference for the claims the frozen analysis supports,
the exact numbers, and the claims it does **not** support. It is a writing aid,
not thesis prose.

**Canonical sources**

- `outputs/tables/v2_final_headline_set.csv` — final 10-row classification.
- `outputs/tables/hypothesis_grid_results_v2.csv` — estimates, DK/FM p, BH q,
  MDE, effective N.
- `outputs/tables/se_concordance.csv` — DK/DC-v2/FM/WB/RW concordance.
- `outputs/tables/quantile_tail_summary.csv` — quantile tails.
- `outputs/tables/event_study_upgraded.csv` — event-study inference.
- `outputs/tables/robustness_headline_survival.csv` — robustness variants.
- `outputs/tables/heterogeneity_subgroups.csv` — subgroup grid.
- `outputs/tables/economic_magnitude.csv` — cost floor.
- `reports/chapter_assets/print_tables/` — print projections; the source CSVs
  remain authoritative.

**Rules**

1. Quote the canonical classification; do not re-derive it from a p-value.
2. Name the gate every time: DK, DC-v2, FM, WB, BH, or RW.
3. A BH pass is not a v2 headline; RW q = .10 is the family-wise gate.
4. `survives_liquidity` and `survives_egarch` are frozen flags, not new tests.
5. Do not describe an association as causal, a fragile null as a finding, or a
   1-SD effect as tradable.

---

## 1. The 10-test grid at a glance

`bp` = basis points per 1 TRAIN-fold standard deviation of the feature. DK is
the primary standard error (Bartlett, bandwidth 5). BH q is the v1 gate over the
family of 10; RW p is the v2 Romano–Wolf family-wise gate (B = 999). WB is the
entity-clustered wild bootstrap (B = 999). FM is Fama–MacBeth.

| H | construct → outcome | β (bp/SD) | DK p | BH q | RW p | WB p | FM p | final classification |
|---|---|---:|---:|---:|---:|---:|---:|---|
| H1 | self-loop ratio → \|return\| | −1.557 | .4306 | .6094 | .915 | .257 | .3404 | `NULL_POWERED` |
| H2 | IF anomaly score → \|return\| | −1.491 | .5753 | .6392 | .915 | .541 | .5304 | `NULL_POWERED` |
| H3 | IF anomaly score → return | +0.957 | .7501 | .7501 | .915 | .794 | .3243 | `NULL_POWERED` |
| H4 | buyer HHI → return | **+7.510** | **.0275** | **.0689** | .159 | **.002** | **.0082** | `EXPLORATORY_POST_HOC` |
| H5 | buyer HHI → \|return\| | −1.856 | .4875 | .6094 | .915 | .357 | .6873 | `NULL_POWERED` |
| H6 | reciprocity → return | **−10.939** | **.0197** | **.0689** | .120 | **.002** | .5403 | `NULL_FRAGILE` |
| H7 | EoD concentration → \|return\| | **+3.952** | **.0274** | **.0689** | .159 | **.022** | **.0094** | `NULL_FRAGILE` |
| H8 | EoD concentration → return | **−4.471** | **.0459** | **.0918** | .203 | **.095** | **.0587** | `NULL_FRAGILE` |
| H9 | self-loop ratio → return | +1.817 | .4587 | .6094 | .915 | .100 | .3875 | `NULL_POWERED` |
| H10 | reciprocity → \|return\| | **+9.492** | **.0138** | **.0689** | **.081** | **.009** | .2896 | `HEADLINE_MODERATE` |

**Reading the table**

- Five rows pass BH (H4, H6, H7, H8, H10); only H10 survives RW q = .10.
- H4's BH pass is opposite-signed to its pre-declaration, so it is
  `EXPLORATORY_POST_HOC`, not confirmation.
- H6/H7/H8 pass BH but fail RW; they are `NULL_FRAGILE`, not headlines.
- H10 passes DK and RW but not FM; its SE concordance is `MODERATE` (3/4:
  DK, DC-v2, WB), not `STRONG`.
- H9's WB p is exactly `.100`; the strict `< .10` counting rule does not count
  it.

---

## 2. H10 — the only headline

**What is supported**

- Construct: reciprocity → absolute next-session return.
- Effect: **+9.492 bp per 1 TRAIN-SD** of reciprocity (raw β
  `0.0009492266420621042`).
- DK p **.0138**; DC-v2 p **.00282**; WB p **.009**; RW p **.081**; FM p
  **.2896**.
- SE concordance **MODERATE** (DK, DC-v2, WB significant at p < .10; FM not).
- Liquidity-controlled β **+9.586 bp**, p **.0117**, a **+0.98%** change from
  the base estimate. The three controls are Amihud, Roll and Corwin–Schultz;
  they are proxies, not quoted spreads.
- EGARCH primary outcome: p **.0383**, sign matches the base. The model is the
  declared symmetric EGARCH(1,1); it is not an asymmetric extension.
- Quantile tails: τ = .10 **+3.083 bp** (p `1.38e-4`); τ = .25 **+2.842**;
  τ = .50 **+4.891**; τ = .75 **+7.530**; τ = .90 **+18.696** (p
  `1.55e-70`); τ90/τ10 ratio **6.064**; `BOTH_TAILS (INCREASING)`.
- External replication tier (ranks 11–15 of the same TRAIN turnover ranking):
  **+5.399 bp**, p **.2315**, n **3,409**, **0/5 BH pass**. The effect shrinks
  and does not replicate.
- Headline-panel turnover split: bottom-7 **+10.344 bp** (p_bonf **.1434**);
  top-3 **+2.698 bp** (p_bonf **1.000**); interaction **−8.973 bp** (p
  **.1383**). No Bonferroni survivor.
- Cost floor: **9.492 bp** is **3.16–5.27× below** the 30–50 bp round-trip
  explicit-cost floor; not standalone tradable at 1 SD.

**What must be disclosed**

- FM p `.2896` and `MODERATE` concordance mean this is not `HEADLINE_ROBUST`.
- RW p `.081` is the sole q = .10 survivor, but it is marginal.
- The DC13 placebo-outcome check found a past-\|return\| association of
  **+19.69 bp**, larger than the forward **+9.49 bp**; part of H10 is a
  persistence/volatility channel, not a clean predictive effect.
- The external tier fails; the result is local to the most-traded tier and the
  12-symbol headline panel.
- The 12-symbol panel is the per-fold top-10 universe, not the 530-symbol
  market.

**Do not write**

- “H10 is robust / strong / confirmed.”
- “Reciprocity predicts returns market-wide.”
- “H10 is a tradable signal.”
- “H10 is causal.”

---

## 3. H4 — exploratory, opposite sign

- Construct: buyer HHI → next-session return.
- Pre-declared direction: **negative**. Estimated: **+7.510 bp/SD**, the
  opposite sign.
- DK p **.0275**; BH q **.0689**; RW p **.159**; WB p **.002**; FM p **.0082**.
- Survives the three liquidity controls (β **+7.357 bp**, p **.0306**, −2.04%
  change) and the EGARCH primary outcome (sign match).
- Quantile tails: τ = .10 **+2.121 bp**; τ = .90 **+9.610 bp**; ratio **4.532**;
  `BOTH_TAILS (INCREASING)`.
- Cost floor: **7.510 bp** is **3.99–6.66× below** the floor; opposite-sign
  post hoc; not standalone tradable.

**Classification:** `EXPLORATORY_POST_HOC`. It is a post-hoc, opposite-sign
association. It may motivate future work; it does not confirm the pre-declared
hypothesis.

**Do not write:** “buyer HHI negatively predicts returns” (the estimate is
positive) or “H4 confirms the concentration story.”

---

## 4. H6, H7, H8 — fragile, not headlines

### H6 — reciprocity → return

- β **−10.939 bp/SD**; DK p **.0197**; BH q **.0689**; RW p **.120**; WB p
  **.002**; FM p **.5403**.
- Quantile: τ = .10 **−12.988 bp**; τ = .90 **−0.466 bp**; tail label
  `LOWER_TAIL (INCREASING)`; the effect is concentrated in the lower tail but
  the FM and RW gates fail.
- `NULL_FRAGILE`.

### H7 — end-of-day concentration → \|return\|

- β **+3.952 bp/SD**; DK p **.0274**; BH q **.0689**; RW p **.159**; WB p
  **.022**; FM p **.0094**.
- Specification curve: **144** executed specifications / **72** unique design
  betas. For `abs_ret`: **72/72 positive**, median **+3.952 bp**, CI excludes
  0 in **.583** of specs, p < .05 in **.542**. For `ret`: **66/72 negative**,
  median **−4.289 bp**. Full-sample CI-exclusion **.958** vs bubble **.292**;
  the 1% EoD cutoff collapses the CI-exclusion share to **0**.
- Trade-size: EoD large-ticket **+4.519 bp**, p **.0356**, the only
  sign-aware pass; the small bucket is **0.35%** of volume. This does not
  rescue H7 from the RW/specification-curve failures.
- `NULL_FRAGILE`. The supported statement is a volatility/absolute-return
  association, not a directional-return effect.

### H8 — end-of-day concentration → return

- β **−4.471 bp/SD**; DK p **.0459**; BH q **.0918**; RW p **.203**; WB p
  **.095**; FM p **.0587**.
- Registered robustness failures: top-1% cutoff **−0.60 bp** (p **.7634**);
  normal era **−4.44 bp** (p **.1703**). MDE₈₀ **6.269 bp**; MDE₈₀ / \|β\|
  **1.426** → `NULL_UNDERPOWERED` in the MDE table, but the final label is
  `NULL_FRAGILE` because the registered failures are the specific demotion.
- Trade-size: medium-ticket **−5.266 bp** (p **.0056**); not a large-ticket
  effect.
- `NULL_FRAGILE`.

**Do not write:** “H6/H7/H8 are headline findings,” or “H8 is a precise zero”
(it is underpowered as well as fragile).

---

## 5. The five powered nulls

| H | construct → outcome | β (bp/SD) | DK p | MDE₈₀ (bp) | what is supported |
|---|---|---:|---:|---:|---|
| H1 | self-loop ratio → \|return\| | −1.557 | .4306 | 5.530 | no detectable association at the declared gates |
| H2 | IF anomaly score → \|return\| | −1.491 | .5753 | 7.452 | anomaly-score null; placebo share .800 |
| H3 | IF anomaly score → return | +0.957 | .7501 | 8.414 | anomaly-score null; placebo share .640 |
| H5 | buyer HHI → \|return\| | −1.856 | .4875 | 7.485 | no detectable association |
| H9 | self-loop ratio → return | +1.817 | .4587 | 6.868 | no detectable association; WB p .100 exactly |

All are `NULL_POWERED`. “Powered null” does **not** mean “proven zero”; it means
the design could detect an effect of the stated MDE and did not. The IF
anomaly-score channel (H2/H3) is the clearest negative result: placebo shares
`.800` and `.640` are close to random.

**Do not write:** “there is no effect” without the MDE caveat; “the anomaly
score is irrelevant” as a universal claim; “self-loop volume is wash trading.”

---

## 6. Event study — no economically meaningful mean effect

- Sample: **686 events** on **393 dates**; **468** events (**68.2%**) share a
  date with another event, so event-level p-values are upper bounds.
- Reconstruction gate: max \|reconstructed CAR − stored CAR\| = **0.0**; no
  re-estimation.
- Mean CAR **+12.861 bp**; SD **591.17 bp**; median **+34.02 bp**; 53.35%
  positive.
- Mean CAR t **0.570** (p **.5690**); BMP t **1.175** (p **.2404**); BMP z
  **1.580** (p **.1141**); Corrado rank z **3.158** (p **.00159**).
- Date-clustered: mean CAR t **0.717** (p **.4740**); rank z **2.522** (p
  **.0120**).
- The uniform market-adjusted mean **−73.41 bp** (p **.00051**) is a
  pre-window-alpha artefact (mean alpha −0.0873%/day; corr(alpha,
  CAR−CAR_ma) = **−.751**), not an event effect.
- The 16-event illiquid appendix (mean **−244.77 bp**) is appendix-only and not
  a headline.

**Supported statement:** the mean abnormal return is not distinguishable from
zero; only the rank distribution shifts, and that shift is weaker under date
clustering.

**Do not write:** “the event study shows positive abnormal returns” or “the
market-adjusted CAR is negative, so the event is harmful.”

---

## 7. Economic magnitude — below the cost floor

| H | effect at 1 SD (bp) | multiple below 30 bp | multiple below 50 bp | standalone tradable? |
|---|---:|---:|---:|---|
| H7 | 3.952 | 7.59× | 12.65× | no |
| H10 | 9.492 | 3.16× | 5.27× | no |
| H4 | 7.510 | 3.99× | 6.66× | no; opposite-sign post hoc |

The floor is **30–50 bp round-trip explicit cost** and excludes brokerage,
bid–ask spread and CNS carry. True all-in costs are higher, so the comparison
is conservative in the direction of making the effects look larger than they
are.

**Do not write:** “H10 is profitable,” “the strategy earns 9.5 bp per trade,” or
“transaction costs are covered.”

---

## 8. Design and sample claims

- Corpus: **57,927,926** raw floorsheet rows → **57,892,630** after
  deduplication (**35,296** drops); **1,167** day files; **530** symbols;
  **938/940** calendar sessions. Gaps: 2021-09-01 and 2023-11-27. **752**
  duplicate keys (**506** exact, **246** signature-conflict); **19**
  missing-broker pairs; **114,167** low-activity symbol-days (<100 trades).
- Headline panel: **12 symbols**, **723 dates**, **7,116** estimable rows;
  **7,126** OOS rows minus **10** missing outcome/feature rows; effective N
  **6,383** = 7,116 − 11 − 722. FM cross-sections **712–714**.
- Validation: **4** anchored expanding folds; **6-session** purge; **938**
  scoring sessions; **686** anomaly events (**9.6%** of scored rows). Warm-up
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

## 9. External replication and locality

- External tier = ranks **11–15** of the same TRAIN turnover ranking:
  **3,414** OOS rows, **3,409** estimable, **264** events.
- **0/5** BH pass; raw p ≥ **.23**. H10 **+5.399 bp** (p **.2315**); H7
  **+2.138** (p **.3532**); H8 **−0.701** (p **.8106**); H4 **+0.288** (p
  **.9416**); H6 **−3.633** (p **.4461**).
- Magnitudes shrink **2–4×** relative to the headline tier.
- Headline-panel turnover split: bottom-7 H10 **+10.344 bp** (p_bonf
  **.1434**); top-3 **+2.698** (p_bonf **1.000**); interaction **−8.973**
  (p **.1383**). No Bonferroni survivor; the tier-locality pattern is
  directional, not statistically established.

**Do not write:** “the effect is market-wide” or “the strategy scales to other
stocks.”

---

## 10. Do-not-claim list

| do not claim | use instead |
|---|---|
| H10 is robust/strong/confirmed | `HEADLINE_MODERATE`; DK/RW survive, FM p .2896, SE `MODERATE` |
| H4 confirms the pre-declared negative relation | `EXPLORATORY_POST_HOC`; estimate is positive, opposite sign |
| H6/H7/H8 are headline findings | `NULL_FRAGILE`; BH pass but RW fail |
| The nulls prove no effect | `NULL_POWERED` with the reported MDE; not a precise zero |
| Self-loop volume is wash trading/manipulation | it is a self-loop volume share; no manipulation ground truth |
| The result is market-wide | external ranks 11–15: 0/5 BH pass, magnitudes shrink |
| The effect is tradable alpha | all 1-SD effects are below the 30–50 bp cost floor |
| The event study shows positive abnormal returns | mean CAR p .569; only the rank distribution shifts |
| The IF anomaly score predicts returns | H2/H3 null; placebo shares .800/.640 |
| Any estimate is causal | predictive/associational only; no instrument or exogenous shock |
| The 39 references are a literature review | metadata-verified candidates; content review is `NOT_REVIEWED` |
| F7 is a histogram of 1,000 draws | frozen permutation quantile summary; draw-level values were not persisted |
| F10 is a fresh network recomputation | composite of two frozen network renders |

---

## 11. Where to find the exact value

| need | file |
|---|---|
| final classification and RW/WB p | `outputs/tables/v2_final_headline_set.csv` |
| DK/FM p, BH q, MDE, effective N | `outputs/tables/hypothesis_grid_results_v2.csv` |
| four-estimator concordance | `outputs/tables/se_concordance.csv` |
| quantile tails | `outputs/tables/quantile_tail_summary.csv` |
| event study | `outputs/tables/event_study_upgraded.csv` |
| robustness variants | `outputs/tables/robustness_headline_survival.csv` |
| external tier | `outputs/tables/robustness_top5_external_grid.csv` |
| subgroups/tier locality | `outputs/tables/heterogeneity_subgroups.csv` |
| trade size | `outputs/tables/trade_size_heterogeneity.csv` |
| specification curve | `outputs/tables/specification_curve_h7_summary.csv` |
| cost floor | `outputs/tables/economic_magnitude.csv` |
| corpus/sample counts | `outputs/tables/corpus_daily_summary.csv`; `hypothesis_grid_results_v2.csv` |
| print-ready versions | `reports/chapter_assets/print_tables/` |
