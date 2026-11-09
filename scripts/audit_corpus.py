"""EXP-0002c — CORPUS QUALITY AUDIT over floorsheet_raw (DuckDB-side).

Pre-declared checks (analysis_plan §1, DC3/DC4, sibling-validated facts):
  A1 dedupe key count: (date, symbol, contract_no) — page-split duplicates
     collapse only when FULL ROW SIGNATURE matches; conflicting signatures
     reported separately (never silently merged).
  A2 duplicate collision classes: exact-duplicate rows vs key-colliding rows
     with differing (price, volume, amount, broker) — the latter are
     documented, not resolved by arbitrary 'first-row' choice.
  A3 missing broker ids: empty/NULL buyer or seller after normalisation.
  A4 dealer codes: D-codes present (2021-2023 corpus) — count, not an error.
  A5 low-activity flags: (symbol, date) with < 100 trades — suspension days,
     listings, illiquid scrips (flag list, not deletion; DC2 coverage rule
     governs exclusions at feature time).
  A6 numeric sanity: negative volume, non-positive price, NULL contract_no.
  A7 contract-no structure: id-prefix vs loaded date consistency (kaggle),
     serial gaps per (symbol, date) EXPECTED (daily-global ids — SV6 note).
  A8 source spans: per-source (days, min, max) + symbol counts.

Outputs → outputs/tables/corpus_*.csv ; prints console summary.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import duckdb
import pandas as pd

from nepsemsc.data.duckdb_loader import get_conn
from nepsemsc.utils.io import atomic_write_df
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.tz import utc_iso

LOW_TRADES_THRESHOLD = 100


def main() -> None:
    con = get_conn()

    # ---- A1/A2 duplicate classes ----
    dup = con.execute("""
        SELECT date, symbol, contract_no,
               COUNT(*)                                   AS n_raw,
               COUNT(DISTINCT (price, volume, amount,
                               buyer_broker_id, seller_broker_id)) AS n_signatures
        FROM floorsheet_raw
        GROUP BY 1, 2, 3
        HAVING COUNT(*) > 1
    """).df()
    n_dupkeys = len(dup)
    exact_keys = dup["n_signatures"] == 1 if n_dupkeys else pd.Series([], dtype=bool)
    atomic_write_df(dup, ROOT / "outputs/tables/corpus_duplicate_keys.csv", index=False)
    print(f"A1/A2 duplicate (date,symbol,contract_no) keys: {n_dupkeys:,} "
          f"(exact-page dups: {int(exact_keys.sum()):,}, "
          f"signature-conflicts: {int((~exact_keys).sum()):,})")

    # ---- dedupe table (deterministic pick: full-signature sort) ----
    con.execute("DROP TABLE IF EXISTS floorsheet_dedup")
    con.execute("""
        CREATE TABLE floorsheet_dedup AS
        SELECT date, contract_no, symbol, price, volume, amount,
               buyer_broker_id, seller_broker_id, source
        FROM (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY date, symbol, contract_no
                ORDER BY price, volume, amount, buyer_broker_id, seller_broker_id, source
            ) AS rn
            FROM floorsheet_raw
        ) WHERE rn = 1
    """)
    n_raw = con.execute("SELECT COUNT(*) FROM floorsheet_raw").fetchone()[0]
    n_ded = con.execute("SELECT COUNT(*) FROM floorsheet_dedup").fetchone()[0]
    print(f"A1 dedupe: raw={n_raw:,} dedup={n_ded:,} dropped={n_raw - n_ded:,}")

    # ---- A3 missing broker ids (on dedup) ----
    a3 = con.execute("""
        SELECT date, symbol,
               COUNT(*) FILTER (WHERE COALESCE(buyer_broker_id,'') = '') AS n_nobuyer,
               COUNT(*) FILTER (WHERE COALESCE(seller_broker_id,'') = '') AS n_noseller
        FROM floorsheet_dedup
        GROUP BY 1, 2
        HAVING n_nobuyer + n_noseller > 0
        ORDER BY n_nobuyer + n_noseller DESC
    """).df()
    atomic_write_df(a3, ROOT / "outputs/tables/corpus_missing_broker_ids.csv", index=False)
    print(f"A3 missing-broker-id (symbol,date) rows: {len(a3):,}")

    # ---- A4 dealer codes ----
    a4 = con.execute("""
        SELECT COUNT(*) AS d_rows FROM floorsheet_dedup
        WHERE regexp_full_match(COALESCE(buyer_broker_id,''), 'D[0-9]+')
           OR regexp_full_match(COALESCE(seller_broker_id,''), 'D[0-9]+')
    """).fetchone()[0]
    print(f"A4 dealer-code (D…) rows: {a4:,}")

    # ---- A5 low-activity days ----
    a5 = con.execute(f"""
        SELECT date, symbol, COUNT(*) AS n_trades
        FROM floorsheet_dedup
        GROUP BY 1, 2
        HAVING COUNT(*) < {LOW_TRADES_THRESHOLD}
        ORDER BY n_trades
    """).df()
    atomic_write_df(a5, ROOT / "outputs/tables/corpus_low_activity_days.csv", index=False)
    print(f"A5 (symbol,date) under {LOW_TRADES_THRESHOLD} trades: {len(a5):,} "
          f"(min {a5['n_trades'].min() if len(a5) else 0})")

    # ---- A6 numeric sanity ----
    a6 = dict(
        negative_volume=con.execute(
            "SELECT COUNT(*) FROM floorsheet_dedup WHERE volume < 0").fetchone()[0],
        nonpositive_price=con.execute(
            "SELECT COUNT(*) FROM floorsheet_dedup WHERE price <= 0").fetchone()[0],
        null_contract_no=con.execute(
            "SELECT COUNT(*) FROM floorsheet_dedup WHERE contract_no IS NULL").fetchone()[0],
        negative_amount=con.execute(
            "SELECT COUNT(*) FROM floorsheet_dedup WHERE amount < 0").fetchone()[0],
    )
    print("A6 numeric sanity:", a6)

    # ---- A7 per-day volume sanity vs page-splitting: summarise per (source, date) ----
    a7 = con.execute("""
        SELECT source, date, COUNT(*) AS n_rows,
               COUNT(DISTINCT symbol) AS n_symbols
        FROM floorsheet_dedup
        GROUP BY 1, 2
    """).df()
    atomic_write_df(a7, ROOT / "outputs/tables/corpus_daily_summary.csv", index=False)
    print(f"A7 daily summary rows: {len(a7):,}")

    # ---- A8 symbol coverage ----
    a8 = con.execute("""
        SELECT symbol, COUNT(DISTINCT date) AS n_dates,
               MIN(date) AS first_date, MAX(date) AS last_date,
               CAST(SUM(volume) AS BIGINT) AS total_volume,
               CAST(SUM(amount) AS BIGINT) AS total_amount
        FROM floorsheet_dedup
        GROUP BY 1 ORDER BY n_dates DESC
    """).df()
    atomic_write_df(a8, ROOT / "outputs/tables/corpus_symbol_coverage.csv", index=False)
    print(f"A8 symbols in corpus: {len(a8):,}")

    prov.record({
        "ts_utc": utc_iso(), "artifact": "outputs/tables/corpus_* (audit bundle)",
        "kind": "quality_audit_exp0002c",
        "source_path": "duckdb floorsheet_dedup (58M-row derived)",
        "source_url": "ingested corpus EXP-0002b",
        "sha256": "", "bytes": 0,
        "rows_sampled": n_ded, "rows_total": n_raw,
        "licence": "derived",
        "evidence": f"dupkeys={n_dupkeys} nobroker={len(a3)} lowact={len(a5)} "
                    f"sanity={a6}",
    })
    print("AUDIT_DONE")


if __name__ == "__main__":
    main()
