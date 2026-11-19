# AI-Use, Research-Integrity and Licence Register (public summary)

**Project:** Broker Networks, Concentration, and Market Integrity in a Frontier
Exchange: Evidence from NEPSE Floorsheets
**Document version:** 2.0.2-prewrite (public summary)
**Last updated:** 2026-11-15
**Status:** public summary. The detailed internal AI-use plan — full model
inventory, approval gates, sprint controls and session-level notes — is
retained in a private audit file outside this repository and is available to
the University on request. This file keeps the factual disclosure and the
licence register that the thesis and chapter crosswalk cite.

This document records the AI assistance and the licence position. It is a
research-integrity record, not legal advice and not a substitute for the
student's institution's rules.

---

## 1. Purpose and scope

The project used AI coding agents inside **OpenCode** for engineering,
verification, documentation scaffolding and figure production. The statistical
design, hypotheses, folds, estimators and interpretation rules were
pre-declared before the relevant results were seen. The frozen analysis is not
re-opened by this summary.

The governing rule: **AI may help build and verify the research
infrastructure; AI must not invent the research, its results, its citations or
its prose.**

---

## 2. Tool and model inventory

| Tool | Model family / identifier | When used | Role on this project |
|---|---|---|---|
| OpenCode | **GLM family** | Early-to-mid engineering build | Pipeline code, tests, notebooks, documentation scaffolding, execution support |
| OpenCode | **DeepSeek family** | Later engineering and v2 freeze work | Code review, verification scripts, robustness plumbing, audit and manifest support |
| OpenCode | **DeepSeek V4.1 Flash Free** (provider `opencode`) | **v2.0.2 pre-write sprint, 2026-11-13 → 2026-11-14** | Independent reproduction checks, licence retrieval and review, static figures, policy rewrite, writing-support assets, suite/commit/tag preparation |

The detailed session record is in the private audit file. If the student
changes model or provider before submission, the change must be added to this
table and to the University disclosure.

---

## 3. Permitted AI roles

AI assistance is permitted for **non-prose research infrastructure**: code
engineering; execution support; verification; data-integrity work;
documentation scaffolding; figure production from frozen tables; and
consistency checks across tables, documents and the experiment register.

---

## 4. Prohibited AI roles

AI must not: invent data, results, citations or quotations; write the thesis
prose or literature review; choose the research question or hypotheses after
seeing results; alter a frozen estimate or classification; make a licence or
ethics decision for the student; or be presented as the author.

---

## 5. Human oversight and approval gates

The student approves the research question, the pre-declared design, the
licence position, the final results and every submission decision. AI-assisted
changes are checked mechanically (hashes, row counts, schema checks, frozen
tables, tests, audits) before they are accepted. Where a check cannot be run,
the item is marked `UNCERTAIN` or `NOT_FOUND`, not asserted.

---

## 6. Reproducibility and provenance controls

Every tracked result is traceable to an experiment-register row and a
provenance-manifest hash. The clean rebuild and freeze records are in
`docs/reproducibility.md`, `configs/v2_freeze/` and the register audit. AI did
not generate the numerical results; it helped write and run the code that did.

---

## 7. Citation and licence integrity

### 7.1 Citations

Every reference must have a real, retrieved DOI or URL, recorded with a
timestamp and the exact source string. An item that does not resolve is marked
`NOT_FOUND` and is not cited. AI may locate and verify metadata; it may not
write the literature-review narrative or invent a supporting quotation. The
Ch.2 scaffold is a list of verified candidates, not a pre-written review.

### 7.2 Data licences

The live licence review is `reports/licence_review.md` (retrieved
2026-11-13T10:21:13Z). Its conclusions are two-layer: the **dataset grant** as
quoted from the source, and the **upstream clarity** where the uploader
scraped or mirrored another service.

