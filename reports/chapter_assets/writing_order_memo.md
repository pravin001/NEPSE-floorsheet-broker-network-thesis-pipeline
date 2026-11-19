# Writing-order memo — v2.0.2 pre-write (still current under v2.1.0)

> **Version note (2026-11-19).** The writing order and chapter workflow are
> unchanged. All numeric claims must now come from
> `reports/chapter_assets/key_claims_sheet.md` (v2.1.0) or the corrected
> `outputs/tables/`; v2.0.2 reciprocity-dependent values are superseded.

**To:** the student
**From:** v2.0.2 pre-write sprint
**Date:** 2026-11-14
**Scope:** suggested order for writing the thesis between the engineering freeze
(2026-11-21) and the deadline (2026-11-27). This is a planning memo, not thesis
prose and not a new analysis.

---

## 1. Constraints

1. The analysis is frozen. No chapter may introduce a new estimate, test,
   robustness check or specification search.
2. The writing window is short. The literature review is the long pole because
   it needs reading time, not typing time.
3. Chapter 5 is the core. Protect its time; compress Chapter 1 before
   compressing the results.
4. Every numeric sentence must resolve to an `EXP-*` key and a canonical table
   or figure. The `key_claims_sheet.md` is the quick reference.
5. The handoff packs are scaffolds, not drafts. The student writes every prose
   sentence.

---

## 2. Recommended order (highest payoff first)

| order | chapter / task | why this order | main assets |
|---:|---|---|---|
| 1 | **Chapter 4 — Data engineering** | Fully specified by Table 4.0–4.5; low interpretive risk; fixes the corpus, sample and licence vocabulary that Chapters 3 and 5 reuse. | `ch4_data_engineering_pack.md`; Tables 4.0–4.5b; F1/F2 |
| 2 | **Chapter 3 — Methodology** | Depends on the Chapter 4 sample vocabulary; must be settled before the results narrative so the pre-declared design is unambiguous. | `ch3_methodology_pack.md`; Tables 3.0–3.5; F3 |
| 3 | **Chapter 5 — Results** | The core contribution. Write the descriptive/robustness sections first, then the v2 adjudication, then the canonical set. | `ch5_results_skeleton.md`; Tables 5.1–5.7e; F4–F9 |
| 4 | **Chapter 6 — Discussion** | Depends on the final classification and the cost-floor result; should not be written before Table 5.3 is fixed. | `ch6_discussion_skeleton.md`; Table 5.3; F9/F10 |
| 5 | **Chapter 1 — Introduction** | Summarises claims that are only stable after Chapters 3–6; write last, with the abstract. | `ch1_introduction_pack.md`; Tables 1.1–1.3 |
| 6 | **Chapter 2 — Literature** | Runs in parallel from the first day because reading cannot be compressed. Finish before Chapter 1 so the gap statement and contributions are consistent. | `ch2_literature_pack.md`; `ch2_references_scaffold.csv`; Tables 2.1–2.2 |

**Parallel rule.** Start the Chapter 2 reading before the writing week. A
realistic pre-writing target is 5–6 papers per day from 15–21 November, filling
`content_review_status`, `student_section` and `student_notes` as you go. Do not
leave 39 papers for 26 November.

---

## 3. Six-day schedule (22–27 November)

| day | morning | afternoon | stop rule |
|---|---|---|---|
| **22 Nov** | Chapter 4 draft: 4.1 pipeline → 4.2 licences → 4.3 audit | Chapter 2 §2.1 broker networks; finish 5–6 reference notes | If Chapter 4 is not drafted, do not start Chapter 3. |
| **23 Nov** | Chapter 3 draft: 3.1 design → 3.2 pre-declaration → 3.3 folds | Chapter 3 §3.4 features → §3.5 estimator/protocol; Chapter 2 §2.2 | If the fold/feature definitions are unclear, fix them before writing results. |
| **24 Nov** | Finish Chapters 3–4; check every table/figure slot | Chapter 5 §5.1 sample → §5.2 grid → preview Table 5.3; Chapter 2 §2.3 | If Chapter 5 §5.1–5.2 slips, move Chapter 2 §2.3 to the next morning. |
| **25 Nov** | Chapter 5 §5.3 placebo/regime → §5.4 event study → §5.5 robustness | Chapter 5 §5.6.1–5.6.9; finish Chapter 2 and the comparison table | Protect §5.6; it is the v2 contribution. |
| **26 Nov** | Chapter 5 §5.7 canonical set; Chapter 6 §6.1–6.2 | Chapter 6 §6.3–6.5; Chapter 1 §1.1–1.3 | Do not write Chapter 1 before Table 5.3 is final. |
| **27 Nov** | Abstract; cross-chapter consistency; figure/table numbering | Compliance checklist; reference list; final read; buffer | Submit only after the `STUDENT` checklist items are checked. |

