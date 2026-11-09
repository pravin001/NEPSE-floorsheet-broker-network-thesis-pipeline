"""EXP-0001a — Phase 1 sample data: NABIL for 2024-12 from the LOCAL
socrateai floorsheet archive (MIT, verified).

Writes data/raw/floorsheet/NABIL/2024-12.csv in the canonical schema and
records provenance rows for every source file (sha256) to
data/metadata/provenance_manifest.csv.

NOTE (SV1 substitution, documented): the brief's primary sources (viking303
archive, nepalstock.com-direct) are BLOCKED/NOT-FOUND (sibling-project D9
evidence 2026-11-08 + HTTP 000 re-verified today). The socrateai archive IS
the "pre-scraped historical archive" of the SV1(b) chain and is already local.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nepsemsc.data.schema import normalize_columns
from nepsemsc.utils import config as cfgmod
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.tz import utc_iso

KRONOS_TIER3 = Path("/home/whacko/research/nepse-kronos-thesis/data/raw/tier3_floorsheets_socrateai")
SYMBOL = "NABIL"
MONTH = "2024-12"


def main() -> None:
    cfg = cfgmod.load_config()
    assert cfg["scope"]["stocks_smoke"] == [SYMBOL], f"config smoke stock changed: {cfg['scope']['stocks_smoke']}"
    src_files = sorted(KRONOS_TIER3.glob(f"floorsheet_{MONTH}-*.csv"))
    if not src_files:
        raise SystemExit(f"BLOCKED: no archive files for {MONTH} under {KRONOS_TIER3}")
    frames = []
    for p in src_files:
        sha = prov.sha256_file(p)
        df = pd.read_csv(p, dtype={"transaction": "int64", "symbol": "string",
                                   "buyer": "Int64", "seller": "Int64",
                                   "quantity": "float64", "rate": "float64",
                                   "amount": "float64", "date": "string"})
        sub = df[df["symbol"] == SYMBOL].copy()
        prov.record({
            "ts_utc": utc_iso(), "artifact": str(Path("data/raw/floorsheet") / SYMBOL / f"{MONTH}.csv"),
            "kind": "tier3_source_slice", "source_path": str(p),
            "source_url": ("github.com/socrateai-official/nepse-open-data "
                           "(archive file, MIT; local copy sha256-verified)"),
            "sha256": sha, "bytes": p.stat().st_size,
            "rows_sampled": len(sub), "rows_total": len(df),
            "licence": "MIT", "evidence": "LICENSE fetched+verified 2026-11-08",
        })
        if not sub.empty:
            sub["date"] = p.stem.split("_")[1]  # re-assert from the archive filename
            frames.append(sub)
    assert frames, f"BLOCKED: {SYMBOL} has zero rows in {MONTH}"
    raw = pd.concat(frames, ignore_index=True)
    canonical = normalize_columns(raw)
    from nepsemsc.data.schema import validate_schema
    schemas_ok, problems = validate_schema(canonical)
    out_dir = ROOT / "data" / "raw" / "floorsheet" / SYMBOL
    out = out_dir / f"{MONTH}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    prov.atomic_write_csv(out, canonical)
    print(f"SCHEMA_VALIDATION: {'PASS' if schemas_ok else 'FAIL'} {problems}")
    print(f"EXTRACT_OK rows={len(canonical)} files={len(src_files)} out={out}")
    missing_ids = int((canonical["buyer_broker_id"].eq("")).sum() + (canonical["seller_broker_id"].eq("")).sum())
    print(f"missing broker ids: {missing_ids} of {len(canonical)} rows")


if __name__ == "__main__":
    main()
