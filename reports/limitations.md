# Limitations — v2 living copy (v2.1.0 reciprocity correction, 2026-11-19)

**Status.** This is the v2 living limitations table required by
`docs/analysis_plan_v2_extension.md` §V2-5. The v1 file `docs/limitations.md`
remains **frozen** (Phase 7, tag `v1.0-freeze`) and is not edited. Every row
below cites the experiment(s) that establish it. Severity is assigned by the
threat to the thesis's stated claims, not by how easy the limitation is to fix.

| severity | definition |
|---|---|
| **CRITICAL** | Could invalidate a headline claim or block deposit/publication if unresolved. Must be stated in the abstract/intro and cannot be argued away by robustness. |
| **MAJOR** | Materially narrows the interpretation, external validity, or identification of a result; must be stated in the results/discussion. |
| **MINOR** | Documented data/engineering caveat with quantified, non-material impact; stated in the data/appendix. |

---

## 1 · Limitation table

| ID | severity | limitation | evidence / impact | EXP |
|---|---|---|---|---|
| L1 | **CRITICAL** | **Predictive, not causal.** All estimates are conditional associations on an observational panel; no instrument, exogenous broker shock, or event timing identifies a causal effect of network structure. | DK/DC/FM/WB + panel FE only; no identification strategy. Any "effect of concentration" wording must be "predictive association". | EXP-0004b, EXP-0009c/d, EXP-0011b/d |
| L2 | **CRITICAL** | **Tier-10 coverage.** The OOS panel is the per-fold top-10 universe (12 symbols), not the 530-symbol market. | External ranks 11–15: 3,414 rows / 256 events; **0/5 BH pass** (smallest raw p .0539, H10); point estimates attenuate for H4/H6/H7/H8, and H10 falls to 80% of base but remains non-significant. Results are tier-local (liquidity/attention), not market-wide. | EXP-0004a, EXP-0005f, EXP-0015 |
| L3 | **CRITICAL** | **No intraday timestamps.** Floorsheet rows are not in execution order; `contract_no` is daily-global. No order-flow, sequence, or intraday-timing statistic is identified. | Per-(symbol,date) contract-id gaps are expected; ordering features sort by `contract_no` and exclude 2023-02-16. | EXP-0002b/c, EXP-0003a |
| L4 | **CRITICAL** | **Licence chain.** Tier1 Kaggle OHLCV declares MIT and an educational/research purpose, but the upstream NEPSE Alpha terms (retrieved 2026-11-14) grant no explicit redistribution right and reserve all rights; upstream status remains `UNCERTAIN`. The author accepted the figure-redistribution caveat for the public code repository on 2026-11-14, so figures are public there, but the derived-only deposit still excludes them. NEPSE index repo licence is `unstated_in_repo`; data licences remain per `provenance_manifest.csv`; code MIT (v2.0.2). | Upstream clearance is not claimed. Any deposit that redistributes materially tier1-derived tables or figures remains exposed unless written permission is obtained or the series is replaced; the index is secondary/shading only and swap-able. | EXP-0002d, EXP-0007; `reports/licence_review.md` §10; deviation #43 |
| L5 | **MAJOR** | **Single exchange.** NEPSE only; no cross-market or cross-country replication. | External validity is bounded to one frontier market and one 2021–2024 window. | EXP-0002b |
| L6 | **MAJOR** | **Corpus gaps.** 938/940 window sessions covered (99.79%); 2021-09-01 and 2023-11-27 exist in no verified source. | Non-imputable; no aggregate crosses the gaps. | EXP-0002b |
| L7 | **MAJOR** | **2023-02-16 `contract_no_defect`.** All 35,043 rows share one transaction id. | Ordering-dependent features (incl. EoD concentration) exclude the day; level aggregates keep it. | EXP-0002c, EXP-0003a |
| L8 | **MAJOR** | **H8 fragility.** H8 loses significance at the 1% EoD cutoff (−0.60 bp, p .7634) and in the normal era (−4.44 bp, p .1703); MDE ratio \|β\|/(MDE₈₀/2) = 1.426 → `NULL_UNDERPOWERED`. | H8 is a bubble-era, mid-tail association, not a stable headline. Final label `NULL_FRAGILE`. | EXP-0005c/e, EXP-0008c, EXP-0012 |
| L9 | **MAJOR** | **H10 dependence.** H10 is DK/DC-v2/WB significant but FM p .4901; SE concordance is MODERATE, not STRONG. | Final label `HEADLINE_MODERATE`, not `HEADLINE_ROBUST`. RW p .012 is a q=.10 survival, but FM disagreement is now larger than in v2.0.2. | EXP-0004b, EXP-0008b, EXP-0009d, EXP-0012, EXP-0015 |
| L10 | **MAJOR** | **Self-loop interpretation.** `self_loop_ratio` = buyer and seller are the same broker; volume counts the buyer side. The ratio is mechanically high for single-broker trades and is **not** a validated manipulation measure. | H1/H9 are null; no order-level benchmark exists. Do not read the ratio as wash-trading incidence. | EXP-0002e, EXP-0003a, EXP-0004b |
| L11 | **MAJOR** | **Circuit-breaker non-implementability.** No circuit-breaker / limit-hit flag exists in the corpus or any verified archive. | Four H4/H7/H8/H10 rows registered `NOT_EXECUTED`; no price-limit proxy fabricated. The heterogeneity grid is incomplete by construction. | EXP-0011d |
| L12 | **MAJOR** | **Liquidity verdict.** Controls are three proxies (Amihud, Roll, Corwin–Schultz), not direct quoted spreads; no intraday quote data. | Every headline estimate moves < 5% and keeps its sign (H10 +19.658 bp, p .0021; H6 −23.182, p .0043). Null estimates move up to +37.1% (H1) / −40.2% (H3) but remain null. Liquidity does not rescue or overturn a headline. | EXP-0009a/b, EXP-0015 |
| L13 | **MAJOR** | **Event-study overlap.** 666 events on 392 dates; 435 events (65.3%) share a date with another event. | Event-level p-values are upper bounds; the date-clustered rank z (2.986, p .0030) is still an upper bound. Mean-based tests are null. | EXP-0004e, EXP-0011e, EXP-0015 |
| L14 | **MAJOR** | **Regime split is descriptive.** Bubble/normal split has no significant interaction (min p .1171); H8 is bubble-era driven. | Era statements rest on magnitude comparisons, not identified interactions. | EXP-0004d, EXP-0005e |
| L15 | **MAJOR** | **Subgroup power.** 36 estimated cells/interactions; two H10 Bonferroni survivors now exist (size-small p_bonf .0473; turnover bottom-7 p_bonf .0183), but every pre-declared interaction is null (smallest p .152). | Survivors are descriptive cells in a separate family; they do not enter the composition rule. The grid still cannot reject homogeneity. | EXP-0011d, EXP-0015 |
| L16 | **MAJOR** | **Specification-curve outcome sensitivity.** H7 is 72/72 positive for `abs_ret` but 66/72 negative for `ret`; the 1% cutoff collapses the CI-exclusion share to zero. | H7 is a volatility/absolute-return association, not a directional-return effect. 144 specs / 72 unique design betas. | EXP-0011b |
| L17 | **MAJOR** | **Broker panel degeneracy.** Monthly aggregation; 18/48 months are exactly complete graphs → betweenness ≡ 0; 1,071/3,026 broker-months (35.4%) zero; core definition depends on the ranking variable (Jaccard .837 eigenvector / .882 value). | Descriptive only (R11); no structural core–periphery claim; 2024 source vintage breaks level comparability. | EXP-0011c |
| L18 | **MINOR** | **Relabel.** Kaggle `2021_03_07_floorsheet.csv` ingested AS 2021-03-08. | Evidence triple: day absent in both OHLCV sources; CGH rate band [635,665] == OHLC; CGH qty 910 == volume. | EXP-0002b, EXP-0002f |
| L19 | **MINOR** | **Dedupe conflicts.** 752 duplicate (date,symbol,contract_no) keys: 506 exact drops + 246 signature-conflict keys kept NON-merged. | 0.006% of rows; deterministic full-signature pick. | EXP-0002c |
| L20 | **MINOR** | **Broker-ID source-format defect.** 275,590 dotted-ID rows (`58.0`) on 15 days; 37/7,116 OOS rows (0.52%) affected. | Canonicalised `Xs.0 → zero-padded integer`; leave-defect-rows-out signs unchanged; only H8 loses raw 5% (p .0563). | EXP-0011c |
| L21 | **MINOR** | **Junk scrape rows.** 19 (symbol,date) pairs + 4 empty-symbol rows with all numerics empty. | Stay in raw with NULL volume; no aggregate touches them (post-SV7 filter). | EXP-0002c, EXP-0003a |
| L22 | **MINOR** | **Dashboard scope.** Extracts-only (top-12 + register tables); no full-corpus read; only labelled descriptive aggregates. | No new inference; `test_layout_builds_without_duckdb` proves the cache-only contract. | EXP-0006 |
| L23 | **MINOR** | **Volume buyer-side reconciliation.** Top-12 floorsheet/OHLCV volume ratio median 1.0000; 94.7% of pairs in [0.98,1.02]. Full-market ~2× ratio is a 100/530-tier1 coverage artifact. | Volume is buyer-side; do not interpret the full-market 2× as double counting. | EXP-0002e |
| L24 | **MINOR** | **Alternative-scorer leg is rank-correlation only (SV5).** Mean OOS Spearman vs IF: Mahalanobis +.86 (range .78–.92), diag-z² +.95 (.93–.96), LOF +.63 (.48–.79), OC-SVM +.54 (.44–.66). | Confirms a shared quadratic-anomaly ordering; score levels/tails stay method-dependent, no inference. | EXP-0005d, EXP-0015 |
| L25 | **MAJOR** | **Reciprocity definition and network size.** The v2.0.2 feature counted each reciprocal pair twice and treated self-loops as reciprocal; v2.1.0 counts each unordered pair once and keeps self-loop volume only in the denominator. The corrected feature correlates .833 with `n_edges` and .765 with `n_nodes`; the design controls log volume, market return, symbol and date, not network size. | Old and corrected values satisfy `old = 2 × (corrected + self_loop_share)` on all 233,706 rows, so the factor 2 is neutral under TRAIN z-scoring but the additive self-loop term was substantive. Old max 2.0 / 1.03% of rows > 1; corrected max 1.0 / 0% > 1. Do not read reciprocity as a network-size-free effect. | EXP-0015 |
| L26 | **MAJOR** | **Version history and superseded results.** v2.1.0 replaces the reciprocity feature and every dependent result. H6 changed from `NULL_FRAGILE` (−10.939 bp, RW .120) to `HEADLINE_ROBUST` (−22.948 bp, RW .031); H10 strengthened from +9.492 to +20.642 bp but remains `HEADLINE_MODERATE`; the event sample changed from 686 to 666; the placebo-outcome association changed from +19.69 to +44.78 bp. | Old tables are preserved byte-for-byte in `outputs/tables/superseded_v2_0_2/` (43 CSVs + manifest); v2.0.2 is not current. H1/H4/H5/H7/H8/H9 regression rows reproduce v2.0.2 to machine precision. Do not mix versions in one table. | EXP-0015; `reports/reciprocity_correction.md` |

