# AI-Use, Research-Integrity and Licence Policy (R9)

**Project:** Broker Networks, Concentration, and Market Integrity in a Frontier
Exchange: Evidence from NEPSE Floorsheets
**Document version:** 2.0.2-prewrite
**Last updated:** 2026-11-14
**Status:** project policy in force for the v2.0.2 pre-write sprint. The
University disclosure section at the end is an explicit **TODO for the
student** and is not complete until the student fills it in.

This document records how AI tools were used, what they were allowed and not
allowed to do, and how the project verified their outputs. It is a research
integrity record, not legal advice and not a substitute for the student's
institution's rules.

---

## 1. Purpose and scope

The project used AI coding agents inside **OpenCode** for engineering,
verification, documentation scaffolding and figure production. The statistical
design, hypotheses, folds, estimators and interpretation rules were
pre-declared in `docs/analysis_plan.md` and
`docs/analysis_plan_v2_extension.md` before the relevant results were seen.
The frozen analysis is not re-opened by this policy.

The policy applies to:

* every AI-assisted code change, test, notebook, table, figure, manifest and
  document in this repository;
* every model family used through OpenCode on this project;
* the v2.0.2 pre-write sprint (Phases A–F) and all earlier build stages whose
  outputs remain in the repository.

The governing rule is simple: **AI may help build and verify the research
infrastructure; AI must not invent the research, its results, its citations or
its prose.**

---

## 2. Tool and model inventory

| Tool | Model family / identifier | When used | Role on this project |
|---|---|---|---|
| OpenCode | **GLM family** | Early-to-mid engineering build | Pipeline code, tests, notebooks, documentation scaffolding, execution support |
| OpenCode | **DeepSeek family** | Later engineering and v2 freeze work | Code review, verification scripts, robustness plumbing, audit and manifest support |
| OpenCode | **DeepSeek V4.1 Flash Free** (provider `opencode`) | **v2.0.2 pre-write sprint, 2026-11-13 → 2026-11-14** | Phase-A independent reproduction checks, Phase-B licence retrieval and review, Phase-C static figures, Phase-D policy rewrite, Phase-E writing-support assets, Phase-F suite/commit/tag preparation |

The model identifier above is the one reported by the harness for this sprint.
Earlier sessions used OpenCode with GLM-family and DeepSeek-family models; the
exact session identifiers, where retained, live in the local OpenCode session
logs rather than in the thesis deposit. If the student changes model or
provider before submission, the change must be appended to this table and to
the University disclosure section.

---

## 3. Permitted AI roles

AI assistance is permitted for **non-prose research infrastructure**, including:

1. **Code engineering** — writing, refactoring and debugging pipeline code,
   tests, notebooks, plotting scripts and command-line utilities.
2. **Execution support** — running the pre-declared pipeline, capturing logs,
   checking exit codes and reporting failures.
3. **Verification** — writing independent reproduction scripts, hash checks,
   schema checks, blank-figure checks and cross-artefact consistency checks.
4. **Data-integrity work** — duplicate accounting, row-filter accounting,
   provenance manifests, freeze manifests and audit tables.
5. **Documentation scaffolding** — README structure, experiment-register rows,
   deviation rows, checklists, table-numbering plans and bullet-point chapter
   skeletons.
6. **Figure production** — generating figures from frozen tables, adding
   labels, footers and manifests; never inventing a plotted value. Figure
   caption scaffolds are factual labels only; the student writes the final
   captions.
7. **Citation metadata retrieval** — locating candidate references and
   checking that a DOI/URL resolves. The student decides what is cited and how
   it is discussed.
8. **Licence evidence collection** — retrieving live licence/terms pages and
   quoting them verbatim, with `UNCERTAIN` where a source is silent.

Every AI-assisted artefact must remain traceable to an experiment row, a frozen
input or a named public source. AI output is a draft artefact until a test, a
hash check or a human review confirms it.

---

## 4. Prohibited AI roles

The following are **not permitted** on this project:

1. **No AI-drafted thesis prose.** No chapter, section, paragraph, literature
   review, theoretical argument, results narrative, discussion, conclusion,
   abstract or viva answer may be drafted by an AI and submitted as the
   student's writing. AI may produce bullet skeletons, table cells, figure
   caption scaffolds and checklists; the student writes every prose sentence,
   including the final figure captions.
2. **No fabricated results.** AI must not invent a coefficient, standard
   error, p-value, sample size, date, event count, network statistic or
   robustness result. Every number must come from executed code on real data
   and be traceable to a frozen artifact.
