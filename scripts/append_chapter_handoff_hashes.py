"""Append hash-bearing provenance rows for the v2.0.1 chapter handoff.

The manifest is append-only.  This script collects every artefact cited by the
verified crosswalk, every chapter pack manifest, and the handoff tooling itself,
then appends ONE current hash-bearing row per file that lacks an aligned row.
It is idempotent: aligned files are skipped.

Usage:
    nepse-msc/bin/python scripts/append_chapter_handoff_hashes.py [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_chapter_map as chapter_audit  # noqa: E402
import audit_register_v2 as regaudit  # noqa: E402
from nepsemsc.utils import provenance as prov  # noqa: E402
from nepsemsc.utils.io import atomic_write_bytes  # noqa: E402

FIXED = [
    "docs/chapter_artifact_map.md",
    "docs/deposit_preflight.md",
    "docs/deposit_readme.md",
    "docs/reproducibility.md",
    "AGENTS.md",
    "outputs/tables/v2_chapter_map_audit.csv",
    "outputs/tables/v2_register_audit.csv",
    "scripts/build_chapter_artifact_map.py",
    "scripts/audit_chapter_map.py",
    "scripts/append_chapter_handoff_hashes.py",
    "scripts/build_deposit_archive.py",
    "tests/test_chapter_map_integrity.py",
]
GLOBS = [
    "reports/chapter_assets/ch[1-6]_*.md",
    "reports/chapter_assets/ch[1-4]_asset_manifest.csv",
    # Deposit inventory: hash every file the derived-only archive can contain.
    "outputs/tables/*.csv",
    # v2.1.0: byte-frozen superseded results are cited by the crosswalk.
    "outputs/tables/superseded_v2_0_2/*.csv",
    "docs/*.md",
    "reports/*.md",
    "scripts/*.py",
    "tests/*.py",
    "src/**/*.py",
    "configs/**/*",
    "notebooks/*.ipynb",
    "data/metadata/*.csv",
    "data/metadata/*.md",
    "data/metadata/*.json",
    "*.md",
    "*.cff",
    "LICENSE",
    "Makefile",
    "pyproject.toml",
    "requirements.txt",
    "requirements-lock.txt",
]


def sha256_and_lines(path: Path) -> tuple[str, int | None]:
    h = hashlib.sha256()
    lines = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            lines += chunk.count(b"\n")
    rows_total = max(lines - 1, 0) if path.suffix == ".csv" else None
    return h.hexdigest(), rows_total


def licence_for(rel: str) -> str:
    if rel.startswith(("scripts/", "tests/", "src/")):
        return "MIT (this repository)"
    if rel.startswith(("docs/", "reports/")):
        return "derived documentation; input licences per this manifest"
    if rel.startswith("outputs/tables/"):
        return "derived; input licences per this manifest"
    if rel.startswith("data/metadata/"):
        return "derived metadata; input licences per this manifest"
    return "derived; input licences per this manifest"


def collect_paths() -> list[str]:
    paths: set[str] = set()
    try:
        for row in chapter_audit.parse_map():
            paths.add(row["artifact_path"])
    except SystemExit:
        pass
    for pattern in GLOBS:
        for path in ROOT.glob(pattern):
            if path.is_file():
                paths.add(str(path.relative_to(ROOT)))
    for rel in FIXED:
        if (ROOT / rel).is_file():
            paths.add(rel)
    # EXP-0014's register cell, if present, is the authoritative citation list.
    for row in regaudit.register_rows():
        if row["id"] != "EXP-0014":
            continue
        for path in regaudit.artifact_paths(row):
            if path.is_file() and path.is_relative_to(ROOT):
                paths.add(str(path.relative_to(ROOT)))
    manifest_rel = str(prov.MANIFEST.relative_to(ROOT))
    return sorted(p for p in paths
                  if (ROOT / p).is_file()
                  and not p.startswith(FORBIDDEN)
                  and p != manifest_rel)


FORBIDDEN = ("data/raw/", "data/duckdb/", "data/processed/",
             "outputs/logs/", "outputs/figures/")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    latest = regaudit.latest_manifest()
    additions = []
    aligned = 0
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for rel in collect_paths():
        path = ROOT / rel
        digest, rows_total = sha256_and_lines(path)
        size = path.stat().st_size
        row_m = latest.get(rel)
        if row_m is not None:
            try:
                recorded = int(float(row_m["bytes"]))
            except (TypeError, ValueError):
                recorded = -1
            if row_m["sha256"] == digest and recorded == size:
                aligned += 1
                continue
        additions.append({
            "ts_utc": utc,
            "artifact": rel,
            "kind": "chapter_handoff_artifact_hash",
            "source_path": "post-freeze v2.0.1 chapter handoff (EXP-0014)",
            "source_url": "",
            "sha256": digest,
            "bytes": size,
            "rows_sampled": "",
            "rows_total": "" if rows_total is None else rows_total,
            "licence": licence_for(rel),
            "evidence": ("v2.0.1 verified chapter handoff; crosswalk/pack audit "
                         "(EXP-0014)"),
        })

    print(f"handoff artefacts collected: {aligned + len(additions)}")
    print(f"already hash-aligned: {aligned}")
    print(f"hash rows to append: {len(additions)}")
    for add in additions:
        print(f"  + {add['artifact']}  {add['sha256'][:12]}  {add['bytes']}")

    if args.dry_run or not additions:
        return

    with open(prov.MANIFEST, newline="", encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
    payload = existing + [{c: str(a.get(c, "")) for c in prov.COLUMNS}
                          for a in additions]
    text = (",".join(prov.COLUMNS) + "\n"
            + "\n".join(prov._quote_row(r) for r in payload) + "\n")
    atomic_write_bytes(prov.MANIFEST, text.encode("utf-8"))
    print(f"manifest rows: {len(existing)} -> {len(payload)}")


if __name__ == "__main__":
    main()
