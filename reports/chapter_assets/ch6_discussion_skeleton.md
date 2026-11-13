# Chapter 6 — Discussion · skeleton (v2.0 A++)

**Stage-5 artifact.** Bullet skeleton + one-sentence claim per numbered
subsection; the student writes prose. No thesis paragraphs here.

Structure note: the 19-day brief is not present in this repository, so the
brief's §5.3 discussion list cannot be transcribed literally. The structure
follows `docs/chapter_artifact_map.md` (negative-result framing → limitations
→ PhD extensions → broker persistence appendix) and the Stage-1–4 findings.
Logged as Stage-5 deviation #28.

Path refresh (v2.0.1 handoff): every table path in this skeleton now resolves
to a tracked v2 artefact and is listed in the verified crosswalk
(`docs/chapter_artifact_map.md`), audited by `scripts/audit_chapter_map.py`.
Figures under `outputs/figures/` are real but remain licence-restricted and are
not part of the derived deposit (`reports/limitations.md` L4).

Severity vocabulary for §6.3: `CRITICAL` / `MAJOR` / `MINOR`, as defined in
`reports/limitations.md`.

---

## 6.1 Negative-result framing

**Claim (one sentence):** The thesis's central result is a disciplined mix of
one moderate predictive association and a set of null or fragile results, not
a portfolio of tradable anomalies.

- The IF anomaly-score channel is null out of sample: H2 placebo share .800,
  H3 .640; event-study mean CAR +12.86 bp (p .569); no BH pass survives RW
  (EXP-0004c/e, EXP-0008b/e).
- Only H10 survives RW q = .10 (p .081); H6 (p .120), H7 (.159) and H8
  (.203) are demoted to `NULL_FRAGILE`; H4 is opposite-sign
  `EXPLORATORY_POST_HOC` (EXP-0008a/b, EXP-0012).
- All 1-SD effects are below the declared 30–50 bp cost floor: H10
  3.16–5.27× below, H7 7.59–12.65×, H4 3.99–6.66× (EXP-0011f).
- Negative results are the registered object, not a failure of the design:
  MDE classifies H1/H2/H3/H5/H9 as `NULL_POWERED` (EXP-0008c).

**Assets.** Table 5.3 (`v2_final_headline_set.csv`);
`reports/economic_magnitude_analysis.md`; `reports/exploratory_findings.md`.

---

## 6.2 Predictive, not causal: what the coefficients mean

**Claim (one sentence):** Every coefficient is a predictive association on a
12-stock panel; no estimate identifies a causal effect of broker-network
structure.

- No instrument, exogenous broker shock, or event timing at broker level;
  panel FE + DK/DC/FM/WB only (EXP-0004b, EXP-0009c/d).
- **Self-loop ratio** (`self_loop_ratio`): buyer and seller are the same
  broker; volume counts the buyer side (EXP-0002e); the ratio is mechanically
  high for single-broker trades and must not be read as manipulation without
  an order-level benchmark. H1/H9 are null (EXP-0004b).
- **H4 concentration premium**: buyer HHI predicts *higher* next-session
  return (+7.51 bp), opposite to the declared liquidity-discount direction;
  normal-era driven (+10.49 bp), FM p .0082 (EXP-0004b/e).
- **H10 persistence caveat**: reciprocity carries the largest past-|ret|
  association in the grid (+19.69 bp vs +9.49 bp forward), so part of its
  content is persistence (EXP-0008d).
- **Tier-10 coverage**: OOS panel is the per-fold top-10 (12 symbols); ranks
  11–15 external replication passes 0/5 BH (raw p ≥ .23) and magnitudes
  shrink 2–4× → tier-local, not market-wide (EXP-0005f).
- **Single exchange**: NEPSE only; no cross-market replication (EXP-0002b).
- **No intraday timestamps**: floorsheet rows are not execution-ordered;
  contract_no is daily-global; no order-flow/sequence statistic is claimed
  (EXP-0002b/c, EXP-0003a).

**Assets.** `reports/limitations.md` (CRITICAL rows L1–L4);
`README.md` (epistemic frame); `docs/analysis_plan.md` §3;
`reports/broker_pilot_phd_seed.md`.

---

## 6.3 Limitations

**Claim (one sentence):** The conclusions are bounded by corpus coverage,
licence restrictions, floorsheet structure, design conventions, and the
fragility of the surviving estimates.

- Full v2 table: `reports/limitations.md` (v1 `docs/limitations.md` remains
  frozen).
- CRITICAL:
  - predictive-not-causal interpretation (all tests);
  - tier-10 coverage and 0/5 external replication;
  - no intraday timestamps / execution order;
  - single-exchange (NEPSE) scope;
  - licence chain: tier1 OHLCV licence pending → figures RESTRICTED;
    index licence unstated; data licences per `provenance_manifest.csv`.
- MAJOR:
  - corpus gaps 2021-09-01 and 2023-11-27 (938/940 sessions);
  - 2023-02-16 `contract_no_defect` (ordering features exclude the day);
  - H8 fragility: 1% EoD cutoff p .7634, normal era p .1703, MDE ratio
    1.426 (`NULL_UNDERPOWERED`);
  - H10 dependence: FM p .2896, MODERATE not STRONG concordance;
  - self-loop interpretation (buyer = seller; buyer-side volume);
  - circuit-breaker split `NOT_EXECUTED` — no flag in corpus or verified
    archive; no proxy fabricated;
  - liquidity verdict: three proxies, no direct spread/quote data; H1/H2/H3
    relative moves up to +37%/−8% but remain null;
  - event-study overlap: 68.2% of events share a date; p-values upper bounds;
  - subgroup grid underpowered: no Bonferroni survivor (min .1434);
  - broker panel: monthly aggregation, 18/48 complete graphs, descriptive
    only.