3. **No fabricated citations.** AI must not generate a reference, DOI, URL,
   author list, title or year from memory. Every cited item must be retrieved
   and recorded; unverifiable items are `NOT_FOUND` or omitted.
4. **No new analyses in a frozen sprint.** The v2.0.2 pre-write sprint forbids
   new regressions, tests, re-fits, robustness checks or specification
   searches. Any post-freeze change requires a new registered experiment row
   and a deviation row before it is run.
5. **No result-driven specification choice.** AI must not select a model,
   sample, control set, threshold or outcome because it produces a preferred
   result. The pre-declared plan is binding; deviations are logged with a
   reason and timestamp.
6. **No silent data modification.** AI must not overwrite raw data, edit a
   frozen numeric table, move a freeze tag, or change a canonical
   classification without an auditable record.
7. **No public actions.** AI must not upload, push, publish, register a DOI,
   create a Zenodo/OSF record, open a GitHub issue/PR, or trigger an external
   workflow on the student's behalf. These are student decisions.
8. **No confidential-data exfiltration.** Raw row-level data, credentials,
   API keys, personal information and unpublished supervisor comments must not
   be posted to public services. The agent works locally; any data that
   reaches a model provider is limited to what is necessary for the task and is
   subject to the provider's terms.
9. **No impersonation.** AI must not sign a declaration, write a supervisor
   endorsement, or state that the student has personally verified something
   the student has not verified.

---

## 5. Human oversight and approval gates

The student remains the author and the responsible researcher. The following
gates apply:

| Gate | What the student confirms | Status |
|---|---|---|
| Pre-declaration | Hypotheses, folds, estimators, outcomes and multiplicity rules are fixed before results | Complete (DC20) |
| Phase-A reproduction | The independent H10 recomputation matches the frozen result exactly | Complete; accepted by the student |
| Phase-B licence review | The verbatim licence record and the `UNCERTAIN` markers are understood; deposit scope is a student decision | Complete; deposit decision remains a student TODO |
| Phase-C figures | Figure footers, manifest hashes and non-blank checks are present | Complete |
| Phase-D policy | The AI-use record is accurate and the University disclosure is completed | Policy complete; University section is a student TODO |
| Phase-E writing assets | References are real and verified; tables and claims trace to frozen artifacts | Complete 2026-11-14: 39 references Crossref 200 / DOI 302; 28 print CSVs hash-validated; 10 figures 300 dpi with PASS blank checks. Content review remains a student TODO |
| Phase-F freeze | Full test suite passes; deviations and `AGENTS.md` are updated; commit and tag are correct | Complete 2026-11-14: full suite **161 passed** (159 tests + 2 notebooks); deviations #35–#40 appended; `AGENTS.md` updated; commit/tag `v2.0.2-prewrite` created at close-out |
| Submission | The student has read every chapter, can defend every claim, and has completed the University disclosure | **Student responsibility** |

The student may reject or rewrite any AI-generated code, label, caption or
scaffold. A green test suite is evidence of mechanical consistency, not proof
that the research is correct or that the student understands it.

---

## 6. Reproducibility and provenance controls

The project uses the following controls against silent AI error:

1. **Frozen inputs and outputs.** v1 and v2 numeric tables are frozen and
   hash-checked; later stages add new files rather than editing old ones.
2. **Experiment register.** Every executed analysis has an `EXP-*` row with
   script, inputs, outputs, status and result summary
   (`docs/experiment_register.md`).
3. **Deviation log.** Every departure from the pre-declared plan is recorded
   with a timestamp in `docs/analysis_deviations.md`; entries continue in one
   numbered sequence.
4. **Provenance manifest.** Source files, derived artifacts and hashes are
   recorded in `data/metadata/provenance_manifest.csv`.
5. **Freeze manifests.** `configs/v2_freeze/` and the freeze tests pin the
   configuration fingerprint, table set, row counts and sign directions.
6. **Independent reproduction.** Phase A recomputed H10 from frozen inputs with
   a separate script and matched the canonical result exactly.
7. **Figure manifest.** Every static figure records its input artifacts, input
   digest, output hashes, pixel dimensions and blank-check result in
   `outputs/figures/static/figure_manifest.csv`.
8. **Tests as guards, not ornaments.** The suite includes leakage, freeze,
   anomaly-scale, chapter-map and engine-validation tests. A failure blocks
   the sprint rather than being explained away.
9. **Human spot checks.** The student reviews the final tables, figures and
   claims against the frozen sources before submission.

