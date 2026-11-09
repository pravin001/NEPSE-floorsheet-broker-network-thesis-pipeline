"""Compute daily buyer/seller HHI + self-loop ratio for the NABIL sample month
in DuckDB (Phase 1 step 7) → outputs/tables/sample_hhi_selfloop.csv."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nepsemsc.data.aggregations import DAILY_CONCENTRATION_SQL
from nepsemsc.data.duckdb_loader import get_conn, init_db
from nepsemsc.utils.provenance import atomic_write_csv


def main() -> None:
    db = ROOT / "data" / "duckdb" / "nepse.duckdb"
    if not db.exists():
        raise SystemExit("BLOCKED: run scripts/init_duckdb_load_sample.py first")
    con = get_conn(db)
    init_db(con)
    df = con.execute(DAILY_CONCENTRATION_SQL).df()
    out = ROOT / "outputs" / "tables" / "sample_hhi_selfloop.csv"
    atomic_write_csv(out, df)
    print(f"rows: {len(df)}  cols: {list(df.columns)}")
    print(df.head(15).to_string(index=False))
    print("\nsummary (sample month):")
    cols = ["buyer_hhi", "seller_hhi", "self_loop_volume_ratio", "end_of_day_concentration",
            "top_3_buyer_share", "top_3_seller_share"]
    print(df[cols].describe().loc[["mean", "std", "min", "max"]])
    con.close()


if __name__ == "__main__":
    main()
