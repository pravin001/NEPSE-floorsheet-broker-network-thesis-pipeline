# Chapter 1 — Introduction · handoff pack (v2.0.1)

**Status:** skeleton + verified asset manifest. **No thesis prose.** The student
writes every paragraph. Numbers below are claim slots with their EXP keys; quote
them only from the cited artefact.

**Canonical result table:** `outputs/tables/v2_final_headline_set.csv`.

---

## 1.1 Frontier-market problem

**Claim slot.** NEPSE is a thin, retail-heavy frontier exchange where every
floorsheet row identifies buyer and seller brokers, making daily broker-network
structure observable without a proprietary dataset.

- Scope anchors: `README.md` (epistemic frame); `docs/analysis_plan.md` §1
  (2021–2024 window, top-10 universe, DC1 per-fold selection).
- Boundary anchors: `reports/limitations.md` L2 (tier-10 coverage), L5 (single
  exchange), L10 (self-loop interpretation).
- **No table/figure slot** — narrative only.

**Citation keys:** EXP-0002a, EXP-0002b, EXP-0012.

## 1.2 Research question and pre-declared hypotheses

**Claim slot.** The thesis tests 5 broker-network features × 2 forward outcomes
= 10 pre-registered hypotheses, with a declared sign for each and BH-FDR q=.10.

- Table 1.1 slot: hypothesis grid (feature, outcome, predicted sign, status).
- Source: `docs/analysis_plan.md` §2 (v1 frozen; do not edit).

**Citation keys:** EXP-0004b (executed grid), EXP-0008a (v2 governance).

## 1.3 Headline preview

**Claim slot.** After v2 adjudication, H10 (reciprocity → next-day absolute
return) is the sole `HEADLINE_MODERATE` association (+9.492 bp/SD; DK p=.0138;
RW p=.081; WB p=.009; MODERATE SE concordance; liquidity and EGARCH pass; both
tails increasing). H4 is `EXPLORATORY_POST_HOC`; H6/H7/H8 are `NULL_FRAGILE`;
H1/H2/H3/H5/H9 are `NULL_POWERED`.

- Table 1.2 slot: canonical final headline set (10 rows × 11 brief columns).
- Source: `outputs/tables/v2_final_headline_set.csv`.

**Citation keys:** EXP-0012 (canonical set), EXP-0008b (RW), EXP-0009c/d
(WB/SE), EXP-0010a/b (EGARCH/quantiles).

## 1.4 Economic significance preview

**Claim slot.** At 1 TRAIN-SD engagement, the H10 effect is 3.16–5.27× below
the declared 30–50 bp round-trip explicit-cost floor; H7 is 7.59–12.65× below
and H4 is 3.99–6.66× below. None is standalone tradable at 1 SD.

- Table 1.3 slot: cost-benefit table.
- Source: `outputs/tables/economic_magnitude.csv`;
  `reports/economic_magnitude_analysis.md`.

**Citation keys:** EXP-0011f.

## 1.5 Contribution and roadmap

**Claim slot.** The contribution is a pre-declared, reproducible predictive
design plus an honest negative/fragile result set, not a trading strategy or a
causal manipulation claim.

- Roadmap slots: Ch.2 literature/gap; Ch.3 design; Ch.4 data engineering;
  Ch.5 results; Ch.6 discussion.
- Crosswalk: `docs/chapter_artifact_map.md`.

**Citation keys:** EXP-0007 (v1 freeze), EXP-0013 (v2 freeze).

---

## Verified asset manifest

Machine-readable: `reports/chapter_assets/ch1_asset_manifest.csv` (one SHA-256
per asset). Every path is covered by `scripts/audit_chapter_map.py` and
`tests/test_chapter_map_integrity.py`.

| asset | role | version | EXP keys |
|---|---|---|---|
| `README.md` | scope + epistemic frame | v2 handoff | EXP-0002b, EXP-0012 |
| `docs/analysis_plan.md` | pre-declared hypotheses/design | v1 frozen | EXP-0004b |
| `reports/limitations.md` | boundary conditions | v2 living | EXP-0012 |
| `outputs/tables/v2_final_headline_set.csv` | canonical headline set | v2 | EXP-0012 |
| `outputs/tables/economic_magnitude.csv` | cost-benefit arithmetic | v2 | EXP-0011f |
| `reports/economic_magnitude_analysis.md` | cost-floor rationale | v2 | EXP-0011f |
