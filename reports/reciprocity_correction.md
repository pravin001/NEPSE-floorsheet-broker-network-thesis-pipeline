# Reciprocity-volume correction — v2.1.0

**Status:** executed; corrected results are primary.
**Release:** `v2.1.0-reciprocity-correction`.
**Supersedes:** the `reciprocity_volume` feature and every result that depends
on it in `v2.0.2-prewrite` (tag `v2.0.2-prewrite`, commit `499f8c2`).
**Preserved record:** `outputs/tables/superseded_v2_0_2/` (43 byte-for-byte
v2.0.2 tables + `MANIFEST.sha256`).
**Code fix:** commit `e2cc72b` on `fix/reciprocity-correction`.

This report records one defect, the exact code change, why a full rerun was
required, and every result that moved. It also records what did **not** move.
No tag was moved and no v2.0.2 file was overwritten in place.

---

## 1 · The defect

`reciprocity_volume` is the share of directed edge volume that flows on
bidirectional broker pairs. The frozen feature dictionary and the analysis plan
define it as

```
2 * sum_{unordered i<j} min(w_ij, w_ji) / sum(all edge weights)
```

The pre-correction implementation (`3a00dea:src/nepsemsc/network/metrics.py`)
was

```python
matched = 0.0
for u, v, d in G.edges(data=True):
    w_ij = d.get("weight", 1.0)
    if G.has_edge(v, u):
        matched += min(w_ij, G[v][u].get("weight", 1.0))
return 2.0 * matched / tot
```

That loop visits **both** directed edges of every reciprocal pair, so the
minimum is added twice; the final `2.0 *` then doubles it again. It also treats
a self-loop `(u, u)` as reciprocal, because `G.has_edge(u, u)` is true.

With `P = sum_{unordered pairs} min(w_ij, w_ji)`, `L = self-loop volume` and
`T = total volume`, the old code computed

```
old = (4P + 2L) / T = 2 * (2P/T + L/T) = 2 * (corrected + self_loop_share)
```

The identity was checked on all **233,706** `(symbol, date)` rows from the
preserved pre-fix parquet:

| check | value |
|---|---:|
| max absolute error of `old − 2·(corrected + self_loop_share)` | `2.22e-16` |
| rows within `1e-12` | `233,706 / 233,706` (100%) |

Consequences in the v2.0.2 feature:

| statistic | old (v2.0.2) | corrected (v2.1.0) |
|---|---:|---:|
| mean | 0.13799 | 0.03212 |
| median | 0.08333 | 0.01210 |
| p99 | 1.0251 | 0.2164 |
| max | **2.0** | **1.0** |
| share > 1.0 | **1.031%** (2,410 rows) | **0%** |

A share above 1.0 is impossible under the declared definition. The old metric
could reach 2.0 because it mixed in the self-loop share and could count a
two-broker symmetric graph as 4× the matched flow.

---

## 2 · The correction

```python
matched = 0.0
seen = set()
for u, v, d in G.edges(data=True):
    if u == v:
        continue                      # self-loop: denominator only
    if (v, u) in seen:
        continue                      # pair already counted
    seen.add((u, v))
    if G.has_edge(v, u):
        matched += min(d.get("weight", 1.0),
                       G[v][u].get("weight", 1.0))
return 2.0 * matched / tot
```

Each unordered pair is counted exactly once. Self-loop volume stays in the
denominator (so the measure remains a share of all volume) but is excluded from
the numerator, because a broker trading with itself is not a reciprocal broker
pair.

`tests/test_network_metrics.py` pins the definition on hand-built graphs:
perfect two-broker symmetry returns 1.0, a one-way pair returns 0.0, a self-loop
returns 0.0 when it is the only edge, and a mixed graph matches a hand-computed
ratio. The correction plus the existing graph tests passed 15/15 before the
rerun.

No other network metric was touched. `density`, `degree_extremes`,
`max_betweenness` and the Borgatti–Everett core measure are unchanged.

---

## 3 · Why the whole pipeline was rerun

It is tempting to argue that a factor-of-two error is inferentially neutral
because every regression standardises the feature with TRAIN-fold constants.
That argument is only half right.

* The **factor 2** in `old = 2·(corrected + self_loop_share)` is neutral under
  z-scoring: `z(2X) = z(X)`.
* The **additive self-loop term** is not neutral. It changes the cross-sectional
  ranking of symbol-sessions, so it changes which observations receive which
  standardised values.

The two features are far from a constant multiple:

