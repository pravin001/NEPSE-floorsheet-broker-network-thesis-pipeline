# Reproducibility guide (living; v1.0 freeze + v2.0 Stage-6 clean rebuild)

## Environment

```bash
cd ~/research/nepse-floorsheet-microstructure
make bootstrap && make install && make lock     # venv `nepse-msc`, py3.11.16 (uv-managed)
```
Pins reproduced in `requirements-lock.txt` (committed after first install).

## Data

1. NABIL 2024-12 sample (Phase 1): `make smoke` (uses LOCAL socrateai
   archive at the sibling project path; sha256 verified per source file).
2. Full top-10 × window (Phase 2): backfill/download via the socrateai index
   + quality audit + OHLCV reconciliation (script noted in AGENTS.md).

## Tests

```bash
make test-fast          # unit + leakage + SE-spec suite
make test               # + nbmake notebook execution (DC19)
```

## Notebooks

Blocks execute top-to-bottom via nbmake; stale-state cheating is a test failure.

## Seeds

`src/nepsemsc/utils/seeds.py` (DC14). Isolation Forest per fold, placebos,
network layout. Pre-declared 2026-11-08 in `docs/analysis_plan.md` §8.

## Git

Every experiment row in `docs/experiment_register.md` names the artefact +
config sha256; manifests in `data/metadata/` + `outputs/manifests/` are
tracked in git.

---

# v2.1.0 reciprocity correction (2026-11-18/19)

## Trigger and fix

`reciprocity_volume` counted every ordered pair `(i,j)` and treated
self-loops as reciprocal flow. The corrected metric counts each unordered pair
once, excludes self-loops from the numerator and keeps them in the denominator:

```text
reciprocity = 2 · Σ_{i<j} min(w_ij, w_ji) / Σ_{i≠j} w_ij
```

The fix is committed before the rebuild as
`e2cc72b` on `fix/reciprocity-correction`
(`src/nepsemsc/features/network.py`; 15/15 network-metric tests). The full
defect/fix/old-versus-new record is `reports/reciprocity_correction.md`;
governance rows are EXP-0015 and deviation #45.

On all 233,706 `(symbol,date)` rows the old and corrected values satisfy

```text
old = 2 × (corrected + self_loop_share)
```

The factor 2 is neutral under TRAIN-fold standardisation. The additive
self-loop term is substantive and is why every dependent result was rebuilt,
not rescaled.

## Scope and command

```bash
cd ~/research/nepse-floorsheet-microstructure
nepse-msc/bin/python scripts/run_stage6_rebuild.py --clean 2>&1 | tee outputs/logs/v2_stage6_rebuild.log
```

The v2.1.0 clean rebuild completed **21/21 steps, exit 0, 4,209.8 s
(70.2 min)**, reading only the untouched raw archives. `data/raw/` was
unchanged (577 files / 611,881,127 bytes). Stage scripts that consume the grid
were rebuilt from source; no inherited v2.0.2 table was reused as an input.
The canonical runner log is `outputs/logs/v2_stage6_rebuild.log`; the
per-stage logs (`v2_stage1.log` … `v2_stage5.log`) remain the historical
v2.0.2 records and are labelled as such in the reports.

## Superseded v2.0.2 record

The 43 pre-correction CSVs that directly carry reciprocity-dependent values
are byte-frozen in `outputs/tables/superseded_v2_0_2/`, with `README.md` and
`MANIFEST.sha256`. They are not mixed into the live tables. The old
classifications (H10 sole `HEADLINE_MODERATE`; H6/H7/H8 `NULL_FRAGILE`) are
the documented v2.0.2 record and are quoted only with that label.

## Reproducibility verdict

The rebuild is **numerically reproducible, not byte-identical**, for the same
reasons as v2.0.2 (float summation order, solver convergence, threshold-adjacent
event flags). The corrected final classifications are read from
`outputs/tables/v2_final_headline_set.csv`: **H6 `HEADLINE_ROBUST`**,
**H10 `HEADLINE_MODERATE`**, H4 `EXPLORATORY_POST_HOC`, H7/H8 `NULL_FRAGILE`,
H1/H2/H3/H5/H9 `NULL_POWERED`.