| Source | Dataset grant | Upstream / deposit position |
|---|---|---|
| Kaggle `viking303` floorsheets (2021–2023) | CC0: Public Domain | Upstream merolagani rights `UNCERTAIN`; local academic use permitted |
| `socrateai` floorsheets (2024) | MIT-style text, © 2025 SocrateAI | Preserve the notice; upstream rights `UNCERTAIN` |
| Kaggle `rohankasichhwa` OHLCV (tier1) | MIT per live Kaggle metadata; description says education/research | Upstream NEPSE Alpha terms retrieved 2026-11-14: no explicit redistribution grant; provider claims data as its own work, all rights reserved. Status `UNCERTAIN`; do not redistribute raw OHLCV |
| `SamirWagle` OHLCV (tier2 gap-fill) | No licence (`license:null`); README says educational | Internal academic use with attribution; **not** for deposit/redistribution |
| `menaceXnadin` NEPSE index | No licence (`license:null`); README says unofficial mirror | Internal regime shading only; **not** for deposit/redistribution |

The student must decide whether the Kaggle-declared MIT grant plus the
education/research statement is sufficient for the University's deposit
requirements, or whether upstream permission is needed. The AI does not make
that decision.

---

## 8. Data handling and confidentiality

Raw archives, DuckDB files and processed parquet files remain outside the
public repository where required. The derived-only deposit excludes raw
row-level data, the DuckDB database, processed parquet files and
licence-restricted figures. No credentials, API keys or personal data are
stored in prompts, notebooks or tracked files. The confidential module brief
and the clarification correspondence are kept outside the public repository.

---

## 9. Model limitations and failure modes

AI agents can hallucinate citations, paths, columns or results; produce code
that silently changes a sample or sign; overfit a narrative; misread a licence;
or claim a test passed when it did not. The project's response is mechanical
verification, not trust.

---

## 10. AI-use record for the v2.0.2 pre-write sprint

The detailed phase-by-phase record (Phases A–G, including the model/session
notes and approval gates) is in the private audit file. The public evidence is
in `outputs/tables/verification_h10_recompute.csv`,
`outputs/tables/verification_spot_checks.csv`, `reports/licence_review.md`,
`outputs/figures/static/figure_manifest.csv`,
`reports/chapter_assets/`, the experiment register and the provenance manifest.
The sprint rules **A1** (statistical layer frozen) and **A2** (no thesis prose)
were enforced throughout.

---

## 11. University disclosure — Coventry University

**Status:** completed disclosure draft, 2026-11-14. The student and supervisor
must sign it after the final thesis text exists. This section is the disclosure
of record; the public summary above is not a substitute for it.

**Institution:** Softwarica College of IT & E-Commerce, Kathmandu, Nepal
(Coventry University partner), Computing Individual Research Project.

**Policy framework (retrieved 2026-11-14):**

- *Coventry University Group Artificial Intelligence Position Statement* —
  <https://teach.coventry.domains/coventry-university-group-artificial-intelligence-position-statement>
- *Artificial Intelligence: A Student Guide* —
  <https://student.ai.coventry.domains/>
- The module's assignment brief (2026), Academic Integrity section. The
  brief's exact AI-acknowledgement wording is retained in the private module
  file and is not reproduced in this public repository.
- The module's AI-expectations guidance. The brief itself is retained with
  the submission and is not published here.

The central Coventry guidance requires acknowledgement where AI is used and
states that AI tools must not be used to generate an assessment and submit it
as the student's own work. It does **not** publish one institution-wide
prescribed declaration wording. The module brief's AI-acknowledgement wording
is ambiguous when read against the central guidance: it may place AI outside
the tools-acknowledgement clause, or it may govern AI separately. It should
not be read as permission to conceal AI assistance. The student has referred
the question to the module leader in writing; the brief and the clarification
correspondence are kept outside the public repository. Until written
clarification is received, the declaration below is retained as the factual
record of the actual use.

### 11.1 Declaration

I acknowledge the use of artificial intelligence (AI) tools in the preparation
of this thesis.