| comparison | value |
|---|---:|
| Pearson correlation, old vs corrected | 0.457 |
| Spearman correlation, old vs corrected | 0.752 |
| old / corrected ratio, median | 3.00 |
| old / corrected ratio, 10th–90th percentile | 2.18–10.60 |

The corrected feature also correlates strongly with network size:

| pair | Spearman |
|---|---:|
| corrected reciprocity vs `n_edges` | **0.833** |
| corrected reciprocity vs `n_nodes` | **0.765** |
| corrected reciprocity vs `self_loop_volume_ratio` | 0.412 |
| corrected reciprocity vs `density` | 0.240 |

This is a new limitation, not a coding defect: on a given day a larger active
broker set mechanically raises the chance of two-way pairs. The model keeps the
log-volume and market controls and the symbol/date fixed effects, but it does
not partial out network size directly. The thesis must not read the
reciprocity coefficient as a pure "reciprocity" effect independent of network
size.

Because the feature enters the Isolation Forest as an input, the anomaly score
also changed (Pearson 0.953, Spearman 0.924 against the old score). Every
artifact downstream of either the reciprocity feature or the anomaly score was
therefore rebuilt from raw archives with

```bash
nepse-msc/bin/python scripts/run_stage6_rebuild.py --clean
```

The rebuild completed **21/21 steps, exit 0**, in **4,209.8 s (70.2 min)**.
`data/raw/` was untouched. The slowest steps were `daily_features`
(3,207.1 s), `v2_stage3` (769.2 s) and `v2_stage4` (90.0 s).

---

## 4 · What changed

### 4.1 The ten-test grid

`bp` is basis points per 1 TRAIN-fold standard deviation. `BH` is the
Benjamini–Hochberg adjusted p over the family of ten; `RW` is the Romano–Wolf
step-down p (B = 999).

| H | old β | new β | old DK p | new DK p | old BH q | new BH q | old RW p | new RW p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| H1 | −1.557 | −1.557 | .4306 | .4306 | .6094 | .6094 | .915 | .918 |
| H2 | −1.491 | −1.494 | .5753 | .5945 | .6392 | .6605 | .915 | .918 |
| H3 | +0.957 | +0.178 | .7501 | .9531 | .7501 | .9531 | .915 | .959 |
| H4 | +7.510 | +7.510 | .0275 | .0275 | .0689 | .0689 | .159 | .152 |
| H5 | −1.856 | −1.856 | .4875 | .4875 | .6094 | .6094 | .915 | .918 |
| **H6** | **−10.939** | **−22.948** | **.0197** | **.0048** | **.0689** | **.0239** | **.120** | **.031** |
| H7 | +3.952 | +3.952 | .0274 | .0274 | .0689 | .0689 | .159 | .152 |
| H8 | −4.471 | −4.471 | .0459 | .0459 | .0918 | .0918 | .203 | .199 |
| H9 | +1.817 | +1.817 | .4587 | .4587 | .6094 | .6094 | .915 | .918 |
| **H10** | **+9.492** | **+20.642** | **.0138** | **.0014** | **.0689** | **.0136** | **.081** | **.012** |

No hypothesis changed sign. No hypothesis crossed the BH gate in either
direction: the BH-passing set remains `{H4, H6, H7, H8, H10}`. The RW family now
has **two** survivors instead of one.

### 4.2 The canonical classification

| H | v2.0.2 label | v2.1.0 label | reason |
|---|---|---|---|
| H1 | `NULL_POWERED` | `NULL_POWERED` | unchanged |
| H2 | `NULL_POWERED` | `NULL_POWERED` | unchanged |
| H3 | `NULL_POWERED` | `NULL_POWERED` | unchanged |
| H4 | `EXPLORATORY_POST_HOC` | `EXPLORATORY_POST_HOC` | opposite sign to pre-declaration |
| H5 | `NULL_POWERED` | `NULL_POWERED` | unchanged |
| **H6** | `NULL_FRAGILE` | **`HEADLINE_ROBUST`** | RW .031, STRONG concordance, liquidity + EGARCH pass |
| H7 | `NULL_FRAGILE` | `NULL_FRAGILE` | RW .152 |
| H8 | `NULL_FRAGILE` | `NULL_FRAGILE` | two registered robustness failures |
| H9 | `NULL_POWERED` | `NULL_POWERED` | unchanged |
| **H10** | `HEADLINE_MODERATE` | **`HEADLINE_MODERATE`** | RW .012, MODERATE concordance, liquidity + EGARCH pass |

