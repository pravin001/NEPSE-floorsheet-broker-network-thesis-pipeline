# Deposit README — NEPSE Floorsheet Microstructure (v2.0)

**Release:** `v2.0.1-handoff` (post-`v2.0-a++-freeze`) · 2026-11-13
**Metadata update:** 2026-11-14 — legal author identity and public-repository
metadata. The sealed v2.0.1 archive predates this update and must be rebuilt
before any deposit.
**Thesis:** *Broker Networks, Concentration, and Market Integrity in a Frontier
Exchange: Evidence from NEPSE Floorsheets.*
**Scope:** predictive associations in the most-traded NEPSE tier, 2021–2024.
Not causal identification, not a trading strategy.

**Deposit status:** derived-only archive built and verified locally, **NOT
deposited**. Uploading the archive to a repository or DOI service is a user
action; see §8. Packaging evidence: `docs/deposit_preflight.md`.

---

## 1 · What this deposit contains

| path | contents |
|---|---|
| `src/nepsemsc/` | pipeline package (data, network, ML, evaluation, utils) |
| `scripts/` | numbered pipeline stages + the Stage-6 rebuild driver |
| `configs/project.yaml` | frozen v1 constants (SHA-256 fingerprinted) |
| `configs/v2_freeze/` | v2 freeze snapshot + `freeze_manifest.csv` (SHA-256 per file) |
| `docs/` | analysis plan (v1 frozen + v2 extension), deviations, experiment register, reproducibility guide, chapter crosswalk |
| `data/metadata/` | provenance manifest, corpus file hashes, universe selection, schema (metadata only) |
| `outputs/tables/` | every derived table of record (v1 + v2; 76 CSVs) |
| `reports/` | data-quality, robustness, heterogeneity, event-study, limitations, Ch.1–Ch.6 handoff packs |
| `notebooks/` | executable 00–01 notebooks (nbmake-tested) |
| `tests/` | unit, leakage, SE-specification, freeze, chapter-map integrity tests |
| `requirements.txt`, `requirements-lock.txt`, `pyproject.toml` | environment pins |
| `CITATION.cff`, `LICENSE`, `README.md` | citation, code licence, overview |

**Not included:** raw floorsheet archives, raw OHLCV archives, the DuckDB store,
and `data/processed/*.parquet` (all gitignored). They are inputs or rebuildable
derived data, not part of the code deposit. `outputs/figures/` is also excluded
from the derived-only archive because public redistribution of price-derived
figures remains subject to the upstream NEPSE Alpha terms, which are
`UNCERTAIN` (`reports/licence_review.md`; §5, limitation L4).
`outputs/logs/` is local rebuild evidence, not payload.
Licences for the raw inputs are recorded per file in
`data/metadata/provenance_manifest.csv`.

The archive itself lives at
`dist/nepse-floorsheet-microstructure-v2.0.1-derived.tar.gz` (gitignored,
deterministically rebuildable with `scripts/build_deposit_archive.py`).
`docs/deposit_preflight.md` records the archive hash, content-manifest hash,
inventory and licence checks; it is a wrapper record and is not inside the
payload.

---

## 2 · Reproduce the environment

The reference environment is Python 3.11.16 (uv-managed) on Linux.

```bash
cd nepse-floorsheet-microstructure
uv venv nepse-msc --python 3.11
uv pip install --python nepse-msc/bin/python -r requirements.txt
uv pip install --python nepse-msc/bin/python -e . --no-deps
# exact pins (153 packages, includes arch==8.0.0)
uv pip freeze --python nepse-msc/bin/python > /tmp/check-lock.txt
diff <(sort requirements-lock.txt) <(sort /tmp/check-lock.txt)
```

`requirements-lock.txt` is the authoritative pin set. `arch==8.0.0` is required
by the EGARCH stage; matplotlib is pulled in by `arch`.

---

## 3 · Reproduce the data layer

The raw archives are **not redistributed**. Reconstruct them per
`data/metadata/provenance_manifest.csv` (source URL, source path, SHA-256,
licence, evidence for every file). The original workstation used these roots:

