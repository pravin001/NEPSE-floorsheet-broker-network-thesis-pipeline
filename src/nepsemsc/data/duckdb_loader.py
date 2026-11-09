"""DuckDB connection + normalized raw-table loader (heavy CSVs never touch pandas).

Production ingestion path: DuckDB `read_csv` over a directory (glob per
symbol-month), type-safe projection into `floorsheet_raw`, broker-id
zero-padding, duplicate-day protection via explicit per-month staging.
"""
from __future__ import annotations

from pathlib import Path

import duckdb

from nepsemsc.utils.paths import data_dir

DB_PATH = data_dir("duckdb") / "nepse.duckdb"

RAW_DDL = """
CREATE TABLE IF NOT EXISTS floorsheet_raw (
    date DATE,
    contract_no BIGINT,
    symbol VARCHAR,
    price DOUBLE,
    volume BIGINT,
    amount DOUBLE,
    buyer_broker_id VARCHAR,
    seller_broker_id VARCHAR,
    source VARCHAR NOT NULL DEFAULT 'unknown'
);
"""


def get_conn(path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    path = Path(path) if path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    return con


def init_db(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(RAW_DDL)


def count_rows(con: duckdb.DuckDBPyConnection) -> int:
    return int(con.execute("SELECT COUNT(*) FROM floorsheet_raw").fetchone()[0])


def has_batch(con: duckdb.DuckDBPyConnection, year: int, month: int) -> bool:
    return bool(con.execute(
        "SELECT COUNT(*) FROM floorsheet_raw WHERE year(date)=? AND month(date)=?",
        [year, month]).fetchone()[0])


# broker-id normalisation shared by ALL ingestion SQL (BROKER_ID_SQL):
#  * purely numeric ids ('8', '100') → zero-padded 2-digit strings ('08','100')
#  * dealer/alphanumeric codes (e.g. 'D01') → kept verbatim uppercase
#    (D01 = NEPSE dealer seat, observed in kaggle 2021-2023 corpus; probes:
#     892 (2021) + 159 (2023) occurrences in sampled files)
BROKER_ID_SQL = ("CASE WHEN regexp_full_match(trim({col}), '^[0-9]+$')\n"
                 "     THEN lpad(trim({col}), 2, '0')\n"
                 "     ELSE upper(trim({col}))\nEND")

_BUYER = BROKER_ID_SQL.format(col="{buyer_expr}")
_SELLER = BROKER_ID_SQL.format(col="{seller_expr}")

_RAW_PROJECTION = (
    "{date_expr}        AS date,\n"
    "TRY_CAST({contract_no_expr} AS BIGINT)   AS contract_no,\n"
    "upper(trim({symbol_expr}))               AS symbol,\n"
    "TRY_CAST({price_expr} AS DOUBLE)         AS price,\n"
    "TRY_CAST({volume_expr} AS BIGINT)        AS volume,\n"
    "TRY_CAST({amount_expr} AS DOUBLE)        AS amount,\n"
    f"{_BUYER} AS buyer_broker_id,\n"
    f"{_SELLER} AS seller_broker_id,\n"
    "'{source}'                               AS source"
)


def load_csv_file(con: duckdb.DuckDBPyConnection, csv_path: str | Path,
                  symbol_filter: str | None = None) -> int:
    """Load ONE floorsheet csv (one-day archive slice) into floorsheet_raw.

    Column projection is inside SQL: pandas needs not see the file. Returns
    the number of rows inserted.
    """
    path = str(Path(csv_path))
    symbol_clause = f"AND symbol = '{symbol_filter.upper()}'" if symbol_filter else ""
    sel = _RAW_PROJECTION.format(
        date_expr="CAST(date AS DATE)",
        contract_no_expr="transaction",
        symbol_expr="symbol",
        price_expr="rate",
        volume_expr="quantity",
        amount_expr="amount",
        buyer_expr="buyer",
        seller_expr="seller",
        source="socrateai",
    )
    sql = f"""
    INSERT INTO floorsheet_raw
    SELECT {sel}
    FROM read_csv('{path}', header = true, all_varchar = true,
                  filename = false)
    WHERE 1 = 1 {symbol_clause}
    """
    con.execute(sql)
    # read the inserted count via changes? use row count diff by key — cheap way:
    return count_rows(con)


def load_extracted_extract(con: duckdb.DuckDBPyConnection, csv_path: str | Path) -> int:
    """Load an ALREADY-extracted per-stock-month csv (produced by
    scripts/extract_sample_month.py, which uses the canonical schema)."""
    path = str(Path(csv_path))
    con.execute(f"""
        INSERT INTO floorsheet_raw
        SELECT CAST(date AS DATE)      AS date,
               CAST(contract_no AS BIGINT)            AS contract_no,
               upper(trim(symbol))                    AS symbol,
               CAST(price AS DOUBLE)                  AS price,
               CAST(volume AS BIGINT)                 AS volume,
               CAST(amount AS DOUBLE)                 AS amount,
               lpad(trim(CAST(buyer_broker_id AS VARCHAR)), 2, '0') AS buyer_broker_id,
               lpad(trim(CAST(seller_broker_id AS VARCHAR)), 2, '0') AS seller_broker_id,
               'extract'                              AS source
        FROM read_csv('{path}', header = true, all_varchar = true)
    """)
    return count_rows(con)


_KAGGLE_DATE_FROM_FILENAME = (
    "CAST(replace(regexp_extract(filename, '([0-9]{4})_([0-9]{2})_([0-9]{2})'),"
    " '_', '-') AS DATE)"
)


def load_kaggle_year_dir(con: duckdb.DuckDBPyConnection, year_dir: str | Path,
                         date_relabel: dict[str, str] | None = None,
                         source: str = "kaggle_viking303") -> int:
    """Bulk-load ONE kaggle year folder (`YYYY_MM_DD_floorsheet.csv` per file).

    date_relabel maps ORIGINAL date strings ('2021-03-07') → CORRECT session
    dates ('2021-03-08'); used ONLY where documented evidence exists (see
    docs/analysis_deviations.md). D01-style dealer codes pass through
    (BROKER_ID_SQL); `#` and scrape-artifact columns are discarded by
    projection.
    """
    year_dir = str(Path(year_dir))
    if date_relabel:
        # filenames are underscore-dated (2021_03_07); keys are ISO (2021-03-07)
        _iso2fn = lambda s: s.replace("-", "_")   # noqa: E731  (filename fmt)
        whens = " ".join(
            f"WHEN filename LIKE '%{_iso2fn(k)}%' THEN DATE '{v}'"
            for k, v in sorted(date_relabel.items()))
        date_expr = f"CASE {whens} ELSE {_KAGGLE_DATE_FROM_FILENAME} END"
    else:
        date_expr = _KAGGLE_DATE_FROM_FILENAME
    sel = _RAW_PROJECTION.format(
        date_expr=date_expr, contract_no_expr='"Transact. No."',
        symbol_expr="Symbol", price_expr="Rate", volume_expr="Quantity",
        amount_expr="Amount", buyer_expr="Buyer", seller_expr="Seller",
        source=source,
    )
    con.execute(f"""
        INSERT INTO floorsheet_raw
        SELECT {sel}
        FROM read_csv('{year_dir}/*_floorsheet.csv', header = true,
                      all_varchar = true, union_by_name = true,
                      filename = 'filename')
    """)
    return count_rows(con)


def load_socrateai_day_glob(con: duckdb.DuckDBPyConnection, glob_pattern: str,
                            source: str = "socrateai") -> int:
    """Bulk-load a day-glob of socrateai floorsheets (date INSIDE each file)."""
    sel = _RAW_PROJECTION.format(
        date_expr="CAST(date AS DATE)", contract_no_expr="transaction",
        symbol_expr="symbol", price_expr="rate", volume_expr="quantity",
        amount_expr="amount", buyer_expr="buyer", seller_expr="seller",
        source=source,
    )
    con.execute(f"""
        INSERT INTO floorsheet_raw
        SELECT {sel}
        FROM read_csv('{glob_pattern}', header = true, all_varchar = true,
                      union_by_name = true)
    """)
    return count_rows(con)


# Specified Phase-1 check query (brief, step 6)
DAILY_COUNTS_SQL = """
SELECT symbol, date, COUNT(*) AS n_trades,
       COUNT(DISTINCT buyer_broker_id) AS n_buyers,
       COUNT(DISTINCT seller_broker_id) AS n_sellers
FROM floorsheet_raw GROUP BY 1, 2 ORDER BY 1, 2 LIMIT 10
"""