The composition rule was not changed. The corrected inputs now produce a
different output: H6 clears every gate it previously failed, and H10 remains
capped at `HEADLINE_MODERATE` by Fama–MacBeth.

### 4.3 H10 — the declared headline

| quantity | v2.0.2 | v2.1.0 |
|---|---:|---:|
| β (bp per 1 TRAIN-SD) | +9.492266 | **+20.641998** |
| DK p | .0137545 | **.001362** |
| DC-v2 p | .0028189 | **< 1e-4** |
| FM p | .289610 | **.4901** |
| WB p | .009 | **.004** |
| RW p | .081 | **.012** |
| SE concordance | MODERATE (3/4) | MODERATE (3/4) |
| liquidity-controlled β (p) | +9.586 (.0117) | **+19.658 (.0021)** |
| EGARCH p (sign match) | .0383 (yes) | **.0497 (yes)** |
| quantile τ=.10 → .90 | +3.08 → +18.70 | **+4.84 → +34.64** |
| τ90/τ10 ratio | 6.06 | **7.16** |
| tail label | BOTH_TAILS (INCREASING) | BOTH_TAILS (INCREASING) |
| 1-SD effect vs 30–50 bp floor | 3.16–5.27× below | **1.45–2.42× below** |

The point estimate roughly doubles and the DK/RW evidence strengthens, but
Fama–MacBeth remains non-significant and is now further from the threshold
(.4901 vs .2896). The label therefore stays `HEADLINE_MODERATE`. The economic
conclusion is unchanged in kind: even the strengthened effect is below the
declared round-trip explicit-cost floor at 1 SD.

### 4.4 H6 — the new robust headline

| quantity | v2.0.2 | v2.1.0 |
|---|---:|---:|
| β (bp per 1 TRAIN-SD) | −10.938552 | **−22.947642** |
| DK p | .0197106 | **.004787** |
| DC-v2 p | .0021170 | **< 1e-4** |
| FM p | .540252 | **.0028** |
| WB p | .002 | **.001** |
| RW p | .120 | **.031** |
| SE concordance | MODERATE (3/4) | **STRONG (4/4)** |
| liquidity-controlled β (p) | −10.989 (.0187) | **−23.182 (.0043)** |
| EGARCH p (sign match) | .0204 (yes) | **.0016 (yes)** |
| quantile τ=.10 → .90 | +12.99 → +0.55 (LOWER_TAIL) | **−21.87 → −3.63 (BOTH_TAILS)** |

H6's pre-declared direction is **ambiguous**, so a significant negative estimate
is not an opposite-sign failure. With four of four estimators significant at
p < .10, Stage 2 records STRONG concordance; liquidity and EGARCH both pass;
the composition rule therefore returns `HEADLINE_ROBUST`.

This does **not** mean H6 survives every robustness variant. See §7.

### 4.5 H2 and H3 — anomaly-score drift

The Isolation Forest is fitted on network features, so correcting reciprocity
changes the scores. The scores remain highly correlated with the old ones
(Pearson 0.953, Spearman 0.924), and both anomaly hypotheses remain null:

| H | old β | new β | old DK p | new DK p | status |
|---|---:|---:|---:|---:|---|
| H2 | −1.491 | −1.494 | .5753 | .5945 | null |
| H3 | +0.957 | +0.178 | .7501 | .9531 | null |

H3's coefficient shrinks toward zero; it was already non-significant. Neither
row passes BH, neither changes label, and neither enters any headline.

### 4.6 The event sample changed

The Isolation Forest score also defines the anomaly-event flag. The corrected
score produces **666 events on 392 dates**, not 686 on 393. All event artifacts
were rebuilt, and the sample label is now `all_666` /
`illiquid_16_appendix`.

| quantity | v2.0.2 (686) | v2.1.0 (666) |
|---|---:|---:|
| mean CAR, v1 method | +12.861 bp | **+19.326 bp** |
| mean-CAR t / p | 0.570 / .5690 | **0.839 / .4018** |
| BMP t / p | 1.175 / .2404 | **1.339 / .1809** |
| Corrado rank z / p | 3.158 / .00159 | **3.481 / .000499** |
| date-clustered mean p | .4740 | **.2363** |
| date-clustered rank p | .0120 | **.0030** |
| market-adjusted mean | −73.41 bp (.00051) | **−75.21 bp (.00050)** |
| illiquid appendix | 16 events, −244.77 bp (.00183) | **16 events, −227.39 bp (.00329)** |

The mean-based tests remain null. The rank test remains positive and is
stronger, but it is still a date-clustered descriptive statistic and an upper
bound on significance because many events share dates. No event-based story is
promoted.

