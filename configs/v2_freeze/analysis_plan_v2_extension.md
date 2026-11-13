# Analysis Plan v2 EXTENSION — PRE-DECLARED 2026-11-10 (before any v2 result)

Pre-declaration for the v2.0 A++ upgrade program (Stages 1–6). The v1 plan
`docs/analysis_plan.md` remains **SACRED and byte-frozen**; this file adds protocols,
it never amends v1 declarations. Written **before any v2 computation was run and
before any v2 result was observed**. The frozen files stay immutable: v1 numeric
CSV cells are NEVER rewritten; v2 adds (a) separate result files, (b) explicitly
declared governance/annotation columns where the brief demands them, each logged as
a numbered deviation row with timestamp, (c) new experiment-register rows.

Deviations live in `docs/analysis_deviations.md` (v1 rows #1–#9 exist; v2 rows start
at #10). Log format unchanged: | ts (UTC+5:45) | deviation | reason | registered? |.

## V2-0 · Conventions (binding for all stages)

- **Seeds.** v2 declares NEW deterministic seed ranges (v1 ranges untouched):
  - score-permutation extension: `V2_SCORE_SEEDS = 826001+i, i=0..999` (first 200
    IDENTICAL to v1 `PLACEBO_SEEDS` — asserted by test);
  - block permutations: `V2_BLOCK_SEEDS = 828001+i, i=0..999`;
  - negative-control within-block shuffles: `V2_NEGCTRL_SEEDS = 829001+i, i=0..1999`;
  - Romano–Wolf bootstrap: `V2_RW_SEEDS = 830001+b, b=0..998` (B=999);
  - wild cluster bootstrap: `V2_WB_SEEDS = 833001+b, b=0..998` (B=999).
  All implemented via `numpy.random.default_rng(seed)`, one seed per draw.
- **Estimator identity.** All bootstrap inference mirrors the v1 PRIMARY estimator:
  DK = `PanelOLS(entity+time effects, drop_absorbed)` kernel covariance
  (Bartlett, bandwidth=5), exactly `fit_driscoll_kraay bw=5` as in
  `src/nepsemsc/ml/panel_regression.py`. Wherever a pseudo-fit t-statistic is
  needed, the engine computes the SAME estimator algebraically from
  (within design X_w, within residual e) and must be **validated numerically
  against full `linearmodels` refits (rel. tolerance 1e-8 on t/SE, ≥6 pseudo-draws
  ≥2 designs) before any bootstrap result is trusted**; on validation failure the
  pre-declared fallback is the slow path: 999 × #tests full `PanelOLS` refits
  (joblib, ≤24 workers) with the identical algebra, never an approximation.
- **Inputs.** Stage-1 analyses read `data/processed/anomaly_scores.parquet` +
  `data/processed/daily_outcomes.parquet` via the shared builder
  `build_oos_panel(..., extra_outcome_cols=...)`. NO re-ingestion, NO re-scoring,
  NO DuckDB writes in Stage 1 (read-only sessions if any).
- **Logs & checkpoints.** Each stage logs to `outputs/logs/v2_stageN.log`.
  Long runs write `outputs/tables/_checkpoint_*.csv` partial state every
  ≤200 iterations and delete the checkpoint files on successful completion.
- **Runtime gates.** Full pytest must pass before each stage commit; after ANY
  dependency change (e.g. `arch` in Stage 3) the SE-spec test runs FIRST.
- **Predictions are not results.** Where the upgrade brief states an expectation
  (e.g. "H6/H8 likely lose significance under RW"), that is a pre-registered
  PREDICTION. Only the executed output is a result.

## V2-1 · Stage 1 — statistical interpretation fixes

### 1.1 Reclassification (governance, no re-estimation)
- NEW file `outputs/tables/hypothesis_grid_results_v2.csv` = frozen v1 grid
  (10 rows, all original columns byte-copied) + governance columns:
  `result_classification ∈ {CONFIRMED_HEADLINE, EXPLORATORY_POST_HOC,
  NULL_FRAGILE, NULL_ROBUST}`, `classification_reason`, `classification_source`
  (v1_result | v2_robustness_rows). The v1 file
  `outputs/tables/hypothesis_grid_results.csv` is NOT edited (DC20 freeze-audit
  bite + R2 immutability); the governance table is the reporting surface.
- Declared rules BEFORE results:
  - H4 → `EXPLORATORY_POST_HOC`, reason `opposite_sign_to_predeclaration`
    (pre-declared direction: buyer_hhi → ret = NEGATIVE; estimate +7.51 bp,
    raw p .02755, BH ≤ .10 — an opposite-sign significant estimate is NOT a
    confirmatory finding under pre-declared directional testing).
  - H8 → `NULL_FRAGILE`, reason `two_registered_robustness_failures`
    (EXP-0005c top-1% cutoff p .7634; EXP-0005e normal-era p .1703 while the
    base/BH pass holds; v1 headline relied on DK-BH only ⇒ fragile classification).
  - Remaining classification (declared now, mechanically derived from v1 numbers):
    H7, H10 → `CONFIRMED_HEADLINE` (BH-passing, sign as declared); H1, H5, H9 →
    `NULL_ROBUST` (BH-failing AND LOO-stable nulls, EXP-0005a 0/12) — final
    authority order: Stage-1 RW (1.2) may demote a CONFIRMED to `NULL_FRAGILE`
    if `rw_p > .10`, recorded in the RW table + deviation; no other promotion
    from null to headline is possible in v2 (no re-fit on new evidence).
    H2/H3 remain `NULL_ROBUST` with the placebo support column preserved.
    H6 starts `CONFIRMED_HEADLINE` (sign ambiguous but BH-disclosed in v1; RW
    adjudicates) — its wording change (if any) is deviation-logged.
- `reports/exploratory_findings.md` (NEW): (a) pre-declared direction, (b) estimate,
  (c) why exploratory-not-confirmatory, (d) candidate explanations for the
  opposite-sign concentration premium (illiquidity/size composition, price-level
  effects under fixed tick, temporary price-pressure, DHM-style normal-era
  phenomenon), each labelled candidate-with-test, plus the H8 regime-artifact
  paragraph (1.2) and the DC13 outcome-placebo result section (1.5).
- Deviation rows: #10 (H4 reclassification + governance-column mechanism),
  #11 (H8 demotion).

### 1.2 Romano–Wolf step-down (FWER, arbitrary dependence)
- Module `src/nepsemsc/evaluation/romano_wolf.py` (+ shared engine
  `src/nepsemsc/evaluation/_panel_boot.py`). Family = the SAME 10 pre-declared
  grid tests (their v1 design: single feature + log_volume_z + market_ret_loo_z,
  two-way absorbed FE, DK bw=5, n=7116 rows).
- Algorithm (declared): B=999 draws; draw b flips the sign of the v1 base-fit
  within-residuals with Rademacher weights **at the (symbol, session) row level**,
  pseudo-outcome ŷ + ε⊙e, re-estimate the SAME DK(cov) for all 10 tests per draw,
  recentered bootstrap t*_h = (β*_h − β̂_h)/SE*_h, two-sided p*_h in the same
  p-functional as the v1 `res.pvalues` (verified normal at runtime; recorded).
- Step-down: hypotheses ordered by observed |t| descending. Adjusted
  `RW_p_k = share( max_{h ≥ k, h in remaining set} |t*_h| ≥ |t_k| )` with
  monotonicity enforcement (cumulative max). ALSO recorded:
  `rw_p_literal_minp_fullset = share(min_h p*_h ≤ p_k)` — the brief's literal
  min-p-over-the-full-family formula — reported as a secondary column and noted
  as valid-but-more-conservative in deviation #12.
- Decision rule: the TRUE headline set after RW = {h: rw_p ≤ 0.10}. RW does not
  alter any v1 file; it creates `outputs/tables/hypothesis_grid_results_rw.csv`
  (all original columns co-reported for readability) and feeds 1.1's
  classification table.
- Engine validation (pre-declared, executed before use): for ≥6 random draws on
  ≥2 test designs, engine t/SE vs full `PanelOLS` pseudo-refit must agree rel ≤1e-8;
  else the joblib slow path (999 × 10 refits, checkpointed) is the result of record.
- Deviation #12 records adoption + the row-level Rademacher implementation
  choice for the DK family (entity-level variant noted as the Stage-2 WB job).

### 1.3 MDE null classification
- Module `src/nepsemsc/evaluation/mde.py`. MDE_80 = (z_{.975}+z_{.80})×SE = 2.8043×SE
  (v1 convention already implemented in the grid). Rows: ALL five v1 BH-failing
  grid nulls (H1, H2, H3 are grid; H5, H9 same) + demoted H8 + the event-study
  overall CAR. Event-study SE derived from the frozen summary (t and CAR of
  record ⇒ SE = CAR/t); no event re-fit.
- Classification: `NULL_POWERED` iff |β_bp| < MDE_80/2, else `NULL_UNDERPOWERED`.
  Output `outputs/tables/null_classification.csv` (test_id, outcome, beta_bp, se_bp,
  mde80_bp, ratio, classification, basis[citation]).

### 1.4 DC13 placebo-OUTCOME test (pre-declared in v1 §3.4; unimplemented there)
- Outcome construction: `abs_ret_lag1 = |close(t−1)/close(t−2) − 1| = |ret(t−1)|`
  on each symbol's OWN available-(non-null-ret)-session adjacency (same convention
  as v1 `ret_fwd1` builder), computed from `daily_outcomes.parquet['ret']`;
  merged through `build_oos_panel(..., extra_outcome_cols=("abs_ret_lag1",))`;
  per-test row set = the test's own non-null outcome set (adds the lag nulls;
  row counts reported). Design/estimator identical to v1 (DK bw=5).
