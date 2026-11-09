# Analysis Plan — FROZEN 2026-11-08 (DC20)

Written **before any test-fold data was observed, scored, or even built.**
Deviations are logged in `docs/analysis_deviations.md` ONLY with a timestamp
and reason; silent deviations are violations, not fallbacks.

## 1. Data scope

| Item | Definition |
|---|---|
| Primary floorsheet window | 2021-01-01 → 2024-12-31 (bubble era per brief) |
| Guaranteed window if 2021–2023 unobtainable | 2024-01-01 → 2026-11-02 (local socrateai archive) |
| Scope fork trigger | no verified 2021–2023 floorsheet source by 2026-11-12 → adopt guaranteed window; R8 regimes then derived from OHLCV drawdown/momentum (rule below), NOT calendar epochs |
| Universe | TOP-10 by mean daily turnover, computed on TRAINING-FOLD data only, re-selected per fold (DC1) |
| Inclusion | stocks with ≥90% of NEPSE sessions present in window (DC2); exclusions to `outputs/tables/universe_exclusions.csv` |
| Trading calendar | derived from OHLCV dates with non-null volume (DC3); `bdate_range` never used |
| Timezone | Asia/Kathmandu +05:45 (DC4) |
| Missing broker IDs | DROP rows (unbiased, loses volume); flag in audit; never switch (SV7 pre-decision) |
| Duplicates | first record kept per (date, symbol, contract_no) |
| Low-activity days | <100 trades flagged; INCLUDED by default (power-preserving, documented) |

## 2. Pre-declared hypothesis grid (R6)

5 features × 2 outcomes = **10 tests**, BH-FDR at q = 0.10 across the grid.

Outcomes: `ret_fwd1` = next-session close-to-close return (calendar from DC3);
`abs_ret_fwd1` = its absolute value (volatility proxy); PCS/Parkinson added in Phase 3.

| # | Feature | Outcome | Status | Predicted sign |
|---|---|---|---|---|
| H1 | self_loop_ratio[t] | abs_ret_fwd1 | **PRIMARY** | positive |
| H2 | anomaly_score[t] | abs_ret_fwd1 | secondary | positive |
| H3 | anomaly_score[t] | ret_fwd1 | secondary | negative (reversal) |
| H4 | buyer_hhi[t] | ret_fwd1 | secondary | negative (concentration → worse liquidity) |
| H5 | buyer_hhi[t] | abs_ret_fwd1 | secondary | positive |
| H6 | reciprocity[t] | ret_fwd1 | secondary | ambiguous |
| H7 | end_of_day_concentration[t] | abs_ret_fwd1 | secondary | positive |
| H8 | end_of_day_concentration[t] | ret_fwd1 | secondary | negative |
| H9 | self_loop_ratio[t] | ret_fwd1 | secondary | negative |
| H10 | reciprocity[t] | abs_ret_fwd1 | secondary | positive |

Controls in EVERY regression: `log(volume[t])`, `market_ret_loo[t]`
(DC9: market return EXCLUDES stock i on its own row), entity + time effects.

## 3. Estimation & inference rules

1. SEs (SV2 chain): Driscoll-Kraay (bartlett kernel, bandwidth=5) primary →
   double-cluster (entity, time) → Fama-MacBeth (NW-HAC on β series) →
   cluster-by-entity ONLY with explicit caveat. **HC1/robust refused in code** (R3).
2. Condition-number pre-purge: if κ(design) > 30, drop most collinear feature
   (expected: seller_hhi vs buyer_hhi) BEFORE any significant finding is quoted.
3. Placebo (R2): anomaly_score permuted with the 200 pre-declared seeds
   (826001..826200), regression re-estimated per permutation. Headline β is
   "significant" iff (placebo share ≤ 0.05) AND BH-adjusted p ≤ 0.10.
4. DC13 outcome-lag test: anomaly_score[t] vs |ret[t-1]| must show NO effect;
   a hit means specification error → investigate BEFORE reporting.
5. Standardised β and bp-of-return magnitude reported for every coefficient
   (DC10): |β_std| < ~2 bps on return outcomes = "statistically detectable but
   economically negligible". MDE reported at 80% power, α=0.05 (DC6).
6. IPS panel unit-root test per regressor; I(1) series entered in differences (DC5).
7. Regressors winsorised at 1/99 **training-fold** percentiles; VIF>10 dropped (DC8).

## 4. Anomaly scoring discipline (R1/R7/DC7)

* 4 anchored expanding purged folds: sessions cut at linspace(0, n, 6) → 5
  chunks; chunk 0 = warm-up train, fold f trains on everything strictly
  before its test chunk and tests on that chunk purged at its start (the
  2021-22 bubble tail and 2024 both receive OOS scores). Purge gap = 6
  sessions (horizon 1 + embargo 5), strict-gap definition unchanged:
  test_start_pos = train_end_pos + gap + 1. DEVIATION from the original
  sequential-pairs default, logged in docs/analysis_deviations.md
  2026-11-09 BEFORE any test-fold data was observed; sequential pairs are
  kept as the Phase-5 robustness variant.
* Per fold: winsor + standardise on TRAIN rows; IsolationForest
  (n_estimators=200, contamination='auto', random_state=if_seed(k) from seeds.py)
  fitted on TRAIN; test rows scored by that model. -decision_function orientation.
* 90th-percentile event threshold comes from the TRAIN-FOLD anomaly distribution
  of that fold — never the pooled/test distribution.
* SV5 fallbacks (Mahalanobis, z-score-sum-of-squares) pre-declared; both run if
  IF degenerates, sensitivity table compares estimators.

## 5. Regime split (R8)

If 2021–2024 scope: regime = calendar (2021-2022 bubble vs 2023-2024 normal),
per brief. If 2024–2026 scope: regime = drawdown/momentum state of the
equal-weight 10-stock OHLCV portfolio index (states: peak-to-trough <20% =
"calm", drawdown >20% or drawup from trough >30% = "stressed/bubble-like");
thresholds chosen ON THE OHLCV TRAINING-FOLD SAMPLE ONLY. Interaction term
feature×regime reported with p-value.

## 6. Event study (SV3 declarations)

Market model estimated on 60 non-event sessions; illiquid-stock trigger R²<0.1
or |β|>3 → market-adjusted returns; raw returns only as last resort with
joint-test caveat. CAR path from t-5 to t+5.

## 7. Replication & robustness (Phase 5 pre-declaration)

Leave-one-stock-out stability; alternative windows t+2/t+3/t+5; alternative
EoD thresholds (top 1%, top 10%); Mahalanobis/LOF/OC-SVM rank-corr vs IF;
drop-bubble-period re-run; 5-stock external cross-section replication.

## 8. Seed registry (DC14)

Values live in `src/nepsemsc/utils/seeds.py` (single source of truth):
GLOBAL_SEED=20261108, IF_FOLD_SEEDS=[917501,917502,917503,917504],
placebo permutations = seeds 826001..826200, NETWORK_LAYOUT_SEED=11082026.
