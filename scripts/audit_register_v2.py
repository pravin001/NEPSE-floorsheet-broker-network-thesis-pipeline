"""Final v2 register audit (plan V2-6).

For every experiment row in `docs/experiment_register.md`:

* parse the `output artefact` cell into repo-relative paths (brace groups,
  bare filenames, globs and `<SYM>/<YYYY-MM>` patterns are resolved);
* require each path to exist (directories reported, not hashed);
* require the LATEST HASH-BEARING provenance-manifest row for that path to
  match the file's current SHA-256 and byte size (placeholder rows with an
  empty digest never satisfy the requirement);
* report the manifest itself as SELF_REFERENTIAL (it cannot hash its own
  post-append bytes) and the historical EXP-0000 lock as
  HISTORICAL_REFERENCE (the live lock is a v2 artifact, not the 142-pin
  initial-commit file).

Writes `outputs/tables/v2_register_audit.csv` and prints a summary.  Exit code
1 if any artefact is missing, unmanifested, or hash-mismatched.
"""
from __future__ import annotations

import csv
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs" / "experiment_register.md"
MANIFEST = ROOT / "data" / "metadata" / "provenance_manifest.csv"
OUT = ROOT / "outputs" / "tables" / "v2_register_audit.csv"

MANIFEST_REL = "data/metadata/provenance_manifest.csv"
HISTORICAL = {("EXP-0000", "requirements-lock.txt")}

ART_EXT = {".csv", ".json", ".parquet", ".duckdb", ".ipynb", ".py", ".md",
           ".log", ".png", ".txt", ".yaml", ".yml", ".cff"}
PREFIXES = ("outputs/", "data/", "reports/", "docs/", "scripts/", "src/",
            "tests/", "configs/", "notebooks/")
SEARCH_DIRS = ("", "outputs/tables", "outputs/figures", "outputs/logs",
               "data/metadata", "data/processed", "reports",
               "reports/chapter_assets", "scripts", "tests", "configs",
               "notebooks")
SKIP_TOKENS = {"git", "initial", "commit", "commit;", "tag", "duckdb",
               "floorsheet_dedup", "and", "plus"}

BRACE_RE = re.compile(r"\{([^{}]+)\}")
PAREN_RE = re.compile(r"\([^)]*\)")
SEP_RE = re.compile(r"\s*[·+]\s*")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def register_rows() -> list[dict[str, str]]:
    rows = []
    header = None
    for line in REGISTER.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        if cells and cells[0] == "id":
            header = cells
            continue
        if header and cells and cells[0].startswith("EXP-"):
            if len(cells) != len(header):
                raise SystemExit(
                    f"row {cells[0]} has {len(cells)} cells, expected {len(header)}")
            rows.append(dict(zip(header, cells)))
    return rows


def latest_manifest() -> dict[str, dict[str, str]]:
    """Latest HASH-BEARING row per artifact.

    The manifest is append-only chronological, but some early rows are
    placeholders with an empty sha256 / zero bytes.  A placeholder must not
    shadow a real hash row (and vice versa), so only rows carrying a digest
    and a positive byte count are eligible.
    """
    latest = {}
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            digest = (row.get("sha256") or "").strip()
            try:
                size = int(float(row.get("bytes") or 0))
            except ValueError:
                size = 0
            if not digest or size <= 0:
                continue
            latest[row["artifact"]] = row  # append-only: last wins
    return latest


def expand_braces(text: str) -> list[str]:
    match = BRACE_RE.search(text)
    if not match:
        return [text]
    expanded = []
    for alt in match.group(1).split(","):
        expanded.extend(expand_braces(
            text[:match.start()] + alt.strip() + text[match.end():]))
    return expanded


def _looks_like_path(token: str) -> bool:
    token = token.strip("`'\"")
    if not token or token in SKIP_TOKENS:
        return False
    if token.startswith("§"):
        return False
    return token.startswith(PREFIXES) or Path(token).suffix in ART_EXT