- Inference: the anomaly score (and every grid feature) must NOT predict the PAST
  absolute return. p ≤ .05 ⇒ specification-error flag for that test;
  p > .05 ⇒ pass. Output `outputs/tables/placebo_outcome_test.csv`
  (test_id, beta_bp, p_dk, verdict, n_obs). No BH family (single declared test per
  feature; family-wise note recorded). Deviation #13 records that DC13 was
  pre-declared in v1 but not executed, and is executed now on frozen inputs.

### 1.5 Expanded placebo battery
- (a) 1000 score permutations via the declared V2_SCORE_SEEDS (first 200 ≡ v1
  seeds), full-panel anomaly_score shuffle, same pseud-fit design; sided shares
  (upper share for H2, lower share for H3) + NEW two-sided share
  `share(|β_perm| ≥ |β_obs|)`.
- (b) Block permutations: within each symbol (test-panel rows in date order),
  the anomaly_score series is cut into consecutive 5-session blocks (NEPSE trading
  week ≈ Sun–Thu; remainder block < 5 kept whole) and whole blocks are permuted
  WITHIN symbol; B=1000, V2_BLOCK_SEEDS; same sided shares. Preserves
  short-range score autocorrelation (declared intent).
- (c) Negative-control FEATURE (declared construction, standardization AFTER
  the shift with the SAME train-fold constants): primary = `negctrl_eod_lead5`
  = end_of_day_concentration at t+5
  (the FUTURE value placed at t; 5 sessions forward within symbol adjacency),
  z-scaled by each fold's TRAIN constants, then the SINGLE-FEATURE H7-style
  design (feature + log_volume_z + market_ret_loo_z, DK bw=5) on both outcomes
  ret_fwd1 / abs_ret_fwd1. Secondary (descriptive): `negctrl_eod_blockshuffle` —
  EoD concentration shuffled within 5-session blocks within symbol, B=1000,
  V2_NEGCTRL_SEEDS first 1000, same design. Significance of either negative
  control ⇒ the design carries lead-lag / persistence content that must be
  disclosed; both results reported whatever they are.