No AI-generated number is accepted merely because the code ran. The code must
run on the declared input, the output must land in the declared artifact, and
the artifact must pass the relevant audit.

---

## 7. Citation and licence integrity

### 7.1 Citations

* Every reference in the thesis must have a real, retrieved DOI or URL.
* Retrieval is recorded with a timestamp and the exact source string.
* If a DOI/URL does not resolve, the item is marked `NOT_FOUND` and is not
  cited.
* AI may locate and verify metadata; it may not write the literature-review
  narrative or invent a supporting quotation.
* The Ch.2 reference scaffold is a list of verified candidates, not a
  pre-written review. The student selects and discusses the final set.

### 7.2 Data licences

The live licence review is `reports/licence_review.md` (retrieved
2026-11-13T10:21:13Z). Its conclusions are two-layer:

* the **dataset grant** as quoted from the source; and
* the **upstream clarity** where the uploader scraped or mirrored another
  service.

The key positions are:

| Source | Dataset grant | Upstream / deposit position |
|---|---|---|
| Kaggle `viking303` floorsheets (2021–2023) | CC0: Public Domain | Upstream merolagani rights `UNCERTAIN`; local academic use permitted |
| `socrateai` floorsheets (2024) | MIT-style text, © 2025 SocrateAI | Preserve the notice; upstream rights `UNCERTAIN` |
| Kaggle `rohankasichhwa` OHLCV (tier1) | MIT per live Kaggle metadata; description says education/research | Upstream NEPSE Alpha terms not retrieved: `UNCERTAIN`; do not redistribute raw OHLCV |
| `SamirWagle` OHLCV (tier2 gap-fill) | No licence (`license:null`); README says educational | Internal academic use with attribution; **not** for deposit/redistribution |
| `menaceXnadin` NEPSE index | No licence (`license:null`); README says unofficial mirror | Internal regime shading only; **not** for deposit/redistribution |

The student must decide whether the Kaggle-declared MIT grant plus the
education/research statement is sufficient for the University's deposit
requirements, or whether upstream permission is needed. The AI does not make
that decision.

---

## 8. Data handling and confidentiality

* The project operates on local files. Raw archives, DuckDB files and processed
  parquet files remain outside the public repository where required.
* The agent had local read access to the repository for code execution and
  verification. Incidental table excerpts in tool output were used for
  debugging and audit; they were not published.
* No credentials, API keys or personal data are stored in prompts, notebooks
  or tracked files.
* The derived-only deposit excludes raw row-level data, the DuckDB database,
  processed parquet files and licence-restricted figures.
* Model-provider data handling is governed by the provider's terms. The student
  should confirm that the provider's retention/training settings are acceptable
  for the institution before submitting any unpublished material.

---

## 9. Model limitations and failure modes

AI agents can:

* hallucinate a citation, a file path, a column name or a numerical result;
* produce plausible-looking code that silently changes a sample or a sign;
* overfit a narrative to a preferred result;
* misread a licence or assume that silence grants permission;
* generate a figure whose labels do not match the underlying table;
* claim that a test passed when it did not.

The project's response is mechanical verification: hashes, row counts, schema
checks, frozen-table comparisons, independent reproduction, non-blank figure
checks, register audits and a full test suite. Where a check cannot be run, the
result is marked `UNCERTAIN` or `NOT_FOUND`, not asserted.

---

## 10. AI-use record for the v2.0.2 pre-write sprint

| Phase | AI contribution | Human decision / check | Artifact |
|---|---|---|---|
| A — canonical verification | Wrote and ran `scripts/verify_h10_independent.py`; compared H10 and spot checks | Student accepted the exact reproduction before Phases B–F | `outputs/tables/verification_h10_recompute.csv`, `verification_spot_checks.csv` |
| B — licences | Retrieved live licence/terms pages; quoted them verbatim; marked silent sources `UNCERTAIN` | Student must decide the tier1 upstream/deposit position | `reports/licence_review.md` |
| C — figures | Wrote `scripts/make_thesis_figures.py`; generated F1–F10 from frozen tables; ran blank checks; built manifest | Visual QA by the agent; student reviews before submission | `outputs/figures/static/*.png/.pdf`, `figure_manifest.csv` |
| D — policy | Rewrote this document from the actual tool/model history | Student completes the University disclosure and confirms accuracy | `docs/ai_use_policy.md` |
| E — writing assets | Built the table plan, 28 print CSVs, a 39-record verified reference scaffold, checklists, memo and claims sheet; no prose | Student selects references and writes the chapters | `reports/chapter_assets/` |
| F — freeze | Ran the full suite (161 passed), appended deviations #35–#40, updated `AGENTS.md`, rebuilt the chapter-map hashes, committed and tagged | Student authorises any push/upload; none is performed by AI | Git history; tag `v2.0.2-prewrite` |
| G — public metadata | Rewrote the 17 commit author/committer identities and three annotated tags to the student's legal name/email; updated `CITATION.cff`, `LICENSE`, `pyproject.toml`, `README.md` and deposit docs; re-sealed only the `pyproject.toml` freeze snapshot after the metadata-only edit | Student supplied the legal name/email and authorised the full public push (including figures, with the upstream caveat accepted) on 2026-11-14 | Git history; `CITATION.cff`; deviations #41–#42 |