## Tests and independent verification

```bash
nepse-msc/bin/python -m pytest tests notebooks/*_*.ipynb --nbmake -q
nepse-msc/bin/python scripts/verify_h10_independent.py
nepse-msc/bin/python scripts/audit_register_v2.py
nepse-msc/bin/python scripts/audit_chapter_map.py
```

Close-out results are recorded in `docs/deposit_preflight.md` and the release
commit message. The corrected H10 recomputation, RW p, spot checks and chapter
crosswalk are regenerated from the corrected tables, not hand-edited.

## Release and archive

The release commit is tagged `v2.1.0-reciprocity-correction`. The derived-only
deposit archive is rebuilt at
`dist/nepse-floorsheet-microstructure-v2.1.0-derived.tar.gz`; its SHA-256 and
inventory are in `docs/deposit_preflight.md`. The v2.0.2 archive is not
overwritten, and `v2.0.2-prewrite` is not moved.

---

# v2.0.2 Stage-6 clean rebuild (2026-11-12/13) — historical, superseded

> **Superseded by v2.1.0.** This section records the pre-correction v2.0.2
> rebuild. The `reciprocity_volume` metric was corrected afterwards; the
> corrected build and its old-versus-new comparison are in
> `reports/reciprocity_correction.md` and the v2.1.0 section below. The
> classifications quoted in this historical section are **not** current.

## Scope and command

The v2 freeze rebuild deletes **only** the two derivative directories and
reruns the documented pipeline from the raw archives:

```bash
nepse-msc/bin/python scripts/run_stage6_rebuild.py --clean
```

| item | value |
|---|---|
| deleted | `data/processed/` (9 files, 33,685,688 bytes) + `data/duckdb/` (1 file, 1,814,573,056 bytes) |
| raw archives | **untouched**: `data/raw/` = 577 files / 611,881,127 bytes before AND after the clean step |
| driver | `scripts/run_stage6_rebuild.py` (21 ordered steps; aborts on any non-zero exit) |
| full log | `outputs/logs/v2_stage6_rebuild.log` |
| per-step timings | `outputs/logs/v2_stage6_rebuild_timings.csv` |
| environment | Python 3.11.16 · Linux 7.0.0-43-generic (24 cores) · lock SHA-256 `0de6eaf8f6b04c2589e784b314e57116f7ce28da768ec5005dc5caf9dc2ac061` |
| window | `2026-11-12T08:28:24Z` → `2026-11-12T09:30:54Z` |
| total wall time | **3,749.9 s = 62.5 min**, 21/21 steps exit 0 |

Slowest steps: `daily_features` 2,875.1 s (47.9 min), `v2_stage3` 643.8 s,
`v2_stage4` 87.3 s, `v2_stage1` 36.1 s, `v2_stage2` 24.9 s. All other steps
are under 25 s. The complete per-step table is the timings CSV above.

## Reproducibility verdict

All 73 tracked table artefacts were compared byte-for-byte and cell-by-cell
against their frozen `HEAD` versions; evidence is
`outputs/tables/v2_clean_rebuild_audit.csv`. This audit predates the
reciprocity correction and is retained as the v2.0.2 record.

| status | n | meaning |
|---|---:|---|
| `IDENTICAL` | 40 | byte-for-byte identical |
| `NUMERIC_EPSILON` | 25 | same values to floating-point precision; max relative error **3.55e-14** on the v1 grid, 2.03e-12 in `broker_id_defect_sensitivity.csv` |
| `REORDERED_ONLY` | 4 | identical row multiset, row order differs (`corpus_*` audit tables) |
| `OPTIMIZER_DRIFT` | 2 | `quantile_regression.csv` / `quantile_tail_summary.csv`: statsmodels QuantReg convergence path, max relative 7.44e-7; tail labels and shapes identical |
| `FLOAT_AGGREGATION` | 1 | `corpus_symbol_coverage.csv`: 11 symbol totals differ by 1 unit on ~1e8-scale sums (max relative 9.09e-8) |
| `THRESHOLD_FLIP` | 1 | `robustness_sequential_variant.csv`: descriptive sequential-fold variant fold-0 event count 146→141 (5 rows, 0.46%); the anchored primary event count stays 686; pooled rank correlation +.8706→+.8703 |