- Output `outputs/tables/placebo_distribution_expanded.csv` (one row per
  construction × test × share-type, with n_perm, seed_range, share, share_lo95,
  share_hi95 binomial-local CI); distribution quantiles of placebo βs included.

### 1.6 Stage-1 register & artifacts
- EXP-0008a reclassification + exploratory findings doc;
  EXP-0008b Romano–Wolf; EXP-0008c MDE classification; EXP-0008d DC13
  placebo-outcome; EXP-0008e expanded placebo battery.
- Tests added at Stage 1 (not deferred): `tests/test_romano_wolf.py`
  (synthetic design: RW p ≥ raw p, monotone, known null set; engine-vs-refit
  validation inside the test), `tests/test_mde.py` (formula + boundary cases),
  `tests/test_v2_seeds.py` (seed ranges + first-200 equivalence).

## V2-2 · Stage 2 — referee-proof robustness battery (protocols pre-declared at plan time)

- **Liquidity features** `src/nepsemsc/features/liquidity.py`, per (symbol,
  session) on the tier-1 outcome panel rows within the OOS panel:
  (a) Amihud = |ret_t| / (value_t) with value = amount (floorsheet rupee value;
     when amount unavailable on the outcome row, |ret_t|/dollar volume proxy from
     OHLCV close×volume, declared fallback, tagged);
  (b) Roll implied spread = 2√(Cov(ΔP_t, ΔP_{t−1})) clipped at 0, 20-session
     rolling (within symbol adjacency);
  (c) Corwin–Schultz two-day high/low effective spread formula as published;
  (d) effective tick proxy (Goyenko et al. 2009): τ = |ΔP| weighted relative
     distance-to-nearest-tick intensity — computed from tick size grid inferred
     from NEPSE price bands (declared implementation note).
  Standardization: TRAIN-fold winsor(1/99)+z via the SAME constants machinery
  (`train_fold_stats` cols extended), never test-fold.
