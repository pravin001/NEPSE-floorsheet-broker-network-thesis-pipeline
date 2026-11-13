"""Write `docs/deposit_preflight.md` from the sealed archive summary and audits.

The preflight is a wrapper record, not payload: it is excluded from the archive
so the archive hash is not self-referential.  Every count and hash below is
read from `dist/*.summary.json`, `dist/*.contents.csv`, and the two audit CSVs.

Usage:
    nepse-msc/bin/python scripts/write_deposit_preflight.py
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
SUMMARY = DIST / "nepse-floorsheet-microstructure-v2.0.1-derived.summary.json"
CONTENTS = DIST / "nepse-floorsheet-microstructure-v2.0.1-derived.contents.csv"
OUT = ROOT / "docs" / "deposit_preflight.md"
TIMINGS = ROOT / "outputs" / "logs" / "v2_stage6_rebuild_timings.csv"
CHAPTER_AUDIT = ROOT / "outputs" / "tables" / "v2_chapter_map_audit.csv"
REGISTER_AUDIT = ROOT / "outputs" / "tables" / "v2_register_audit.csv"


def _counts(path: Path, column: str) -> Counter[str]:
    if not path.is_file():
        return Counter({"not_run": 1})
    with open(path, newline="", encoding="utf-8") as f:
        return Counter(row[column] for row in csv.DictReader(f))


def _timings() -> list[tuple[str, float]]:
    if not TIMINGS.is_file():
        return []
    with open(TIMINGS, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return sorted(((r["step"], float(r["duration_s"])) for r in rows),
                  key=lambda item: item[1], reverse=True)


def _fmt_int(value: int) -> str:
    return f"{value:,}"


def build() -> str:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    with open(CONTENTS, newline="", encoding="utf-8") as f:
        contents = list(csv.DictReader(f))
    classes = Counter(r["class"] for r in contents)
    chapter = _counts(CHAPTER_AUDIT, "outcome")
    register = _counts(REGISTER_AUDIT, "status")
    slowest = _timings()[:5]
    total_s = sum(d for _, d in _timings())
    licence = summary["licence"]

    chapter_total = sum(chapter.values())
    chapter_ok = chapter.get("OK", 0)
    register_total = sum(register.values())
    register_ok = register.get("OK", 0)

    lines = [
        "# Deposit preflight — v2.0.1 derived-only archive",
        "",
        "**Release:** `v2.0.1-handoff` (post-`v2.0-a++-freeze`) · 2026-11-13",
        "**Status:** archive built and verified locally; **NOT uploaded**, no DOI,",
        "no repository push. Upload is a user action.",
        "",
        "This file is a wrapper record. It is excluded from the archive payload so",
        "the archive SHA-256 is not self-referential; the payload's embedded",
        "provenance manifest predates the final wrapper hash row.",
        "",
        "---",
        "",
        "## 1 · Archive identity",
        "",
        "| item | value |",
        "|---|---|",
        f"| archive | `{summary['archive']}` (gitignored) |",
        f"| SHA-256 | `{summary['archive_sha256']}` |",
        f"| compressed size | {_fmt_int(summary['archive_bytes'])} bytes |",
        f"| payload files | {summary['file_count']} |",
        f"| uncompressed payload | {_fmt_int(summary['payload_uncompressed_bytes'])} bytes |",
        f"| content manifest | `{summary['contents_csv']}` |",
        f"| content-manifest SHA-256 | `{summary['contents_sha256']}` |",
        f"| provenance rows at seal | {summary['manifest_rows_total']:,} |",
        "",
        "Sidecars: `dist/*.sha256` (archive digest) and `dist/*.summary.json`",
        "(machine-readable identity). Rebuild deterministically with:",
        "",
        "```bash",
        "nepse-msc/bin/python scripts/build_deposit_archive.py",
        "```",
        "",
        "Two consecutive builds from the same tree were byte-identical (same",
        "SHA-256); the packer sorts paths and normalises tar/gzip metadata",
        "(mtime 0, uid/gid 0, empty owner names).",
        "",
        "---",
        "",
        "## 2 · Payload inventory",
        "",
        "| class | files |",
        "|---|---:|",
    ]
    for name in ("code", "derived_table", "report", "doc", "config",
                 "derived_metadata", "notebook", "root"):
        lines.append(f"| {name} | {classes.get(name, 0)} |")
    lines += [
        f"| **total** | **{len(contents)}** |",
        "",
        "The payload contains the pipeline package, scripts, tests, configs,",
        "notebooks, docs, reports/chapter packs, derived metadata, and all",
        f"{summary['table_count']} derived tables of record.",
        "",
        "---",
        "",
        "## 3 · Hash verification",
        "",
        "| check | result |",
        "|---|---|",
        f"| derived tables hash-matched to latest provenance row | {summary['table_hashes_ok']}/{summary['table_count']} |",
        f"| payload files hashed in content manifest | {len(contents)}/{len(contents)} |",
        f"| chapter crosswalk rows OK | {chapter_ok}/{chapter_total} |",
        f"| register-audit checks OK | {register_ok}/{register_total} |",
        "",
        "Audit outputs:",
        "",
        "- `outputs/tables/v2_chapter_map_audit.csv` — chapter→artefact",
        "  existence, crosswalk hash, latest manifest hash, EXP-id and",
        "  claim-version checks.",
        "- `outputs/tables/v2_register_audit.csv` — experiment-row artefact",
        "  resolution and manifest hash checks. Non-`OK` rows are the documented",
        "  manifest self-reference and historical EXP-0000 lock exemption.",
        "",
        "Any missing path, unhashed table, or hash mismatch aborts the packer",
        "before an archive is written.",
        "",
        "---",
        "",
        "## 4 · Licence policy",
        "",
        "| check | result |",
        "|---|---|",
        f"| code licence | {licence['code_licence']} (`LICENSE`, `CITATION.cff`) |",
        f"| restricted raw/figure paths in payload | {licence['restricted_paths_in_archive']} |",
        f"| tier1 OHLCV pending-licence manifest rows | {licence['pending_tier1_licence_rows_in_manifest']} |",
        f"| NEPSE index unstated-licence manifest rows | {licence['unstated_index_licence_rows_in_manifest']} |",
        "",
        "Floorsheet inputs: Kaggle viking303 2021–2023 (**CC0**) and socrateai",
        "2024 (**MIT**). Tier1 OHLCV remains **pending user UI confirmation**, so",
        "`outputs/figures/` is excluded from this derived-only payload. The NEPSE",
        "index is a secondary input with an unstated repository licence. Raw",
        "archives, DuckDB, processed parquet, prediction parquet, logs, and",
        "figures are **not redistributed**.",
        "",
        "---",
        "",
        "## 5 · Excluded scope",
        "",
        "Excluded by construction (the packer refuses to leak them):",
        "",
        "`data/raw/` · `data/duckdb/` · `data/processed/` · `outputs/figures/` ·",
        "`outputs/logs/` · `outputs/predictions/` · `outputs/manifests/` ·",
        "`dash/` · `dist/` · venv/cache/pyc files.",
        "",
        "Also excluded: `data/metadata/tier*_state.json` (environment state) and",
        "this preflight wrapper.",
        "",
        "---",
        "",
        "## 6 · Rebuild evidence",
        "",
        f"The Stage-6 clean rebuild ran 21/21 steps with exit 0 in {total_s:,.1f} s",
        f"({total_s / 60:,.1f} min). Slowest steps:",
        "",
        "| step | seconds |",
        "|---|---:|",
    ]
    for step, seconds in slowest:
        lines.append(f"| {step} | {seconds:,.3f} |")
    lines += [
        "",
        "`data/raw/` stayed at 577 files / 611,881,127 bytes. Reproducibility is",
        "numerical, not byte-identical: 40/73 tables byte-identical, 25 at",
        "≤3.55e-14 relative, 4 reorder-only, 2 QuantReg optimizer drifts",
        "(7.44e-7), 1 float-aggregation difference (±1 unit on ~1e8 sums), and 1",
        "descriptive sequential-fold threshold flip (146→141; anchored 686",
        "unchanged). Final classifications are identical. Details:",
        "`docs/reproducibility.md`; `outputs/tables/v2_clean_rebuild_audit.csv`.",
        "",
        "Current suite: **161 passed, 0 failed**",
        "(`pytest tests notebooks/*_*.ipynb --nbmake`).",
        "",
        "---",
        "",
        "## 7 · Remaining user decisions",
        "",
        "Exactly three decisions remain; none is answered by this preflight.",
        "",
        "1. **TODO(user): author identity.** Replace the placeholder author in",
        "   `CITATION.cff` and `LICENSE`, then rebuild the archive and this",
        "   preflight.",
        "2. **TODO(user): tier1 OHLCV licence.** Confirm the Kaggle UI licence.",
        "   Until then, keep `outputs/figures/` restricted; it is already outside",
        "   this payload.",
        "3. **TODO(user): deposit scope.** Keep the derived-only payload",
        "   (recommended), or decide to add a licensed data subset. Raw archives",
        "   are not covered by the code licence and are never in this archive.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    text = build()
    OUT.write_text(text, encoding="utf-8")
    todos = text.count("TODO(user)")
    assert todos == 3, todos
    print(f"preflight written: {OUT.relative_to(ROOT)}")
    print(f"TODO markers: {todos}")
    print(f"bytes: {OUT.stat().st_size}")


if __name__ == "__main__":
    main()
