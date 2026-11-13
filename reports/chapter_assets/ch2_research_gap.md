# Chapter 2 — Research gap · scaffold (v2.0.1)

**Status:** structural scaffold only. No thesis prose and **no bibliographic
claims**. The student must verify every citation. This file exists so the
chapter handoff has an explicit gap statement slot rather than an invented one.

---

## 2.1 What is established

- [ ] Broker-level trading relationships can carry information beyond aggregate
  price/volume (verify anchors in `ch2_literature_matrix.csv`).
- [ ] Concentration and liquidity are linked in intermediated markets; the sign
  and mechanism are market-dependent (verify anchors).
- [ ] Frontier-market microstructure differs from developed-market regularities
  in coverage, liquidity, and intermediation (verify anchors).

## 2.2 What is unresolved

- [ ] Whether daily broker-network topology **predicts** next-session
  returns/volatility out of sample, rather than merely describing same-day
  activity.
- [ ] Whether any apparent predictive content survives multiplicity, dependence,
  liquidity, distributional and specification checks.
- [ ] Whether effects are market-wide or localised to the most-traded tier.

## 2.3 NEPSE-specific gap

- [ ] No verified NEPSE study uses row-level floorsheet broker identities to
  build daily broker networks over the 2021–2024 bubble/normal cycle.
- [ ] Existing NEPSE evidence does not separate self-loop volume,
  concentration, reciprocity and end-of-day concentration as distinct
  predictive constructs.
- [ ] No NEPSE study reports a pre-declared multiplicity/dependence battery for
  this design.

## 2.4 Thesis contribution (claim slots)

- [ ] **Design contribution:** pre-declared 10-test grid, anchored purged
  walk-forward, train-only scoring and constants (`docs/analysis_plan.md` §2–§4;
  EXP-0004a/b).
- [ ] **Measurement contribution:** daily broker-network constructs from
  floorsheet identities, with source/licence/quality audit
  (`data/metadata/corpus_files_sha256.csv`; EXP-0002b/c).
- [ ] **Inference contribution:** v2 adjudication across RW, WB, four-SE
  concordance, liquidity, EGARCH, quantile tails, trade size, specification
  curve and subgroups (`outputs/tables/v2_final_headline_set.csv`; EXP-0012).
- [ ] **Negative-result contribution:** the IF anomaly-score channel is null;
  one moderate association survives; all 1-SD effects are below the declared
  cost floor (`reports/limitations.md`; EXP-0008b/e, EXP-0011f).

## 2.5 Boundary conditions / falsification

- [ ] Tier-10 coverage: 0/5 external replication at ranks 11–15 (limitation L2;
  EXP-0005f).
- [ ] Predictive, not causal: no instrument or exogenous broker shock
  (limitation L1; EXP-0004b).
- [ ] Licence chain: tier1 OHLCV pending; figures restricted (limitation L4;
  EXP-0002d).
- [ ] Falsification conditions listed in `reports/limitations.md` §falsification.

---

## Citation keys

`EXP-0002b`, `EXP-0002c`, `EXP-0002d`, `EXP-0004a`, `EXP-0004b`, `EXP-0005f`,
`EXP-0008b`, `EXP-0008e`, `EXP-0011f`, `EXP-0012`.

## Verified assets

- `reports/chapter_assets/ch2_literature_matrix.csv`
- `reports/chapter_assets/ch2_comparison_table.csv`
- `docs/analysis_plan.md` (v1 frozen)
- `reports/limitations.md` (v2 living)