### 4.7 The placebo-outcome test became more adverse

`reciprocity` predicts **past** absolute return more strongly than forward
absolute return:

| outcome | v2.0.2 | v2.1.0 |
|---|---:|---:|
| forward `abs_ret_fwd1` | +9.492 bp | +20.642 bp |
| past `abs_ret_lag1` | +19.69 bp (p 6.9e-5) | **+44.78 bp (p 8.7e-10)** |
| ratio backward / forward | 2.07 | **2.17** |

The persistence/volatility channel is therefore not resolved by the
correction; it is strengthened. `HEADLINE_ROBUST` for H6 and
`HEADLINE_MODERATE` for H10 describe the pre-declared composition rule, not a
claim that the association is a clean forward-looking signal. The thesis must
state this in the same paragraph as the headline.

### 4.8 Robustness battery

The five headline tests (H4, H6, H7, H8, H10) were re-run across the declared
variants. BH pass by variant:

| variant | BH-passing headlines | notes |
|---|---|---|
| base t+1 | H4, H6, H7, H8, H10 | 5/5 |
| t+2 | none | 0/5 |
| t+3 | H6, H7 | 2/5 (H6 new) |
| t+5 | H6, H7 | 2/5 (H6 new) |
| drop bubble (2023+) | H4, H6, H7, H10 | H8 fails (p .3405) |
| leave-one-stock-out | all five sign-stable 12/12 | H6/H10 p<.10 in 12/12 |
| external top-5 (ranks 11–15) | none | H10 +16.44 bp, raw p .0539, 0/5 BH |

At longer horizons H6 strengthens sharply (−40.37 bp at t+3, −55.73 bp at t+5)
and becomes BH-significant; H10 remains positive but loses BH significance. The
external tier still fails for every headline.

This is the main interpretive tension in v2.1.0: the label `HEADLINE_ROBUST`
is earned on the pre-declared Stage-1/2/3 gates, while the later robustness
battery is mixed. The label is not a claim of universal robustness, and the
thesis must show the battery.

### 4.9 Economics, subgroups, specification curve

**Cost floor.** The cost-benefit table is unchanged in method and now reads the
rebuilt grid:

| H | effect (bp/SD) | multiple below 30–50 bp floor | tradable at 1 SD |
|---|---:|---:|---|
| H7 | +3.952 | 7.59–12.65× | no |
| H10 | +20.642 | **1.45–2.42×** | no |
| H4 | +7.510 | 3.99–6.66× | no |

**Subgroups.** The pre-declared subgroup grid (H4/H7/H8/H10) now contains two
Bonferroni survivors, both for H10:

| split | group | β (bp) | raw p | Bonferroni p |
|---|---|---:|---:|---:|
| size | small | +26.791 | .0079 | **.0473** |
| turnover tier | bottom-7 | +22.715 | .0031 | **.0183** |

The interactions are not significant (size interaction p .319; tier
interaction p .152), and no H4/H7/H8 cell survives Bonferroni. The subgroup
grid is descriptive and remains so; a survivor is not a new headline and was
not added to the composition rule.

**Specification curve (H7).** The H7 curve is unaffected by the correction:
144 declared specs, median +1.235 bp, 39.6% of specs with a CI excluding zero.
The H7 inputs did not change.

### 4.10 Collinearity audit

The corrected feature is less collinear with the other regressors than the old
one. VIF max is now **2.05** (`anomaly_score_z`), not 2.38
(`reciprocity_z`). No VIF > 5 and no |r| > 0.7 flag fires, so the declared
drop-sensitivity run is not required.

---

## 5 · What did not change

The correction is surgical. The following hypotheses do not use reciprocity or
the anomaly score, and their regression rows reproduce the v2.0.2 values to
machine precision:

| H | feature | old β | new β | max relative difference |
|---|---|---:|---:|---:|
| H1 | self-loop ratio | −1.556594 | −1.556594 | 0 |
| H4 | buyer HHI | +7.509961 | +7.509961 | 0 |
| H5 | buyer HHI | −1.856088 | −1.856088 | 0 |
| H7 | end-of-day concentration | +3.952373 | +3.952373 | 0 |
| H8 | end-of-day concentration | −4.470947 | −4.470947 | 0 |
| H9 | self-loop ratio | +1.817473 | +1.817473 | 0 |

`tests/test_freeze.py::test_correction_invariance_for_untouched_features`
enforces this on `bp`, `p_dk` and `beta_dc` at `abs=1e-12`.