---

## 2 · Required caveats, expanded

### 2.1 Predictive, not causal (L1)

The design estimates conditional associations with panel fixed effects and
Driscoll–Kraay / two-way / Fama–MacBeth / wild-bootstrap standard errors. It
does not identify exogenous variation in broker concentration or reciprocity.
The correct verb is **predicts**, never **causes**. H4's opposite sign is the
clearest warning: a plausible causal prior (concentration → worse liquidity)
is contradicted by a positive predictive coefficient, which is exactly what an
observational design can produce when the feature proxies attention or
liquidity provision.

### 2.2 Self-loop interpretations (L10)

`self_loop_ratio` measures the share of a symbol-day's volume in which the same
broker appears on both sides. Floorsheet volume counts the **buyer** side
(EXP-0002e), so a single-broker match contributes once to volume but creates a
self-loop. The ratio therefore rises mechanically when a symbol-day is traded
by few brokers, even without any manipulative intent. It is not a wash-trading
detector, and H1/H9 are null. Any manipulation interpretation requires
order-level data and a legal/regulatory definition that this corpus does not
contain.

### 2.3 Tier-10 coverage (L2)

The per-fold top-10 selection is a pre-declared design choice (DC1), not a
post-hoc filter. It buys a clean 12-symbol panel with high floorsheet/OHLCV
coverage, but it excludes the rest of the 530-symbol market. The ranks 11–15
external test is the direct falsification: 0/5 BH passes, raw p ≥ .23,
magnitudes 2–4× smaller. The honest scope sentence is **"the most-traded
NEPSE tier"**, not "the NEPSE market".