- MINOR:
  - 2021-03-07→03-08 relabel (evidence triple);
  - 752 duplicate keys (506 exact / 246 signature-conflict non-merged);
  - broker-ID source-format defect (275,590 dotted rows; 37/7,126 OOS rows;
    signs unchanged, H8 p .0563);
  - junk scrape rows (19 pairs + 4 empty-symbol rows; NULL volume);
  - dashboard extracts-only (no full-corpus read; no new inference).

**Assets.** `reports/limitations.md`; EXP-0002b/c/e, EXP-0004c/d/e,
EXP-0005c/e/f, EXP-0008c, EXP-0009a/b/d, EXP-0011c/d/e, EXP-0012.

---

## 6.4 Broker persistence, core–periphery, and PhD extensions

**Claim (one sentence):** The descriptive broker panel documents a dense,
stable top-50 club and an 11-broker core, but monthly aggregation and
complete-graph degeneracy block structural interpretation.

- Panel: 48 months, **91 canonical brokers**, **3,026 broker-months**;
  active set 50–90 (median 51) (EXP-0011c).
- Core: top-decile betweenness AND ≥6 top-decile months in trailing 12;
  **11 brokers / 219 core broker-months**; leaders 58 (43), 34 (41), 45 (40),
  49 (38) (EXP-0011c).
- Transitions: 183 core→core; 28 core→periphery; 36 periphery→core
  (EXP-0011c).
- Top-50 Jaccard .9669 overall; **1.000 when ≤60 active** (31/47 transitions)
  vs .9084 when >60 active (17/47) (EXP-0011c).
- **18/48 months are exactly complete graphs** → betweenness ≡ 0; 1,071/3,026
  broker-months (35.4%) zero betweenness; 63 core months zero. The declared
  rule is retained; eigenvector/value cores agree at Jaccard .837/.882
  (EXP-0011c).
- Snapshots: 2021-10 = 51 nodes / 1,275 edges / 4 core; 2023-06 = 52 / 1,318
  / 5 (EXP-0011c).
- Source-format defect: 275,590 dotted-ID rows on 15 days; canonicalisation
  `Xs.0 → zero-padded integer`; 37/7,126 OOS rows affected; signs unchanged
  (EXP-0011c).
- PhD questions: network formation, core/liquidity provision, source-vintage
  discontinuity as measurement change, centrality → price impact with
  exogenous broker shocks (EXP-0011c; `reports/broker_pilot_phd_seed.md`).

**Assets.** `outputs/tables/broker_level_panel.csv`;
`outputs/tables/broker_top50_persistence.csv`;
`outputs/tables/broker_core_transitions.csv`;
`outputs/tables/broker_core_definition_sensitivity.csv`;
`outputs/figures/broker_network_bubble.png`;
`outputs/figures/broker_network_normal.png`;
`reports/broker_pilot_phd_seed.md` (Appendix B).

---

## 6.5 Implications, falsification, and next steps

**Claim (one sentence):** The results support an information-content
interpretation of network concentration, not a tradable-alpha or policy claim,
and the thesis states the conditions under which that reading would change.

- H10 +9.49 bp/SD is 3.16–5.27× below the explicit-cost floor; no directional
  signal is established for the |ret| outcomes (EXP-0011f).
- Tier-local: the effect family is concentrated in the most-traded tier and
  does not replicate at ranks 11–15 (EXP-0005f).
- Falsification conditions:
  - a licensed broker-level dataset with identities, licence types, or
    outages;
  - intraday execution timestamps or order-level data;
  - a directional signal with all-in cost data (spread + CNS carry);
  - cross-exchange or full-market replication;
  - a circuit-breaker / limit-hit flag enabling the missing subgroup test.
- Dashboard is extracts-only and computes no new inference (EXP-0006).
- Deposit/reproducibility pointers: `docs/reproducibility.md`,
  `docs/deposit_readme.md` (Stage 6), `CITATION.cff` (Stage 6),
  `LICENSE` (Stage 6).

**Assets.** `reports/limitations.md` §3 (what would change the conclusions);
`docs/reproducibility.md`; Stage-6 deposit files.

---

## Chapter asset checklist

| asset | file | used in |
|---|---|---|
| canonical headline set | `outputs/tables/v2_final_headline_set.csv` | §6.1, Table 5.3 |
| limitations table | `reports/limitations.md` | §6.3 |
| broker panel | `outputs/tables/broker_level_panel.csv` | §6.4 |
| broker summary | `outputs/tables/broker_panel_summary.csv` | §6.4 |
| core sensitivity | `outputs/tables/broker_core_definition_sensitivity.csv` | §6.4 |
| cost-benefit | `outputs/tables/economic_magnitude.csv` | §6.5 |
| exploratory findings | `reports/exploratory_findings.md` | §6.1/§6.2 |
| PhD seed | `reports/broker_pilot_phd_seed.md` | §6.4, Appendix B |
| verified crosswalk | `docs/chapter_artifact_map.md` | all sections |
| audit guard | `tests/test_chapter_map_integrity.py` | build check |