The panel shape, design, controls, fixed effects, standard errors, MDE formula,
BH family, RW family and composition rule are unchanged. The sample remains
7,116 rows, 723 dates, 12 symbols, effective N 6,383. The 30–50 bp cost floor,
the event-study window, the quantile taus and the subgroup splits are unchanged.
No new hypothesis, regression, robustness variant or supervised prediction
model was added.

The following artifacts are also unchanged because they do not use either
corrected input: the universe selection, corpus audit counts, OHLCV table,
volume reconciliation, broker-persistence tables, broker-level monthly panel,
H7 specification curve, liquidity proxy summary, EGARCH fit accounting and the
declared design tables.

---

## 6 · Interpretation rules for the thesis

1. **Do not double-count H6 and H10 as independent evidence.** They are the
   same feature (reciprocity) predicting two outcomes: the signed return level
   (H6, negative) and the absolute return (H10, positive). A single construct
   with two faces is weaker evidence than two unrelated headlines.
2. **Report the persistence/volatility caveat with the headline.** Reciprocity
   predicts past |return| at +44.78 bp, more than twice its forward association.
   Part of both headlines is a volatility-persistence channel.
3. **Respect the label semantics.** `HEADLINE_ROBUST` is the output of the
   pre-declared Stage-1/2/3 composition rule. It is not a claim that the effect
   survives every later robustness variant. Show the battery (§4.8).
4. **Do not read reciprocity as network-size-free.** The corrected feature
   correlates .833 with `n_edges` and .765 with `n_nodes`. The design controls
   for log volume, market return, symbol and date, not for network size.
5. **Do not call either effect tradable.** H10 is 1.45–2.42× below the declared
   cost floor at 1 SD; H6 is a negative return-level effect and the long-only
   implementation is not specified. Neither is a net-of-cost strategy.
6. **Do not treat the subgroup Bonferroni survivors as new headlines.** They
   are descriptive cells in a separate family, and the interactions are null.
7. **Do not quote v2.0.2 numbers as current.** They remain available for audit
   in `outputs/tables/superseded_v2_0_2/`; current numbers are the live
   `outputs/tables/` files.

---

## 7 · Reproduction and audit trail

```bash
# 1. metric fix + unit tests
git show e2cc72b -- src/nepsemsc/network/metrics.py tests/test_network_metrics.py
nepse-msc/bin/python -m pytest tests/test_network_metrics.py -q

# 2. full clean rebuild (deletes only data/processed + data/duckdb)
nepse-msc/bin/python scripts/run_stage6_rebuild.py --clean

# 3. audit
nepse-msc/bin/python -m pytest tests notebooks/*_*.ipynb --nbmake
nepse-msc/bin/python scripts/audit_register_v2.py
nepse-msc/bin/python scripts/audit_chapter_map.py

# 4. deposit archive (derived-only)
nepse-msc/bin/python scripts/build_deposit_archive.py
nepse-msc/bin/python scripts/write_deposit_preflight.py
```

Evidence:

| item | path |
|---|---|
| corrected metric | `src/nepsemsc/network/metrics.py` |
| unit tests | `tests/test_network_metrics.py` |
| corrected grid | `outputs/tables/hypothesis_grid_results.csv` |
| governance labels | `outputs/tables/hypothesis_grid_results_v2.csv` |
| final set | `outputs/tables/v2_final_headline_set.csv` |
| RW family | `outputs/tables/hypothesis_grid_results_rw.csv` |
| placebo outcome | `outputs/tables/placebo_outcome_test.csv` |
| event study | `outputs/tables/event_study_upgraded.csv` |
| robustness | `outputs/tables/robustness_headline_survival.csv` |
| economics | `outputs/tables/economic_magnitude.csv` |
| clean rebuild log | `outputs/logs/v2_stage6_rebuild.log` |
| timings | `outputs/logs/v2_stage6_rebuild_timings.csv` |
| preserved v2.0.2 tables | `outputs/tables/superseded_v2_0_2/` |
| register row | `docs/experiment_register.md` EXP-0015 |
| deviation row | `docs/analysis_deviations.md` #45 |

The v2.0.2 archive (`d222ab1a…`, 307 files, 78/78 tables hash-aligned) is not
rewritten. The new deposit archive is `v2.1.0` and is built from this tree.

---

## 8 · Disclosure

The defect was found in review, the metric fix and the mechanical rebuild were
implemented with AI assistance under the author's direction, and every reported
number is traceable to the artifacts in §7. The author remains responsible for
the interpretation and for the thesis prose.
