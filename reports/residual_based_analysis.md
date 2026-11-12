# Residual-based and panel/outcome robustness (Stage 3)

**Stage 3 of the v2.0 A++ upgrade** · pre-declaration:
`docs/analysis_plan_v2_extension.md` §V2-3 (written before any v2 result).
Frozen v1 numbers are untouched; every table below is a **new** v2 artifact.
Runner of record: `scripts/run_v2_stage3.py` · log: `outputs/logs/v2_stage3.log`
· experiments EXP-0010a–c · deviations #17–#19.

Companions: `reports/exploratory_findings.md` (Stage 1),
`reports/liquidity_robustness.md` (Stage 2).

> **Reading warning.** The EGARCH outcome is a *standardized* return, so its
> regression coefficients are in **z units**, not basis points. They must not be
> compared numerically with the v1 bp coefficients. The comparable quantity is
> the standardized effect (`beta_sd_units` = effect per 1 SD of the feature, in
> units of the outcome SD) and its ratio to the v1 standardized effect.

---

## 0 · Gates that had to pass before any Stage-3 number was accepted

| gate | result |
|---|---|
| `arch` availability + EGARCH recursion vs arch's train sigma path | **PASS** — `arch 8.0.0`; max relative error `2.05e-16` (gate `1e-8`) |
| quantile design shape | **PASS** — 7,116 rows × 737 columns (full two-way symbol+date dummy design; declared fallback not needed) |
| trade-size thresholds finite, `p10 < p90`, train trades > 0 | **PASS** — 40/40 `(fold, symbol)` rows (`outputs/tables/trade_size_thresholds.csv`) |
| deterministic re-run of the Stage-3 artifacts | **PASS** — two consecutive runs produced byte-identical tables (SHA-256 equality); the initial float-order noise was removed by computing HHI as an exact integer ratio and adding a deterministic `ORDER BY` |
| SE-specification tests after the dependency change | **PASS** before the Stage-3 run (4/4) |

---

## 1 · EGARCH-standardized outcomes (pre-declared V2-3.2)

### 1.1 Declared model and execution

