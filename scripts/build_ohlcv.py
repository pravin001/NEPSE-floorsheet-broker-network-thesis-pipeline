"""EXP-0002d — DAILY OHLCV standardisation into data/processed/daily_ohlcv.parquet.

Policy (declared BEFORE inspection):
  * tier1_kaggle (100 symbol CSVs, 2012→2025-09) is PRIMARY; its 940-session
    window calendar (2021-01-01→2024-12-31) is the DC3 calendar already
    frozen in data/processed/nepse_calendar.parquet.
  * tier2_samirwagle (→2026-11-05) FILLS (symbol, date) gaps only
    (incl. 2025-01 tail needed for next-day returns of 2024-12 sessions;
     and 2026 rows for the Phase-5 extension).
  * every row carries `ohlcv_source` ∈ {tier1_kaggle, tier2_samirwagle} so
    any sensitivity analysis can isolate the source.
  * columns: date, symbol, open, high, low, close, volume, turnover.
    tier1 'Close' → close; tier2 'ltp' → close.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from nepsemsc.utils import provenance as prov
from nepsemsc.utils.io import atomic_write_df, sha256_file
from nepsemsc.utils.tz import utc_iso

T1 = Path("/home/whacko/research/nepse-kronos-thesis/data/raw/tier1_kaggle")
T2 = Path("/home/whacko/research/nepse-kronos-thesis/data/raw/tier2_samirwagle_prices")


def main() -> None:
    frames = []
    for p in sorted(T1.glob("*.csv")):
        df = pd.read_csv(p, usecols=["Symbol", "Date", "Open", "High", "Low",
                                     "Close", "Volume", "Turnover"])
        df.columns = [c.lower() for c in df.columns]
        frames.append(df)
    t1all = pd.concat(frames, ignore_index=True)
    t1all["date"] = pd.to_datetime(t1all["date"], errors="coerce").dt.date
    t1all = t1all.dropna(subset=["date"])
    t1all["ohlcv_source"] = "tier1_kaggle"
    print(f"tier1 rows={len(t1all):,} symbols={t1all['symbol'].nunique()} "
          f"span={t1all['date'].min()}→{t1all['date'].max()}")

    t2frames = []
    for p in sorted(T2.glob("*_prices.csv")):
        sym = p.name.removesuffix("_prices.csv").upper()
        df = pd.read_csv(p, usecols=["date", "open", "high", "low", "ltp",
                                     "qty", "turnover"])
        df["symbol"] = sym
        df = df.rename(columns={"ltp": "close", "qty": "volume"})
        t2frames.append(df)
    t2all = pd.concat(t2frames, ignore_index=True)
    t2all["date"] = pd.to_datetime(t2all["date"], errors="coerce").dt.date
    t2all = t2all.dropna(subset=["date"])
    t2all["ohlcv_source"] = "tier2_samirwagle"
    print(f"tier2 rows={len(t2all):,} symbols={t2all['symbol'].nunique()} "
          f"span={t2all['date'].min()}→{t2all['date'].max()}")

    cols = ["date", "symbol", "open", "high", "low", "close", "volume", "turnover", "ohlcv_source"]
    t1k = t1all[cols].set_index(["symbol", "date"])
    t2k = t2all[cols].set_index(["symbol", "date"])
    union = t2k[~t2k.index.isin(t1k.index)]
    out = pd.concat([t1k, union]).reset_index()
    print(f"union rows={len(out):,} (tier1 filled {len(t2k) - len(union):,} of tier2)")
    atomic_write_df(out, ROOT / "data/processed/daily_ohlcv.parquet")

    overlaps = t1k.index.intersection(t2k.index)
    print(f"tier1∩tier2 (symbol,date) overlaps: {len(overlaps):,} — tier1 kept")
    both = pd.merge(t1k[["close"]].rename(columns={"close": "t1"}),
                    t2k[["close"]].rename(columns={"close": "t2"}),
                    left_index=True, right_index=True)
    both = both.dropna()
    rel = ((both.t1 - both.t2).abs() / both.t2).median()
    print(f"median |close_t1-close_t2|/t2 across overlaps: {rel:.4%}")

    prov.record({
        "ts_utc": utc_iso(),
        "artifact": "data/processed/daily_ohlcv.parquet",
        "kind": "ohlcv_standardisation_exp0002d",
        "source_path": "tier1_kaggle (primary) + tier2_samirwagle (gap fill)",
        "source_url": "kaggle rohankasichhwa OHLCV (licence pending user UI check); "
                      "github samirwagle prices (attribution logged)",
        "sha256": sha256_file(ROOT / "data/processed/daily_ohlcv.parquet"),
        "bytes": (ROOT / "data/processed/daily_ohlcv.parquet").stat().st_size,
        "rows_sampled": len(out), "rows_total": len(out),
        "licence": "tier2 attribution documented; tier1 licence pending",
        "evidence": f"tier1 primary; tier2 gap-fill; overlap median reldiff={rel:.4%}",
    })
    print("OHLCV_DONE")


if __name__ == "__main__":
    main()
