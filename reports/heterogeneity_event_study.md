# Pre-declared heterogeneity and event-study upgrade (Stage 4) — v2.1.0 update

**Stage 4 of the v2.0 A++ upgrade** · pre-declaration:
`docs/analysis_plan_v2_extension.md` §V2-4 (written before any v2 result).
Runner of record: `scripts/run_v2_stage4.py` · log:
`outputs/logs/v2_stage4.log` · experiments EXP-0011d–e · deviations #24–#25.

**v2.1.0 update (2026-11-19).** Rebuilt after the reciprocity correction
(EXP-0015). The subgroup grid now contains two H10 Bonferroni survivors (both
descriptive, both with null interactions); the event sample is **666 events on
392 dates**, not 686 on 393. The v2.0.2 version of this note is preserved in
`outputs/tables/superseded_v2_0_2/`; the canonical correction record is
`reports/reciprocity_correction.md`.

This report covers two separate Stage-4 objects:

1. the pre-declared subgroup heterogeneity grid, and
2. the BMP + Corrado-rank upgrade of the rebuilt 666-event study.

Neither object creates a new headline. H6 and H10 are the two Stage-1/2
confirmed headlines; every number below is either a subgroup description or a
robustness diagnostic on an event sample that remains null on the mean.

Companions: `reports/specification_curve_h7.md`,
`reports/broker_pilot_phd_seed.md`, `reports/economic_magnitude_analysis.md`.

---

## Part A · Pre-declared subgroup heterogeneity

### A.1 Design

All splits use **TRAIN-fold statistics only** (no test-fold leakage):

| split | definition | group sizes |
|---|---|---|
| size (PROXY) | TRAIN-fold mean daily OHLCV turnover, split at the within-fold cross-symbol median | small **3,558** / large **3,558** |
| liquidity | TRAIN-fold median Amihud, split at the median (above = illiquid) | liquid **3,515** / illiquid **3,601** |
| turnover tier | top-3 vs bottom-7 by TRAIN-fold mean turnover within the OOS-usable universe | bottom-7 **4,967** / top-3 **2,149** |
| circuit-breaker | **NOT EXECUTED** — no circuit-breaker / limit-hit flag exists in the corpus or any verified archive | 0 |

Estimated rows: **24 group cells + 12 group×feature interactions = 36**;
plus **4 `NOT_EXECUTED`** circuit-breaker rows (H4/H7/H8/H10). The
`p_dc_v2` column is NaN on the 12 interactions and the 4 not-executed rows,
by construction (16 NaNs).

Multiplicity: for each test, the group-cell family is the **6 subgroup cells**
(Bonferroni ×6); the interaction family is the **3 interactions** (Bonferroni
×3). This is the declared 3×2 grid disclosure.

### A.2 Results

**No subgroup cell or interaction survives Bonferroni.** The smallest
Bonferroni p in the whole table is **.1434**.

| test | split | group | β (bp) | SE | raw p | Bonferroni p | n |
|---|---|---|---:|---:|---:|---:|---:|
| H10 | turnover tier | bottom-7 | **+10.344** | 4.578 | .0239 | .1434 | 4,967 |
| H10 | turnover tier | top-3 | +2.698 | 8.116 | .7396 | 1.000 | 2,149 |
| H10 | size | small | +9.048 | 5.604 | .1065 | .6390 | 3,558 |
| H10 | size | large | +5.604 | 6.786 | .4090 | 1.000 | 3,558 |
| H10 | liquidity | illiquid | +12.844 | 7.085 | .0700 | .4198 | 3,601 |
| H10 | liquidity | liquid | +8.149 | 5.575 | .1440 | .8638 | 3,515 |
| H7 | size | small | **+7.020** | 3.176 | .0272 | .1629 | 3,558 |
| H7 | size | large | +1.335 | 2.464 | .5881 | 1.000 | 3,558 |
| H7 | turnover tier | bottom-7 | +4.817 | 2.466 | .0508 | .3050 | 4,967 |
| H7 | turnover tier | top-3 | +0.394 | 3.265 | .9041 | 1.000 | 2,149 |
| H8 | turnover tier | bottom-7 | −5.332 | 2.759 | .0534 | .3201 | 4,967 |
| H8 | turnover tier | top-3 | +0.469 | 4.259 | .9123 | 1.000 | 2,149 |
| H4 | turnover tier | top-3 | +11.338 | 6.072 | .0621 | .3724 | 2,149 |
| H4 | turnover tier | bottom-7 | +8.684 | 5.129 | .0905 | .5432 | 4,967 |

