"""Provenance manifest (R4/R9, brief: DATA STRATEGY — PROVENANCE).

Every acquired/derivated artefact appends a row with timestamp, source,
sha256, sizes, licence evidence. Manifest is a TRACKED csv so git history
certifies the audit trail (sibling-project convention D2/D12).
"""
from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from nepsemsc.utils.io import atomic_write_bytes, sha256_file, ensure_dir
from nepsemsc.utils.paths import data_dir
from nepsemsc.utils.tz import utc_iso

MANIFEST = data_dir("metadata") / "provenance_manifest.csv"

COLUMNS = ["ts_utc", "artifact", "kind", "source_path", "source_url", "sha256",
           "bytes", "rows_sampled", "rows_total", "licence", "evidence"]


def record(row: dict) -> None:
    for c in COLUMNS:
        row.setdefault(c, "")
    existing = []
    if MANIFEST.exists():
        with open(MANIFEST, newline="") as f:
            existing = list(csv.DictReader(f))
    existing.append({**{c: str(row.get(c, "")) for c in COLUMNS}})
    data = ",".join(COLUMNS) + "\n" + "\n".join(
        _quote_row(r) for r in existing) + "\n"
    atomic_write_bytes(MANIFEST, data.encode("utf-8"))


def _quote_row(row: dict) -> str:
    import io
    import csv as _csv
    buf = io.StringIO()
    w = _csv.writer(buf, quoting=_csv.QUOTE_MINIMAL)
    w.writerow([row[c] for c in COLUMNS])
    return buf.getvalue().rstrip("\n")


def read_manifest() -> pd.DataFrame:
    if not MANIFEST.exists():
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(MANIFEST)


__all__ = ["record", "read_manifest", "sha256_file", "MANIFEST", "utc_iso",
           "atomic_write_csv", "atomic_write_json"]


def atomic_write_json(path: str | Path, obj, indent: int = 2) -> Path:
    from nepsemsc.utils.io import atomic_write_json as _awj
    return _awj(path, obj, indent=indent)


def atomic_write_csv(path: str | Path, df: pd.DataFrame, index: bool = False) -> Path:
    ensure_dir(Path(path).parent)
    tmp = Path(str(path) + ".tmp")
    df.to_csv(tmp, index=index)
    out = Path(path)
    import os
    os.replace(tmp, out)
    return out