- **Liquidity-controlled regression** (declared: the headline multi-feature spec,
  featuring the headlines jointly as the prompt specifies): outcome ret / abs_ret;
  regressors = the four headline features + log_volume_z + market_ret_loo_z +
  amihud_z + roll_spread_z + corwin_schultz_z; DK bw=5; plus the v1
  single-feature grid re-run with liquidity controls for per-test sensitivity.
  KEY DIAGNOSTIC = β of each headline before/after γ's with same row set.
  Output `outputs/tables/headline_with_liquidity_controls.csv` +
  `reports/liquidity_robustness.md` (+ EXP rows).
- **Wild cluster bootstrap** (`src/nepsemsc/evaluation/wild_bootstrap.py`):
  CGM-2008 ReBWB; B=999; η_g Rademacher per symbol (cluster); pseudo
  ŷ + η_g⊙e; recentered t*; p_WB = share(|t*| ≥ |t_obs|) per test (all 10);
  V2_WB_SEEDS. Engine shares the validated Stage-1 machinery with cluster-weight
  generation (same validation gates).
- **SE concordance**: every one of the 10 tests under DK / DC / FM / WB at once:
  `outputs/tables/se_concordance.csv` with concordance class
  STRONG (4/4 p<.10) · MODERATE (3/4) · WEAK (2/4) · FRAGILE (1/4) · NULL (0/4).
  Values p from the respective estimators (RW excluded from the count; reported
  alongside). Headline set after Stage 2 = STRONG ∪ MODERATE ∩ other Stage-1
  demotions.
- **VIF / correlation audit**: pairwise correlations of the FULL design matrix
  (all 8 features incl. the liquidity γ-s on their common row set), VIF per
  feature in the controlled specification; outputs
  `outputs/tables/vif_audit.csv`, `outputs/figures/feature_correlation.png`
  (static PNG via plotly/ kaleido or matplotlib — declared matplotlib for the
  thesis-grade PNG), flag rules |r|>0.7 or VIF>5; if flagged, the collinear
  feature's controlled-drop sensitivity run is added.

## V2-3 · Stage 3 — tail and residual analyses (protocols pre-declared at plan time)

- **Quantile panel**: τ ∈ {0.10,0.25,0.50,0.75,0.90}; primary implementation
  = statsmodels `QuantReg` on the two-way-demeaned design dummies-absorbed via
  sparse `C(symbol)+C(date)` dummies IF memory allows (7116 rows × ~650 dummies
  feasible); fallback declared = per-timestamp pooled quantile with
  within-transform + cluster-robust covariance (with disclosure of the
  approximation; a deviation row decides which was executed). β(τ) curves + 95%
  CI (rank-based / bootstrap stated), figures `outputs/figures/quantile_*.png`,
  table `outputs/tables/quantile_regression.csv`, hypotheses = the 10 grid tests
  (outcome abs_ret primary where applicable) + headline set re-checked.
  INTERPRETATION rule declared: tail-concentration claims require the effect
  SIGN and CI behavior at τ extremes; means-only language is not permitted post-3.1.
- **EGARCH standardized outcomes** (`src/nepsemsc/models/egarch_outcomes.py`):
  `pip install arch` AFTER rerunning SE-spec tests (gotcha); per symbol, EGARCH(1,1)
  (mean='Constant', vol='EGARCH', p=1,q=1, dist='normal') fit on TRAIN-fold
  daily returns of that symbol only (any symbol with <60 train obs excluded,
  counted); OOS rows get z_{t+1} = one-step-ahead standardized residual mapped
  via the fit's conditional variance path (+ forecast); outcome |z_{t+1}|
  (and z_{t+1} for ret) in the same grid designs:
  `outputs/tables/headline_with_egarch_outcome.csv`,
  `reports/residual_based_analysis.md`. Note: fitting uses TRAIN rows ONLY; the
  OOS z's rely on the TRAIN-estimated EGARCH applied forward (leak-free by
  construction; declared).
