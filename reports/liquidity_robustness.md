# Liquidity robustness, wild cluster bootstrap, SE concordance, VIF audit

**Stage 2 of the v2.0 A++ upgrade** · pre-declaration:
`docs/analysis_plan_v2_extension.md` §V2-2 (written before any v2 result).
Frozen v1 numbers are untouched; every table below is a **new** v2 artifact.
Runner of record: `scripts/run_v2_stage2.py` · log: `outputs/logs/v2_stage2.log`
· experiments EXP-0009a–d · deviations #15–#16.

Companion: `reports/exploratory_findings.md` (Stage 1).

---

## 0 · Gates that had to pass before any Stage-2 number was accepted

| gate | result |
|---|---|
| frozen v1 grid replication (10/10 designs, n=7,116) | **PASS** — max C1 rel `2.48e-16`; calibration constant `1.115535350368`; identical row order |
| liquidity complete cases on the OOS panel | **7,116 / 7,116** (all four proxies non-null) |
| wild-cluster engine vs FULL entity-clustered `PanelOLS` refits | **PASS** — max rel `5.11e-13` (gate `1e-8`), 3 designs × 3 draws + base fit |
| SE-spec test after dependency change (matplotlib installed) | **PASS** before the Stage-2 run |

No Stage-2 estimate below is a re-estimate of a v1 number: the v1 cells are
loaded from the frozen grid and re-used verbatim in the concordance table.

---

## 1 · Liquidity proxies (pre-declared constructions)

Built by `src/nepsemsc/features/liquidity.py`, merged on `(date, symbol)`, then
standardized with **TRAIN-fold** winsor(1/99)+z constants through the same
`train_fold_stats`/`standardize_test` machinery as every other regressor.

| proxy | construction | OOS coverage | mean | median | q99 | max |
|---|---|---|---:|---:|---:|---:|---:|
| `amihud` | `1e6·|ret|/turnover`; OHLCV `close×volume` turnover fallback (`amihud_value_source=ohlcv_turnover`) | 7,116 | 0.000790 | 0.000347 | 0.005481 | 0.232132 |
| `roll_spread` | Roll (1984) `2√max(0,−Cov(Δp_t,Δp_{t−1}))`, 20-session trailing, min 10; expressed **relative to close** | 7,116 | 0.007368 | 0.000000 | 0.058376 | 0.108965 |
| `corwin_schultz` | Corwin–Schultz (2012) two-day high/low estimator on the **trailing** pair, averaged over 20 trailing pairs (min 10); α≤0 → 0 | 7,116 | 0.008341 | 0.007911 | 0.018250 | 0.032109 |
| `effective_tick` | banded NEPSE tick / close (`<100 ⇒ 0.1`, `≥100 ⇒ 1.0`); diagnostic only | 7,116 | 0.002518 | 0.001945 | 0.006863 | 0.007886 |

Implementation facts of record:
- **No look-ahead**: every proxy is trailing (tests pin prefix-stability for
  Roll and Corwin–Schultz; test file `tests/test_liquidity_controls.py`).
- The effective-tick band is empirically exact on the top-12 floorsheet
  extracts: **every traded price is an integer rupee value**, so the `≥100` band
  (tick = 1.0) covers the entire OOS universe. The `<100` branch is declared
  but unexercised on these data.
- `effective_tick` is **not** one of the three γ controls; the controlled spec
  uses `amihud`, `roll_spread`, `corwin_schultz` exactly as pre-declared.
- Train-side coverage (for standardization constants) is 99.78%/98.07%/98.11%
  for Amihud/Roll/CS; the **OOS** panel is complete after the inner join, so the
  controlled and base specifications use the **identical 7,116 rows**
  (`outputs/tables/liquidity_row_accounting.csv`).

---

## 2 · Liquidity-controlled regressions

### 2.1 Single-feature grid re-run with the three liquidity γ's

Same feature + `log_volume_z` + `market_ret_loo_z`, **plus** the three liquidity
z-columns; DK bw=5; same rows. `Δ = β_controlled − β_base` in bp.

| test | feature → outcome | base bp | controlled bp | Δ bp | Δ % | p (controlled) |
|---|---|---:|---:|---:|---:|---:|
| H1 | self_loop → abs_ret | −1.557 | −0.979 | +0.578 | +37.1% | .6165 |
| H2 | anomaly → abs_ret | −1.491 | −1.197 | +0.295 | +19.8% | .6470 |
| H3 | anomaly → ret | +0.957 | +0.882 | −0.075 | −7.8% | .7699 |
| H4 | buyer_hhi → ret | +7.510 | +7.357 | −0.153 | −2.0% | .0306 |
| H5 | buyer_hhi → abs_ret | −1.856 | −1.841 | +0.015 | +0.8% | .4959 |
| H6 | reciprocity → ret | −10.939 | −10.989 | −0.051 | −0.5% | .0187 |
| H7 | EoD → abs_ret | +3.952 | +3.723 | −0.229 | −5.8% | .0354 |
| H8 | EoD → ret | −4.471 | −4.535 | −0.064 | −1.4% | .0425 |
| H9 | self_loop → ret | +1.817 | +1.911 | +0.094 | +5.2% | .4325 |
| H10 | reciprocity → abs_ret | +9.492 | **+9.586** | **+0.093** | **+1.0%** | **.0117** |

