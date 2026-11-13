"""Audit the verified chapter -> artefact crosswalk (v2.0.1 handoff).

Checks, for every row of `docs/chapter_artifact_map.md`:

* required columns and allowed `claim_version` / `status` values;
* unique `claim_id`;
* the artifact path exists, is a file, is repo-relative, and is deposit-safe
  (no raw data, DuckDB, processed parquet, logs, or licence-restricted figures);
* the SHA-256 in the crosswalk matches the live file;
* the latest hash-bearing provenance-manifest row exists and matches the live
  SHA-256 and byte size;
* every comma-separated EXP id exists in `docs/experiment_register.md`.

Writes `outputs/tables/v2_chapter_map_audit.csv`.  Exit code 1 on any failure.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "docs" / "chapter_artifact_map.md"
OUT = ROOT / "outputs" / "tables" / "v2_chapter_map_audit.csv"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_register_v2 as regaudit  # noqa: E402

COLUMNS = ["chapter", "section", "claim_id", "artifact_path", "exp_id",
           "sha256", "claim_version", "status"]
AUDIT_COLUMNS = ["claim_id", "chapter", "section", "artifact_path", "exp_id",
                 "claim_version", "status", "file_exists",
                 "crosswalk_hash_match", "manifest_hash_match",
                 "exp_ids_valid", "outcome", "detail"]
ALLOWED_VERSIONS = {"v1", "v2"}
ALLOWED_STATUS = {"VERIFIED", "VERIFIED_V1_IMMUTABLE", "SCAFFOLD"}
FORBIDDEN_PREFIXES = ("data/raw/", "data/duckdb/", "data/processed/",
                      "outputs/logs/", "outputs/figures/")
EXP_RE = re.compile(r"^EXP-\d{4}[a-z]?$")
GLOB_CHARS = set("*?[")


def _clean(cell: str) -> str:
    return cell.strip().strip("`").strip()


def parse_map() -> list[dict[str, str]]:
    lines = MAP.read_text(encoding="utf-8").splitlines()
    header = None
    rows: list[dict[str, str]] = []
    for line in lines:
        if not line.startswith("|"):
            continue
        if set(line.strip()) <= set("|-: "):
            continue
        cells = [_clean(c) for c in line.strip().strip("|").split(" | ")]
        if cells == COLUMNS:
            header = cells
            continue
        if header is None or not cells or cells[0] in {"---", ""}:
            continue
        if len(cells) != len(COLUMNS):
            raise SystemExit(
                f"crosswalk row has {len(cells)} cells, expected {len(COLUMNS)}: "
                f"{line[:120]}")
        rows.append(dict(zip(COLUMNS, cells)))
    if header is None:
        raise SystemExit("crosswalk header not found")
    return rows


def register_exp_ids() -> set[str]:
    return {row["id"] for row in regaudit.register_rows()}


def _manifest_for(path: str) -> dict[str, str] | None:
    return regaudit.latest_manifest().get(path)


def audit_row(row: dict[str, str], exp_ids: set[str]) -> dict[str, str]:
    artifact = row["artifact_path"]
    path = ROOT / artifact
    problems: list[str] = []

    file_exists = path.is_file()
    if not file_exists:
        problems.append("file absent")
    if artifact.startswith("/") or ".." in Path(artifact).parts:
        problems.append("not repo-relative")
    if artifact.startswith(FORBIDDEN_PREFIXES):
        problems.append("deposit-excluded path")
    if any(ch in artifact for ch in GLOB_CHARS):
        problems.append("glob is not a concrete path")

    live_sha = regaudit.sha256(path) if file_exists else ""
    crosswalk_ok = bool(file_exists and live_sha == row["sha256"])
    if file_exists and not crosswalk_ok:
        problems.append(
            f"crosswalk hash {row['sha256'][:12]} != live {live_sha[:12]}")

    manifest_row = _manifest_for(artifact) if file_exists else None
    manifest_ok = False
    if manifest_row is None:
        problems.append("no hash-bearing manifest row")
    else:
        try:
            recorded_size = int(float(manifest_row["bytes"]))
        except (TypeError, ValueError):
            recorded_size = -1
        live_size = path.stat().st_size if file_exists else -1
        manifest_ok = (manifest_row.get("sha256") == live_sha
                       and recorded_size == live_size)
        if not manifest_ok:
            problems.append(
                f"manifest {str(manifest_row.get('sha256'))[:12]}/"
                f"{manifest_row.get('bytes')} != live {live_sha[:12]}/{live_size}")

    row_exps = [e.strip() for e in re.split(r"[,\s]+", row["exp_id"]) if e.strip()]
    invalid_exps = [e for e in row_exps if not EXP_RE.match(e) or e not in exp_ids]
    exp_ok = bool(row_exps) and not invalid_exps
    if not row_exps:
        problems.append("no EXP id")
    if invalid_exps:
        problems.append("unknown EXP: " + ",".join(invalid_exps))

    if row["claim_version"] not in ALLOWED_VERSIONS:
        problems.append(f"bad claim_version {row['claim_version']}")
    if row["status"] not in ALLOWED_STATUS:
        problems.append(f"bad status {row['status']}")
    if row["status"] == "VERIFIED_V1_IMMUTABLE" and row["claim_version"] != "v1":
        problems.append("VERIFIED_V1_IMMUTABLE requires v1")
    if row["status"] == "SCAFFOLD" and row["claim_version"] != "v2":
        problems.append("SCAFFOLD requires v2")

    return {
        "claim_id": row["claim_id"],
        "chapter": row["chapter"],
        "section": row["section"],
        "artifact_path": artifact,
        "exp_id": row["exp_id"],
        "claim_version": row["claim_version"],
        "status": row["status"],
        "file_exists": str(file_exists).lower(),
        "crosswalk_hash_match": str(crosswalk_ok).lower(),
        "manifest_hash_match": str(manifest_ok).lower(),
        "exp_ids_valid": str(exp_ok).lower(),
        "outcome": "OK" if not problems else "FAIL",
        "detail": "hash-aligned" if not problems else "; ".join(problems),
    }


def build_results() -> list[dict[str, str]]:
    rows = parse_map()
    exp_ids = register_exp_ids()
    seen: set[str] = set()
    results: list[dict[str, str]] = []
    for row in rows:
        if row["claim_id"] in seen:
            result = audit_row(row, exp_ids)
            result["outcome"] = "FAIL"
            result["detail"] = "duplicate claim_id; " + result["detail"]
            results.append(result)
        else:
            seen.add(row["claim_id"])
            results.append(audit_row(row, exp_ids))
    return results


def write_results(results: list[dict[str, str]]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_COLUMNS,
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)


def main() -> None:
    results = build_results()
    write_results(results)
    failures = [r for r in results if r["outcome"] != "OK"]
    chapters = sorted({r["chapter"].split()[0] for r in results})
    artifacts = {r["artifact_path"] for r in results}
    versions = {r["claim_version"] for r in results}
    print(f"crosswalk rows: {len(results)}")
    print(f"chapters: {len(chapters)} ({', '.join(chapters)})")
    print(f"distinct artefacts: {len(artifacts)}")
    print(f"claim versions: {sorted(versions)}")
    print(f"outcomes: OK={len(results) - len(failures)} FAIL={len(failures)}")
    print(f"audit written: {OUT.relative_to(ROOT)}")
    if failures:
        for r in failures:
            print(f"  FAIL {r['claim_id']:24s} {r['artifact_path']} — {r['detail']}")
        sys.exit(1)
    print("ALL CROSSWALK ARTEFACTS EXIST AND ARE HASH-ALIGNED")


if __name__ == "__main__":
    main()