- **Trade-size heterogeneity**: DuckDB single-writer session; per symbol-size
  percentiles computed on TRAIN-FOLD session rows only (declared anti-leakage
  choice; the alternative (full-window) percentiles noted in a deviation);
  buckets = small (<p10), medium (p10–p90), large (>p90) by TRADE SIZE
  (Quantity); per bucket: buyer-side HHI, top-3 share, EoD-style contracted-order
  concentration; the H7/H8 designs re-run with bucket-concentration features
  (single-feature at a time, same controls/standardizer):
  `outputs/tables/trade_size_heterogeneity.csv`. Declared success criterion:
  large-ticket concentration ≥ small-ticket concentration in (a) magnitude AND
  (b) raw p — honest reporting either way.

## V2-4 · Stage 4 — polish, heterogeneity, PhD seed (protocols pre-declared at plan time)

- **Specification curve (H7)**: factor grid = SE family {DK, DC, FM, WB-as-SE}
  × outcome {ret, abs_ret} × liquidity controls {none, γ-all} × subsample
  {full, bubble, normal} × EoD cutoff {5%, 1%, 10%} = 4×2×2×3×3 = 72 specs
  (within the declared 48–72 range). Per spec: β_H7 + 95% CI (normal ±1.96·SE
  for parametric; WB percentile CI declared for the WB-family entries).
  Figure `outputs/figures/specification_curve_h7.png` (β sorted with CI bars +
  inclusion panel). Median β, share CI-excluding-0, and the "robustness ratio"
  (β range / median) reported in the doc `reports/specification_curve_h7.md`.
  Anomaly-estimator factor (3 scorers) applies to the H2/H3-style spec-curve ONLY
  IF a second curve is produced (declared optional; not required by the brief for
  H7 — note recorded).
- **Effective N**: `n_stocks`, `n_dates`, `n_obs`, `n_effective`
  (= n_obs − absorbed df for PanelOLS = observation rows minus entity+time FE
  df; = n_cross_sections for FM) columns on the v2 grid tables (1.1 file) +
  `outputs/tables/hypothesis_grid_results_rw.csv`.
- **Broker-level panel (PhD seed, DESCRIPTIVE only — R11)**: per (broker, month):
  buy/sell value, stock breadth, cross-stock HHI, network centrality
  (betweenness + eigenvector on the MONTHLY broker graph, aggregated pair edges),
  month-over-month top-N (N=50) Jaccard persistence, net position;
  core brokers = top-10% by monthly betweenness AND persistent ≥6 of the last 12
  months; core↔periphery transition counts table; snapshots 2021-10 (bubble
  peak) vs 2023-06 (normal) rendered with networkx→matplotlib spring layout on
  top-100 brokers by value (declared render cap); outputs
  `outputs/tables/broker_level_panel.csv`,
  `outputs/figures/broker_network_bubble.png`,
  `outputs/figures/broker_network_normal.png`,
  `reports/broker_pilot_phd_seed.md` (1 page, descriptive summary + PhD framing).
- **Cost-benefit / economic magnitude** `reports/economic_magnitude_analysis.md`:
  declared cost params table (NEPSE commissions ≈0.3–0.5% + brokerage + spread+CNS
  carry; range used, not point-claimed) vs headline β bp/SD magnitudes (H7 +3.95,
  H10 +9.49, H4 +7.51-opposite-sign); conclusion FRAMED (per promote): the
  effects are statistical/informational content, NOT standalone tradable alpha at
  1-SD engagement; conditional tradability via conditioning (stacked signals) is
  speculative-listed, not claimed.
- **Subgroup heterogeneity** (pre-declared splits; ALL on TRAIN-fold stats):
  (i) size proxy (PROXY tag): train-fold mean daily value traded, split at
  train median; (ii) liquidity: train-fold median Amihud (from 2.1 features);
  (iii) **circuit-breakers: NOT IMPLEMENTABLE — this corpus contains no
  circuit-breaker/limit-hit flag and no archive exposes one; the row is
  registered NOT EXECUTED with reason, NOT faked**; (iv) turnover tier: top-3 vs
  bottom-7 by train-fold mean turnover within the OOS-usable universe.
  Each subgroup: joint-headline H7/H8/H10/H4-style designs per subgroup with
  group-by-group β + 95% CI + group×feature interaction term for heterogeneity
  testing (the interaction t is the declared heterogeneity test; Bonferroni-family
  disclosure across the 3×2 subgroup grid). Output
  `outputs/tables/heterogeneity_subgroups.csv`.