### 2.4 No intraday timestamps (L3)

Floorsheet rows are not execution-ordered. `contract_no` is a daily-global
identifier, so within a (symbol,date) the id sequence is incomplete by
construction. End-of-day concentration is computed from the **contracted
order** (highest `contract_no`), and the 2023-02-16 defect day is excluded
from all ordering-dependent features. No claim about intraday timing, order
flow, or execution quality is made.

### 2.5 Circuit-breaker non-implementability (L11)

The pre-declared heterogeneity grid includes a circuit-breaker split. Neither
the corpus nor any verified archive exposes a limit-hit / circuit-breaker flag.
Constructing a proxy from price bands would be an unregistered and invalid
measurement choice. The four affected rows are registered `NOT_EXECUTED` and
carry no estimate; the remaining subgroup cells are reported with their
Bonferroni families.

### 2.6 Liquidity verdict (L12)

The liquidity check is a **proxy** check. Three trailing proxies are used
(Amihud, Roll, Corwin–Schultz); there are no quoted spreads or intraday quotes.
For the five BH-passing tests, every estimate moves by less than 5% and keeps
its sign: H10 **+19.658 bp** (p **.0021**, −4.77% change), H6 **−23.182 bp**
(p **.0043**, −1.02%), H4 **+7.357 bp** (p **.0306**, −2.04%), H7 **+3.723**
(p **.0354**), H8 **−4.535** (p **.0425**). For the null tests, relative moves
can be large (H1 +37.1%, H3 −40.2%) because the base estimate is near zero;
none becomes significant. The verdict is: **liquidity controls do not overturn
or rescue a headline**, and they cannot establish a liquidity mechanism.

