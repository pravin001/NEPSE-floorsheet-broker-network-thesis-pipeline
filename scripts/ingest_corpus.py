"""EXP-0002b — FULL-CORPUS floorsheet ingestion into DuckDB (window 2021-2024).

Declared BEFORE ingestion (DC1, results in outputs/tables/universe_selected_top10.csv
registered EXP-0002a BEFORE this script is run):

Source assignment per session (declared in AGENTS.md data map + deviations log):
  * 2021-01-01 → 2023-12-31 : kaggle viking303 CC0 floorsheets
      (~/root cache under kagglehub; validated counts vs OHLCV calendar at
       ingestion; 2022 = 242/242 exact)
  * 2024-01-01 → 2024-12-31 : socrateai archive (232/232 sessions, MIT)
      — kaggle-2024 (229 days) retained as CROSS-CHECK source only
  * one documented relabel: kaggle file 2021_03_07_floorsheet.csv is ingested
    AS 2021-03-08. Evidence (REAL, recorded in docs/analysis_deviations.md):
      (a) 2021-03-07 absent from BOTH OHLCV sources; 2021-03-08 present
      (b) CGH trade-rate range in the file [635, 665] == tier1 CGH
          2021-03-08 OHLC [open 635, low 635, high 665, close 665]
      (c) CGH quantity sum in the file = 910 == tier1 CGH 2021-03-08
          volume 910 (ratio 1.000)
Known kaggle gaps (no source, documented): 2021-09-01, 2023-11-27.

This script: sha256-catalogue corpus → fresh DuckDB init → bulk load →
calendar coverage check → top-12 per-stock-month extracts → manifest rows.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import duckdb
import pandas as pd

from nepsemsc.data.duckdb_loader import (
    DB_PATH, get_conn, init_db, load_kaggle_year_dir, load_socrateai_day_glob,
    count_rows,
)
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.io import atomic_write_df
from nepsemsc.utils.tz import utc_iso

KAGGLE_ROOT = Path(
    "/home/whacko/.cache/kagglehub/datasets/viking303/nepse-historical-floorsheet/versions/14/NEPSE_data")
SOCR_DIR = Path("/home/whacko/research/nepse-kronos-thesis"
                "/data/raw/tier3_floorsheets_socrateai")
RELABEL = {"2021-03-07": "2021-03-08"}   # evidence triple in docstring
KAGGLE_LICENCE = "CC0 Public Domain (Kaggle viking303/nepse-historical-floorsheet v14)"
SOCR_LICENCE = "MIT (socrateai-official/nepse-open-data)"
KAGGLE_CITE = "Kaggle viking303/nepse-historical-floorsheet (merolagani-sourced); CC0"
SOCR_CITE = "github socrateai-official/nepse-open-data; MIT"


def sha256_all(paths: list[Path], rows: list[dict], source: str) -> None:
    for p in paths:
        rows.append({"source": source, "path": str(p), "sha256": prov.sha256_file(p),
                     "bytes": p.stat().st_size})


def main() -> None:
    import os
    skip_load = os.environ.get("NEPSEMS_SKIP_LOAD") == "1"
    t0 = time.time()

    # ---------- 1. corpus catalogue (sha256) ----------
    catalog: list[dict] = []
    kg_years = {}
    for yr in ("2021", "2022", "2023", "2024"):
        files = sorted((KAGGLE_ROOT / yr).glob("*_floorsheet.csv"))
        kg_years[yr] = files
        if not skip_load:
            sha256_all(files, catalog, "kaggle_viking303")
    socr_2024 = sorted(SOCR_DIR.glob("floorsheet_2024-*.csv"))
    if not skip_load:
        sha256_all(socr_2024, catalog, "socrateai")
        atomic_write_df(
            pd.DataFrame(catalog), ROOT / "data/metadata/corpus_files_sha256.csv", index=False)
    print(f"catalogued {len(catalog) if not skip_load else 'pre-existing'} day files "
          f"(kaggle {[len(kg_years[y]) for y in kg_years]}, socrateai-2024 {len(socr_2024)})")

    if skip_load:
        assert DB_PATH.exists(), "NEPSEMS_SKIP_LOAD=1 but no database present"
        con = get_conn()
        print("skip-load mode: reusing existing DB with",
              f"{count_rows(con):,} rows")
    else:
        if DB_PATH.exists():
            DB_PATH.unlink()
        con = get_conn()
        init_db(con)

        # ---------- 3. load ----------
        n0 = load_kaggle_year_dir(con, KAGGLE_ROOT / "2021", date_relabel=RELABEL)
        print(f"kaggle 2021 loaded → total {n0:,}")
        n1 = load_kaggle_year_dir(con, KAGGLE_ROOT / "2022")
        print(f"kaggle 2022 loaded → total {n1:,}")
        n2 = load_kaggle_year_dir(con, KAGGLE_ROOT / "2023")
        print(f"kaggle 2023 loaded → total {n2:,}")
        n3 = load_socrateai_day_glob(con, str(SOCR_DIR / "floorsheet_2024-*.csv"))
        print(f"socrateai 2024 loaded → total {n3:,}")
        assert n3 >= n2 >= n1 >= n0, "row counts must be non-decreasing"

    totals = con.execute("""
        SELECT source, COUNT(*) AS rows, COUNT(DISTINCT date) AS days,
               MIN(date) AS dmin, MAX(date) AS dmax
        FROM floorsheet_raw GROUP BY source ORDER BY source
    """).df()
    print(totals.to_string(index=False))

    # ---------- 4. calendar coverage (DC3 calendar from EXP-0002a) ----------
    cal = str(ROOT / "data/processed/nepse_calendar.parquet")
    missing = con.execute(f"""
        WITH cal AS (
            SELECT CAST(session_date AS DATE) AS date
            FROM read_parquet('{cal}')),
             ingested AS (
            SELECT DISTINCT date FROM floorsheet_raw)
        SELECT c.date
        FROM cal c
        LEFT JOIN ingested i USING (date)
        WHERE i.date IS NULL
        ORDER BY 1
    """).df()
    miss_path = ROOT / "outputs/tables/ingestion_session_gaps.csv"
    atomic_write_df(missing, miss_path, index=False)
    n_cal = con.execute(f"SELECT COUNT(*) FROM read_parquet('{cal}')").fetchone()[0]
    n_days = con.execute("SELECT COUNT(DISTINCT date) FROM floorsheet_raw").fetchone()[0]
    print(f"calendar sessions={n_cal} ingested sessions={n_days} "
          f"gaps={len(missing)} → {miss_path.name}")
    if len(missing):
        print("gap dates:", missing["date"].astype(str).tolist())

    # ---------- 5. per-stock-month extracts for top-12 ----------
    meta = json.loads((ROOT / "data/metadata/universe_selected.json").read_text())
    symbols = meta["top12_buffer"]
    ex_root = ROOT / "data/raw/floorsheet"
    n_extracts = 0
    months = con.execute("""
        SELECT DISTINCT strftime(date, '%Y-%m') AS ym FROM floorsheet_raw ORDER BY 1
    """).fetchall()
    for sym in symbols:
        (ex_root / sym).mkdir(parents=True, exist_ok=True)
        for (ym,) in months:
            out = ex_root / sym / f"{ym}.csv"
            con.execute(f"""
                COPY (
                    SELECT date, contract_no, symbol, price, volume, amount,
                           buyer_broker_id, seller_broker_id, source
                    FROM floorsheet_raw
                    WHERE symbol = '{sym}' AND strftime(date, '%Y-%m') = '{ym}'
                    ORDER BY date, contract_no
                ) TO '{out}' (HEADER, DELIMITER ',')
            """)
            n_extracts += 1
    print(f"extracts written: {n_extracts} per-stock-month files (top-12 buffer)")

    # ---------- 6. provenance rows ----------
    for yr in ("2021", "2022", "2023"):
        year_rows = con.execute(
            "SELECT COUNT(*) FROM floorsheet_raw "
            f"WHERE year(date)={yr} AND source='kaggle_viking303'"
        ).fetchone()[0]
        prov.record({
            "ts_utc": utc_iso(), "artifact": f"duckdb floorsheet_raw {yr}",
            "kind": "corpus_ingestion_exp0002b",
            "source_path": f"{KAGGLE_ROOT}/{yr} ({len(kg_years[yr])} files)",
            "source_url": KAGGLE_CITE, "sha256": "", "bytes": 0,
            "rows_sampled": year_rows, "rows_total": year_rows,
            "licence": KAGGLE_LICENCE,
            "evidence": "per-file sha256 in data/metadata/corpus_files_sha256.csv",
        })
    socr_rows = con.execute(
        "SELECT COUNT(*) FROM floorsheet_raw WHERE year(date)=2024").fetchone()[0]
    prov.record({
        "ts_utc": utc_iso(), "artifact": "duckdb floorsheet_raw 2024",
        "kind": "corpus_ingestion_exp0002b",
        "source_path": f"{SOCR_DIR} (floorsheet_2024-*.csv, {len(socr_2024)} files)",
        "source_url": SOCR_CITE, "sha256": "", "bytes": 0,
        "rows_sampled": socr_rows, "rows_total": socr_rows,
        "licence": SOCR_LICENCE,
        "evidence": "per-file sha256 in data/metadata/corpus_files_sha256.csv; "
                    "kaggle-2024 kept as cross-check",
    })
    print(f"PROVENANCE rows appended; total manifest entries: {len(prov.read_manifest())}")
    print(f"INGEST_DONE rows={count_rows(con):,} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
