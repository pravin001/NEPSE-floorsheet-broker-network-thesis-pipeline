"""Integrity guard for the v2.0.1 chapter -> artefact crosswalk.

These tests fail the build, not the thesis, when a chapter asset path, hash,
manifest row, EXP key, or claim version drifts.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_chapter_map as chapter_audit  # noqa: E402
import audit_register_v2 as regaudit  # noqa: E402

ASSETS = ROOT / "reports" / "chapter_assets"
EXP_RE = re.compile(r"^EXP-\d{4}[a-z]?$")
PLACEHOLDERS = {
    "main_regression.csv", "placebo_distribution.csv", "regime_split.csv",
    "event_study_car.csv", "robustness_matrix.csv", "broker_persistence.csv",
}


def _rows():
    return chapter_audit.parse_map()


def _pack_manifests():
    return sorted(ASSETS.glob("ch[1-4]_asset_manifest.csv"))


def _exp_ids():
    return {row["id"] for row in regaudit.register_rows()}


def test_crosswalk_has_required_shape_and_unique_claims():
    rows = _rows()
    assert len(rows) >= 60
    assert {r["claim_version"] for r in rows} == {"v1", "v2"}
    assert {r["status"] for r in rows} <= chapter_audit.ALLOWED_STATUS
    chapters = {r["chapter"].split()[0] for r in rows}
    assert chapters == {"Ch.1", "Ch.2", "Ch.3", "Ch.4", "Ch.5", "Ch.6"}
    ids = [r["claim_id"] for r in rows]
    assert len(ids) == len(set(ids))


def test_claim_versions_keep_v1_immutable_claims_distinct_from_v2():
    rows = _rows()
    v1 = [r for r in rows if r["claim_version"] == "v1"]
    v2 = [r for r in rows if r["claim_version"] == "v2"]
    assert v1 and v2
    assert all(r["status"] == "VERIFIED_V1_IMMUTABLE" for r in v1)
    assert any(r["claim_id"] == "CH5-5.2-H7-V1-P0274" for r in v1)
    assert any(r["claim_id"] == "CH5-5.7-FINAL" and r["claim_version"] == "v2"
               for r in v2)


def test_crosswalk_paths_are_concrete_and_deposit_safe():
    for row in _rows():
        path = row["artifact_path"]
        assert not path.startswith("/")
        assert ".." not in Path(path).parts
        assert not set("*?[").intersection(path)
        assert not path.startswith(chapter_audit.FORBIDDEN_PREFIXES)


def test_crosswalk_has_no_stage5_placeholder_artifacts():
    names = {Path(r["artifact_path"]).name for r in _rows()}
    assert not (names & PLACEHOLDERS)


def test_crosswalk_artifacts_match_crosswalk_and_manifest():
    results = chapter_audit.build_results()
    failures = [r for r in results if r["outcome"] != "OK"]
    assert not failures, failures
    assert all(r["file_exists"] == "true" for r in results)
    assert all(r["crosswalk_hash_match"] == "true" for r in results)
    assert all(r["manifest_hash_match"] == "true" for r in results)
    assert all(r["exp_ids_valid"] == "true" for r in results)


def test_pack_manifests_are_complete_and_hash_aligned():
    manifests = _pack_manifests()
    assert [p.name for p in manifests] == [
        "ch1_asset_manifest.csv", "ch2_asset_manifest.csv",
        "ch3_asset_manifest.csv", "ch4_asset_manifest.csv"]
    exp_ids = _exp_ids()
    latest = regaudit.latest_manifest()
    for manifest in manifests:
        with open(manifest, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) >= 4, manifest
        for row in rows:
            path = ROOT / row["artifact_path"]
            assert path.is_file(), (manifest.name, row["artifact_path"])
            digest = regaudit.sha256(path)
            assert digest == row["sha256"], (manifest.name, row["artifact_path"])
            manifest_row = latest.get(row["artifact_path"])
            assert manifest_row is not None, row["artifact_path"]
            assert manifest_row["sha256"] == digest
            assert int(float(manifest_row["bytes"])) == path.stat().st_size
            for exp in re.split(r"[,\s]+", row["exp_id"]):
                if exp:
                    assert EXP_RE.match(exp) and exp in exp_ids, exp
            assert row["claim_version"] in {"v1", "v2"}


def test_audit_csv_matches_a_fresh_build():
    audit_csv = ROOT / "outputs" / "tables" / "v2_chapter_map_audit.csv"
    assert audit_csv.is_file()
    with open(audit_csv, newline="", encoding="utf-8") as f:
        stored = list(csv.DictReader(f))
    assert stored == chapter_audit.build_results()
