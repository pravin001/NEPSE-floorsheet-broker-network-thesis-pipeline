# Chapter 2 — Literature and research gap · handoff pack (v2.0.1)

**Status:** scaffold + verified asset manifest. **No thesis prose and no
invented citations.** The student completes and verifies the literature matrix,
gap statement and comparison table.

**Rule:** the old Stage-5 map named “literature matrix / research_gap /
comparison table” but none existed. This pack creates empty, auditable scaffolds
only; it does not assert bibliographic facts.

---

## 2.1 Broker networks and information flow

**Claim slot.** Broker-level trading relationships can carry information beyond
aggregate price and volume; the thesis tests whether daily topology predicts the
next session.

- Table 2.1 slot: literature matrix rows `LIT-BN`.
- Source: `reports/chapter_assets/ch2_literature_matrix.csv`.
- Candidate anchors are marked `TODO(student): verify bibliographic metadata`.

**Citation keys:** EXP-0002b (broker identities observable), EXP-0003a
(network metrics), EXP-0004b (predictive grid).

## 2.2 Concentration, liquidity and manipulation

**Claim slot.** Concentration can proxy for liquidity provision or for
crowding/distortion; the thesis separates four constructs rather than treating
“concentration” as one variable.

- Table 2.1 slot: literature matrix rows `LIT-CONC`.
- Constructs: `buyer_hhi` (H4/H5), `reciprocity` (H6/H10), `self_loop_ratio`
  (H1/H9), `end_of_day_concentration` (H7/H8).
- Definition source: `reports/chapter_assets/ch3_feature_dictionary.csv`.

**Citation keys:** EXP-0003a, EXP-0004b, EXP-0012; limitation L10 (no
manipulation ground truth; do not call self-loop volume wash trading).

## 2.3 Frontier-market and NEPSE evidence

**Claim slot.** NEPSE-specific evidence is thin; the thesis contributes a
row-level, broker-identified, four-year panel and a pre-declared inference
battery.

- Table 2.1 slot: literature matrix rows `LIT-FRONTIER` and `LIT-NEPSE`.
- Gap scaffold: `reports/chapter_assets/ch2_research_gap.md` §2.3.
- Boundary anchors: `reports/limitations.md` L2/L5.

**Citation keys:** EXP-0002b (corpus), EXP-0005f (tier locality), EXP-0012.

## 2.4 Positioning and comparison

**Claim slot.** The comparison table positions this thesis by market, sample,
data granularity, network measure, method, outcome and finding; each row must be
verified before it enters the thesis.

- Table 2.2 slot: comparison table (`CMP-TODO-*` rows are intentionally empty).
- Source: `reports/chapter_assets/ch2_comparison_table.csv`.
- Hypothesis mapping: `docs/analysis_plan.md` §2 (v1 frozen).

**Citation keys:** EXP-0004b, EXP-0012.

---

## Verified asset manifest

Machine-readable: `reports/chapter_assets/ch2_asset_manifest.csv`.

| asset | role | version | EXP keys |
|---|---|---|---|
| `reports/chapter_assets/ch2_literature_matrix.csv` | matrix scaffold | v2 handoff | EXP-0014 |
| `reports/chapter_assets/ch2_research_gap.md` | gap scaffold | v2 handoff | EXP-0014 |
| `reports/chapter_assets/ch2_comparison_table.csv` | comparison scaffold | v2 handoff | EXP-0014 |
| `docs/analysis_plan.md` | hypothesis mapping | v1 frozen | EXP-0004b |
| `reports/limitations.md` | boundary conditions | v2 living | EXP-0012 |