The sprint rule **A1** (statistical layer frozen) and **A2** (no thesis prose)
were enforced throughout. Deviations #33–#41 record the figure-representation
choices (#33: F7 uses frozen placebo quantiles because draw-level values were
not persisted; #34: F10 composites the two frozen network renders), the
Phase-A verification-only recomputation (#35), the two-layer licence finding
(#36), the static-figure production conventions (#37), the metadata-only
reference verification scope (#38), the canonical table numbering/print
projections (#39), the Phase-F chapter-map hash repair (#40) and the
public-metadata/identity finalisation (#41). No deviation changed a frozen
estimate, p-value, classification or seeded draw.

---

## 11. University disclosure — TODO (student)

> **Status: TODO. This section must be completed by the student before
> submission. Do not submit the thesis with this section unchanged.**

The student must insert the institution's required disclosure. The following
checklist is a prompt, not a substitute for the institution's form:

- [ ] **Policy reference.** Insert the University/Faculty/Department policy
      name, version and URL that governs AI use in assessed work.
- [ ] **Declaration form.** Confirm whether a separate AI-use declaration form
      is required; if yes, attach it or cite its submission reference.
- [ ] **Exact disclosure wording.** Insert the exact wording required by the
      institution. Do not paraphrase a mandatory declaration.
- [ ] **Tools and models.** List OpenCode, the GLM-family sessions, the
      DeepSeek-family sessions and **DeepSeek V4.1 Flash Free** (this sprint),
      with dates and versions where known.
- [ ] **Parts of the work assisted.** State that AI assisted with code,
      tests, data-integrity checks, licence retrieval, figures, manifests and
      document scaffolding; state that the student wrote all thesis prose.
- [ ] **No AI-drafted prose.** Confirm that no chapter, section, paragraph,
      literature review, discussion or conclusion was drafted by an AI and
      submitted as the student's own writing.
- [ ] **No AI-generated results or citations.** Confirm that all numerical
      results come from executed code on real data and that all citations were
      retrieved and verified.
- [ ] **Supervisor review.** Record the supervisor's name/date of review (or
      the institution's equivalent sign-off).
- [ ] **Retention.** State whether session logs, prompts or AI outputs are to
      be retained and for how long, in line with the institution's policy.
- [ ] **Final wording check.** Confirm that the disclosure matches the final
      thesis, including any model change after 2026-11-13.

**Student signature / date:** ______________________________

**Supervisor signature / date (if required):** ______________________________

---

## 12. Document control

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-11-08 | Initial R9 note (OpenCode/GLM; licence table; scraping etiquette) |
| 2.0.2-prewrite | 2026-11-13 | Full rewrite for the pre-write sprint: model inventory (GLM, DeepSeek, DeepSeek V4.1 Flash Free), permitted/prohibited roles, approval gates, provenance controls, citation/licence integrity, data handling, limitations, sprint record, University disclosure TODO |
| 2.0.2-prewrite (Phase-F close-out) | 2026-11-14 | Phase E/F gates closed; full suite 161 passed; deviations #35–#40; chapter-map hash repair; tag `v2.0.2-prewrite` |
| 2.0.2-prewrite (public metadata) | 2026-11-14 | Legal author identity finalised in `CITATION.cff`/`LICENSE`/`pyproject.toml`; 17 commits and three annotated tags rewritten; deposit-doc and README licence wording aligned with `reports/licence_review.md`; targeted `pyproject.toml` freeze re-seal; author authorised full public push incl. figures with the upstream caveat accepted; deviations #41–#42 |

This policy is reviewed whenever a new model, provider or AI-assisted artifact
class is introduced. The review is recorded as a new version row; the policy is
never silently edited.