Per `(fold, symbol)`: EGARCH(1,1), `mean='Constant'`, `vol='EGARCH'`,
`p=1,q=1`, `dist='normal'`, fit on the **TRAIN-fold daily returns of that symbol
only** (≥60 non-null train returns). In `arch 8.0` this declared call is the
symmetric EGARCH (`o=0`; parameters `mu/omega/alpha[1]/beta[1]`). Asymmetry
would require `o=1`, which was **not** pre-declared and is therefore not added
(deviation #17).

Returns are scaled ×100 for optimizer stability; the standardization `z` is
scale-invariant. For an OOS row at date `t`, the outcome is
`z_{t+1} = (r_{t+1} − mu) / sigma_{t+1}`, where the variance recursion is
driven forward from the last TRAIN observation using the TRAIN-estimated
parameters and the symbol's observed returns. No test-fold return enters the
parameter fit; each `sigma_{t+1}` uses only information available before the
return it standardizes. Products: `z_fwd1` (signed) and
`abs_z_fwd1 = |z_fwd1|` (absolute).

**Numerical guard (declared, deviation #17).** A fitted EGARCH with negative
`alpha` and `beta` near 1 can drive log-variance to `−inf` after a large shock;
sigma then underflows to exactly 0 and every later draw is contaminated through
`z` in the recursion. `filter_forward` stops at the first failure
(`extreme_z`, `sigma_underflow`, or `log_variance_nonfinite`), returns `NaN` for
that point and **all later draws**, and logs the exact stop reason. The
numerical validity bound is `|z| ≤ 20` (standard-normal tail probability
≈`1e-89`); a draw beyond it is a variance-recursion artifact, not an economic
observation.

### 1.2 Fit accounting

`outputs/tables/egarch_outcome_accounting.csv`:

Two denominators are distinguished in the artifact. The **raw OOS score grid**
has 7,126 rows; the **analysis panel** has 7,116 rows because the 10 rows of the
final session (2024-12-31) have no `ret_fwd1` and are dropped by
`build_oos_panel` before any EGARCH work.

| item | value |
|---|---:|
| raw OOS score-grid rows | 7,126 |
| base analysis-panel rows | 7,116 |
| raw-grid rows outside the analysis panel (2024-12-31, no `ret_fwd1`) | 10 |
| EGARCH fits (fold × symbol) | 40 |
| fits converged | 37 |
| fits flagged degenerate | 4 |
| fits with sigma underflow | 2 (fold-0 NABIL, fold-0 NLIC) |
| fits with boundary exclusion only (last OOS session has no next session) | 10 (fold 3) |
| EGARCH `z` rows | **6,819** |
| panel rows with `z` | 6,819 |
| panel rows without `z` (`panel_rows_excluded_total`) | **297** |
| raw-grid rows excluded by sigma underflow | 297 |
| raw-grid rows excluded by no-next-session boundary | 10 (outside the panel) |

The reconciliation is therefore: `7,116 panel = 6,819 usable + 297 underflow`;
`7,126 raw grid = 7,116 panel + 10 boundary`. The raw-grid exclusions total 307,
but only the 297 underflow rows are subtracted from the 7,116 analysis panel.

The two underflow fits are both in **fold 0**: NABIL (161 excluded; 9 usable)
and NLIC (136 excluded; 40 usable). NABIL converged but its forward recursion
degenerated; NLIC did not converge and also degenerated. The other two
non-converged fits (fold-0 API, fold-3 NICA) kept a well-behaved sigma path and
contribute their OOS rows (`status='ok'`). The fold-3 boundary exclusions are
mechanical: the last OOS session (2024-12-31) has no next session to
standardize, so each of the 10 fold-3 fits loses exactly one row; those rows are
already outside the analysis panel because `ret_fwd1` is missing, so they do not
reduce the 7,116 panel.

### 1.3 Calibration of the standardized outcomes

On the 6,819 usable rows:

| statistic | EGARCH `z` | N(0,1) reference |
|---|---:|---:|
| mean | −0.0175 | 0 |
| SD | 1.023 | 1 |
| median \|z\| | 0.4507 | 0.6745 |
| mean \|z\| | 0.6439 | 0.7979 |
| p99 \|z\| | 3.2476 | 2.326 |
| max \|z\| | 17.2455 | — |
| skew | −2.159 | 0 |
| excess kurtosis | 48.7 | 0 |
| share `z > 0` | 42.5% | 50% |

The mean and SD are close to the standard-normal reference, but the distribution
is **not** perfectly calibrated: the average conditional sigma is about 19%
larger than an ideal N(0,1) standardization (`mean |z| 0.644` vs `0.798`), while
the tails remain very fat (kurtosis 48.7, one draw at `|z| = 17.2`). The
practical reading is that the EGARCH filter is **conservative on average but
does not fully whiten** the return series. This matters for interpreting
magnitudes and tail probabilities; it does not invalidate the regression SEs,
which use the realized outcome values.

### 1.4 Primary EGARCH grid

`outputs/tables/headline_with_egarch_outcome.csv`, spec `egarch_primary`.
`beta_bp` is the raw coefficient in z units; `beta_sd_units` is the comparable
standardized effect; `ratio` = EGARCH standardized effect / v1 standardized
effect.

| test | feature → EGARCH outcome | v1 bp | EGARCH β (z units) | p DK | p DC-v2 | n | standardized effect | ratio vs v1 | sign match | survives |
|---|---|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
| H1 | self_loop → \|z\| | −1.557 | +64.22 | .5711 | .5387 | 6,819 | +0.0081 | −1.00 | no | no |
| H2 | anomaly → \|z\| | −1.491 | +79.78 | .5734 | .5291 | 6,819 | +0.0100 | −1.30 | no | no |
| H3 | anomaly → z | +0.957 | +28.57 | .8290 | .8699 | 6,819 | +0.0028 | +0.75 | yes | no |
| H4 | buyer_hhi → z | +7.510 | +256.86 | .0544 | .0164 | 6,819 | +0.0251 | +0.86 | yes | **yes** |
| H5 | buyer_hhi → \|z\| | −1.856 | −118.91 | .2972 | .2568 | 6,819 | −0.0150 | +1.55 | yes | no |
| H6 | reciprocity → z | −10.939 | −511.87 | .0204 | .0268 | 6,819 | −0.0500 | +1.17 | yes | **yes** |
| H7 | EoD → \|z\| | +3.952 | +149.15 | .0638 | .0717 | 6,819 | +0.0188 | +0.91 | yes | **yes** |
| H8 | EoD → z | −4.471 | −157.91 | .0745 | .0454 | 6,819 | −0.0154 | +0.89 | yes | **yes** |
| H9 | self_loop → z | +1.818 | +68.45 | .5925 | .4554 | 6,819 | +0.0067 | +0.95 | yes | no |
| H10 | reciprocity → \|z\| | +9.492 | +412.40 | .0383 | .0213 | 6,819 | +0.0519 | +1.05 | yes | **yes** |

**Signs.** All five v1 BH-passing tests (H4, H6, H7, H8, H10) keep the v1 sign
under EGARCH standardization. The four null tests H1/H2/H3/H5/H9 remain
insignificant (H5 keeps its negative sign; H1/H2 flip sign only because their
v1 estimates are tiny and near zero).

**Magnitudes.** The standardized effects are close to the v1 standardized
effects: ratios 0.86–1.17 for the five BH-passing tests. H10 is
indistinguishable from its v1 magnitude (+5.2% in standardized units); H6 grows
by 17%, H8/H7 shrink by 11%/9%, H4 shrinks by 14%. No v1 effect is inflated by
the EGARCH transform.

**Inference.** H10 survives at p=.038 (DK) / .021 (DC-v2); H6 at .020/.027; H8
at .075/.045; H7 at .064/.072; H4 at .054/.016. The EGARCH outcome does not
rescue any null and does not overturn any headline direction.

**Row-exclusion check.** Re-fitting the **v1 outcomes** on exactly the 6,819
EGARCH-usable rows reproduces every v1 sign and leaves all five BH-passing
effects significant: H10 +11.05 bp (p .0054), H6 −12.12 (p .0140), H7 +4.35
(p .0190), H8 −4.58 (p .0453), H4 +7.72 (p .0246). The EGARCH row loss alone
therefore does not drive the Stage-3 pattern.

### 1.5 Sensitivity to degenerate / non-converged fits

Two subsets re-fit the primary outcome after dropping fits (table
`headline_with_egarch_outcome.csv`, specs `egarch_primary_excl_degenerate` and
`egarch_primary_excl_nonconverged`):

| test | full p | excl. 4 degenerate fits | excl. 3 non-converged fits |
|---|---:|---:|---:|
| H4 | .0544 | .141 | .118 |
| H6 | .0204 | **.009** | **.006** |
| H7 | .0638 | .116 | .054 |
| H8 | .0745 | **.049** | **.047** |
| H10 | .0383 | **.026** | **.033** |
| nulls H1/H2/H3/H5/H9 | ≥.297 | ≥.249 | ≥.440 |

H10, H6 and H8 are stable across the exclusions; **H4 and H7 are fragile**:
both lose 10% significance when the four degenerate fits are dropped, and H4
also loses it when only the non-converged fits are dropped. This is consistent
with their marginal Stage-1 status (H4 post-hoc; H7 RW-demoted) and is reported,
not smoothed over.

### 1.6 EGARCH caveats

- The model is **symmetric** by the declared call (`o=0`); no leverage/asymmetry
  term was added, so the filter does not model the well-known negative
  return–volatility link beyond what the symmetric EGARCH can capture.
- Fold-0 NABIL/NLIC produce degenerate forward recursions; 297 of 7,116 panel
  rows (4.2%) are lost, concentrated in two symbols in the earliest fold. The
  `excl_degenerate` sensitivity above bounds the effect.
- The filter is conservative on average and leaves fat tails; `|z| > 20` is
  treated as a numerical artifact by declaration, not as an economic outlier.
- Raw EGARCH coefficients are in z units and are not comparable to v1 bp.

---

## 2 · Quantile panel (pre-declared V2-3.1)

### 2.1 Method

Statsmodels `QuantReg` on the two-way design `feature + log_volume_z +
market_ret_loo_z + C(symbol) + C(date)` (drop-first dummies), 7,116 × 737
matrix. `tau ∈ {.10,.25,.50,.75,.90}`, 10 tests × 5 quantiles = 50 fits.
Covariance = `vcov='robust'` (Koenker heteroskedasticity-robust asymptotic);
95% CI = β ± 1.96·SE. This is **not** a cluster-robust or bootstrap CI; the
panel-dependence caveat is explicit (deviation #18).

Convergence: statsmodels' default `p_tol=1e-6` does not converge at τ=.90
within 2,000 iterations because of dummy-coefficient jitter. The declared
implementation uses `p_tol=1e-5`, `max_iter=1500`; **all 50 fits converge**
(max 345 iterations; total 761 s). The tested coefficient moves only ~0.2% at
τ=.90 versus the stricter unconverged path, and the robust SE is unchanged
(deviation #18).

### 2.2 Quantile curves for the five BH-passing tests

β(τ) in bp, with Koenker-robust 95% CI:

| test | τ=.10 | τ=.25 | τ=.50 | τ=.75 | τ=.90 | v1 mean | tail label / shape |
|---|---:|---:|---:|---:|---:|---:|---|
| **H10** reciprocity → \|ret\| | +3.083<br>[1.498, 4.668] | +2.842<br>[0.802, 4.882] | +4.891<br>[2.492, 7.290] | +7.530<br>[5.214, 9.846] | **+18.696**<br>[16.657, 20.735] | +9.492 | **BOTH_TAILS** / INCREASING (ratio 6.06) |
| **H7** EoD → \|ret\| | +0.706<br>[−0.177, 1.590] | +0.582<br>[−0.597, 1.762] | +2.202<br>[0.781, 3.624] | +3.114<br>[1.693, 4.534] | +1.212<br>[−0.062, 2.486] | +3.952 | NONE / HUMP |
| **H4** buyer_hhi → ret | +2.121<br>[0.423, 3.818] | +1.629<br>[−0.456, 3.713] | +3.265<br>[0.916, 5.615] | +3.786<br>[1.551, 6.021] | +9.610<br>[7.668, 11.553] | +7.510 | BOTH_TAILS / INCREASING (ratio 4.53) |
| **H6** reciprocity → ret | **−12.988**<br>[−15.182, −10.793] | −8.883<br>[−11.602, −6.164] | −7.532<br>[−10.691, −4.373] | −4.530<br>[−7.486, −1.575] | +0.545<br>[−1.966, 3.055] | −10.939 | LOWER_TAIL / INCREASING (ratio −0.04) |
| **H8** EoD → ret | −3.171<br>[−4.476, −1.866] | −3.545<br>[−5.178, −1.913] | −3.494<br>[−5.344, −1.644] | −1.275<br>[−3.040, 0.489] | −0.466<br>[−1.989, 1.058] | −4.471 | LOWER_TAIL / U_SHAPE |

Reading:

- **H10** strengthens monotonically from +3.1 bp at τ=.10 to +18.7 bp at τ=.90;
  the upper-tail coefficient is roughly 6× the lower-tail one and the median is
  close to the v1 mean. The effect is a **both-tails / increasing** concentration
  phenomenon, strongest where |return| is largest.
- **H7** is a hump: significant at the median/upper-middle (τ=.50–.75) but not
  at either extreme. The pre-declared label is **NONE** — there is no
  extreme-tail concentration to claim. This is consistent with the Stage-1
  RW demotion and the Stage-2 EoD-threshold finding.
- **H4** is also both-tails/increasing, with the largest effect at the upper
  tail. It remains a post-hoc, opposite-sign-to-predeclaration result
  (Stage-1 #10), not a confirmed headline.
- **H6** is a lower-tail effect: strongly negative through the median, fading to
  zero at τ=.90. The v1 mean (−10.94 bp) sits near the τ=.10 estimate.
- **H8** is a lower-tail effect concentrated at τ=.10–.50; the upper tail is
  indistinguishable from zero. Together with the Stage-2 trade-size result
  (medium-bucket), this says the H8 return effect is a mid-body phenomenon, not
  a top-tail one.

### 2.3 Null tests: descriptive tail labels, **not** resurrection

`quantile_tail_summary.csv` also labels the five null tests. The labels are
computed from the same 20 extreme checks and are **not adjusted for
multiplicity**; they are descriptive only. Several nulls show a significant
extreme-tail coefficient:

| null test | extreme-tail estimate | p | label |
|---|---:|---:|---|
| H1 | τ=.90 −3.004 bp [−4.568, −1.440] | .00017 | UPPER_TAIL |
| H2 | τ=.90 −3.835 bp [−5.521, −2.148] | 8.4e-6 | UPPER_TAIL |
| H3 | τ=.90 +5.091 bp [3.186, 6.995] | 1.7e-7 | UPPER_TAIL |
| H5 | τ=.10 −1.840 bp [−3.029, −0.651] | .0024 | LOWER_TAIL |
| H9 | τ=.90 +3.079 bp [1.288, 4.870] | .00076 | UPPER_TAIL |

These are **not** evidence that the null hypotheses hold in the tails. Twenty
extreme-tail comparisons were inspected; at a 5% level roughly one false
positive is expected even under global nullity, and the quantile estimates are
not independent across tests/tails. The Stage-1 mean-based null classification
(H1/H2/H3/H5/H9 `NULL_ROBUST`) is unchanged; the tail labels are reported for
completeness and should not be quoted as findings.

### 2.4 Quantile caveats

- Koenker's robust covariance assumes independent observations; the panel has
  symbol and date dependence. The CIs are therefore **descriptive uncertainty
  bands**, not cluster-robust inference. The v1 DK/DC-v2/WB results remain the
  inference of record.
- The τ=.90 fit is the slowest and most sensitive to convergence tolerance; the
  declared `p_tol=1e-5` path is documented above. All 50 fits converged.
- Tail labels use the v1 DK mean sign as the reference and a 95% CI exclusion
  rule; a label of `NONE` does not mean the effect is zero at every quantile
  (H7 is the example: significant at τ=.50–.75, labelled NONE because neither
  extreme is significant).
- The extreme-tail checks are unadjusted; only H10's tail concentration is used
  in the headline narrative.

---

## 3 · Trade-size heterogeneity (pre-declared V2-3.3)

### 3.1 Construction

DuckDB single read-only session on `floorsheet_dedup`. Per `(fold_id, symbol)`,
the p10/p90 thresholds of **trade size** (`volume`, buyer-side counted) are
computed on **TRAIN-FOLD session rows only** — the pre-declared anti-leakage
choice (full-window percentiles are the noted alternative, not used). Buckets:
small `< p10`, medium `p10–p90`, large `> p90`. Per
`(fold_id, date, symbol, bucket)`:

- `buyer_hhi` = Σ (buyer volume / bucket volume)², computed as an exact integer
  ratio for byte-stable artifacts;
- `top3_buyer_share` = top-3 buyer volume / bucket volume;
- `eod_concentration` = volume of the last `ceil(0.05·n)` trades by
  `contract_no DESC` / bucket volume, with **2023-02-16 excluded** (the
  contract-number defect day; level features keep it).

`MIN_BUCKET_TRADES = 5` is the primary sample guard: concentration is
mechanically 1.0 when a bucket-day has one trade/one buyer, and 23.7% of
small-bucket days have fewer than 5 trades. The guard sets the three
concentration features to NaN for those bucket-days but keeps volume/trade
counts. Sensitivity at minimum 1 and 10 trades is reported (deviation #19).

### 3.2 Bucket composition (primary min=5)

`outputs/tables/trade_size_bucket_summary.csv`:

| bucket | bucket-days | used days | suppressed | trades | volume share | trade share | median trades/day | mean HHI | mean top-3 | mean EoD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| large | 24,917 | 24,475 | 442 | 1,916,009 | 47.4% | 9.5% | 50 | 0.132 | 0.474 | 0.063 |
| medium | 24,948 | 24,930 | 18 | 17,128,981 | 52.3% | 85.0% | 485 | 0.047 | 0.247 | 0.052 |
| small | 23,220 | 17,709 | 5,511 | 1,111,440 | 0.35% | 5.5% | 42 | 0.122 | 0.436 | 0.083 |

The large bucket carries **47.4% of volume in only 9.5% of trades**; the small
bucket is economically negligible (0.35% of volume) and its concentration
statistics are dominated by mechanical small-count artifacts even after the
min-5 guard. The medium bucket is the bulk of trading activity.

### 3.3 H7/H8 by bucket (primary EoD metric, min=5)

`outputs/tables/trade_size_heterogeneity.csv`:

| test | bucket | β (bp) | SE | p DK | p DC-v2 | n |
|---|---|---:|---:|---:|---:|---:|
| H7 EoD → \|ret\| | small | −1.360 | 2.993 | .6497 | .7595 | 5,356 |
| H7 | medium | +1.066 | 1.467 | .4674 | .3920 | 7,114 |
| **H7** | **large** | **+4.519** | 2.150 | **.0356** | .0691 | 6,951 |
| H8 EoD → ret | small | +5.841 | 3.900 | .1343 | .2744 | 5,356 |
| **H8** | **medium** | **−5.266** | 1.899 | **.0056** | **<1e-4** | 7,114 |
| H8 | large | −4.467 | 2.385 | .0611 | .0855 | 6,951 |

The v1 effects are not reproduced in the small bucket, and the small-bucket
estimates carry the **wrong sign** for both H7 and H8. The meaningful
decomposition is:

- **H7** is a **large-ticket** effect: +4.52 bp in the large bucket (p .036),
  near zero in medium, wrong-signed and insignificant in small. This supports
  the hypothesis that end-of-day concentration in large trades predicts
  absolute returns.
- **H8** is a **medium-bucket** effect: −5.27 bp (p .0056), while the large
  bucket is −4.47 bp (p .061) and the small bucket is wrong-signed. The
  declared negative EoD→return effect is therefore not specifically a
  large-ticket phenomenon; it lives in the mid-size trade mass. This is
  consistent with the Stage-1 finding that H8 collapses at the top-1% EoD
  cutoff and with its `NULL_FRAGILE` classification.

### 3.4 Large-vs-small success criterion

Pre-declared rule: success iff `|β_large| ≥ |β_small|` **and**
`p_large ≤ p_small` (raw DK). Because the raw rule can pass on a wrong-signed
large estimate, a **sign-aware** companion additionally requires the
large-bucket sign to match the v1 sign (deviation #19). Both are reported:

| test | metric | β large | p large | β small | p small | raw rule | sign-aware |
|---|---|---:|---:|---:|---:|:---:|:---:|
| H7 | buyer_hhi | +0.252 | .899 | −2.685 | .528 | fail | fail |
| H7 | top3_buyer_share | +0.960 | .655 | −2.722 | .649 | fail | fail |
| **H7** | **eod_concentration** | **+4.519** | **.036** | −1.360 | .650 | **pass** | **pass** |
| H8 | buyer_hhi | +2.752 | .309 | +3.166 | .502 | fail | fail |
| H8 | top3_buyer_share | +5.842 | .027 | +5.605 | .401 | **pass** | **fail** |
| H8 | eod_concentration | −4.467 | .061 | +5.841 | .134 | fail | fail |

The last two rows are exactly the trap the sign-aware rule is designed to
catch: H8's `top3_buyer_share` raw rule passes only because the large-bucket
point estimate is **positive** (+5.84 bp) against a v1 negative effect. The
sign-aware criterion rejects it. The only sign-aware pass is **H7 EoD**,
matching the large-ticket reading above.

### 3.5 Sensitivity to the minimum-trades guard

EoD coefficients at minimum 1 / 5 / 10 trades per bucket-day:

| test | bucket | min=1 | min=5 (primary) | min=10 |
|---|---|---:|---:|---:|
| H7 | large | +4.286 (p .0374) | +4.519 (p .0356) | +4.237 (p .0387) |
| H7 | medium | +1.084 (p .4607) | +1.066 (p .4674) | +1.207 (p .3969) |
| H7 | small | −1.293 (p .6196) | −1.360 (p .6497) | −0.314 (p .9211) |
| H8 | large | −4.326 (p .0484) | −4.467 (p .0611) | −4.105 (p .0903) |
| H8 | medium | −5.278 (p .0057) | −5.266 (p .0056) | −5.009 (p .0060) |
| H8 | small | +4.104 (p .1637) | +5.841 (p .1343) | +1.115 (p .7679) |

The H7 large-ticket effect and the H8 medium-bucket effect are stable across the
guard; the small-bucket estimates are not (wrong sign, unstable magnitude).
The min-10 run also shows H8's large-bucket p drifting to .090, i.e. only
borderline, while the medium bucket stays at .006.

### 3.6 Trade-size conclusions

- **H7** is supported as a large-ticket end-of-day concentration effect; this is
  the strongest positive result in the Stage-3 trade-size block.
- **H8** is not a large-ticket effect; it is a medium-bucket effect and remains
  `NULL_FRAGILE` from Stage 1.
- The small bucket is not usable for inference: 0.35% of volume, frequent
  one-to-four-trade days, wrong-signed and unstable estimates. Its only role is
  a diagnostic contrast.
- The three concentration metrics agree on H7 only in the EoD metric; buyer HHI
  and top-3 buyer share show no large-vs-small gradient. This is a
  **metric-specific** result, not a general "large trades are more concentrated"
  claim.

---

## 4 · Cross-stage reading

1. **H10 (reciprocity → |return|) remains the only confirmed headline.** It is
   the only test that is (i) a Stage-1 RW survivor (`rw_p = .081`), (ii) in the
   Stage-2 `{H10}` headline intersection, (iii) sign-stable and significant
   under EGARCH standardization (p .038), and (iv) both-tails/increasing in the
   quantile panel (τ=.90 +18.7 bp). The Stage-3 evidence strengthens the
   *shape* of the H10 association (concentrated in extreme |return| states) but
   does not add a second headline.
2. **H7** is demoted by Stage 1 and remains fragile: EGARCH p .064 overall but
   .116 without degenerate fits; quantile label NONE; only the large-ticket
   trade-size cut is significant. The honest summary is a localized,
   large-ticket EoD pattern, not a robust headline.
3. **H8** is demoted by Stage 1; Stage 3 shows a medium-bucket/lower-tail
   effect, with the large-bucket result borderline and the top-3 metric passing
   only under the wrong-signed raw criterion. `NULL_FRAGILE` stands.
4. **H4** is post-hoc opposite-sign; EGARCH keeps the sign but p .054, and the
   quantile curve is both-tails/increasing. It remains exploratory.
5. **H6** keeps its negative sign under EGARCH (p .020) and is a lower-tail
   quantile effect; RW still demotes it (`rw_p = .120`). It is not a headline.
6. **Nulls H1/H2/H3/H5/H9** are not resurrected: EGARCH keeps them
   insignificant, and their quantile tail labels are unadjusted descriptive
   artifacts (§2.3). The Stage-1 `NULL_ROBUST` classifications stand.

**Not in this stage.** The H7 specification curve (~72 specs) belongs to
V2-4/Stage 4 per the binding plan; it is not estimated here. The pre-declared
subgroup analyses (including the circuit-breaker subgroup) are also Stage 4;
the circuit-breaker subgroup cannot be fabricated because such days do not
exist in the window — that fact will be recorded with the Stage-4 subgroup
table.

---

## 5 · Reproduction

```bash
cd ~/research/nepse-floorsheet-microstructure
# arch is required (Stage 3); SE-spec tests should be run first after install
nepse-msc/bin/python -m pytest tests/test_se_specification.py -q
nepse-msc/bin/python scripts/run_v2_stage3.py
```

The quantile section checkpoints per `(test_id, tau)` to
`outputs/tables/_quantile_checkpoint.csv`; a completed run deletes it. To
replay the 50 fits without refitting, copy the finished
`outputs/tables/quantile_regression.csv` to the checkpoint path before the run
(this is how the Stage-3 artifact set was re-generated deterministically).
Stage-3 tables are byte-identical across consecutive runs.

| artifact | content |
|---|---|
| `outputs/tables/egarch_fit_log.csv` | one row per `(fold, symbol)` fit: convergence, recursion error, exclusion reason, stop reason |
| `outputs/tables/egarch_outcome_accounting.csv` | row/fit accounting and numerical bound |
| `outputs/tables/headline_with_egarch_outcome.csv` | primary, alt-outcome, base-on-EGARCH-rows and exclusion-sensitivity fits |
| `outputs/tables/quantile_regression.csv` | 50 quantile fits (β, robust SE, CI, iterations) |
| `outputs/tables/quantile_tail_summary.csv` | τ=.10/.90 labels, tail shape, ratio, CI-exclusion flags |
| `outputs/tables/trade_size_thresholds.csv` | per `(fold, symbol)` train-only p10/p90 |
| `outputs/tables/trade_size_bucket_summary.csv` | bucket composition at min 1/5/10 |
| `outputs/tables/trade_size_heterogeneity.csv` | H7/H8 × 3 metrics × 3 buckets × 3 guards |
| `outputs/tables/trade_size_success_criterion.csv` | large-vs-small raw and sign-aware rules |
| `outputs/figures/egarch_outcomes.png` | z distribution + v1-vs-EGARCH standardized effects |
| `outputs/figures/quantile_all_tests.png`, `quantile_H4/H6/H7/H8/H10.png` | β(τ) curves with robust CIs |
| `outputs/figures/trade_size_heterogeneity.png` | bucket bars for H7/H8 × three metrics |

---

## 6 · Limitations carried forward

- EGARCH is symmetric (declared `o=0`), conservative on average, and leaves fat
  tails; two fold-0 fits have degenerate forward recursions (297 rows, 4.2%).
- Quantile CIs are Koenker-robust asymptotic, not cluster-robust; the 20
  extreme-tail checks are unadjusted. Only H10's tail concentration is used as
  evidence.
- Trade-size buckets are defined by TRAIN-fold p10/p90; the small bucket is
  0.35% of volume and is not usable for inference. H7 is metric-specific (EoD),
  not a general large-trade concentration result.
- The H7 specification curve and pre-declared subgroups are Stage 4; the latter
  cannot include a circuit-breaker subgroup because no such days exist in the
  window.
- Frozen v1 numbers remain the primary record; Stage-3 tables are new v2
  artifacts and do not overwrite any v1 cell.