- **Event-study upgrade**: BMP (cross-sectional t on standardized ARs, Boehmer
  adjustment with event-clustering understatement caveat kept) + Corrado rank
  test on the 686-event sample; market-adjusted variant on the SAME 60-session
  estimation windows (declared: no re-estimation of windows — reuse v1 ARs and
  computing standardizations on them); n=16 illiquid subsample MOVED TO APPENDIX
  (its result stays registered; headline quoting restricted to n=686). Output
  `outputs/tables/event_study_upgraded.csv`.

## V2-5 · Stage 5 — chapter skeletons & canonical tables

- `outputs/tables/v2_final_headline_set.csv` — EXACT columns per the brief:
  hypothesis, pre_declared_direction, estimated_beta, dk_p, rw_p,
  wild_bootstrap_p, se_concordance, survives_liquidity, survives_egarch,
  tail_concentration, final_classification ∈ {HEADLINE_ROBUST,
  HEADLINE_MODERATE, EXPLORATORY_POST_HOC, NULL_POWERED, NULL_FRAGILE,
  NULL_UNDERPOWERED}. Composition rule declared: final = Stage-1 classification
  ∩ Stage-2 concordance ∩ Stage-3 checks (each demotion rationale citable).
- `reports/chapter_assets/ch5_results_skeleton.md` + `ch6_discussion_skeleton.md`
  — structure EXACTLY as the brief §5.2/§5.3 lists them; skeletons (bullet
  facts + table/figure pointers + one-sentence claim per numbered subsection),
  NO thesis prose.
- `docs/experiment_register.md`: add `chapter_section` mapping column (data
  addition to a tracked doc — allowed, logged v2-5 row) + v2 EXP rows through
  EXP-0012 level.
- `reports/limitations.md` (v2 living copy; v1 `docs/limitations.md` frozen):
  limitation table with `severity ∈ {CRITICAL, MAJOR, MINOR}` + the
  predictive-not-causal caveat, self-loop interpretations, tier-10 coverage,
  no-intraday-timestamps, circuit-breaker non-implementability, liquidity-verdict,
  single-exchange, licence chain. Cross-linked EXP citations.

## V2-6 · Stage 6 — reproducibility, deposit, final freeze

- Clean-rebuild verification: delete `data/processed/` and `data/duckdb/` ONLY
  (raw archives untouched; they are the provenance anchors), full re-run of the
  documented pipeline, timed, recorded in `docs/reproducibility.md`; notebooks
  re-executed via nbmake.
- Tests added: `test_wild_bootstrap.py` (analytic-SE sanity on well-specified
  model + coverage), `test_liquidity_controls.py` (Amihud/Roll/CS toy values),
  `test_quantile_panel.py` (shape/τ-monotone smoke), `test_egarch_outcomes.py`
  (conditional-vol mapping sanity), `test_specification_curve.py` (72 specs run),
  `test_freeze_v2.py` (SHA-256 of `configs/v2_freeze/*`). Full suite ≥80.
- Config freeze: `configs/v2_freeze/` snapshot + SHA-256 per file (violating
  change ⇒ test fails).
- Env freeze: `requirements-lock.txt` regenerated from the live venv AFTER all
  Stage-3 installs (SE-spec test FIRST after any dependency change), pinned.
- Deposit prep: `docs/deposit_readme.md` (structure/repro/licence), `CITATION.cff`,
  `LICENSE` (code MIT; data licences remain per `provenance_manifest.csv`).
  NO upload happens (user action).
- Final register audit: every number-to-be-quoted traces to an EXP row with a
  real output file hash-aligned to the manifest; orphan numbers purged or
  EX-registered.
- AGENTS.md final-state section; commit + tag `v2.0-a++-freeze`.

## V2-7 · PREDICTIONS registered at plan time (not results; deviation-logged if falsified)

- RW: H6 and/or H8 lose ≤.10; H7 and/or H10 survive; step-down pulls H4 > .10
  already (it is exploratory anyway).
- Liquidity controls: H7 magnitude shrinks (Amihud and concentration share
  variance); survival is an empirical question.
- WB: borderline DK p's inflate materially (H8 especially).
- If any result surprises MORE than these priors, an explicit investigation row
  is REQUIRED before reporting (R-integrity).

— END OF PRE-DECLARATION (written before any v2 execution) —