| input | expected local root |
|---|---|
| kaggle viking303 floorsheets 2021–2023 (CC0) | `/home/whacko/.cache/kagglehub/datasets/viking303/nepse-historical-floorsheet/versions/14/NEPSE_data` |
| socrateai 2024 floorsheets (MIT) | `/home/whacko/research/nepse-kronos-thesis/data/raw/tier3_floorsheets_socrateai` |
| tier1 Kaggle OHLCV (100 symbols; licence pending) | `/home/whacko/research/nepse-kronos-thesis/data/raw/tier1_kaggle` |
| tier2 SamirWagle prices (gap-fill) | `/home/whacko/research/nepse-kronos-thesis/data/raw/tier2_samirwagle_prices` |

Those absolute paths are embedded in `scripts/select_top10.py`,
`scripts/ingest_corpus.py`, and `scripts/build_ohlcv.py`. On a different
machine, either recreate the same layout or edit those three constants before
running. The per-file hashes in the provenance manifest let you confirm that a
local copy is the exact archive used here.

The per-symbol floorsheet slices under `data/raw/floorsheet/` are derived
extracts of the two verified archives; their SHA-256 values are also in the
manifest.

---

## 4 · Reproduce the analysis (clean rebuild)

```bash
# deletes ONLY data/processed/ and data/duckdb/; raw archives are untouched
nepse-msc/bin/python scripts/run_stage6_rebuild.py --clean
```

The driver runs the documented pipeline in order, writes the full log to
`outputs/logs/v2_stage6_rebuild.log`, and writes per-step wall times to
`outputs/logs/v2_stage6_rebuild_timings.csv`. The measured freeze rebuild
completed **21/21 steps with exit 0 in 3,749.9 s (62.5 min)**; `data/raw/`
stayed at 577 files / 611,881,127 bytes. Reproducibility is **numerical, not
byte-identical**: 40/73 tables byte-identical, 25 at ≤3.55e-14 relative,
4 reorder-only, 2 QuantReg optimizer drifts (7.44e-7), 1 float-aggregation
difference (±1 unit on ~1e8 sums), 1 descriptive sequential-fold threshold
flip (146→141 events; anchored 686 unchanged). Full evidence:
`outputs/tables/v2_clean_rebuild_audit.csv`; details in
`docs/reproducibility.md`.

Pipeline stages: universe → floorsheet ingest → corpus audit → OHLCV →
volume reconciliation → daily features → outcomes → broker-persistence table →
feature summary → anomaly scoring → panel regressions → regime split → event
study → robustness → dashboard cache → v2 engine validation → v2 Stages 1–4 →
canonical final headline set.

> `scripts/run_stage6_rebuild.py --clean` is destructive only to the two
> derivative directories named above. It asserts that `data/raw/` is
> byte-count/size-identical before and after deletion.

Notebooks execute top-to-bottom against the rebuilt artifacts:

```bash
nepse-msc/bin/python -m pytest tests notebooks/*_*.ipynb --nbmake
```

The v2.0.1 handoff run passed **161 tests, 0 failed** (unit/leakage/SE-spec/
freeze/chapter-map integrity + four executed notebooks). The Stage-6 freeze run
passed 154; the seven added tests are the chapter-map integrity guards.

---

## 5 · Licence and redistribution status

**Code:** MIT — see `LICENSE`. Copyright © 2026 Prabin Shrestha.

| input | licence | deposit consequence |
|---|---|---|
| kaggle viking303 floorsheets 2021–2023 | **CC0** (verified) | usable; raw not deposited here |
| socrateai 2024 floorsheets | **MIT** (verified; LICENCE fetched) | usable with attribution; raw not deposited here |
| tier1 Kaggle OHLCV | **MIT** declared on Kaggle; upstream NEPSE Alpha `UNCERTAIN` | academic use is covered by the declared grant and the dataset's educational/research statement; **public figure redistribution remains AMBER pending the upstream check**, so figures are excluded from this derived-only archive; derived tables remain numerically derived |
| tier2 SamirWagle prices | no licence file; analytic use with attribution | gap-fill only; not redistributed |
| NEPSE composite index | `unstated_in_repo` (GitHub API `license: null`) | secondary regime shading/benchmark only; swap-able |
| code | MIT | this deposit |