The two large relative moves are on **null** tests (H1/H2, where the base
estimate is near zero); every v1 BH-passing estimate moves by **less than 6%**
and no sign changes. In particular the sole Stage-1 confirmed headline H10
moves by **+0.09 bp (+1.0%)** and its p-value *falls* slightly (.0138 → .0117):
the three liquidity proxies do **not** absorb the reciprocity → |return|
association. The same holds for H4, H6, H7 and H8.

### 2.2 Joint four-feature specification

The plan's "four headline features" is operationalized as the four constructed
network features — `buyer_hhi`, `self_loop_ratio`, `reciprocity`,
`end_of_day_concentration` — entered jointly with the two controls and the three
liquidity γ's (deviation #15). This specification is **diagnostic**, not a
replacement for the pre-registered single-feature tests: its coefficients are
conditional on the other three network features, so they answer "which
dimension survives within the shared network structure", not "does the
registered hypothesis replicate".

| outcome | feature | joint base bp | joint + liquidity bp | Δ % | p (with liquidity) |
|---|---|---:|---:|---:|---:|
| ret | buyer_hhi | +5.395 | +5.188 | −3.8% | .0897 |
| ret | self_loop_ratio | +12.859 | +13.175 | +2.5% | .0097 |
| ret | reciprocity | −24.533 | −24.872 | −1.4% | .0047 |
| ret | EoD | −4.024 | −4.090 | −1.6% | .0658 |
| abs_ret | buyer_hhi | +0.238 | +0.048 | −79.6% | .9854 |
| abs_ret | self_loop_ratio | −12.607 | −11.482 | +8.9% | .0050 |
| abs_ret | reciprocity | +22.615 | +21.521 | −4.8% | .0023 |
| abs_ret | EoD | +3.613 | +3.415 | −5.5% | .0518 |

Within the joint spec the reciprocity coefficient is roughly twice the
single-feature magnitude and keeps the outcome-specific sign (negative for
`ret` = H6's direction; positive for `abs_ret` = H10's direction). This is
**suppression by the shared self-loop / concentration variance**, not a sign
flip of a registered hypothesis. The single-feature comparison in §2.1 is the
clean diagnostic and is the one carried forward.

Liquidity γ's themselves (joint spec): on `ret`, none is significant at 10%
(Amihud p .278, Roll p .146, CS p .161); on `abs_ret`, Amihud +12.39 bp
(p<1e-4) and Roll −7.15 bp (p .0011) are significant, CS +6.07 bp (p .250).
That is expected — illiquidity predicts volatility — and it does not remove the
network effects.

---

## 3 · Wild cluster bootstrap (CGM-2008 ReBWB)

### 3.1 Protocol actually executed

- cluster = **symbol** (entity); **12 clusters** (union of the four fold
  universes: AHPC, AKPL, API, HDL, NABIL, NBL, NHPC, NICA, NLIC, NRIC, SHIVM,
  UPPER); cluster sizes 170–722 rows.
- `B = 999`, seeds `V2_WB_SEEDS = 833001…833999`.
- One Rademacher sign `η_g ∈ {−1,+1}` per symbol per draw, **shared across the
  10-test family**.
- Pseudo-outcome `ŷ + η_g ⊙ e`; refit the same two-way FE model; recentered
  `t* = (β* − β̂)/SE*` where **both** the pseudo-draw and the observed
  statistic use the **entity-clustered** covariance.
- `p_WB = (1 + #{|t*| ≥ |t_obs|})/(B+1)`, two-sided.

An earlier Stage-2 implementation reused the **DK time-kernel** covariance on
cluster-weighted draws and compared it to the DK observed t. That is a
covariance/statistic mismatch; it produced absurd p≈.001 for four tests with
only 12 clusters. The mismatch was caught before any Stage-2 number of record,
the engine was rewritten to use entity-clustered covariance on **both** sides,
and the invalid p-values are **not reported anywhere**. The corrected engine
passes the full-refit gate at `5.11e-13`.

### 3.2 Results

