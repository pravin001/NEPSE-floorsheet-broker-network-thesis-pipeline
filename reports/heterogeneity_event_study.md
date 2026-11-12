# Pre-declared heterogeneity and event-study upgrade (Stage 4)

**Stage 4 of the v2.0 A++ upgrade** · pre-declaration:
`docs/analysis_plan_v2_extension.md` §V2-4 (written before any v2 result).
Runner of record: `scripts/run_v2_stage4.py` · log:
`outputs/logs/v2_stage4.log` · experiments EXP-0011d–e · deviations #24–#25.

This report covers two separate Stage-4 objects:

1. the pre-declared subgroup heterogeneity grid, and
2. the BMP + Corrado-rank upgrade of the frozen 686-event study.

Neither object creates a new headline. H10 remains the only Stage-1/2
confirmed headline; every number below is either a subgroup description or a
robustness diagnostic on an already-null event sample.

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
| H10 | turnover tier | −8.973 | 6.054 | .1383 | .4150 |
| H7 | liquidity | +2.215 | 3.415 | .5167 | 1.000 |
| H4 | turnover tier | −3.227 | 5.345 | .5461 | 1.000 |
| H4 | size | −2.856 | 4.874 | .5579 | 1.000 |

### A.3 Reading

- The **direction** of the subgroup pattern is consistent with the Stage-1 /
  EXP-0005f tier-locality story: H10 and H7 are larger in the bottom-7 /
  small-size / illiquid cells; H8 is more negative in the bottom-7 cell.
- The **formal heterogeneity tests do not reject homogeneity**. The strongest
  interaction is H7 × size (−5.557 bp, raw p .0644), which is not significant
  at 5% even before Bonferroni and has a Bonferroni p of .1932.
- The subgroup exercise is **underpowered** for interactions: each group cell
  has 2,149–4,967 rows, but the interaction SE is 3.0–6.1 bp, so only a
  >6–12 bp difference would be detectable at 5%.
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
| events | **686** |
| dates | **393** |
| max \|reconstructed CAR − stored CAR\| | **0.0** |
| incomplete AR paths | 0 |
| events sharing a date with another event | **468 / 686 = 68.2%** |
| dates with >1 event | 175 / 393 = 44.5% |

Because 68.2% of events share a date, all event-level p-values are **upper
bounds**. A supplementary date-clustered table aggregates each statistic to
the date level and runs a t-test across the 393 dates; it is still descriptive
and still an upper bound, but it removes the most obvious cross-sectional
dependence.

### B.2 Headline sample (686 events, v1 method)

| test | statistic | p | reading |
|---|---:|---:|---|
| mean CAR t | +0.570 | .5690 | null |
| BMP cross-sectional t | +1.175 | .2404 | null |
| BMP z | +1.580 | .1141 | null |
| Corrado rank z | **+3.158** | **.00159** | rank distribution shifted |
| **date-clustered mean CAR t** | **+0.717** | **.4740** | null |
| **date-clustered rank z** | **+2.522** | **.0120** | weaker but still positive |

Mean CAR = **+0.001286** (+12.86 bp), SD = 0.0591; median CAR = **+0.003402**
(+34.02 bp); **53.35%** of events have a positive CAR. The mean is pulled down
by a negative tail, which is why the rank test and the mean test disagree.

The rank test is not a mean test. It rejects the null that the event-window
ARs are drawn from the same rank distribution as the estimation-window ARs,
but the economic magnitude is small: a 34 bp median and a 12.9 bp mean are
both below the 30–50 bp cost floor. The correct conclusion is **mixed
statistical evidence, no economically meaningful event reaction**, not “a
significant event effect”.

Mean AR path (all 686 events):

| lag | mean AR | median AR |
|---:|---:|---:|
| −5 | +0.00118 | +0.00039 |
| −4 | −0.00041 | −0.00076 |
| −3 | −0.00002 | −0.00086 |
| −2 | +0.00000 | −0.00043 |
| −1 | +0.00068 | −0.00019 |
| **0** | **+0.00040** | **+0.00003** |
| +1 | +0.00008 | −0.00033 |
| +2 | −0.00004 | +0.00010 |
| +3 | −0.00053 | −0.00036 |
| +4 | −0.00020 | −0.00029 |
| +5 | +0.00012 | −0.00073 |

There is no post-event drift; the path oscillates around zero at the 1–5 bp
level.

### B.3 Uniform market-adjusted variant (same windows)

| test | statistic | p |
|---|---:|---:|
| mean CAR t | **−3.490** | **.000514** |
| BMP t | −2.518 | .0120 |
| BMP z | −2.725 | .00643 |
| Corrado rank z | +3.141 | .00168 |
| date-clustered rank z | +2.276 | .0234 |

Mean CAR = **−0.007341** (−73.41 bp). This is **mechanical**, not an
independent negative event effect:

- For the 670 market-model events, the mean pre-window alpha is
  **−0.000873/day**; over the average 11-session window that is
  **−0.00953** (−95.3 bp).
- The mean difference between the v1-method CAR and the market-adjusted CAR is
  **+0.008833** (+88.3 bp), and the correlation between `alpha_est` and
  `car − car_ma` is **−0.7505**.
- In other words, the market-model CAR adds back the negative estimation-window
  drift; the market-adjusted variant does not. The −73 bp mean is the
  pre-window drift, not an event reaction.

The v1-method (market-model) estimate is therefore the appropriate headline;
the market-adjusted variant is a diagnostic that shows how sensitive the mean
is to the estimation-window alpha.

### B.4 Illiquid appendix (16 events)

| test | statistic | p |
|---|---:|---:|
| mean CAR t | −3.776 | .00183 |
| BMP t | −3.763 | .00188 |
| BMP z | −0.624 | .533 |
| Corrado rank z | +0.732 | .464 |

Mean CAR = **−0.024477** (−244.77 bp). The mean is driven by a few extreme
negative CARs; the BMP z and rank tests are null, so there is no evidence of a
broad negative shift. With n=16 this block is **appendix only** and is not
quoted as a headline. It remains registered because the v1 result existed and
must not be hidden.

### B.5 Verdict

1. The **mean-based** event-study tests are null on the 686-event sample; the
   date-clustered mean is also null.
2. The **rank-based** test is positive at the event level and survives a simple
   date aggregation (z 2.52, p .012), but the economic magnitude is small and
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
