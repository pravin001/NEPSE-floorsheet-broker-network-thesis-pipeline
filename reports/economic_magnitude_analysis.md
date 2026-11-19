# Economic magnitude and cost-benefit (Stage 4) — v2.1.0 update

**Stage 4 of the v2.0 A++ upgrade** · pre-declaration:
`docs/analysis_plan_v2_extension.md` §V2-4 (written before any v2 result).
Runner of record: `scripts/run_v2_stage4.py` · log:
`outputs/logs/v2_stage4.log` · experiment EXP-0011f · deviation #26.

**v2.1.0 update (2026-11-19).** Rebuilt after the reciprocity correction
(EXP-0015). H7 and H4 are unchanged; H10 roughly doubled from +9.492 to
+20.642 bp/SD, so its cost multiple improved from 3.16–5.27× to **1.45–2.42×
below** the floor. The v2.0.2 version of this note is preserved in the
superseded record (`outputs/tables/superseded_v2_0_2/` and
`reports/reciprocity_correction.md`). This remains a **framing exercise**, not
a trading strategy, not a backtest, and not a new estimate.

---

## 1 · Declared cost parameters

| parameter | declared value | treatment |
|---|---|---|
| explicit round-trip cost | **30–50 bp** (plan: commissions ≈0.3–0.5%) | floor; excludes brokerage, bid–ask spread and CNS carry |
| brokerage | not quantified | excluded → true hurdle is **higher** |
| spread + CNS carry | not quantified | excluded → true hurdle is **higher** |
| holding horizon | t+1 session (`ret_fwd1` / `abs_ret_fwd1`) | no annualisation; overlapping windows make annualised figures meaningless |
| engagement | 1 SD of the train-fold-standardised feature | a statistical unit, not a position size |

Because the 30–50 bp range omits three real cost components, every “cost
multiple” below is an **upper bound on the net edge**. A strategy that fails
against the floor fails against the true hurdle.

---

## 2 · Headline conversions

The three economic candidates named in the pre-declaration:

| test | effect (bp per 1 SD) | direction | cost multiple (30 bp) | cost multiple (50 bp) | standalone tradable at 1 SD? |
|---|---:|---|---:|---:|---|
| H7 EoD → \|ret\| | **+3.952** | positive | **7.59×** short | **12.65×** short | **No** |
| H10 reciprocity → \|ret\| | **+20.642** | positive | **1.45×** short | **2.42×** short | **No** |
| H4 buyer HHI → ret | **+7.510** | opposite sign (post hoc) | **3.99×** short | **6.66×** short | **No** (and cannot be traded as declared) |

Read the multiples as “the gross 1-SD effect is this many times **smaller** than
the cost floor.” H10 is the closest to viability and still needs a 1.5–2.4×
larger gross move to break even. H7 needs 7.6–12.7×.

Break-even coefficients:

| test | break-even β at 30 bp | break-even β at 50 bp | observed β |
|---|---:|---:|---:|
| H7 | +30.0 bp/SD | +50.0 bp/SD | +3.95 |
| H10 | +30.0 bp/SD | +50.0 bp/SD | +20.64 |
| H4 | −30.0 bp/SD (declared sign) | −50.0 bp/SD | +7.51 (wrong sign) |

Linear extrapolation to 3–13 SD is **not** supported by the data: the features
are winsorised at the 1st/99th percentile within fold, and the quantile panel
shows the H10 effect is strongly tail-concentrated (τ=.90: +34.64 bp), not
linear. The break-even table is an accounting identity, not a forecast.

---

## 3 · Why the 1-SD framing is already generous

1. **The coefficients are conditional averages.** They are not the return of a
   trade; they are the average next-session outcome associated with a one-SD
   higher feature value, holding the two controls fixed.
2. **The outcome is absolute return for H7/H10.** A positive \|ret\| effect can
   be monetised only with a direction forecast; the same feature may predict
   volatility without predicting the sign. H8 (signed return) is negative but
   fragile, so the directional leg is not established.
3. **The horizon is one session.** Turnover at daily frequency makes the
   all-in cost per unit of exposure at least the declared floor, and likely
   higher because the strategy must re-enter.
4. **Overlapping windows.** The 7,116-row panel has 723 dates and 12 symbols;
   observations are not independent trades. The effective sample is smaller
   than the row count (n_effective = 6,383), so the precision of the economic
   estimate is lower than the raw n suggests.
5. **H4 is post hoc and wrong-signed.** Its 7.51 bp cannot be counted as an
   economic candidate; it is an exploratory association that contradicts the
   pre-registered direction.

---

## 4 · Conditional / stacked tradability (speculative listing, not a claim)

The only subgroup cells that are directionally interesting are also below the
cost floor:

| candidate | estimate | raw p | Bonferroni p | vs 30 bp floor |
|---|---:|---:|---:|---|
| H10, bottom-7 turnover tier | **+22.715 bp** | **.0031** | **.0183** | 1.3× short |
| H7, small-size group | +7.020 bp | .0272 | .1629 | 4.3× short |
| H7, bottom-7 turnover tier | +4.817 bp | .0508 | .3050 | 6.2× short |

A hypothetical stack of H10 + H7 in the bottom-7 tier would be ~27.5 bp if the
two effects were additive and independent. Neither condition is established:
the signals share the same small/illiquid segment, the H10 × tier interaction is
null (p .152), and the sum is still below the 30 bp floor. The H10 bottom-7 cell
now survives its Bonferroni family, but a subgroup survivor is not a new
headline and is not a portfolio. This is listed only because the
pre-declaration asks for the conditional possibility to be acknowledged; it is
**not** a recommended strategy and **not** a result.

---

## 5 · Verdict

1. The frozen effects are **statistical and informational**, not standalone
   tradable alpha at 1-SD engagement.
2. H10 is the strongest economic candidate at +20.64 bp/SD, but it is still
   1.45–2.42× below the explicit-cost floor and its Stage-1 placebo-outcome
   diagnostic is the largest in the grid (+44.78 bp association with past
   \|ret\|, p 8.7e-10), so part of its predictive content is persistence.
3. H7 and H4 are further below the floor; H4 additionally has the wrong sign.
4. Conditional/stacked tradability remains **speculative**. Any future test
   would need (a) a directional signal, (b) a portfolio construction that maps
   feature values to position sizes, and (c) all-in cost data including spread
   and CNS carry. None of those is in this thesis.

The correct thesis sentence is therefore: *the network features carry
measurable next-session information, but the magnitudes are an order of
magnitude below the cost of acting on them at the engagement levels studied.*

---

## 6 · Pointers

| artifact | content |
|---|---|
| `outputs/tables/economic_magnitude.csv` | per-test effect, direction, cost range, multiples, tradability flag |
| `outputs/tables/hypothesis_grid_results_v2.csv` | frozen β / p / n_effective source rows |
| `outputs/tables/heterogeneity_subgroups.csv` | subgroup cells quoted in §4 |
| `outputs/tables/quantile_regression.csv` | tail shape behind the non-linearity caveat |
| `outputs/tables/hypothesis_grid_results_rw.csv` | RW p-values behind the “not a headline” status of H7/H4 |