def _resolve_one(token: str, previous: Path | None) -> list[Path]:
    token = token.strip("`'\"")
    if token.startswith("./"):
        token = token[2:]
    if token.startswith("_"):
        if previous is None:
            return []
        token = previous.stem + token
    token = (token.replace("<SYM>", "*").replace("<YYYY-MM>", "*")
                  .replace("<", "*").replace(">", "*"))
    if token.startswith("/"):
        candidates = [Path(token)]
    elif token.startswith(PREFIXES):
        candidates = [ROOT / token]
    elif Path(token).suffix in ART_EXT:
        candidates = [(ROOT / d / token) if d else (ROOT / token)
                      for d in SEARCH_DIRS]
    else:
        return []

    for candidate in candidates:
        rel = str(candidate.relative_to(ROOT)) if candidate.is_relative_to(ROOT) else str(candidate)
        if any(ch in rel for ch in "*?["):
            matches = sorted(ROOT.glob(rel))
            if matches:
                return matches
        elif candidate.exists():
            return [candidate]
    # nothing exists: report the most plausible intended path
    return [candidates[0]]


def artifact_paths(row: dict[str, str]) -> list[Path]:
    """Resolve one register row's artefact cell into concrete paths."""
    cell = PAREN_RE.sub("", row.get("output artefact", ""))
    tokens: list[str] = []
    for chunk in SEP_RE.split(cell):
        for piece in expand_braces(chunk):
            for token in piece.split():
                if _looks_like_path(token):
                    tokens.append(token)

    paths: list[Path] = []
    seen: set[str] = set()
    previous: Path | None = None
    for token in tokens:
        for path in _resolve_one(token, previous):
            key = str(path)
            if key not in seen:
                seen.add(key)
                paths.append(path)
            previous = path
    return paths


def main() -> None:
    rows = register_rows()
    manifest = latest_manifest()
    audit = []
    problems = 0

    for row in rows:
        eid = row["id"]
        paths = artifact_paths(row)
        if not paths:
            audit.append({"experiment_id": eid, "artifact": "",
                          "status": "NO_ARTIFACT_PATH",
                          "detail": row.get("output artefact", "")[:120]})
            problems += 1
            continue
        for path in paths:
            if path.is_relative_to(ROOT):
                rel = str(path.relative_to(ROOT))
            else:
                rel = str(path)
            if not path.exists():
                audit.append({"experiment_id": eid, "artifact": rel,
                              "status": "MISSING", "detail": "path absent"})
                problems += 1
                continue
            if path.is_dir():
                audit.append({"experiment_id": eid, "artifact": rel,
                              "status": "DIRECTORY", "detail": "exists"})
                continue
            if rel == MANIFEST_REL:
                audit.append({"experiment_id": eid, "artifact": rel,
                              "status": "SELF_REFERENTIAL",
                              "detail": "manifest cannot record its own post-append hash"})
                continue
            if (eid, rel) in HISTORICAL:
                audit.append({"experiment_id": eid, "artifact": rel,
                              "status": "HISTORICAL_REFERENCE",
                              "detail": "initial-commit artifact; live replacement audited elsewhere"})
                continue
            row_m = manifest.get(rel)
            if row_m is None:
                audit.append({"experiment_id": eid, "artifact": rel,
                              "status": "NO_MANIFEST_HASH", "detail": "exists"})
                problems += 1
                continue
            digest = sha256(path)
            size = path.stat().st_size
            try:
                recorded_size = int(float(row_m["bytes"]))
            except ValueError:
                recorded_size = -1
            if digest != row_m["sha256"] or size != recorded_size:
                audit.append({"experiment_id": eid, "artifact": rel,
                              "status": "HASH_MISMATCH",
                              "detail": f"live {digest[:12]}/{size} vs "
                                        f"manifest {row_m['sha256'][:12]}/"
                                        f"{row_m['bytes']}"})
                problems += 1
            else:
                audit.append({"experiment_id": eid, "artifact": rel,
                              "status": "OK", "detail": "hash-aligned"})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "experiment_id", "artifact", "status", "detail"],
            lineterminator="\n")
        writer.writeheader()
        writer.writerows(audit)

    counts: dict[str, int] = {}
    for r in audit:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"register rows: {len(rows)}")
    print(f"artefact checks: {len(audit)}; by status: {counts}")
    print(f"audit written: {OUT.relative_to(ROOT)}")
    if problems:
        for r in audit:
            if r["status"] not in {"OK", "DIRECTORY", "SELF_REFERENTIAL",
                                   "HISTORICAL_REFERENCE"}:
                print(f"  {r['status']:18s} {r['experiment_id']:10s} "
                      f"{r['artifact']} — {r['detail']}")
        sys.exit(1)
    print("ALL REGISTER ARTEFACTS EXIST AND ARE HASH-ALIGNED")


if __name__ == "__main__":
    main()