| test | bp | se DK | t DK | se entity-cluster | t entity-cluster | p DK | **p WB** |
|---|---:|---:|---:|---:|---:|---:|---:|
| H1 | −1.557 | 1.97e-4 | −0.788 | 1.34e-4 | −1.161 | .4306 | .257 |
| H2 | −1.491 | 2.66e-4 | −0.560 | 2.32e-4 | −0.643 | .5753 | .541 |
| H3 | +0.957 | 3.01e-4 | +0.318 | 3.02e-4 | +0.317 | .7501 | .794 |
| H4 | +7.510 | 3.41e-4 | +2.204 | 2.11e-4 | +3.563 | .0275 | .002 |
| H5 | −1.856 | 2.67e-4 | −0.694 | 2.07e-4 | −0.899 | .4875 | .357 |
| H6 | −10.939 | 4.69e-4 | −2.332 | 3.13e-4 | −3.490 | .0197 | .002 |
| H7 | +3.952 | 1.79e-4 | +2.206 | 1.37e-4 | +2.881 | .0274 | .022 |
| H8 | −4.471 | 2.24e-4 | −1.997 | 2.19e-4 | −2.040 | .0459 | .095 |
| H9 | +1.817 | 2.45e-4 | +0.741 | 1.15e-4 | +1.580 | .4587 | .100 |
| H10 | +9.492 | 3.85e-4 | +2.464 | 2.85e-4 | +3.326 | .0138 | .009 |

Bootstrap t* distributions are close to centred (means −0.06…+0.01) with
SD ≈ 0.96–1.38; no numerical pathology.

### 3.3 Small-cluster caveat — **CRITICAL, do not suppress**

There are only **12 symbol clusters**. The CGM asymptotic justification needs
many clusters; with 12, the entity-clustered covariance is itself noisy and
generally **downward-biased**, so the WB p-values above are *anti-conservative*
relative to a large-G reference. Two concrete consequences:

- H4/H6/H10's entity-clustered SEs are 26–38% smaller than DK, which is why
  their WB p-values are much smaller than DK. That is a covariance-estimator
  difference, not independent evidence.
- H8 (p=.095) and H9 (p=.100) sit on opposite sides of the 10% line by
  bootstrap granularity alone. The concordance count must not be read as a
  precise 4/4 vs 0/4 ranking.

The wild cluster bootstrap is therefore carried as **one concordance signal**
in §4, never as the primary test, and no Stage-2 reclassification is driven by
it. The honest summary is: *the network effects are robust to liquidity
controls; their significance under entity clustering is consistent with the DK
and DC-v2 estimates, but the 12-cluster bootstrap cannot independently certify
them.*

---

## 4 · True two-way clustered SEs and the v1 `p_dc` disclosure

The frozen v1 `p_dc` column is **numerically identical to `p_dk` in all 10
rows**. Cause (verified in the installed linearmodels 7.1 source and by direct
probe): the v1 wrapper passed a **transposed `(2, nobs)` cluster array**;
linearmodels rejected it, and the wrapper silently fell back to the
time-kernel covariance (`cov_type_used =
"double_clustered_fallback_time_kernel"`). The v1 outputs are **not edited**;
v2 adds `fit_double_clustered_v2`, which passes a row-aligned two-column
DataFrame and executes a genuine `(entity, time)` two-way cluster.
`tests/test_wild_bootstrap.py` pins both the v1 fallback and the v2 execution.

| test | p DK | p DC-v2 | p FM | p WB | # significant (<.10) | class |
|---|---:|---:|---:|---:|---:|---|
| H1 | .4306 | .2851 | .3404 | .257 | 0 | NULL |
| H2 | .5753 | .5563 | .5304 | .541 | 0 | NULL |
| H3 | .7501 | .7783 | .3243 | .794 | 0 | NULL |
| H4 | .0275 | .0053 | .0082 | .002 | 4 | **STRONG** |
| H5 | .4875 | .4117 | .6873 | .357 | 0 | NULL |
| H6 | .0197 | .0021 | .5403 | .002 | 3 | **MODERATE** |
| H7 | .0274 | .0086 | .0094 | .022 | 4 | **STRONG** |
| H8 | .0459 | .0574 | .0587 | .095 | 4 | **STRONG** |
| H9 | .4587 | .1845 | .3875 | .100 | 0 | NULL |
| H10 | .0138 | .0028 | .2896 | .009 | 3 | **MODERATE** |

Notes:
- `p_dc_v2` is systematically smaller than DK for the four largest effects;
  the two-way cluster difference is not a sign of a stronger effect, only of a
  different variance estimator. v1's frozen numbers remain the primary record.
- FM is the discordant estimator for H6 and H10 (p .540 / .290): they are
  **DK/DC-v2/WB concordant, FM-discordant**. H4/H7/H8 are 4/4.
- The `NULL` label is pre-declared. Pandas' default `read_csv` treats the
  literal string `NULL` as missing; read this column with
  `keep_default_na=False`, or use the numeric `n_sig_p_lt_10` column.

### Stage-2 headline set

