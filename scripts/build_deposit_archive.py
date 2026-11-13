"""Build the deterministic derived-only deposit archive (v2.0.1 handoff).

Scope: code, documentation, chapter handoff packs, derived metadata, and the
derived tables of record.  Raw archives, DuckDB, processed parquet, logs, and
licence-restricted figures are excluded by construction.

The packer is deterministic: files are sorted, tar metadata is normalised
(mtime=0, uid/gid=0, empty uname/gname), and gzip is written with mtime=0.
Building twice from the same tree must yield the same SHA-256.

`docs/deposit_preflight.md` is a wrapper record, not payload, so it is
excluded from the archive to avoid a self-referential hash.

Usage:
    nepse-msc/bin/python scripts/build_deposit_archive.py
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import stat
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ARCHIVE_NAME = "nepse-floorsheet-microstructure-v2.0.1-derived.tar.gz"
CONTENTS_NAME = "nepse-floorsheet-microstructure-v2.0.1-derived.contents.csv"
SUMMARY_NAME = "nepse-floorsheet-microstructure-v2.0.1-derived.summary.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_register_v2 as regaudit  # noqa: E402

INCLUDE_ROOTS = [
    "src",
    "scripts",
    "tests",
    "configs",
    "notebooks",
    "docs",
    "reports",
    "data/metadata",
    "outputs/tables",
]
ROOT_FILES = [
    ".gitignore",
    "CITATION.cff",
    "LICENSE",
    "Makefile",
    "README.md",
    "pyproject.toml",
    "requirements-lock.txt",
    "requirements.txt",
]
EXCLUDE_PREFIXES = (
    "data/raw/",
    "data/duckdb/",
    "data/processed/",
    "outputs/figures/",
    "outputs/logs/",
    "outputs/predictions/",
    "outputs/manifests/",
    "dash/",
    "dist/",
)
EXCLUDE_NAMES = {
    "__pycache__", ".pytest_cache", ".ipynb_checkpoints", ".git",
    "nepse-msc", ".venv", "build",
}
EXCLUDE_FILES = {
    "docs/deposit_preflight.md",
    "data/metadata/tier1_state.json",
    "data/metadata/tier2_state.json",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".parquet", ".duckdb", ".log", ".png",
                    ".jpg", ".jpeg", ".pdf"}
RESTRICTED_LICENCES = ("pending_user_ui_check", "unstated_in_repo")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _skip(rel: str) -> bool:
    return (rel in EXCLUDE_FILES
            or rel.startswith(EXCLUDE_PREFIXES)
            or any(part in EXCLUDE_NAMES for part in Path(rel).parts)
            or Path(rel).suffix in EXCLUDE_SUFFIXES)


def collect_files() -> list[str]:
    files: set[str] = set()
    for root in INCLUDE_ROOTS:
        base = ROOT / root
        if not base.is_dir():
            raise SystemExit(f"missing include root: {root}")
        for path in base.rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            rel = str(path.relative_to(ROOT))
            if not _skip(rel):
                files.add(rel)
    for rel in ROOT_FILES:
        path = ROOT / rel
        if path.is_file() and not path.is_symlink() and not _skip(rel):
            files.add(rel)
    return sorted(files)


def classify(rel: str) -> str:
    if rel.startswith(("src/", "scripts/", "tests/")):
        return "code"
    if rel.startswith("configs/"):
        return "config"
    if rel.startswith("notebooks/"):
        return "notebook"
    if rel.startswith("docs/"):
        return "doc"
    if rel.startswith("reports/"):
        return "report"
    if rel.startswith("outputs/tables/"):
        return "derived_table"
    if rel.startswith("data/metadata/"):
        return "derived_metadata"
    return "root"


def licence_for(rel: str, manifest: dict[str, dict[str, str]]) -> str:
    row = manifest.get(rel)
    if row is not None and row.get("licence"):
        return row["licence"]
    kind = classify(rel)
    if kind in {"code", "config", "root"}:
        return "MIT (this repository)"
    if kind == "notebook":
        return "MIT (this repository)"
    if kind in {"doc", "report"}:
        return "derived documentation; input licences per this manifest"
    if kind == "derived_table":
        return "derived; input licences per this manifest"
    if kind == "derived_metadata":
        return "derived metadata; input licences per this manifest"
    return "derived; input licences per this manifest"


def verify_policy(files: list[str]) -> None:
    for rel in files:
        if rel.startswith(EXCLUDE_PREFIXES):
            raise SystemExit(f"excluded path leaked into deposit: {rel}")
        if rel in EXCLUDE_FILES:
            raise SystemExit(f"wrapper/state file leaked into deposit: {rel}")
        if Path(rel).suffix in EXCLUDE_SUFFIXES:
            raise SystemExit(f"excluded suffix leaked into deposit: {rel}")


def verify_tables(files: list[str], manifest: dict[str, dict[str, str]]) -> int:
    tables = [rel for rel in files if rel.startswith("outputs/tables/")]
    failures: list[str] = []
    for rel in tables:
        path = ROOT / rel
        row = manifest.get(rel)
        if row is None:
            failures.append(f"{rel}: NO_MANIFEST_HASH")
            continue
        try:
            recorded_size = int(float(row["bytes"]))
        except (TypeError, ValueError):
            recorded_size = -1
        if row["sha256"] != sha256_file(path) or recorded_size != path.stat().st_size:
            failures.append(
                f"{rel}: HASH_MISMATCH live {sha256_file(path)[:12]}/"
                f"{path.stat().st_size} vs {row['sha256'][:12]}/{row['bytes']}")
    if failures:
        raise SystemExit("table provenance verification failed:\n  "
                         + "\n  ".join(failures))
    return len(tables)


def verify_licence_policy(files: list[str],
                          manifest: dict[str, dict[str, str]]) -> dict[str, object]:
    licence_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    if not licence_text.startswith("MIT License"):
        raise SystemExit("LICENSE is not the MIT licence text")
    if "license: MIT" not in citation:
        raise SystemExit("CITATION.cff does not declare license: MIT")
    if any(rel.startswith(("data/raw/", "outputs/figures/")) for rel in files):
        raise SystemExit("restricted raw/figure path present in deposit")

    counts: dict[str, int] = {}
    for rel in files:
        licence = licence_for(rel, manifest)
        counts[licence] = counts.get(licence, 0) + 1
    restricted = {
        rel: licence_for(rel, manifest)
        for rel in files
        if any(token in licence_for(rel, manifest)
               for token in RESTRICTED_LICENCES)
    }
    if restricted:
        raise SystemExit("restricted licence path present in deposit: "
                         + ", ".join(sorted(restricted)[:5]))
    with open(regaudit.MANIFEST, newline="", encoding="utf-8") as f:
        all_manifest_rows = list(csv.DictReader(f))
    pending_input_rows = sum(
        1 for row in all_manifest_rows
        if "pending_user_ui_check" in (row.get("licence") or ""))
    unstated_input_rows = sum(
        1 for row in all_manifest_rows
        if "unstated_in_repo" in (row.get("licence") or ""))
    return {
        "code_licence": "MIT",
        "restricted_paths_in_archive": 0,
        "pending_tier1_licence_rows_in_manifest": pending_input_rows,
        "unstated_index_licence_rows_in_manifest": unstated_input_rows,
        "licence_counts": dict(sorted(counts.items())),
    }


def write_contents(files: list[str],
                   manifest: dict[str, dict[str, str]]) -> tuple[Path, str, int]:
    out = DIST / CONTENTS_NAME
    total = 0
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["artifact_path", "class", "licence", "bytes", "sha256"])
        for rel in files:
            path = ROOT / rel
            size = path.stat().st_size
            total += size
            writer.writerow([rel, classify(rel), licence_for(rel, manifest),
                             size, sha256_file(path)])
    return out, sha256_file(out), total


def tar_payload(files: list[str]) -> bytes:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w",
                      format=tarfile.USTAR_FORMAT) as tar:
        for rel in files:
            path = ROOT / rel
            data = path.read_bytes()
            info = tarfile.TarInfo(rel)
            info.size = len(data)
            info.mtime = 0
            info.mode = (0o755 if os.access(path, os.X_OK)
                         else stat.S_IRUSR | stat.S_IWUSR
                         | stat.S_IRGRP | stat.S_IROTH)
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.type = tarfile.REGTYPE
            tar.addfile(info, io.BytesIO(data))
    return raw.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    DIST.mkdir(exist_ok=True)
    manifest = regaudit.latest_manifest()
    files = collect_files()
    verify_policy(files)
    table_count = verify_tables(files, manifest)
    licence = verify_licence_policy(files, manifest)

    contents_csv, contents_sha, uncompressed = write_contents(files, manifest)
    payload = tar_payload(files)
    archive_bytes = gzip.compress(payload, compresslevel=9, mtime=0)
    archive = DIST / ARCHIVE_NAME
    archive.write_bytes(archive_bytes)
    archive_sha = sha256_bytes(archive_bytes)
    (DIST / f"{ARCHIVE_NAME}.sha256").write_text(
        f"{archive_sha}  {ARCHIVE_NAME}\n", encoding="utf-8")

    summary = {
        "archive": f"dist/{ARCHIVE_NAME}",
        "archive_sha256": archive_sha,
        "archive_bytes": len(archive_bytes),
        "contents_csv": f"dist/{CONTENTS_NAME}",
        "contents_sha256": contents_sha,
        "file_count": len(files),
        "manifest_rows_total": sum(1 for _ in
                                   open(regaudit.MANIFEST, encoding="utf-8")) - 1,
        "payload_uncompressed_bytes": uncompressed,
        "table_count": table_count,
        "table_hashes_ok": table_count,
        "excluded_prefixes": list(EXCLUDE_PREFIXES),
        "excluded_files": sorted(EXCLUDE_FILES),
        "licence": licence,
    }
    (DIST / SUMMARY_NAME).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if not args.quiet:
        print(f"archive: dist/{ARCHIVE_NAME}")
        print(f"sha256: {archive_sha}")
        print(f"bytes: {len(archive_bytes)}")
        print(f"files: {len(files)}")
        print(f"payload uncompressed bytes: {uncompressed}")
        print(f"tables: {table_count}/{table_count} hash-aligned")
        print(f"contents manifest: dist/{CONTENTS_NAME} ({contents_sha[:12]})")
        print("licence policy: MIT code; 0 restricted paths; "
              f"{licence['pending_tier1_licence_rows_in_manifest']} pending "
              "tier1 manifest rows (figures excluded)")


if __name__ == "__main__":
    main()
