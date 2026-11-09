"""Init data/duckdb/nepse.duckdb, then load the NABIL 2024-12 sample extract,
then run the brief's specified check query (Phase 1 step 6)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nepsemsc.data.duckdb_loader import (DAILY_COUNTS_SQL, DB_PATH, get_conn,
                                         init_db, load_extracted_extract)


def main() -> None:
    extract = ROOT / "data" / "raw" / "floorsheet" / "NABIL" / "2024-12.csv"
    if not extract.exists():
        raise SystemExit("BLOCKED: run scripts/extract_sample_month.py first")
    # idempotent Phase 1: cold-start the DB file fresh
    import duckdb
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = get_conn()
    init_db(con)
    n = load_extracted_extract(con, extract)
    total = con.execute("SELECT COUNT(*) FROM floorsheet_raw").fetchone()[0]
    print(f"DuckDB ready at {DB_PATH}")
    print(f"run 1: {n:,} rows reported by count_rows (probe)")
    print(f"floorsheet_raw total rows: {total:,}  <- rounds to run-1 count")
    rows = con.execute(DAILY_COUNTS_SQL).fetchall()
    cols = [d[0] for d in con.description]
    print(f"\n{DAILY_COUNTS_SQL.strip().splitlines()[0][:50]}... query result:")
    print(" | ".join(cols))
    for r in rows:
        print(" | ".join(str(x) for x in r))
    con.close()


if __name__ == "__main__":
    main()