**Tools and dates.** I used OpenCode as an AI coding-agent harness with
GLM-family models, DeepSeek-family models, and **DeepSeek V4.1 Flash Free**
between 8 November and 14 November 2026. Model identifiers and session records
are retained in the private audit file.

**What AI assisted with.** AI assisted with: writing and refactoring code;
writing and running tests; data-integrity and reproducibility checks; retrieving
and quoting licence/terms pages; generating figures; building provenance
manifests; and drafting or editing internal documentation and scaffolding. AI
also helped check consistency between tables, documents, and the experiment
register.

**What I did.** I am responsible for the research question, the choice and
verification of data, the interpretation of results, and every submission
decision. I wrote the thesis prose. No chapter, section, paragraph, literature
review, discussion, or conclusion was drafted by an AI and submitted as my own
writing.

**Results and citations.** All numerical results come from executed code on
real data and are traceable to an experiment-register row. AI did not generate
data, results, or citations. Citation metadata were retrieved from Crossref/DOI
records and checked; no citation was invented. I remain responsible for the
content of every cited work.

**Responsibility and retention.** I take responsibility for the accuracy and
integrity of the whole thesis, including the AI-assisted parts. The private
audit file and the provenance records are retained for University review. The
retention period will follow Coventry University policy; if the University
specifies a different period, that period applies.

### 11.2 Pre-submission checks

- [ ] The module's AI-expectations guidance has been checked, and the brief
      is retained with the submission.
- [ ] The final thesis text has been checked against this declaration; no AI
      text remains presented as the student's own prose.
- [ ] Any model or tool change after 2026-11-14 has been added to this
      declaration.
- [ ] Supervisor review has been recorded, if the module requires it.
- [ ] The final wording matches any institution-specific form supplied with the
      assignment brief.

**Student signature / date:** ______________________________

**Supervisor signature / date (if required):** ______________________________

---

## 12. Document control

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-11-08 | Initial R9 note (OpenCode/GLM; licence table; scraping etiquette) |
| 2.0.2-prewrite | 2026-11-13 | Full internal policy: model inventory, permitted/prohibited roles, approval gates, provenance controls, citation/licence integrity, data handling, limitations, sprint record, University disclosure TODO |
| 2.0.2-prewrite (Phase-F close-out) | 2026-11-14 | Phase E/F gates closed; full suite 161 passed; deviations #35–#40; chapter-map hash repair; tag `v2.0.2-prewrite` |
| 2.0.2-prewrite (public metadata) | 2026-11-14 | Legal author identity finalised in `CITATION.cff`/`LICENSE`/`pyproject.toml`; 17 commits and three annotated tags rewritten; deposit-doc and README licence wording aligned with `reports/licence_review.md`; targeted `pyproject.toml` freeze re-seal; author authorised full public push incl. figures with the upstream caveat accepted; deviations #41–#42 |
| 2.0.2-prewrite (University disclosure) | 2026-11-14 | §11 completed for the Coventry-partnered Computing Individual Research Project; the module brief's AI-acknowledgement wording recorded as ambiguous and referred to the module leader in writing; confidential brief text and personal contact details are not published; disclosure retained until written clarification; no AI-use record deleted |
| 2.0.2-prewrite (public summary) | 2026-11-15 | Detailed internal AI-use plan moved to a private audit file outside the repository; public file keeps the short factual disclosure and the licence register; no AI-use record deleted; no thesis prose generated |
| 2.1.0-reciprocity-correction (close-out) | 2026-11-19 | Reciprocity defect fixed and the 21-step pipeline rebuilt from raw archives under the same model (`DeepSeek V4.1 Flash Free`); corrected results propagated to tables, figures, reports and deposit tooling; no new analysis or thesis prose; v2.0.2 values preserved and superseded |

This public summary is reviewed whenever a new model, provider or AI-assisted
artifact class is introduced. The review is recorded as a new version row; the
summary is never silently edited.