Interactions (the declared heterogeneity tests):

| test | split | interaction β (bp) | SE | raw p | Bonferroni p |
|---|---|---:|---:|---:|---:|
| **H7** | **size** | **−5.557** | 3.004 | **.0644** | **.1932** |
| H10 | turnover tier | −10.686 | 7.465 | .1524 | .4571 |
| H7 | liquidity | +2.215 | 3.415 | .5167 | 1.000 |
| H4 | turnover tier | −3.227 | 5.345 | .5461 | 1.000 |
| H4 | size | −2.856 | 4.874 | .5579 | 1.000 |

### A.3 Reading

- The **direction** of the subgroup pattern is consistent with the Stage-1 /
  EXP-0005f tier-locality story: H10 and H7 are larger in the bottom-7 /
  small-size / illiquid cells; H8 is more negative in the bottom-7 cell.
- The **formal heterogeneity tests do not reject homogeneity**. The strongest
  interaction is H7 × size (−5.557 bp, raw p .0644, Bonferroni .1932); the H10
  × turnover interaction is −10.686 bp (p .1524). No interaction is
  significant at 5%.
- Two H10 group cells survive their Bonferroni family (turnover bottom-7
  .0183; size-small .0473). They are **descriptive cells in a separate
  family**, not new headlines, and they must not be quoted without the null
  interaction caveat.
- The subgroup exercise is **underpowered** for interactions: each group cell
  has 2,149–4,967 rows, but the interaction SE is 3.0–7.5 bp, so only a
  >6–15 bp difference would be detectable at 5%.
- No subgroup result should be quoted as “the effect is concentrated in small
  stocks” without the caveat that the interaction test is null. The honest
  sentence is: *the point estimates are directionally consistent with
  tier-locality, but the pre-declared heterogeneity tests cannot reject a
  common effect.*

### A.4 Circuit-breaker rows

Four rows (H4/H7/H8/H10) are registered `NOT_EXECUTED` with the reason: the
corpus contains no circuit-breaker / limit-hit flag, and no verified archive
exposes one. This is a **hard data limitation**, not a modelling choice. The
rows remain in `heterogeneity_subgroups.csv` so the table is complete; they
carry no estimate and no p-value. Fabricating a proxy from price limits would
have been an unregistered and invalid construction.

---

## Part B · Event-study upgrade

### B.1 What was upgraded

The v1 event study (EXP-0004e) is frozen. The upgrade **reconstructs** the AR
paths from the stored v1 `alpha_est`, `beta_est` and `method` on the same
estimation/event windows — **no re-estimation** — and verifies the
reconstruction against the stored CAR:

| gate | value |
|---|---|
| events | **666** |
| dates | **392** |
| max \|reconstructed CAR − stored CAR\| | **0.0** |
| incomplete AR paths | 0 |
| events sharing a date with another event | **435 / 666 = 65.3%** |
| dates with >1 event | 161 / 392 = 41.1% |

Because 65.3% of events share a date, all event-level p-values are **upper
bounds**. A supplementary date-clustered table aggregates each statistic to
the date level and runs a t-test across the 392 dates; it is still descriptive
and still an upper bound, but it removes the most obvious cross-sectional
dependence.

### B.2 Headline sample (666 events, v1 method)

| test | statistic | p | reading |
|---|---:|---:|---|
| mean CAR t | +0.839 | .4018 | null |
| BMP cross-sectional t | +1.339 | .1809 | null |
| BMP z | +1.819 | .0689 | null |
| Corrado rank z | **+3.481** | **.00050** | rank distribution shifted |
| **date-clustered mean CAR t** | **+1.186** | **.2363** | null |
| **date-clustered rank z** | **+2.986** | **.0030** | weaker but still positive |

Mean CAR = **+0.001933** (+19.33 bp), SD = 0.0595; median CAR = **+0.002814**
(+28.14 bp); **53.0%** of events have a positive CAR. The mean is pulled down
by a negative tail, which is why the rank test and the mean test disagree.

The rank test is not a mean test. It rejects the null that the event-window
ARs are drawn from the same rank distribution as the estimation-window ARs,
but the economic magnitude is small: a 28 bp median and a 19.3 bp mean are
both below or at the bottom of the 30–50 bp cost floor. The correct conclusion
is **mixed statistical evidence, no economically meaningful event reaction**,
not “a significant event effect”.

