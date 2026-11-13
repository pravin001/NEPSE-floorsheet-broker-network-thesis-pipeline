"""Backfill hash-bearing provenance rows for every register artefact (V2-6).

The v1 manifest recorded several tables with placeholder rows (empty sha256 /
zero bytes) and recorded raw-slice *source-day* hashes under the slice path.
This Stage-6 script walks the experiment register, resolves every artefact to
a concrete file, and appends ONE current hash-bearing row per file that lacks
a matching hash row.  It is idempotent: aligned files are skipped.

The manifest is append-only; existing rows are never edited.  The latest
hash-bearing row per artifact is the audit-of-record (the register audit
ignores placeholder rows).

Usage:
    nepse-msc/bin/python scripts/append_v2_manifest_hashes.py [--dry-run]
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

import audit_register_v2 as audit  # noqa: E402

from nepsemsc.utils import provenance as prov  # noqa: E402
from nepsemsc.utils.io import atomic_write_bytes  # noqa: E402


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
    if rel.startswith("data/raw/floorsheet/"):
        return ("mixed: Kaggle viking303 CC0 (2021-2023) / socrateai MIT "
                "(2024); per-file source in corpus_files_sha256.csv")
    if rel.startswith(("scripts/", "tests/", "src/", "configs/",
                       "notebooks/")):
        return "MIT (this repository)"
    return "derived; input licences per this manifest"


def source_for(rel: str, phase: str) -> str:
    if rel.startswith("data/raw/floorsheet/"):
        return "data/duckdb/nepse.duckdb (derived top-12 extract)"
    if rel == "data/duckdb/nepse.duckdb":
        return "data/raw/floorsheet + external source archives"
    phase = phase.strip("`")
    first = phase.split()[0] if phase else ""
    return first if first.startswith(("scripts/", "src/", "notebooks/")) else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = audit.register_rows()
    latest = audit.latest_manifest()

    # artifact -> (first resolving row, set of experiment ids)
    wanted: dict[str, tuple[dict[str, str], set[str]]] = {}
    for row in rows:
        for path in audit.artifact_paths(row):
            if not path.is_file():
                continue
            rel = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
            if rel == audit.MANIFEST_REL or (row["id"], rel) in audit.HISTORICAL:
                continue
            if rel not in wanted:
                wanted[rel] = (row, set())
            wanted[rel][1].add(row["id"])

    additions = []
    aligned = 0
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for rel in sorted(wanted):
        path = ROOT / rel
        digest, rows_total = sha256_and_lines(path)
        size = path.stat().st_size
        row_m = latest.get(rel)
        if row_m is not None:
            try:
                recorded = int(float(row_m["bytes"]))
            except ValueError:
                recorded = -1
            if row_m["sha256"] == digest and recorded == size:
                aligned += 1
                continue
        src_row, eids = wanted[rel]
        kind = ("stage6_raw_slice_hash_exp0002b"
                if rel.startswith("data/raw/floorsheet/")
                else "stage6_register_artifact_hash")
        additions.append({
            "ts_utc": utc,
            "artifact": rel,
            "kind": kind,
            "source_path": source_for(rel, src_row.get("phase/notebook", "")),
            "source_url": "",
            "sha256": digest,
            "bytes": size,
            "rows_sampled": "",
            "rows_total": "" if rows_total is None else rows_total,
            "licence": licence_for(rel),
            "evidence": ("v2 Stage-6 final register audit: current file hashed "
                         f"at freeze (EXP-0013); cited by {','.join(sorted(eids))}"),
        })

    print(f"register artefacts resolved: {len(wanted)}")
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
