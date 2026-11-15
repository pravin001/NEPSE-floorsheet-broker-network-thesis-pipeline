# Deposit preflight — v2.0.2 derived-only archive

**Release:** `v2.0.2-prewrite` + post-publication documentation · 2026-11-14
**Status:** archive built and verified locally; **NOT uploaded**, no DOI,
no deposit-repository push. Upload is a user action; the public code
repository is separate from this derived-only archive.

This file is a wrapper record. It is excluded from the archive payload so
the archive SHA-256 is not self-referential; the payload's embedded
provenance manifest predates the final wrapper hash row.

---

## 1 · Archive identity

| item | value |
|---|---|
| archive | `dist/nepse-floorsheet-microstructure-v2.0.2-derived.tar.gz` (gitignored) |
| SHA-256 | `d222ab1aec3a0704c4437a4ba528c81e384a48cd1a4eafef55c91cedddbd5f04` |
| compressed size | 2,772,950 bytes |
| payload files | 307 |
| uncompressed payload | 14,189,694 bytes |
| content manifest | `dist/nepse-floorsheet-microstructure-v2.0.2-derived.contents.csv` |
| content-manifest SHA-256 | `c43e55042449bbe225950a05bfc056153129b60a30b0505ba3bd36aa5ac4842e` |
| provenance rows at seal | 1,038 |

Sidecars: `dist/*.sha256` (archive digest) and `dist/*.summary.json`
(machine-readable identity). Rebuild deterministically with:

```bash
nepse-msc/bin/python scripts/build_deposit_archive.py
```

Two consecutive builds from the same tree were byte-identical (same
SHA-256); the packer sorts paths and normalises tar/gzip metadata
(mtime 0, uid/gid 0, empty owner names).

---

## 2 · Payload inventory

| class | files |
|---|---:|
| code | 131 |
| derived_table | 78 |
| report | 64 |
| doc | 10 |
| config | 9 |
| derived_metadata | 5 |
| notebook | 2 |
| root | 8 |
| **total** | **307** |

The payload contains the pipeline package, scripts, tests, configs,
notebooks, docs, reports/chapter packs, derived metadata, and all
78 derived tables of record.

---

## 3 · Hash verification

| check | result |
|---|---|
| derived tables hash-matched to latest provenance row | 78/78 |
| payload files hashed in content manifest | 307/307 |
| chapter crosswalk rows OK | 67/67 |
| register-audit checks OK | 719/721 |

Audit outputs:

- `outputs/tables/v2_chapter_map_audit.csv` — chapter→artefact
  existence, crosswalk hash, latest manifest hash, EXP-id and
  claim-version checks.
- `outputs/tables/v2_register_audit.csv` — experiment-row artefact
  resolution and manifest hash checks. Non-`OK` rows are the documented
  manifest self-reference and historical EXP-0000 lock exemption.

Any missing path, unhashed table, or hash mismatch aborts the packer
before an archive is written.

---

## 4 · Licence policy

| check | result |
|---|---|
| code licence | MIT (`LICENSE`, `CITATION.cff`) |
| restricted raw/figure paths in payload | 0 |
| historical tier1 manifest rows carrying the superseded pending label | 3 |
| NEPSE index unstated-licence manifest rows | 1 |

Floorsheet inputs: Kaggle viking303 2021–2023 (**CC0**) and socrateai
2024 (**MIT**). Tier1 OHLCV is **MIT-declared on Kaggle** with an
educational/research statement, but its prices are “scraped from NEPSE
Alpha”; the provider's terms (retrieved 2026-11-14) grant no explicit
redistribution right and reserve all rights. Upstream status remains
**UNCERTAIN**, so `outputs/figures/` is excluded from this derived-only
payload. The author accepted the figure-redistribution caveat for the
public code repository; this preflight does not treat that as upstream
clearance. The NEPSE index is a secondary input with an unstated
repository licence. Raw archives, DuckDB, processed parquet, prediction
parquet, logs, and figures are **not redistributed by this deposit**.

---

## 5 · Excluded scope

Excluded by construction (the packer refuses to leak them):

`data/raw/` · `data/duckdb/` · `data/processed/` · `outputs/figures/` ·
`outputs/logs/` · `outputs/predictions/` · `outputs/manifests/` ·
`dash/` · `dist/` · venv/cache/pyc files.

Also excluded: `data/metadata/tier*_state.json` (environment state),
this preflight wrapper, and the internal viva-preparation note
(`reports/viva_prep.md`).

---

## 6 · Rebuild evidence

The Stage-6 clean rebuild ran 21/21 steps with exit 0 in 3,749.9 s
(62.5 min). Slowest steps:

| step | seconds |
|---|---:|
| daily_features | 2,875.138 |
| v2_stage3 | 643.849 |
| v2_stage4 | 87.327 |
| v2_stage1 | 36.060 |
| v2_stage2 | 24.884 |

`data/raw/` stayed at 577 files / 611,881,127 bytes. Reproducibility is
numerical, not byte-identical: 40/73 tables byte-identical, 25 at
≤3.55e-14 relative, 4 reorder-only, 2 QuantReg optimizer drifts
(7.44e-7), 1 float-aggregation difference (±1 unit on ~1e8 sums), and 1
descriptive sequential-fold threshold flip (146→141; anchored 686
unchanged). Final classifications are identical. Details:
`docs/reproducibility.md`; `outputs/tables/v2_clean_rebuild_audit.csv`.

Current suite: **161 passed, 0 failed**
(`pytest tests notebooks/*_*.ipynb --nbmake`).

---

## 7 · Remaining user decisions

Two items are resolved; one deposit decision remains. None is answered
by this preflight.

1. **RESOLVED (2026-11-14): author identity.** `CITATION.cff` and
   `LICENSE` name `Prabin Shrestha <itsme_prabin@outlook.com>`. The
   v2.0.2 archive and this preflight are built from that tree.
2. **RESOLVED FOR THE PUBLIC REPO (2026-11-14): tier1 upstream caveat.**
   The author accepted public release of figures with the upstream
   NEPSE Alpha position unresolved. The terms were retrieved and grant
   no explicit redistribution right; upstream clearance is not claimed.
   This deposit still excludes figures and does not redistribute raw
   OHLCV.
3. **TODO(user): deposit scope and destination.** Keep the derived-only
   payload (recommended), or decide to add a licensed data subset, and
   name the repository/DOI service. Upload requires explicit
   authorisation. Raw archives are not covered by the code licence and
   are never in this archive.
