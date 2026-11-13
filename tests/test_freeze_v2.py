"""v2 freeze guard (plan V2-6): SHA-256 of every binding file.

`configs/v2_freeze/freeze_manifest.csv` is the freeze record.  Two checks:

1. each snapshot under `configs/v2_freeze/` still hashes to its recorded value;
2. each live binding file is byte-identical to its snapshot.

A post-freeze edit to the plan, config, lock, or seed files therefore fails
this test instead of silently invalidating the deposit.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs" / "v2_freeze"
MANIFEST = FREEZE / "freeze_manifest.csv"

REQUIRED = {
    "configs/project.yaml",
    "docs/analysis_plan.md",
    "docs/analysis_plan_v2_extension.md",
    "requirements-lock.txt",
    "pyproject.toml",
    "src/nepsemsc/utils/seeds.py",
    "src/nepsemsc/utils/seeds_v2.py",
}
COLUMNS = ["source_path", "snapshot_file", "sha256", "bytes", "frozen_utc", "note"]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def rows() -> list[dict[str, str]]:
    assert MANIFEST.is_file(), "configs/v2_freeze/freeze_manifest.csv missing"
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == COLUMNS
        data = list(reader)
    assert data, "freeze manifest is empty"
    return data


def test_manifest_covers_every_binding_file(rows):
    sources = {r["source_path"] for r in rows}
    assert sources == REQUIRED
    assert len(rows) == len(REQUIRED)
    assert len({r["snapshot_file"] for r in rows}) == len(rows)


def test_snapshots_are_unchanged(rows):
    for r in rows:
        snap = FREEZE / r["snapshot_file"]
        assert snap.is_file(), f"missing snapshot: {snap}"
        assert _sha256(snap) == r["sha256"], f"snapshot hash drift: {snap}"
        assert snap.stat().st_size == int(r["bytes"])


def test_live_files_still_match_freeze(rows):
    for r in rows:
        live = ROOT / r["source_path"]
        assert live.is_file(), f"missing live binding file: {live}"
        assert _sha256(live) == r["sha256"], (
            f"post-freeze change to {r['source_path']} — re-freeze is a "
            "registered governance action, not a silent edit"
        )


def test_lock_contains_arch_and_no_duplicate_pins(rows):
    lock = (ROOT / "requirements-lock.txt").read_text().splitlines()
    pins = [line for line in lock if line and not line.startswith("#")]
    names = [line.split("==")[0] for line in pins]
    assert len(names) == len(set(names)), "duplicate package pins in lock"
    assert any(line.startswith("arch==") for line in pins)
    assert "arch==8.0.0" in pins

def test_v1_config_fingerprint_still_frozen(rows):
    row = next(r for r in rows if r["source_path"] == "configs/project.yaml")
    assert row["sha256"] == (
        "9a60208f16040c8246108f79060fa81b69f0fa5609a4a365c4c898898d6b012f"
    )