Per the pre-declared rule (`STRONG ∪ MODERATE` ∩ Stage-1
`CONFIRMED_HEADLINE`):

```
stage2_headline = {H10}
```

H4, H7 and H8 have STRONG SE concordance but **cannot enter the headline set**:
H4 is `EXPLORATORY_POST_HOC` (opposite sign to its pre-registration), H7/H8
were demoted to `NULL_FRAGILE` by the Stage-1 Romano–Wolf step-down. This is
the intended behaviour of the rule — estimator concordance is not hypothesis
confirmation. H6 remains `MODERATE` but is `NULL_FRAGILE` after RW.

**H10 is the only Stage-2 headline candidate**, now with the additional
caveats (i) FM discordance (p .290), (ii) the Stage-1 DC13 past-|ret|
association (+19.69 bp vs +9.49 bp forward) that flags a persistence channel,
and (iii) the 12-cluster bootstrap limitation. These are carried into the
Stage-5 final classification; none is resolved in H10's favour by Stage 2.

---

## 5 · VIF / correlation audit

Within-transformed design (two-way FE absorbed), 8 features + 3 liquidity γ's
+ 2 controls, common 7,116-row set.

| feature | VIF | max |r| with any other regressor |
|---|---:|---:|
| reciprocity_z | 2.538 | .529 |
| self_loop_ratio_z | 2.506 | .529 |
| anomaly_score_z | 1.933 | .635 |
| buyer_hhi_z | 1.611 | .635 |
| log_volume_z | 1.427 | .518 |
| amihud_z | 1.101 | .302 |
| end_of_day_concentration_z | 1.075 | .165 |
| market_ret_loo_z | 1.050 | .083 |
| roll_spread_z | 1.017 | .195 |
| corwin_schultz_z | 1.009 | .405 |

- **No VIF > 5 and no |r| > 0.7.** The largest correlation is
  `buyer_hhi ↔ anomaly_score` at +.635 and the largest VIF is 2.538
  (reciprocity). The pre-declared drop-sensitivity run is therefore **not
  required** and was not added.
- Figure: `outputs/figures/feature_correlation.png` (matplotlib 3.11.2,
  Agg backend, 180 dpi).
- The liquidity γ's are close to orthogonal to the network features
  (max |r| = .405, CS ↔ log volume), which is why the controlled estimates in §2 move
  so little.

---

## 6 · What Stage 2 changes, and what it does not

**Changes**
- v2 gains a liquidity-controlled replication: the network effects are **not**
  a liquidity/illiquidity artifact.
- v2 gains a genuine two-way clustered estimator; the v1 `p_dc` column is
  disclosed as a silent time-kernel fallback.
- v2 gains the wild cluster bootstrap and the 4-estimator concordance table;
  H10 is the only Stage-2 headline under the pre-declared intersection rule.

**Does not change**
- No frozen v1 numeric cell (`docs/analysis_plan.md`,
  `hypothesis_grid_results.csv`, `configs/project.yaml` are byte-untouched).
- No Stage-1 classification: H10 remains `CONFIRMED_HEADLINE`; H4
  `EXPLORATORY_POST_HOC`; H6/H7/H8 `NULL_FRAGILE`; H1/H2/H3/H5/H9
  `NULL_ROBUST`.
- The Stage-2 headline is a **governance label for the Stage-5/6 reporting
  surface**, not a new hypothesis test.

**Open limitations carried forward**
1. 12 clusters → WB is a weak-G diagnostic, not confirmation.
2. H10's FM discordance and the DC13 persistence association.
3. Liquidity proxies are daily proxies on the tier-1 OHLCV-covered universe;
   they do not capture intraday depth or order-book state.
4. Amihud uses OHLCV turnover, not floorsheet rupee amount (declared fallback;
   the two agree closely on the top-12 recon sample, but not identically).

---

## 7 · Artifacts of record

| artifact | content |
|---|---|
| `outputs/tables/liquidity_summary.csv` | proxy distributions + `amihud_value_source` tag |
| `outputs/tables/liquidity_row_accounting.csv` | per-proxy and complete-case coverage |
| `outputs/tables/headline_with_liquidity_controls.csv` | single-feature base/controlled + joint 4-feature spec |
| `outputs/tables/wild_cluster_bootstrap.csv` | DK vs entity-clustered t, WB p, B, cluster count |
| `outputs/tables/se_concordance.csv` | DK/DC-v2/FM/WB p, count, class, Stage-1/2 labels |
| `outputs/tables/vif_audit.csv` | VIF, max |r|, flag columns |
| `outputs/tables/feature_correlation.csv` | full design correlation matrix |
| `outputs/figures/feature_correlation.png` | thesis-grade heatmap |
| `outputs/logs/v2_stage2.log` | complete run log |
| tests | `tests/test_liquidity_controls.py` (8), `tests/test_wild_bootstrap.py` (6) |
