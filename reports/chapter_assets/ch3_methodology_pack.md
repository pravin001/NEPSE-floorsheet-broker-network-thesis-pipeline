# Chapter 3 — Methodology · handoff pack (v2.0.1)

**Status:** skeleton + verified asset manifest. **No thesis prose.** The student
writes the methods narrative; this pack supplies section slots, verified sources
and EXP keys.

**Frozen design sources:** `docs/analysis_plan.md` (v1, byte-frozen) and
`docs/analysis_plan_v2_extension.md` (v2, pre-declared before any v2 result).

---

## 3.1 Research design and epistemic frame

**Claim slot.** The design is predictive, not causal: panel fixed effects plus
DK/DC/FM/WB inference, with no instrument, exogenous broker shock, or
manipulation ground truth.

- Table 3.0 slot: design summary (unit of observation, panel dimensions,
  outcomes, controls, estimators).
- Sources: `docs/analysis_plan.md` §1/§3; `README.md` epistemic frame.
- Boundary: `reports/limitations.md` L1.

**Citation keys:** EXP-0004b, EXP-0009c/d, EXP-0012.

## 3.2 Pre-declaration, governance and freeze

**Claim slot.** All v1 constants and hypotheses were frozen before scoring; all
v2 protocols were declared before v2 results; post-freeze changes require a new
experiment row.

- Table 3.1 slot: pre-declaration timeline (v1 plan, fold-mode deviation,
  v2 extension, Stage-6 freeze).
- Sources: `docs/analysis_plan.md`; `docs/analysis_plan_v2_extension.md` §V2-0;
  `configs/v2_freeze/freeze_manifest.csv`.
- Guard: `tests/test_freeze_v2.py`.

**Citation keys:** EXP-0007, EXP-0008a, EXP-0013.

## 3.3 Anchored purged walk-forward

**Claim slot.** Four anchored expanding folds score 938 corpus sessions; each
fold trains strictly before its test chunk, purges 6 sessions, and fits
winsorisation, standardisation, Isolation Forest and the q90 threshold on TRAIN
rows only.

- Figure 3.1 slot: walk-forward schematic
  (`reports/chapter_assets/ch3_walk_forward_diagram.md`).
- Table 3.2 slot: fold boundaries and OOS counts.
- Source: `docs/analysis_plan.md` §4.

**Citation keys:** EXP-0004a (scoring), EXP-0011a (effective N), EXP-0005g
(sequential variant).

## 3.4 Feature and outcome definitions

**Claim slot.** Ten tests use four network features plus the anomaly score, two
forward outcomes, two controls, and (in v2) three liquidity controls; every
definition is traceable to code or the frozen plan.

- Table 3.3 slot: feature dictionary
  (`reports/chapter_assets/ch3_feature_dictionary.csv`).
- Sources: `docs/analysis_plan.md` §2; `src/nepsemsc/network/`;
  `src/nepsemsc/ml/panel_data.py`; `src/nepsemsc/features/liquidity.py`.

**Citation keys:** EXP-0003a/b, EXP-0004b, EXP-0009a.

## 3.5 Estimation and inference

**Claim slot.** DK(bw=5) is primary; DC-v2, FM and entity-clustered WB are
concordance checks; BH q=.10 is the v1 gate and Romano–Wolf q=.10 is the v2
family-wise gate.

- Table 3.4 slot: estimator matrix (assumption, clustering, role, EXP).
- Sources: `docs/analysis_plan.md` §3;
  `docs/analysis_plan_v2_extension.md` §V2-1/§V2-2.
- Guard: `tests/test_se_spec.py` (SE family) and `tests/test_wild_bootstrap.py`.

**Citation keys:** EXP-0004b, EXP-0008b, EXP-0009c/d.

## 3.6 Event study and robustness protocols

**Claim slot.** The event study reconstructs v1 ARs exactly and adds BMP,
Corrado rank and date-clustered inference; the robustness battery covers LOO,
horizons, EoD thresholds, alternative scorers, drop-bubble, external top-5 and
sequential folds.

- Table 3.5 slot: protocol matrix (test, pre-declared variant, EXP, verdict).
- Sources: `docs/analysis_plan.md` §6/§7;
  `docs/analysis_plan_v2_extension.md` §V2-2/§V2-4.

**Citation keys:** EXP-0004e, EXP-0005a–g, EXP-0011e.

---

## Verified asset manifest

Machine-readable: `reports/chapter_assets/ch3_asset_manifest.csv`.

| asset | role | version | EXP keys |
|---|---|---|---|
| `docs/analysis_plan.md` | v1 frozen design | v1 | EXP-0004a/b |
| `docs/analysis_plan_v2_extension.md` | v2 pre-declaration | v2 | EXP-0008a–0013 |
| `configs/v2_freeze/freeze_manifest.csv` | binding-file hashes | v2 | EXP-0013 |
| `reports/chapter_assets/ch3_walk_forward_diagram.md` | Figure 3.1 scaffold | v2 handoff | EXP-0004a, EXP-0013 |
| `reports/chapter_assets/ch3_feature_dictionary.csv` | Table 3.3 scaffold | v2 handoff | EXP-0003a/b, EXP-0009a |
