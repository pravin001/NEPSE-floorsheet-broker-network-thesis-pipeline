"""EXP-0002e — VOLUME/AMOUNT RECONCILIATION: floorsheet corpus vs OHLCV.

Pre-declared comparison (analysis_plan §1 disclosure):
  fs_volume(d,s)  = SUM(volume) over floorsheet_dedup for (symbol, date)
  ohlcv_volume(d) = daily OHLCV volume
  fs_amount(d,s)  = SUM(amount)          [floorsheet is trade-level]
  ohlcv_turnover(d) = daily turnover column
Acceptance: volume_ratio ∈ [0.95, 1.25] for ≥95% of (symbol, date) rows
(looser upper bound: floorsheet may double-count cross-legs on some
sessions; only systematic departures are findings). Scope: top-12 buffer
symbols × window 2021-01-01→2024-12-31 (the analysis universe), plus a
full-market spot summary.
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

import json


def main() -> None:
    con = get_conn()
    ohlcv = str(ROOT / "data/processed/daily_ohlcv.parquet")
    uni = json.loads((ROOT / "data/metadata/universe_selected.json").read_text())
    syms = ", ".join(f"'{s}'" for s in uni["top12_buffer"])

    rec = con.execute(f"""
        WITH fs AS (
            SELECT symbol, date, SUM(volume) AS fs_volume, SUM(amount) AS fs_amount,
                   COUNT(*) AS fs_trades
            FROM floorsheet_dedup
            WHERE symbol IN ({syms})
            GROUP BY 1, 2
        ), px AS (
            SELECT symbol, date, volume AS ohlcv_volume, turnover AS ohlcv_turnover
            FROM read_parquet('{ohlcv}')
            WHERE symbol IN ({syms}) AND date BETWEEN DATE '2021-01-01' AND DATE '2024-12-31'
        )
        SELECT fs.symbol, fs.date, fs.fs_volume, px.ohlcv_volume,
               fs.fs_volume::DOUBLE / NULLIF(px.ohlcv_volume, 0) AS volume_ratio,
               fs.fs_amount, px.ohlcv_turnover,
               fs.fs_amount / NULLIF(px.ohlcv_turnover, 0) AS amount_ratio,
               fs.fs_trades
        FROM fs FULL OUTER JOIN px USING (symbol, date)
        ORDER BY 2, 1
    """).df()
    n = len(rec)
    both = rec.dropna(subset=["volume_ratio"])
    in_band = both["volume_ratio"].between(0.95, 1.25).mean()
    in_band_tight = both["volume_ratio"].between(0.98, 1.02).mean()
    print(f"pairs={n:,} both-sides={len(both):,} "
          f"volume in [0.95,1.25]: {in_band:.1%} in [0.98,1.02]: {in_band_tight:.1%} "
          f"median ratio={both['volume_ratio'].median():.4f}")
    atomic_write_df(rec, ROOT / "outputs/tables/volume_reconciliation.csv", index=False)

    # full-market spot summary (one line per year — consoles only)
    spot = con.execute(f"""
        WITH fs AS (
            SELECT year(date) y, SUM(volume) v_fs FROM floorsheet_dedup GROUP BY 1
        ), px AS (
            SELECT year(CAST(date AS DATE)) y, SUM(volume) v_px
            FROM read_parquet('{ohlcv}')
            WHERE date BETWEEN DATE '2021-01-01' AND DATE '2024-12-31'
            GROUP BY 1
        )
        SELECT y, v_fs, v_px, v_fs::DOUBLE / NULLIF(v_px, 0) AS ratio FROM fs JOIN px USING (y)
    """).df()
    print(spot.to_string(index=False))

    prov.record({
        "ts_utc": utc_iso(),
        "artifact": "outputs/tables/volume_reconciliation.csv",
        "kind": "reconciliation_exp0002e",
        "source_path": "floorsheet_dedup × daily_ohlcv.parquet",
        "source_url": "EXP-0002b/d sources", "sha256": "", "bytes": 0,
        "rows_sampled": n, "rows_total": n,
        "licence": "derived",
        "evidence": f"band_95_125={in_band:.1%} tight={in_band_tight:.1%}",
    })
    print("RECON_DONE")


if __name__ == "__main__":
    main()