This schedule is deliberately front-loaded. If a day slips, protect Chapter 5
and Chapter 2; shorten Chapter 1 or move detail to an appendix rather than
cutting the results or the reference reading.

---

## 4. Section-level sequence

### Chapter 4 (first)

1. §4.1 pipeline architecture — Table 4.0, F1.
2. §4.2 provenance and licensing — Table 4.1. Use the live licence review, not
   the stale “tier1 pending” wording in limitation L4; L4 is hash-audited and
   is not edited.
3. §4.3 corpus audit — Tables 4.2–4.3, F2.
4. §4.4 universe — Tables 4.4a–4.4b.
5. §4.5 clean rebuild and drift — Tables 4.5a–4.5b.

### Chapter 3 (second)

1. §3.1 design — Table 3.0.
2. §3.2 pre-declaration and freeze — Table 3.1.
3. §3.3 anchored purged walk-forward — Table 3.2, F3.
4. §3.4 features and outcomes — Table 3.3.
5. §3.5 estimator and protocol — Tables 3.4–3.5.

### Chapter 5 (third)

1. §5.1 sample, folds, effective N — Table 5.1.
2. §5.2 main grid — Table 5.2; preview the canonical set in Table 5.3.
3. §5.3 placebo, anomaly-score nullity, regime diagnostics — no new numbered
   main-text table; use the placebo/regime assets.
4. §5.4 event study — Table 5.4, F6.
5. §5.5 robustness battery — Table 5.5.
6. §5.6.1–5.6.9 v2 reclassification — Table 5.6 and Tables 5.7a–5.7e; F4, F5,
   F7, F8, F9.
7. §5.7 canonical headline set — return to Table 5.3; do not create a second
   canonical table.

**Why Table 5.3 appears early.** It is previewed in §5.2 when the grid narrows
to the final classification, then discussed in §5.7. That preserves the
existing table slot and avoids a second 10-row headline table.

### Chapter 6 (fourth)

1. §6.1 negative-result framing — Table 5.3.
2. §6.2 predictive, not causal — limitations L1, L3.
3. §6.3 limitations — `reports/limitations.md`; Appendix C.1 if tabulated.
4. §6.4 broker persistence/core–periphery — F10; Appendix B.1.
5. §6.5 implications, falsification, next steps — no new numbers.

### Chapter 1 (last)

1. §1.1 problem and context — Tables 1.1–1.2.
2. §1.2 contribution — Table 1.3; the negative-result contribution.
3. §1.3 roadmap — no new claims.

### Chapter 2 (parallel)

1. §2.1 broker networks and information flow — NET records.
2. §2.2 concentration, liquidity and manipulation — LIQ/MAN records.
3. §2.3 frontier-market and NEPSE evidence — EM/NP records.
4. §2.4 positioning and comparison — Table 2.2; fill every `CMP-TODO-*` row.

---

## 5. Definition of done, per chapter

- Every table and figure slot in the chapter pack is either filled or
  explicitly removed with a reason.
- Every numeric sentence has an `EXP-*` key and a table/figure pointer.
- Every reference has `content_review_status = REVIEWED_<date>`.
- No `TODO(student)`, `CMP-TODO-*`, `NOT_REVIEWED`, or placeholder row remains.
- The chapter's claims match `v2_final_headline_set.csv`; no chapter invents a
  stronger label than the canonical one.
- The chapter does not describe a predictive association as causal, a fragile
  null as a headline, or a 1-SD effect as tradable.
- The student can explain every number without the AI or the scaffold open.

---

## 6. Risk controls

| risk | early warning | response |
|---|---|---|
| Literature reading finishes late | fewer than 25 reviewed references by 24 Nov | stop drafting new sections; read and annotate in the morning, write in the afternoon; cut optional references, not the core 25 |
| Chapter 5 becomes a table narration | every paragraph starts with “Table X shows” | rewrite around the claim, then point to the table; use the key-claims sheet |
| Chapter 1 overclaims | “robust”, “market-wide”, “profitable”, “causal” | replace with the canonical label and the limitation |
| Chapter 4 licence text drifts | “tier1 pending” appears | use Table 4.1 and `reports/licence_review.md`; do not edit L4 |
| Table/figure numbers drift | two different numbers for the same table | use `table_numbering_plan.md`; renumber once, globally |
| Last-day panic | 27 Nov starts with unwritten chapters | the schedule has already failed; protect the examinable core (Ch.3–5) and ask the supervisor about an extension rather than fabricating content |

---

## 7. Do not do

- Do not run a new regression, robustness check or specification search to fill
  a gap in the narrative.
- Do not ask an AI to draft prose, a literature review, a discussion or an
  abstract.
- Do not add a reference that is not in the verified scaffold unless it passes
  the same Crossref/DOI check.
- Do not edit a print CSV by hand; change the source or generator and rerun
  `scripts/make_print_tables.py`.
- Do not upload, push, register a DOI or create a repository record without the
  student's explicit decision.