### 2.7 Single exchange (L5)

All data are NEPSE. There is no cross-exchange replication, so the results
describe one frontier market's most-traded tier in 2021–2024. Generalisation
to other markets is a hypothesis for future work, not a finding.

### 2.8 Licence chain (L4)

| input | licence | status | consequence |
|---|---|---|---|
| kaggle viking303 floorsheets 2021–2023 | CC0 | verified | usable |
| socrateai 2024 floorsheets | MIT | verified | usable |
| tier1 Kaggle OHLCV | Kaggle MIT declared; upstream NEPSE Alpha no explicit redistribution grant | **UNCERTAIN upstream** | academic use per declared grant; figures public in the code repo by the author's accepted risk; excluded from the derived deposit |
| tier2 SamirWagle prices | attribution | verified | gap-fill only |
| NEPSE composite index | `unstated_in_repo` | secondary | shading/benchmark only; swap-able |
| code | MIT (v2.0.2) | verified | code deposit |

The provenance manifest is the authoritative per-file record
(`data/metadata/provenance_manifest.csv`); the licence column there overrides
this summary if they ever differ.

### 2.9 Findings-level caveats carried from v1 (updated for v2.1.0)

- The IF anomaly-score channel is null: H2/H3 placebo shares .805/.540;
  666-event mean CAR +19.33 bp (p .4018); only the rank distribution shifts
  (clustered rank z 2.986, p .0030); no event-based story (EXP-0004c/e).
- H4 is opposite-sign and normal-era driven (+10.49 bp normal era; FM p .0082)
  → exploratory, never a confirmed headline (EXP-0004b/e, EXP-0008a).
- H6 now has STRONG concordance (DK + DC-v2 + FM + WB; RW .031) and
  `HEADLINE_ROBUST`. H10 has MODERATE concordance (DK + DC-v2 + WB; FM p
  .4901) and remains `HEADLINE_MODERATE`. The FM-disagreement caveat applies
  to H10, not to H6 (EXP-0009d, EXP-0015).
- Reciprocity predicts past \|return\| at +44.78 bp (p 8.7e-10), more than twice
  its forward +20.64 bp association. Both reciprocity headlines carry a
  volatility-persistence component (EXP-0015).
- The corrected reciprocity feature correlates .833 with `n_edges` and .765
  with `n_nodes`; the design does not partial out network size (L25).
- Regime interactions are null (min p .1171); era statements are magnitude
  comparisons (EXP-0004d).
- The 16-event illiquid appendix is small-n and not a headline (EXP-0004e).
- Alternative EoD cutoffs and horizons are declared sensitivity analyses, not
  fresh BH families (EXP-0005b/c).
- v2.0.2 numbers are superseded; do not mix them with v2.1.0 in one table or
  paragraph (L26).

---

## 3 · What would change the conclusions

1. A licensed broker-level dataset with identities, licence types, or
   exogenous outages → enables causal/network-formation designs.
2. Intraday execution timestamps or order-level data → enables order-flow and
   manipulation tests, and a proper circuit-breaker flag.
3. A directional signal with all-in cost data (spread + CNS carry) → could
   move H7/H10 from "informational" to "conditional tradability".
4. Full-market or cross-exchange replication → could move the tier-local
   result to a market-wide claim (or falsify it).
5. A source/licence upgrade for tier1 OHLCV or the NEPSE index → changes the
   deposit/redistribution status, not the estimates.

Any such change must be registered as a **new experiment row** (DC20), never a
silent edit to a frozen artifact. The v1 `docs/limitations.md` remains the
frozen record; this file is the living v2 copy.
