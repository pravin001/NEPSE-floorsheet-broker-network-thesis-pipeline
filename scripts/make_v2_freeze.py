"""Create the v2 freeze snapshot (`configs/v2_freeze/`) with SHA-256 per file.

Run ONCE after the clean rebuild has been verified.  Re-running is allowed but
is a governance action: it replaces the snapshot and manifest, and must be
logged in `docs/analysis_deviations.md`.
"""
from __future__ import annotations

import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs" / "v2_freeze"

FILES = [
    ("configs/project.yaml", "project.yaml",
     "v1 frozen config fingerprint 9a60208f...b012f"),
    ("docs/analysis_plan.md", "analysis_plan.md",
     "v1 plan — byte-frozen, never edited by v2"),
    ("docs/analysis_plan_v2_extension.md", "analysis_plan_v2_extension.md",
     "v2 pre-declaration, written before any v2 result"),
    ("requirements-lock.txt", "requirements-lock.txt",
     "live venv freeze after all Stage-3 installs; 153 pins incl. arch==8.0.0"),
    ("pyproject.toml", "pyproject.toml",
     "package metadata + declared dependencies (incl. arch>=8.0)"),
    ("src/nepsemsc/utils/seeds.py", "seeds.py",
     "v1 seed constants (DC14)"),
    ("src/nepsemsc/utils/seeds_v2.py", "seeds_v2.py",
     "v2 seed ranges (plan V2-0)"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    FREEZE.mkdir(parents=True, exist_ok=True)
    frozen = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for source, snapshot, note in FILES:
        src = ROOT / source
        if not src.is_file():
            raise SystemExit(f"missing binding file: {source}")
        dst = FREEZE / snapshot
        shutil.copyfile(src, dst)
        digest = sha256(dst)
        rows.append({
            "source_path": source,
            "snapshot_file": snapshot,
            "sha256": digest,
            "bytes": dst.stat().st_size,
            "frozen_utc": frozen,
            "note": note,
        })
        print(f"{digest}  {source} -> configs/v2_freeze/{snapshot}")

    with open(FREEZE / "freeze_manifest.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "source_path", "snapshot_file", "sha256", "bytes", "frozen_utc", "note"],
            lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"freeze manifest written: {len(rows)} files @ {frozen}")


if __name__ == "__main__":
    main()
