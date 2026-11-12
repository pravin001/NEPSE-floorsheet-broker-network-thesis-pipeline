# H7 specification curve (Stage 4)

**Stage 4 of the v2.0 A++ upgrade** · pre-declaration:
`docs/analysis_plan_v2_extension.md` §V2-4 (written before any v2 result).
Frozen v1 numbers are untouched; every table below is a **new** v2 artifact.
Runner of record: `scripts/run_v2_stage4.py` · log:
`outputs/logs/v2_stage4.log` · experiment EXP-0011b · deviations #20–#21.

Companions: `reports/exploratory_findings.md` (Stage 1),
`reports/liquidity_robustness.md` (Stage 2),
`reports/residual_based_analysis.md` (Stage 3).

> **Reading warning.** The curve is a **descriptive robustness surface**, not a
> new hypothesis test. H7 remains `NULL_FRAGILE` after the Stage-1 Romano–Wolf
> correction (`rw_p = .159`). Nothing in this curve resurrects H7; it measures
> how the frozen H7 design behaves when the declared nuisance choices move.

---

## 0 · Gates that had to pass before any curve number was accepted

| gate | result |
|---|---|
| Stage-4 panel shape | **PASS** — 7,116 rows / 723 dates / 12 symbols |
| frozen H7 base design reproduced | **PASS** — DK `+3.952373 bp`, `p = .027432` (frozen `+3.952373` / `.027432`) |
| DC-v2 base design reproduced | **PASS** — `p = .008626` (Stage-2 `p_dc_v2 = .0086`) |
| FM base design reproduced | **PASS** — `+6.670832 bp`, `p = .009449` (frozen `p_fm = .0094`) |
| WB base design reproduced | **PASS** — `p = .0220` (Stage-2 `p_wb = .0220`) |
| deterministic re-run | **PASS** — two consecutive full runs produced byte-identical outputs (SHA-256 equality) |

The base design is `DK | abs_ret | base controls | full sample | 5% EoD`.
It is one cell of the curve, not a special case added after inspection.

---

## 1 · Declared grid and the 144-vs-72 arithmetic correction

The binding plan declares five factors:

| factor | levels | count |
|---|---|---:|
| SE family | DK, DC, FM, WB | 4 |
| outcome | `abs_ret_fwd1` (H7), `ret_fwd1` (H8 direction) | 2 |
| liquidity controls | `base` (`log_volume_z` + `market_ret_loo_z`), `gamma_all` (+ Amihud, Roll, Corwin–Schultz) | 2 |
| subsample | full, bubble (year ≤ 2022), normal (year ≥ 2023) | 3 |
| EoD cutoff | 1%, 5%, 10% | 3 |

The product is **4 × 2 × 2 × 3 × 3 = 144**, not the plan's stated 72. The
statement “= 72” is consistent with dropping the outcome factor, but the outcome
was explicitly declared and both outcomes are executed. Dropping a declared
factor would have been an unregistered design change, so the full 144-cell
factorial is retained and the arithmetic slip is logged as deviation #20.

`outputs/tables/specification_curve_h7.csv` has 144 rows and 72 unique
**design** betas. DK, DC and WB reuse the same OLS point estimate (they differ
only in the standard error / p-value); FM re-estimates the cross-sectional
slopes and therefore has its own point estimate. This is why the file has 144
specifications but not 144 distinct betas.

---

## 2 · Results

### 2.1 Shape of the curve

`outputs/tables/specification_curve_h7_summary.csv`:

| group | specs | median β (bp) | mean β (bp) | min | max | range | 95% CI excludes 0 | p < .05 | share β > 0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| overall (mixed signs) | 144 | +1.235 | +0.521 | −19.280 | +17.893 | 37.173 | .396 | .354 | .542 |
| `abs_ret` (H7 direction) | 72 | **+3.952** | +5.331 | +1.254 | +17.893 | 16.639 | **.583** | .542 | **1.000** |
| `ret` (H8 direction) | 72 | −4.289 | −4.289 | −19.280 | +1.216 | 20.496 | .208 | .167 | .083 |

The overall row mixes a positive absolute-return coefficient with a negative
signed-return coefficient; it is reported for completeness but is not
interpretable as a single effect. The outcome-split rows are the object of
interest.

**The `abs_ret` median is exactly the base-design beta.** That is an ordering
coincidence, not a duplication bug: 34 specs lie below +3.952373 bp, 3 are
exactly equal (the DK/DC/WB copies of the base design), and 35 lie above. The
even-sample median therefore lands on the three tied copies. The base design is
the 12th of 18 unique DK design cells; the FM cells pull the upper half of the
distribution up.

