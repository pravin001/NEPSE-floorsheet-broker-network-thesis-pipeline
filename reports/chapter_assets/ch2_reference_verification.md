# Ch.2 reference verification note — v2.0.2 pre-write

**Status:** writing-support asset, not a literature review and not thesis prose.
**Scaffold:** `reports/chapter_assets/ch2_references_scaffold.csv` (39 records).
**Retrieval log:** `reports/chapter_assets/ch2_reference_retrieval_log.csv`.
**Verification date:** 2026-11-14 (DOI re-check); Crossref metadata retrieved
2026-11-13T10:44:48Z–10:46:02Z.

---

## 1. What was verified

Each record satisfies all of the following:

1. **Real DOI.** The DOI was retrieved from the Crossref REST API at
   `https://api.crossref.org/works/{doi}` with HTTP **200**.
2. **Resolvable DOI.** A no-follow request to `https://doi.org/{doi}` returned
   HTTP **302** to a publisher landing page; the target is recorded in
   `doi_redirect_target`.
3. **Bibliographic fields present.** Authors, year, title, container, volume,
   issue, pages/article number (where Crossref records them), publisher type
   and DOI are recorded from Crossref, not from memory.
4. **Year convention.** `year` is the print/volume year when Crossref records
   one; otherwise it is the issued year. The raw Crossref years are retained in
   `crossref_issued_year` and `crossref_print_year` for audit.

**Counts by stream**

| stream | records | pack section hint |
|---|---:|---|
| Broker networks and intermediation | 11 | 2.1 |
| Liquidity, concentration and microstructure | 10 | 2.2 |
| Manipulation and closing prices | 6 | 2.2 |
| Emerging and frontier markets | 7 | 2.3 |
| Nepal / NEPSE evidence | 5 | 2.3 |
| **Total** | **39** | |

**Source status**

| status | records | note |
|---|---:|---|
| `FINAL_PUBLISHED_VERSION` | 38 | Journal articles with a Crossref journal record. |
| `POSTED_CONTENT_NOT_FINAL` | 1 | SSRN `10.2139/ssrn.2793509`; no final published version verified. |

---

## 2. What was **not** verified

`content_review_status = NOT_REVIEWED` on every row. Metadata verification is
**not** a claim that the paper was read, that its findings support a sentence in
the thesis, or that it is the best reference for a proposition. The student must:

- obtain and read the paper;
- confirm that the cited claim is actually made there;
- check the volume, issue, pages and year against the publisher's version;
- change `content_review_status` to `REVIEWED_<YYYY-MM-DD>` only after reading;
- fill `student_section` and `student_notes` with the section and the specific
  use of the reference.

If a paper cannot be obtained, remove the row or mark it `NOT_FOUND`; do not cite
it. The scaffold deliberately contains no quotations and no findings summaries,
so it cannot be mistaken for a pre-written literature review.

---

## 3. Selection and coverage

The 39 records are a candidate set, not a required citation list. They cover the
five streams named in `reports/chapter_assets/ch2_literature_pack.md`:

- **NET (11):** broker/intermediary networks, OTC dealer networks, financial
  connectedness, network topology, centrality, core–periphery.
- **LIQ (10):** Kyle/Glosten–Milgrom foundations, Amihud, Roll,
  Corwin–Schultz, liquidity-measure validation, commonality and market
  efficiency.
- **MAN (6):** closing-price manipulation, stock-market manipulation,
  intermediary manipulation, end-of-day dislocation.
- **EM (7):** emerging-market liquidity, commonality, market-efficiency tests,
  domestic/foreign investor evidence, individual-investor losses, trading costs.
- **NP (5):** NEPSE concentration/turnover, variance-ratio efficiency,
  technical analysis and EMH, small-capital-market behaviour, market turnover.

The set is deliberately weighted toward the constructs the thesis actually
uses (`buyer_hhi`, `reciprocity`, `self_loop_ratio`,
`end_of_day_concentration`, liquidity controls and NEPSE market context). It is
not a systematic-review search and makes no claim of exhaustive coverage.

---

## 4. Known limitations of this scaffold

1. **One posted-content record.** The Pradhan (2016) SSRN item is not a final
   journal article. If the student cites it, the reference list must label it
   as an SSRN working paper, and the claim must be one the posted version
   supports.
2. **Crossref metadata is not the publisher's typeset reference.** Page ranges,
   issue numbers and author capitalisation can differ from the published PDF.
   The student should verify the final citation against the publisher page.
3. **No content review.** See §2. This is the largest limitation and the reason
   the compliance checklist keeps a separate reference sign-off item.
4. **Citation-key suggestions are not mandatory.** They are unique and readable,
   but the student may rename them in the reference manager; the DOI is the
   stable identifier.
5. **No claim that the 39 are sufficient.** The student may add references, but
   every addition must pass the same Crossref/DOI checks and be appended to the
   scaffold and retrieval log with a timestamp.

---

## 5. How to use the scaffold

1. Filter by `stream_code` or `pack_section_hint` when drafting a section.
2. Read the paper; record the exact claim and page in `student_notes`.
3. Set `content_review_status` to `REVIEWED_<date>`.
4. Copy the record into the reference manager using the DOI; do not retype the
   metadata.
5. In the thesis, cite the author–year form; the DOI belongs in the reference
   list, not in the body text.
6. Keep `TODO(student)` cells out of the final thesis. They are placeholders,
   not content.

---

## 6. Traceability

| artifact | role |
|---|---|
| `reports/chapter_assets/ch2_references_scaffold.csv` | 39 metadata-verified candidate records with content-review status |
| `reports/chapter_assets/ch2_reference_retrieval_log.csv` | per-record Crossref URL/status/timestamp and DOI HTTP status/redirect |
| `reports/chapter_assets/ch2_literature_matrix.csv` | stream-level matrix scaffold; still student-authored |
| `reports/chapter_assets/ch2_comparison_table.csv` | five `CMP-TODO-*` rows; still student-authored |
| `reports/chapter_assets/ch2_research_gap.md` | gap-statement scaffold; no bibliographic assertions |
| `docs/ai_use_policy.md` §7.1 | citation-integrity rule: real DOI/URL, timestamp, `NOT_FOUND` if unresolvable |

This note does not change any frozen result, table, figure or classification.
