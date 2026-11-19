# Viva preparation — H6/H10, the nulls, and the limitations

**Status:** study aid for the candidate · updated 2026-11-19 (v2.1.0)
**Scope:** explanations and likely examiner questions. This file is **not
thesis prose** and contains **no new analysis**. Every number below is a
projection of a frozen artefact; the canonical sources are named at the end.

**Version note.** The reciprocity correction (EXP-0015, deviation #45) changed
H6 from a fragile null to the `HEADLINE_ROBUST` result and roughly doubled the
H10 association. Use only the v2.1.0 numbers below; v2.0.2 values are
superseded and preserved in `outputs/tables/superseded_v2_0_2/`.

**Ground rule.** Answer at the level of the claim the design supports. Do not
upgrade a predictive association into a causal effect, a fragile result into a
headline, or a powered null into proof of no effect.

---

## 1 · The thesis in one minute

The thesis asks whether broker-network structure in the most-traded tier of
NEPSE carries next-session information about returns and volatility. It uses
57.9 million floorsheet rows (2021–2024), builds a 12-symbol out-of-sample
panel (7,116 rows, effective N 6,383), and tests ten pre-declared hypotheses
with Driscoll–Kraay, two-way, Fama–MacBeth and wild-bootstrap inference,
Romano–Wolf multiplicity control, liquidity and EGARCH checks, quantile tails,
and a specification curve.

The result is deliberately mixed:

- **One robust headline:** H6, reciprocity → next-session signed return,
  −22.948 bp per 1 TRAIN-SD (DK p .0048; RW p .031; WB p .001; FM p .0028;
  4/4 STRONG concordance).
- **One moderate headline:** H10, reciprocity → next-session absolute return,
  +20.642 bp per 1 TRAIN-SD (DK p .0014; RW p .012; WB p .004; FM p .4901;
  MODERATE concordance). H6 and H10 are two outcomes of the same feature, not
  independent confirmations.
- **One exploratory post-hoc result:** H4, buyer HHI → return, +7.510 bp but
  the **opposite** sign to the pre-declaration.
- **Two fragile nulls:** H7 and H8 pass BH but fail Romano–Wolf.
- **Five powered nulls:** H1, H2, H3, H5, H9; the design could detect their
  stated MDEs and did not.
- **No tradable alpha:** every 1-SD effect is below the declared 30–50 bp
  round-trip cost floor.

The honest one-sentence takeaway: *network structure carries measurable
next-session information in this tier, but the associations are moderate,
tier-local, partly persistent, and far below the cost of acting on them.*

---

## 2 · H10 — the moderate headline

### 2.1 What H10 says

| item | value |
|---|---|
| feature | `reciprocity` — share of directed edge volume flowing on bidirectional broker pairs; `2·Σ min(w_ij, w_ji) / Σ all weights` |
| outcome | `abs_ret_fwd1` — absolute next-session close-to-close return (a volatility proxy, not a direction) |
| pre-declared direction | positive |
| estimate | **+20.642 bp per 1 TRAIN-fold SD** |
| DK p (primary) | **.0014** |
| DC-v2 p | **1.00e-5** |
| wild bootstrap p (entity-clustered, B=999) | **.004** |
| Romano–Wolf p (B=999, q=.10) | **.012** — one of two survivors |
| Fama–MacBeth p | **.4901** — does **not** agree |
| SE concordance | **MODERATE** (DK, DC-v2, WB significant; FM not) |
| liquidity-controlled β | **+19.658 bp**, p **.0021** (−4.8% vs base) |
| EGARCH-standardised outcome | p **.0497**, sign matches |
| quantile tails | τ=.10 **+4.838**; τ=.50 **+8.929**; τ=.90 **+34.643**; ratio **7.161**; `BOTH_TAILS (INCREASING)` |
| final classification | **`HEADLINE_MODERATE`** |
| cost floor | **1.45–2.42× below** the 30–50 bp explicit round-trip floor |

### 2.2 Why it is `HEADLINE_MODERATE`, not `HEADLINE_ROBUST`

Four independent reasons; give all four before an examiner asks:

1. **FM disagreement.** Fama–MacBeth p is .4901. The result is not stable
   across all four standard-error families.
2. **Moderate, not strong, concordance.** Three of the four SE families agree,
   but the pre-declared `HEADLINE_ROBUST` tier requires all four (as H6 has).
3. **Persistence caveat.** The DC13 placebo-outcome check finds reciprocity
   predicting **past** |return| at **+44.78 bp** (p 8.7e-10), which is larger
   than the forward +20.64 bp. Part of H10 may inherit persistent volatility
   rather than identify a clean forward channel.
4. **Tier locality.** The external ranks 11–15 test gives H10 **+16.437 bp**,
   raw p **.0539**, BH **.539**, n 3,409, and **0/5 BH pass**. The effect
   attenuates and does not replicate outside the headline tier.

`HEADLINE_MODERATE` is therefore the correct label: the association survives
the declared primary and family-wise gates, but not every robustness gate.

### 2.3 The 60-second answer

> “Ten hypotheses were pre-declared. Two reciprocity tests survive
> Romano–Wolf correction at q=.10: H6 on signed returns and H10 on absolute
> returns. Reciprocity is the share of volume on two-way broker pairs. For H10,
> a one-standard-deviation increase is associated with about 21 basis points
> higher absolute next-session return, with DK p=.001, wild-bootstrap p=.004,
> and RW p=.012. I classify it as a moderate headline, not a robust one,
> because Fama–MacBeth p=.49, the concordance is moderate, the placebo-outcome
> check shows reciprocity also predicts past volatility more strongly, and the
> effect does not replicate in the next turnover tier. H6 is the robust half of
> the pair: −23 bp on signed returns with all four SE families agreeing. Both
> are predictive associations, not causal effects, and both are below the
> explicit cost floor.”

### 2.4 The 2-minute answer (add the economics)

Add after the 60-second answer:

> “Economically, reciprocity is a two-way intermediation measure. A high value
> means brokers are trading with each other in both directions, which is
> consistent with active liquidity provision or a dense trading network. That
> is a candidate interpretation, not an identified mechanism: the design has no
> instrument, no exogenous broker shock, and no intraday order data. The
> quantile panel shows the H10 association is stronger in the upper tail —
> about +34.6 bp at τ=.90 — so it is not a constant linear premium. The cost
> comparison uses a 30–50 bp explicit round-trip floor that excludes brokerage,
> spread and CNS carry, so the true hurdle is higher. The correct conclusion is
> informational content, not a trading strategy.”

### 2.5 Likely H10 questions

| question | answer |
|---|---|
| “Why reciprocity rather than centrality?” | Reciprocity was one of the ten pre-declared network features; centrality was not the H10 construct. The thesis does not run a centrality horse-race. |
| “Why absolute return?” | H10 was pre-declared on `abs_ret_fwd1`; the |return| outcome is a volatility proxy. A positive coefficient means more movement, not a direction. |
| “Isn’t H10 just volatility persistence?” | Partly, and the thesis says so. Reciprocity predicts past |return| at +44.78 bp versus +20.64 bp forward. The forward association survives controls, but the persistence channel is a disclosed limitation (L9). |
| “Why does H6 have the opposite sign?” | H6 is the same feature on **signed** return; H10 is on **absolute** return. A feature can be associated with lower directional return and higher volatility. They are not independent tests, but they are different outcomes. |
| “Why is FM p .49?” | Fama–MacBeth estimates the average cross-sectional slope; with 12 symbols and 712–714 cross-sections it weights the panel differently and is imprecise here. The thesis reports the disagreement rather than hiding it. |
| “Why not use FM as primary?” | The pre-declared primary is DK with a two-way/FM/WB concordance battery. Changing the primary after seeing FM would be post hoc. |
| “Is RW p .012 significant?” | Yes, at the pre-declared q=.10 gate; H6 (.031) and H10 (.012) both survive. H10 is classified moderate because of the FM and concordance evidence, not the RW p. |
| “Why q=.10?” | The family-wise gate was pre-declared in the v2 extension. It is less conservative than .05; the literal full-family variant is co-reported. |
| “Could H10 be a fluke?” | One can never rule that out. The evidence is the pre-declaration, DK/WB/RW survival, liquidity and EGARCH sign match, and tail monotonicity. The FM failure and external attenuation are the counterweights. |
| “Is +20.64 bp economically meaningful?” | Statistically detectable, economically small. It is 1.45–2.42× below the explicit cost floor and cannot be traded at 1 SD without a directional signal and all-in costs. |
| “Why 1 SD?” | It is a statistical unit, not a position size. The features are winsorised at 1/99 within fold; extrapolating to 3–13 SD is not supported. |
| “What would make H10 robust?” | A licensed broker-level dataset, intraday timestamps, an exogenous network shock, and FM concordance. None is in this thesis. |

### 2.6 H6 — the robust headline

| item | value |
|---|---|
| feature | `reciprocity` (same construct as H10) |
| outcome | `ret_fwd1` — signed next-session close-to-close return |
| pre-declared direction | ambiguous (`amb`); sign is reported, not gated |
| estimate | **−22.948 bp per 1 TRAIN-fold SD** |
| DK p | **.0048** |
| DC-v2 p | **6.71e-6** |
| wild bootstrap p | **.001** |
| Romano–Wolf p | **.031** |
| Fama–MacBeth p | **.0028** — agrees |
| SE concordance | **STRONG 4/4** |
| liquidity-controlled β | **−23.182 bp**, p **.0043** (−1.0%) |
| EGARCH-standardised outcome | p **.0016**, sign matches |
| quantile tails | τ=.10 **−21.865**; τ=.50 **−9.324**; τ=.90 **−3.628**; ratio **0.166**; `BOTH_TAILS (INCREASING)` |
| final classification | **`HEADLINE_ROBUST`** |
| cost floor | −22.95 bp is an absolute-return association, not a directional strategy; not tradable at 1 SD |

**Why H6 is robust.** It passes Stage-1 RW (.031), Stage-2 four-SE concordance
(STRONG 4/4), liquidity controls (−1.0%), EGARCH (p .0016) and both-tail
monotonicity. It also survives leave-one-symbol-out 12/12 and the drop-bubble
normal-era check (−31.979 bp, p .0045). The one qualification is the same
persistence caveat as H10: reciprocity is not orthogonal to past |return|.

**Why the sign is negative.** H6's direction was pre-declared ambiguous, so the
negative sign is a reported result rather than a confirmation of a signed
hypothesis. It says that denser two-way intermediation is followed by lower
signed returns in this tier. That is a directional association, not a
volatility effect, and it should not be presented as a profitable short
strategy: the estimate is 23 bp per SD and far below costs.

---

## 3 · The nulls

### 3.1 Taxonomy — do not use “null” as one category

| label | meaning | tests |
|---|---|---|
| `HEADLINE_ROBUST` | Passed the Stage-1 RW gate, Stage-2 4/4 SE concordance, liquidity, EGARCH and both-tail checks. | H6 |
| `HEADLINE_MODERATE` | Survived the primary and RW gates but failed at least one concordance check (FM or SE tier). | H10 |
| `NULL_POWERED` | The design could detect the stated MDE at 80% power and did not; not a precise zero. | H1, H2, H3, H5, H9 |
| `NULL_FRAGILE` | Passed BH but failed a registered v2 gate (RW, threshold, era, MDE); not a headline. | H7, H8 |
| `EXPLORATORY_POST_HOC` | A real sample pattern, but opposite to the pre-declared sign or selected after the fact; cannot confirm the hypothesis. | H4 |

### 3.2 The five powered nulls

| H | construct → outcome | β (bp) | DK p | MDE₈₀ (bp) | placebo / note |
|---|---|---:|---:|---:|---|
| H1 | self-loop ratio → \|return\| | −1.557 | .4306 | 5.530 | LOO-stable null |
| H2 | IF anomaly score → \|return\| | −1.494 | .5945 | 7.452 | placebo share **.805** |
| H3 | IF anomaly score → return | +0.178 | .9531 | 8.414 | placebo share **.540** |
| H5 | buyer HHI → \|return\| | −1.856 | .4875 | 7.485 | LOO-stable null |
| H9 | self-loop ratio → return | +1.817 | .4587 | 6.868 | WB p **.100** exactly; strict rule does not count it |

**What “powered” means.** The minimum detectable effect at 80% power, α=.05,
is reported for each test. The estimated |β| is below that MDE, so the test
could have detected an effect of the stated size and did not. It does **not**
mean the true effect is exactly zero.

**The anomaly-score null is the thesis's strongest negative result.** The
Isolation Forest score fails on both outcomes, with placebo shares close to
random (.805 and .540). The expanded battery — 1,000 full-panel shuffles and
within-symbol block shuffles — confirms it. This is a substantive negative
finding: a standard unsupervised anomaly score does not predict next-session
returns in this panel.

### 3.3 The two fragile nulls

| H | construct → outcome | β (bp) | DK p | BH q | RW p | WB p | FM p | why not a headline |
|---|---|---:|---:|---:|---:|---:|---:|---|
| H7 | EoD concentration → \|return\| | +3.952 | .0274 | .0689 | .152 | .022 | .0094 | RW fail; spec curve outcome-sensitive |
| H8 | EoD concentration → return | −4.471 | .0459 | .0918 | .199 | .095 | .0587 | RW fail; 1% cutoff and normal era fail; MDE-underpowered |

**H7 in one line.** It is a volatility/absolute-return association, not a
directional-return effect. The specification curve is 72/72 positive for
`abs_ret` but 66/72 negative for `ret`; the 1% EoD cutoff collapses the
CI-exclusion share to zero. It is a fragile, outcome-dependent regularity.

**H8 in one line.** The negative EoD → return association is a bubble-era,
mid-tail phenomenon: at the top-1% cutoff it is −0.60 bp (p .7634), and in the
normal era it is −4.44 bp (p .1703). MDE₈₀/|β| = 1.426, so it is also
underpowered. It is not a precise zero and not a headline.

### 3.4 H4 — exploratory, opposite sign

H4 pre-declared a **negative** buyer-HHI → return relation. The estimate is
**+7.510 bp** (DK p .0275; BH q .0689; RW p .152; WB p .002; FM p .0082).
A significant estimate in the opposite direction does not confirm the
hypothesis; it is reported as `EXPLORATORY_POST_HOC`. Two live explanations are
illiquidity/size composition and a persistent-volatility channel; the thesis
does not choose between them.

### 3.5 Likely null questions

| question | answer |
|---|---|
| “So you found nothing?” | No. The thesis reports two reciprocity headlines (one robust, one moderate), one exploratory opposite-sign result, two fragile results, and five powered nulls. The anomaly-score null is itself a substantive finding. |
| “Why not say ‘no effect’?” | Because a powered null is bounded by its MDE. The correct statement is “no detectable association at the declared gates,” not “the effect is zero.” |
| “Why do H7/H8 pass BH but fail RW?” | BH controls the false-discovery rate over ten tests; RW controls the family-wise error rate. RW is stricter, and the v2 extension pre-declared it as the headline gate. |
| “Aren’t you just p-hacking with ten tests?” | The ten tests were pre-declared before results; the v2 gates were pre-declared before v2 results; every deviation is logged. The fact that only two survive is the opposite of p-hacking. |
| “Why keep H4 if it is opposite-sign?” | Because it is a reproducible sample pattern and hiding it would be selective reporting. It is labelled exploratory and never counted as confirmation. |
| “Why is H9 null if WB p is .100?” | The pre-declared counting rule is strict p < .10, and H9 fails DK/BH/RW. A single boundary p-value does not rescue it. |
| “What is the economic story for the nulls?” | There is no stable, exploitable network anomaly in this tier. The market is thin, the panel is small, and the features are persistent; the design cannot support a stronger story. |

---

## 4 · Limitations — the 26-row table in viva form

### 4.1 The four CRITICAL limitations

| ID | limitation | what it blocks | how to answer |
|---|---|---|---|
| **L1** | Predictive, not causal | Any “effect of” wording | “The design is observational; no instrument or exogenous broker shock. The correct verb is predicts.” |
| **L2** | Tier-10 coverage | Market-wide claims | “The panel is the per-fold top-10 universe (12 symbols). Ranks 11–15 give 0/5 BH pass and attenuated estimates; H10 falls to 80% of base and is non-significant.” |
| **L3** | No intraday timestamps | Order-flow, execution-order, manipulation claims | “Floorsheet rows are not execution-ordered; `contract_no` is daily-global. No intraday statistic is claimed.” |
| **L4** | Licence chain | Clean deposit clearance | “The Kaggle tier1 grant is MIT, but upstream NEPSE Alpha grants no explicit redistribution right and reserves all rights. Public figures are the author's accepted risk; the derived deposit excludes them.” |

### 4.2 The MAJOR limitations

| ID | limitation | one-line viva answer |
|---|---|---|
| **L5** | Single exchange | “NEPSE only; no cross-market replication. Generalisation is a hypothesis, not a finding.” |
| **L6** | Corpus gaps | “938/940 sessions; 2021-09-01 and 2023-11-27 are absent from every verified source and are not imputed.” |
| **L7** | 2023-02-16 contract-ID defect | “All 35,043 rows share one ID; ordering-dependent features exclude the day, level aggregates keep it.” |
| **L8** | H8 fragility | “Top-1% cutoff p .7634, normal era p .1703, MDE ratio 1.426; it is fragile and underpowered.” |
| **L9** | H10 dependence | “FM p .4901 and moderate concordance; RW p .012 survives comfortably, but FM does not agree. It is a moderate headline.” |
| **L10** | Self-loop interpretation | “It is a volume share, not a wash-trading detector; buyer-side volume makes it mechanically high in single-broker trades.” |
| **L11** | Circuit-breaker non-implementability | “No limit-hit flag exists in the corpus or any verified archive; four subgroup rows are NOT_EXECUTED, and no proxy was fabricated.” |
| **L12** | Liquidity verdict | “Three proxies, not quoted spreads; every BH-passing estimate moves <6% and keeps its sign. Liquidity neither rescues nor overturns a headline.” |
| **L13** | Event-study overlap | “666 events on 392 dates; 65.3% share a date, so event-level p-values are upper bounds. Date-clustered rank z is 2.99, p .0030.” |
| **L14** | Regime split is descriptive | “No significant interaction (min p .1171); era statements are magnitude comparisons, not identified effects.” |
| **L15** | Subgroup power | “36 estimated cells; two H10 descriptive cells survive Bonferroni (turnover bottom-7 p_bonf .0183; size-small .0473), but no interaction does (min .1524). The grid cannot reject homogeneity.” |
| **L16** | Specification-curve outcome sensitivity | “H7 is 72/72 positive for absolute return but 66/72 negative for signed return; it is a volatility association, not a directional effect.” |
| **L17** | Broker-panel degeneracy | “Monthly aggregation; 18/48 months are complete graphs, so betweenness is zero; the panel is descriptive only.” |

### 4.3 The MINOR limitations

| ID | limitation | one-line viva answer |
|---|---|---|
| **L18** | 2021-03-07 → 03-08 relabel | “Evidence triple: the day is absent in both OHLCV sources, CGH's rate band matches OHLC, and CGH quantity equals volume.” |
| **L19** | Duplicate keys | “752 keys: 506 exact drops, 246 signature-conflict keys kept non-merged; 0.006% of rows, deterministic pick.” |
| **L20** | Broker-ID source-format defect | “275,590 dotted-ID rows on 15 days; 37/7,116 analysis-panel rows (0.52%) affected; leave-out signs unchanged, H8 p .0563.” |
| **L21** | Junk scrape rows | “19 symbol-days plus 4 empty-symbol rows with NULL volume; no aggregate touches them.” |
| **L22** | Dashboard scope | “Extracts-only, no full-corpus read, no new inference; the cache-only contract is tested.” |
| **L23** | Buyer-side volume reconciliation | “Top-12 median floorsheet/OHLCV ratio is 1.0000; the full-market ~2× ratio is a 100/530 coverage artifact.” |
| **L24** | Alternative-scorer leg | “Rank correlations only: Mahalanobis .86, diag-z² .95, LOF .63, OC-SVM .54; score levels remain method-dependent.” |
| **L25** | Reciprocity construct overlap | “Reciprocity correlates .833 with `n_edges` and .765 with `n_nodes`; the design does not partial out network size, so ‘reciprocity’ is not cleanly separated from ‘more connected market’.” |
| **L26** | Version history | “v2.1.0 corrects `reciprocity_volume`; all v2.0.2 reciprocity-dependent values are superseded and preserved, not mixed with current numbers.” |

### 4.4 The limitations answer in 45 seconds

> “The binding limitations are four. First, the design is predictive, not
> causal. Second, the panel is the most-traded tier, not the market: the next
> tier gives 0/5 BH pass and attenuated estimates. Third, there are no
> intraday timestamps, so I make no order-flow or manipulation claim. Fourth,
> the licence chain is unresolved upstream: the Kaggle grant is MIT, but NEPSE
> Alpha grants no explicit redistribution right. The major limitations are
> H10's FM disagreement and the shared reciprocity persistence caveat, H8's
> fragility and underpowering, the three-proxy liquidity check, event overlap,
> subgroup power, and the descriptive-only broker panel. None of these is
> hidden; each is tied to an EXP row.”

### 4.5 What would change the conclusions

1. Licensed broker identities, licence types, or exogenous outages → causal
   network-formation designs.
2. Intraday execution timestamps or order-level data → order-flow and
   manipulation tests, and a real circuit-breaker flag.
3. A directional signal with all-in cost data (spread + CNS carry) → could move
   H6/H7/H10 from informational to conditionally tradable.
4. Full-market or cross-exchange replication → could move the result from
   tier-local to market-wide, or falsify it.
5. A source/licence upgrade for tier1 OHLCV or the NEPSE index → changes
   deposit/redistribution status, not the estimates.

---

## 5 · Likely examiner questions beyond H10 and the nulls

### 5.1 Design and method

| question | answer |
|---|---|
| “What is the contribution?” | A reproducible, pre-declared predictive study of broker-network structure in a frontier market, with a disciplined negative-result set and a documented data-engineering pipeline. It is not a causal or trading thesis. |
| “Why 2021–2024?” | The verified floorsheet corpus covers that window; 2021–2022 is the bubble era and 2023–2024 the normal era, which permits a descriptive regime split. |
| “Why only 12 stocks?” | The per-fold top-10 turnover universe is a pre-declared design choice (DC1) that buys clean floorsheet/OHLCV coverage. It is a tier, not the market. |
| “Why 7,116 rows and effective N 6,383?” | 7,126 OOS rows minus 10 missing outcome/feature rows; 7,116 − (12−1) − (723−1) = 6,383 after two-way fixed-effect absorption. |
| “How do you prevent leakage?” | Anchored expanding purged folds, 6-session purge, TRAIN-only winsorisation/standardisation/Isolation Forest/q90 threshold; separate leakage tests. |
| “Why Driscoll–Kraay?” | It handles serial and cross-sectional dependence in a long panel; bandwidth 5 was pre-declared. The thesis also reports two-way, FM and wild bootstrap as a concordance battery. |
| “Why not HC1?” | The pre-declared specification refuses HC1/robust as inadequate for this dependence structure (R3). |
| “Why Romano–Wolf?” | It controls family-wise error over the ten-test family while accounting for dependence; B=999, common row-level Rademacher signs, recentred t*. |
| “Why wild bootstrap?” | It provides an entity-clustered small-G check; 12 clusters is a caveat, so it is corroborative, not primary. |
| “What is the DC13 test?” | A placebo-outcome check: the feature is regressed on **past** |return|. A significant coefficient flags persistence/specification risk. Five of five unique features flag; EoD passes. |
| “Why quantile regression?” | To test whether the association is constant or tail-concentrated. H10 is increasing across quantiles (τ=.10 +4.84 to τ=.90 +34.64 bp); H6 is also both-tails/increasing with a negative slope (τ=.10 −21.87 to τ=.90 −3.63 bp). |
| “Why EGARCH?” | To check whether the result survives a volatility-standardised outcome. Both headlines sign-match: H6 p=.0016, H10 p=.0497; the model is symmetric EGARCH(1,1), not an asymmetric extension. |
| “What is the event study for?” | It tests whether anomaly events have abnormal returns. Mean CAR is +19.33 bp (p .402); only the rank distribution shifts, and the market-adjusted mean is an alpha artifact. |

### 5.2 Data and reproducibility

| question | answer |
|---|---|
| “How large is the corpus?” | 57,927,926 raw rows → 57,892,630 after deduplication; 1,167 day files; 530 symbols; 938/940 sessions. |
| “How do you know the data are correct?” | Per-file SHA-256 provenance, duplicate audit, volume reconciliation (top-12 median ratio 1.0000), OHLCV cross-checks, and a clean 21/21-step rebuild. |
| “Is the rebuild byte-identical?” | No, numerical: the v2.0.2 audit had 40/73 tables byte-identical, 25 at ≤3.55e-14 relative, 4 reorder-only, 2 QuantReg optimizer drifts (7.44e-7), one float aggregation ±1 unit, one threshold flip 146→141. The v2.1.0 correction rebuild completed 21/21 steps in 70.2 min from untouched raw archives; its dependent tables are the corrected record. |
| “How many tests?” | 161 passed, including notebooks (v2.0.2 count; re-confirmed at the v2.1.0 release). |
| “Where is the code?” | Public GitHub repository; `main` at the v2.1.0 release; tags `v1.0-freeze`, `v2.0-a++-freeze`, `v2.0.1-handoff`, `v2.0.2-prewrite`, `v2.1.0-reciprocity-correction`. |
| “Is the deposit uploaded?” | No. The derived-only v2.1.0 archive is built and hashed locally; no DOI, no upload. |
| “What is excluded from the deposit?” | Raw archives, DuckDB, processed parquet, prediction parquet, logs, figures, dashboard cache. The deposit is code/docs/tables/metadata only. |

### 5.3 Interpretation and policy

| question | answer |
|---|---|
| “What does reciprocity mean economically?” | The share of volume on two-way broker pairs; a dense, reciprocal intermediation network. It is consistent with liquidity provision or relationship trading, but the design does not identify the mechanism. |
| “What is the policy implication?” | A surveillance/monitoring signal, not a trading rule or a finding of manipulation. The result is tier-local and below the cost floor. |
| “Can NEPSE use this?” | As a research lead for monitoring network structure, with the caveats: no causality, no intraday order data, no market-wide replication. |
| “Why not call self-loop volume wash trading?” | The ratio is mechanically high when few brokers trade a symbol; volume counts the buyer side. A manipulation finding needs order-level data and a legal definition. |
| “What is the PhD extension?” | Network formation, core/liquidity provision, source-vintage discontinuity as measurement change, and centrality → price impact with exogenous broker shocks. |
| “Why should we trust the negative results?” | They are pre-declared, powered, and reported with MDEs. The anomaly-score null is confirmed at 1,000 permutations and block permutations. |

### 5.4 Authorship and AI use

| question | answer |
|---|---|
| “Did you write this yourself?” | “I wrote the thesis prose and am responsible for every claim. AI assisted with code, tests, data-integrity checks, figures, manifests and document scaffolding. That assistance is disclosed in the University disclosure and the repository's AI-use record.” |
| “Did AI generate the results?” | “No. Every number comes from executed code on real data, with provenance and experiment-register rows. AI did not invent results or citations.” |
| “Did AI draft the chapters?” | “No chapter, section, literature review, discussion or conclusion was drafted by an AI and submitted as my own writing.” |
| “Why is there an AI policy in the repo?” | “The public summary records the assistance and the licence register; the detailed plan is kept private for audit. Removing the record would misrepresent the work, so the disclosure stays.” |
| “Why disclose AI use if the module brief is unclear?” | “Coventry's central guidance says AI use must be acknowledged. I asked the module leader for written clarification and kept the disclosure until that is resolved.” |

### 5.5 Assessment alignment

Map the thesis explicitly to the module's published assessment criteria. The
four high-level areas to address are: research methods and literature; tools
and solution construction; project management and performance; and legal,
social and ethical issues. Do not assume the examiner will infer the mapping.

**Project-management evidence to cite.** The project ran from the Phase-0
environment survey on 2026-11-08 to the writing window ending 2026-11-27.
Use `AGENTS.md` (phase status, risks, deviations), `reports/research_progress.md`
(progress narrative), `docs/analysis_deviations.md` (every change and why),
and `docs/reproducibility.md` (clean rebuild, 21/21 steps, 62.5 min,
numerical-not-byte-identical result). The strongest project-management answer
is the **deviation log**: it shows that changes were recorded before or when
they happened, not reconstructed after the fact.

**Gap to close in the report.** The current Ch.1–Ch.6 structure covers
research methods, literature, tools, results, discussion, and limitations, but
it does **not** have a dedicated project-management/performance-evaluation
section. Add a section (or a substantial subsection) covering: timeline and
milestones; resource/coordination choices; risk register (data access, licence,
compute time, scope); what went well; what went poorly; and what you would do
differently. Use the repository evidence; do not invent a retrospective.

**Length discipline.** Keep the report within the module's word limit. The
repository's chapter packs are scaffolding, not prose. The student must write
the report and keep the assessment areas visible in the structure. A long
report cannot reproduce every table; use the canonical tables and put the rest
in appendices.

**Literature caveat.** The 39 references in
`reports/chapter_assets/ch2_references_scaffold.csv` are metadata-verified
candidates, not a finished literature review; every row is marked
`content_review_status = NOT_REVIEWED`. The student must read the sources,
write the review, and cite only what has been read.

---

## 6 · Ten-minute viva walkthrough

1. **Minute 0–1:** scope and question. Predictive, top-tier, 2021–2024.
2. **Minute 1–2:** data. 57.9M rows, 938/940 sessions, 12-symbol OOS panel.
3. **Minute 2–3:** design. Ten pre-declared tests, DK primary, four-SE battery,
   RW gate, liquidity/EGARCH/quantile/spec-curve checks.
4. **Minute 3–5:** headlines. H6 robust (−22.9 bp, 4/4 SE families, RW .031);
   H10 moderate (+20.6 bp, FM .49, RW .012); shared persistence caveat, tier
   locality, cost floor.
5. **Minute 5–7:** nulls and fragile results. Taxonomy, MDE, anomaly-score
   null, H4 opposite sign, H7/H8 demotions.
6. **Minute 7–9:** limitations. L1–L4 critical; L8/L9/L12/L13 major.
7. **Minute 9–10:** contribution and what would change the conclusions.
   Reproducibility, licence position, no causal/trading claim.

---

## 7 · Do-not-say list

| do not say | say instead |
|---|---|
| “H10 is robust / strong / confirmed.” | “H10 is a moderate headline; DK/WB/RW survive, FM p .4901, concordance moderate. H6 is the robust one.” |
| “H6 is a fragile null.” | “H6 is the robust headline: −22.9 bp, STRONG 4/4 concordance, RW .031.” |
| “Reciprocity causes higher volatility.” | “Reciprocity predicts higher next-session absolute return and lower signed return in this panel.” |
| “H4 confirms the concentration story.” | “H4 is opposite-sign and exploratory post hoc.” |
| “H7/H8 are findings.” | “They are fragile nulls; BH pass but RW fail.” |
| “The nulls prove no effect.” | “Powered nulls: no detectable association at the stated MDE.” |
| “Self-loop volume is wash trading.” | “Self-loop volume share; not a manipulation measure.” |
| “The result is market-wide.” | “Tier-local; ranks 11–15 give 0/5 BH pass.” |
| “H10 is tradable.” | “1.45–2.42× below the explicit cost floor; not standalone tradable at 1 SD.” |
| “The event study shows positive abnormal returns.” | “Mean CAR p .402; only the rank distribution shifts.” |
| “The anomaly score predicts returns.” | “H2/H3 null; placebo shares .805/.540.” |
| “The licence is clear.” | “Kaggle tier1 is MIT-declared; upstream NEPSE Alpha grants no explicit redistribution right.” |
| “AI wrote the thesis.” | “AI assisted with code/tests/docs; I wrote the prose and own the claims.” |

---

## 8 · Evidence map

| need | canonical file |
|---|---|
| final classification, RW/WB p | `outputs/tables/v2_final_headline_set.csv` |
| DK/FM p, BH q, MDE, effective N | `outputs/tables/hypothesis_grid_results_v2.csv` |
| four-estimator concordance | `outputs/tables/se_concordance.csv` |
| quantile tails | `outputs/tables/quantile_tail_summary.csv` |
| event study | `outputs/tables/event_study_upgraded.csv` |
| robustness variants | `outputs/tables/robustness_headline_survival.csv` |
| external tier | `outputs/tables/robustness_top5_external_grid.csv` |
| subgroups / tier locality | `outputs/tables/heterogeneity_subgroups.csv` |
| trade size | `outputs/tables/trade_size_heterogeneity.csv` |
| H7 specification curve | `outputs/tables/specification_curve_h7_summary.csv` |
| cost floor | `outputs/tables/economic_magnitude.csv` |
| limitations | `reports/limitations.md` |
| exploratory findings / DC13 | `reports/exploratory_findings.md` |
| H10 narrative source | `reports/chapter_assets/key_claims_sheet.md` |
| correction record | `reports/reciprocity_correction.md` |
| superseded v2.0.2 values | `outputs/tables/superseded_v2_0_2/` |
| licence position | `reports/licence_review.md` §10 |
| chapter crosswalk | `docs/chapter_artifact_map.md` |

**Final reminder.** The viva is not a test of whether every result is
significant. It is a test of whether the candidate knows what the design can
and cannot support. The strongest answer is often the bounded one.