**v2.0.2 classifications (superseded):** H10 `HEADLINE_MODERATE`; H4
`EXPLORATORY_POST_HOC`; H6/H7/H8 `NULL_FRAGILE`; H1/H2/H3/H5/H9
`NULL_POWERED`. The corrected v2.1.0 labels are read from
`outputs/tables/v2_final_headline_set.csv`.

This is **numerical reproducibility, not byte-identity**: floating-point
summation order, solver convergence, and threshold-adjacent event flags move
at the last digits. No estimate, p-value, tail label, or classification of
record changed. After the audit, all tracked tables were restored
byte-for-byte from `HEAD` so the deposit remains the frozen artefact set; the
rebuilt snapshot is retained outside git at `/tmp/opencode/rebuilt_tables/`
as the audit evidence. The rebuilt `data/processed/`, `data/duckdb/`, and
dashboard cache are the Stage-6 outputs (gitignored, reproducible).

## Freeze snapshot

`configs/v2_freeze/` holds byte copies of the seven binding files with a
SHA-256 manifest (`freeze_manifest.csv`):

| source | sha256 |
|---|---|
| `configs/project.yaml` | `9a60208f…b012f` (v1 frozen fingerprint) |
| `docs/analysis_plan.md` | `7d29da6b…dead2` |
| `docs/analysis_plan_v2_extension.md` | `5599c5a3…d9d98` |
| `requirements-lock.txt` | `0de6eaf8…ac061` (153 pins, `arch==8.0.0`) |
| `pyproject.toml` | `a7956986…6dcc3` |
| `src/nepsemsc/utils/seeds.py` | `2705b672…75ba` |
| `src/nepsemsc/utils/seeds_v2.py` | `71d1024d…74073` |

`tests/test_freeze_v2.py` verifies both the snapshot hashes and that the live
binding files still match them; a post-freeze edit fails the suite.

## Final register audit

`scripts/audit_register_v2.py` resolves every artefact cited by the 48
experiment rows, expands brace groups/globs/raw-slice patterns, and requires
the latest **hash-bearing** manifest row to match the current SHA-256 and byte
size. It writes `outputs/tables/v2_register_audit.csv`.

Result: **697 artefact checks — 695 `OK`, 1 `SELF_REFERENTIAL` (the manifest
cannot record its own post-append hash), 1 `HISTORICAL_REFERENCE` (EXP-0000's
142-pin initial-commit lock; the live v2 lock is frozen separately).** No
missing, unmanifested, or hash-mismatched artefact.

The Stage-6 backfill appended 629 hash-bearing rows covering 626 distinct
artefacts (576 raw-slice extracts, 45 pre-existing register artefacts, 5
Stage-6 artefacts); three rows are refreshed hashes after line-ending
normalization and audit-status stabilization. Earlier placeholder and
source-day rows are retained unchanged, and the audit ignores rows without a
digest.

## Final test suite

```bash
nepse-msc/bin/python -m pytest tests notebooks/*_*.ipynb --nbmake
```

The Stage-6 freeze run passed **154 tests, 0 failed** (in 9.23 s): all
unit/leakage/SE-specification tests, the five `tests/test_freeze_v2.py` snapshot
checks, and the four executed notebooks. This clears the V2-6 ≥80-test
requirement.

The post-freeze v2.0.1 handoff adds seven chapter-map integrity tests; the
current suite is **161 passed, 0 failed** (in 9.36 s).

## v2.0.1 deposit archive

```bash
nepse-msc/bin/python scripts/build_deposit_archive.py
```

The packer is deterministic (sorted file list, mtime/uid/gid normalised,
gzip mtime 0), writes `dist/nepse-floorsheet-microstructure-v2.0.1-derived.tar.gz`,
and refuses to build if any `outputs/tables/*.csv` lacks a matching
hash-bearing provenance row or if a raw/figure/log path leaks into the payload.
`docs/deposit_preflight.md` records the archive hash, content-manifest hash,
inventory, licence checks and the three remaining user decisions.