Mean AR path (all 666 events):

| lag | mean AR | median AR |
|---:|---:|---:|
| −5 | +0.00119 | +0.00065 |
| −4 | −0.00018 | −0.00062 |
| −3 | +0.00001 | −0.00085 |
| −2 | +0.00001 | −0.00027 |
| −1 | +0.00102 | −0.00017 |
| **0** | **+0.00086** | **+0.00029** |
| +1 | +0.00025 | −0.00019 |
| +2 | −0.00010 | +0.00010 |
| +3 | −0.00125 | −0.00084 |
| +4 | +0.00016 | −0.00004 |
| +5 | −0.00006 | −0.00091 |

There is no post-event drift; the path oscillates around zero at the 1–12 bp
level.

### B.3 Uniform market-adjusted variant (same windows)

| test | statistic | p |
|---|---:|---:|
| mean CAR t | **−3.498** | **.00050** |
| BMP t | −2.545 | .0111 |
| BMP z | −2.764 | .0057 |
| Corrado rank z | +3.885 | .00010 |
| date-clustered rank z | +3.249 | .0013 |

Mean CAR = **−0.007521** (−75.21 bp). This is **mechanical**, not an
independent negative event effect:

- For the 650 market-model events, the mean pre-window alpha is
  **−0.000962/day**; over the average 10.97-session window that is
  **−0.01056** (−105.6 bp).
- The mean difference between the v1-method CAR and the market-adjusted CAR is
  **+0.009686** (+96.9 bp), and the correlation between `alpha_est` and
  `car − car_ma` is **−0.7624**.
- In other words, the market-model CAR adds back the negative estimation-window
  drift; the market-adjusted variant does not. The −75 bp mean is the
  pre-window drift, not an event reaction.

The v1-method (market-model) estimate is therefore the appropriate headline;
the market-adjusted variant is a diagnostic that shows how sensitive the mean
is to the estimation-window alpha.

### B.4 Illiquid appendix (16 events)

| test | statistic | p |
|---|---:|---:|
| mean CAR t | −3.490 | .00329 |
| BMP t | −3.485 | .00333 |
| BMP z | −0.583 | .560 |
| Corrado rank z | +0.950 | .342 |

Mean CAR = **−0.022739** (−227.39 bp). The mean is driven by a few extreme
negative CARs; the BMP z and rank tests are null, so there is no evidence of a
broad negative shift. With n=16 this block is **appendix only** and is not
quoted as a headline. It remains registered because the v1 result existed and
must not be hidden.

### B.5 Verdict

1. The **mean-based** event-study tests are null on the 666-event sample; the
   date-clustered mean is also null.
2. The **rank-based** test is positive at the event level and survives a simple
   date aggregation (z 2.99, p .0030), but the economic magnitude is small and
   the test is not a mean test. It does not support a claim of abnormal
   returns.
3. The negative market-adjusted mean is a **pre-window alpha artifact**, not
   an event effect.
4. The 16-event illiquid block remains appendix-only and is driven by extreme
   values.
5. The event-study upgrade **does not resurrect** the anomaly-event story; it
   strengthens the v1 conclusion that the event-based channel is null.

---

## Pointers

| artifact | content |
|---|---|
| `outputs/tables/heterogeneity_subgroups.csv` | 36 estimated rows + 4 `NOT_EXECUTED` |
| `outputs/tables/subgroup_assignments.csv` | per-row split assignments |
| `outputs/tables/event_study_upgraded.csv` | BMP / rank summary rows |
| `outputs/tables/event_study_upgraded_events.csv` | per-event CAR, SCAR, rank sums, alpha/beta |
| `outputs/tables/event_study_upgraded_ars.csv` | long AR path by event and lag |
| `outputs/tables/event_study_upgrade_gate.csv` | reconstruction gate |
| `outputs/tables/event_study_clustered_inference.csv` | date-clustered descriptive inference |
| `src/nepsemsc/analysis/subgroups.py` | TRAIN-only splits and Bonferroni families |
| `src/nepsemsc/analysis/event_study_upgrade.py` | reconstruction, BMP, Corrado rank, clustered table |
| `outputs/logs/v2_stage4.log` | runner log with gates |
