# Deposit preflight — v2.1.0 derived-only archive

**Release:** `v2.1.0-reciprocity-correction` · 2026-11-19
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
| archive | `dist/nepse-floorsheet-microstructure-v2.1.0-derived.tar.gz` (gitignored) |
| SHA-256 | `57519e42465ccf18e8ca089d77811bf3f81a14194606c3b78fa43ec6097b07be` |
| compressed size | 3,054,635 bytes |
| payload files | 354 |
| uncompressed payload | 14,996,830 bytes |
| content manifest | `dist/nepse-floorsheet-microstructure-v2.1.0-derived.contents.csv` |
| content-manifest SHA-256 | `13c6d996c6116572ccfff00055bf4787cdee82bc3617713b39ecbabe94dc6858` |
| provenance rows at seal | 1,225 |

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
| code | 132 |
| derived_table | 123 |
| report | 65 |
| doc | 10 |
| config | 9 |
| derived_metadata | 5 |
| notebook | 2 |
| root | 8 |
| **total** | **354** |

The payload contains the pipeline package, scripts, tests, configs,
notebooks, docs, reports/chapter packs, derived metadata, and all
123 derived tables of record.

---

## 3 · Hash verification

| check | result |
|---|---|
| derived tables hash-matched to latest provenance row | 123/123 |
| payload files hashed in content manifest | 354/354 |
| chapter crosswalk rows OK | 67/67 |
| register-audit checks OK | 738/741 |

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
| historical tier1 manifest rows carrying the superseded pending label | 4 |
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
(kept in the private workspace, not in the repository).

---

## 6 · Rebuild evidence

The Stage-6 clean rebuild ran 21/21 steps with exit 0 in 4,209.8 s
(70.2 min). Slowest steps:

| step | seconds |
|---|---:|
| daily_features | 3,207.142 |
| v2_stage3 | 769.211 |
| v2_stage4 | 90.048 |
| v2_stage1 | 33.055 |
| panel_regressions | 24.388 |

`data/raw/` stayed at 577 files / 611,881,127 bytes. Reproducibility is
numerical, not byte-identical. The v2.1.0 build intentionally changes
every artifact that depends on `reciprocity_volume`; hypotheses that do
not use that feature are checked for exact reproduction. The v2.0.2
equivalence audit remains at `outputs/tables/v2_clean_rebuild_audit.csv`,
and the byte-frozen v2.0.2 tables are in
`outputs/tables/superseded_v2_0_2/`. The correction record and the
old-versus-corrected comparison are in
`reports/reciprocity_correction.md`. Details: `docs/reproducibility.md`.

Current suite: see the latest `outputs/logs/v2_stage6_pytest*.log`;
the release gate is zero failures.

---

## 7 · Remaining user decisions

Two items are resolved; one deposit decision remains. None is answered
by this preflight.

1. **RESOLVED (2026-11-14): author identity.** `CITATION.cff` and
   `LICENSE` name `Prabin Shrestha <itsme_prabin@outlook.com>`. The
   v2.1.0 archive and this preflight are built from that tree.
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