### 2.2 Factor-level behaviour (`abs_ret`, 72 specs)

| factor | level | n | median β (bp) | 95% CI excludes 0 | p < .05 |
|---|---|---:|---:|---:|---:|
| controls | `base` | 36 | +4.088 | .583 | .528 |
| controls | `gamma_all` | 36 | +3.723 | .583 | .556 |
| subsample | bubble | 24 | +3.242 | .292 | .208 |
| subsample | full | 24 | +3.754 | **.958** | .958 |
| subsample | normal | 24 | +4.545 | .500 | .458 |
| cutoff | 1% | 24 | +3.971 | .625 | .583 |
| cutoff | 5% | 24 | +3.952 | .542 | .542 |
| cutoff | 10% | 24 | +4.068 | .583 | .500 |
| SE family | DK | 18 | +3.720 | .444 | .444 |
| SE family | DC | 18 | +3.720 | .611 | .611 |
| SE family | FM | 18 | +8.812 | .444 | .444 |
| SE family | WB | 18 | +3.720 | **.833** | .667 |

Readings:

- **Sign is completely stable** in the H7 direction: all 72 `abs_ret` specs are
  positive.
- **Significance is not uniform.** The full-sample cells are significant in
  95.8% of cases; the bubble cells in only 29.2%. The effect is strongest in the
  full sample and weakest in 2021–22.
- **Liquidity controls do not absorb the effect.** Adding Amihud, Roll and
  Corwin–Schultz moves the median by −0.37 bp; the CI-exclusion share is
  unchanged at .583.
- **Cutoff choice is not the driver.** The 1%, 5% and 10% medians are within
  0.12 bp of each other.
- **The FM point estimate is roughly twice the panel estimate** (+8.81 vs
  +3.72 median). FM is a different estimator, not merely a different SE; its
  weighting of cross-sections changes the estimand. This is not evidence for or
  against H7, only a reminder that “SE family” is an imperfect label for FM.
- **WB has the highest CI-exclusion share** (.833), while DK has the lowest
  (.444). With only 12 symbol clusters, WB is a concordance signal, not a
  superior test (Stage-2 caveat).

### 2.3 Signed-return curve (H8 direction)

The same EoD feature predicts signed returns negatively in 66 of 72 specs
(median −4.289 bp; only 6 positive cells). The 1% cutoff is the clear
exception: median −0.601 bp and **zero** CIs exclude zero. At 5% and 10% the
medians are −4.471 and −4.283 bp with CI-exclusion shares .208 and .417. This
matches the frozen v1 threshold sensitivity: H8's return effect lives in the
middle/upper EoD tail and collapses at the top 1% (EXP-0005c).

---

## 3 · Robustness ratio and figure

The plan defines the robustness ratio as `(max β − min β) / median β`.
For the H7-direction curve the range is 16.639 bp and the median is
+3.952 bp, giving **4.210**. For the signed-return curve the signed ratio is
−4.779; its absolute counterpart is **4.779**. The overall mixed-sign ratio
(30.101) is algebraically defined but economically meaningless because the
median crosses zero; it should not be quoted.

`outputs/figures/specification_curve_h7.png` shows the 144 β estimates sorted
by magnitude with 95% CI bars, coloured by SE family, plus an inclusion panel
by factor level. The base design is marked in the underlying table, not
specially highlighted in the figure.

---

## 4 · Verdict

1. The H7-direction coefficient is **positive in every declared
   specification** and significant at 5% in 54.2% of them; the full-sample
   cells are significant in 95.8%.
2. The result is **not fragile to liquidity controls, cutoff choice or SE
   family**, but it is **materially weaker in the bubble era** (29.2% CI
   exclusion) and the FM estimator gives a different magnitude.
3. The signed-return / H8 direction is negative overall but **fragile at the
   1% cutoff**, confirming the Stage-3 threshold finding.
4. This is a robustness description of an already **RW-demoted** hypothesis.
   The final classification of H7 remains `NULL_FRAGILE`; the curve supports
   “informational content”, not a headline claim.

---

## 5 · Pointers

| artifact | content |
|---|---|
| `outputs/tables/specification_curve_h7.csv` | 144 specification rows with β, SE, CI, p, n, factor labels |
| `outputs/tables/specification_curve_h7_summary.csv` | overall / outcome-split medians, ranges, CI shares, robustness ratios |
| `outputs/figures/specification_curve_h7.png` | sorted β + CI bars and factor inclusion panel |
| `outputs/logs/v2_stage4.log` | full runner log with gates and timings |
| deviation #20 | 144-vs-72 arithmetic correction and curve conventions |
| deviation #21 | effective-N conventions used alongside the curve |
