# Deposit preflight — v2.0.1 derived-only archive

**Release:** `v2.0.1-handoff` (post-`v2.0-a++-freeze`) · 2026-11-13
**Metadata update:** 2026-11-14 — legal author identity recorded. The archive
hashes below are the v2.0.1 seal and predate this metadata-only update; rebuild
the archive and this preflight before any deposit.
**Status:** archive built and verified locally; **NOT deposited**, no DOI.
Deposit upload is a user action; the public code repository is separate from
this derived-only archive.

This file is a wrapper record. It is excluded from the archive payload so
the archive SHA-256 is not self-referential; the payload's embedded
provenance manifest predates the final wrapper hash row.

---

## 1 · Archive identity

| item | value |
|---|---|
| archive | `dist/nepse-floorsheet-microstructure-v2.0.1-derived.tar.gz` (gitignored) |
| SHA-256 | `98ec4354c104ed67b22c45f53660a210e26504154701b47e28adad65c9c10ee6` |
| compressed size | 2,664,102 bytes |
| payload files | 264 |
| uncompressed payload | 13,830,497 bytes |
| content manifest | `dist/nepse-floorsheet-microstructure-v2.0.1-derived.contents.csv` |
| content-manifest SHA-256 | `a7c1c0e2286742de14dd472c0ae151e36bd219e0f59f162768a69687a616beef` |
| provenance rows at seal | 938 |

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
| code | 128 |
| derived_table | 76 |
| report | 26 |
| doc | 10 |
| config | 9 |
| derived_metadata | 5 |
| notebook | 2 |
| root | 8 |
| **total** | **264** |

The payload contains the pipeline package, scripts, tests, configs,
notebooks, docs, reports/chapter packs, derived metadata, and all
76 derived tables of record.

---

## 3 · Hash verification

| check | result |
|---|---|
| derived tables hash-matched to latest provenance row | 76/76 |
| payload files hashed in content manifest | 264/264 |
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
| tier1 OHLCV manifest rows carrying the superseded pending label | 3 |
| NEPSE index unstated-licence manifest rows | 1 |

Floorsheet inputs: Kaggle viking303 2021–2023 (**CC0**) and socrateai
2024 (**MIT**). Tier1 OHLCV is **MIT-declared on Kaggle** with an explicit
educational/research statement, but its prices are “scraped from NEPSE Alpha”
and upstream terms remain **UNCERTAIN** (`reports/licence_review.md`). Three
historical manifest rows still carry the superseded `pending_user_ui_check`
label. `outputs/figures/` remains excluded from this derived-only payload
pending the author's public-redistribution decision. The NEPSE index is a
secondary input with an unstated repository licence. Raw archives, DuckDB,
processed parquet, prediction parquet, logs, and figures are **not
redistributed**.

---

## 5 · Excluded scope

Excluded by construction (the packer refuses to leak them):

`data/raw/` · `data/duckdb/` · `data/processed/` · `outputs/figures/` ·
`outputs/logs/` · `outputs/predictions/` · `outputs/manifests/` ·
`dash/` · `dist/` · venv/cache/pyc files.

Also excluded: `data/metadata/tier*_state.json` (environment state) and
this preflight wrapper.

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

Two user decisions remain (item 1 is retained as the resolution record).

1. **RESOLVED (2026-11-14): author identity.** `CITATION.cff` and `LICENSE`
   now name `Prabin Shrestha <itsme_prabin@outlook.com>`. The recorded archive
   hashes above predate this metadata-only update; rebuild the archive and
   this preflight before deposit.
2. **TODO(user): tier1 OHLCV upstream.** Confirm the upstream NEPSE Alpha
   position. Kaggle declares MIT and states an educational/research purpose,
   but that grant may not exhaust upstream rights. Until the position is
   resolved or explicitly accepted, keep `outputs/figures/` restricted; it is
   already outside this payload.
3. **TODO(user): deposit scope.** Keep the derived-only payload
   (recommended), or decide to add a licensed data subset. Raw archives
   are not covered by the code licence and are never in this archive.