`data/metadata/provenance_manifest.csv` is authoritative; if this summary and
the manifest differ, the manifest wins. Do not publish `outputs/figures/`
publicly until the upstream NEPSE Alpha position is resolved or explicitly
accepted by the author. The v2 limitations table records this as CRITICAL row
L4 (`reports/limitations.md`); the current two-layer review is in
`reports/licence_review.md`.

---

## 6 · Governance and verification

- `docs/analysis_plan.md` — v1 plan, byte-frozen; do not edit.
- `docs/analysis_plan_v2_extension.md` — v2 pre-declaration, written before any
  v2 result.
- `docs/analysis_deviations.md` — every implementation/reclassification choice
  with timestamp and reason (#1–#9 v1; #10–#30 v2; #31–#32 post-freeze
  chapter-map defect and v2.0.1 handoff).
- `docs/experiment_register.md` — every quotable number maps to one EXP row;
  numeric claims must cite an EXP id (EXP-0013 records the clean rebuild and
  freeze; EXP-0014 records the chapter handoff and deposit preflight).
- `outputs/tables/v2_register_audit.csv` — register-to-manifest audit, re-run
  for v2.0.1; the current check count is in `docs/deposit_preflight.md`.
- `docs/chapter_artifact_map.md` + `outputs/tables/v2_chapter_map_audit.csv` —
  verified 67-claim crosswalk; every cited path exists and hash-matches the
  latest provenance row.
- `tests/test_chapter_map_integrity.py` — build-breaking guard for the
  chapter→artefact surface that the Stage-6 register audit did not cover.
- `outputs/tables/v2_final_headline_set.csv` — canonical 10-hypothesis final set
  (exact brief columns; composition rule Stage-1 ∩ Stage-2 ∩ Stage-3).
- `configs/v2_freeze/freeze_manifest.csv` + `tests/test_freeze_v2.py` — SHA-256
  snapshot of the binding config/plan/seeds/lock files; any later change fails
  the test.
- `docs/reproducibility.md` — clean-rebuild record and measured timings.

Frozen v1 numeric cells are immutable. v2 analyses write new files or
explicitly declared governance columns; they never rewrite a v1 result.

---

## 7 · Headline result of record

Read `outputs/tables/v2_final_headline_set.csv`. In one sentence: **H10
(reciprocity → next-day absolute return) is the sole `HEADLINE_MODERATE`
association; H4 is `EXPLORATORY_POST_HOC`; H6/H7/H8 are `NULL_FRAGILE`;
H1/H2/H3/H5/H9 are `NULL_POWERED`.** All 1-SD effects are below the declared
30–50 bp round-trip cost floor, and the design is predictive, not causal. The
canonical table carries the exact coefficients, p-values, concordance flags,
liquidity/EGARCH survival, and tail labels; do not quote a number from this
README instead of the table.

---

## 8 · Deposit action (user)

No archive upload, DOI registration, or deposit push has been performed. The
derived-only archive is built, hashed and audited locally. The author identity
was resolved on 2026-11-14 (`Prabin Shrestha <itsme_prabin@outlook.com>`);
because the sealed v2.0.1 archive predates that metadata update, rebuild it
before deposit. Two user decisions remain before upload:

1. **Tier1 OHLCV upstream** — the Kaggle metadata declares MIT and the
   dataset states an educational/research purpose, but its prices are scraped
   from NEPSE Alpha, whose terms are `UNCERTAIN`. Resolve or explicitly accept
   that position before publishing price-derived figures; the derived-only
   archive already excludes them.
2. **Deposit scope** — keep the derived-only archive (recommended), or decide
   to add a licensed data subset. Raw archives are not covered by the code
   licence and are never part of this archive.
