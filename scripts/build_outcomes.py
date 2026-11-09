"""EXP-0003b — OUTCOME PANEL per (symbol, date): returns + volatility proxies.

Pre-declared (analysis_plan §2, before any outcome is joined to features):
  * ret[t]      = close[t]/close[prev session of that SYMBOL on the DC3
                  calendar] - 1 (tier1 OHLCV only — consistent close series).
  * ret_fwd1[t] = ret[t+1 session]; abs_ret_fwd1 = |ret_fwd1|. The LAST
                  session's fwd return uses each symbol's first available
                  tier1 close after the window (2025-01) — reported as
                  coverage, NaN otherwise. NO look-ahead beyond t+1.
  * parkinson_vol[t] = ln(high/low) / sqrt(4 ln 2) (PCS/Parkinson line).
  * loo_market_ret[t] joined per row ("market_ret_loo"): equal-weight mean
    return across ALL tier1 OHLCV symbols EXCLUDING stock i's own return
    (DC9); symbols with a computable back-to-back return that session only.
  * Scope note [limitation]: tier1 = 100 of 530 corpus scrips → the "market"
    here is the OHLCV-covered segment; documented in the register + plan §1.
No returns are joined to features inside this script (Phase 4 does that on
TRAIN-only stats) — this artefact is a pure outcome table.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd

from nepsemsc.utils.io import atomic_write_df, sha256_file
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.tz import utc_iso

WIN_START, WIN_END = "2021-01-01", "2024-12-31"


def main() -> None:
    px = pd.read_parquet(ROOT / "data/processed/daily_ohlcv.parquet")
    px["date"] = pd.to_datetime(px["date"]).dt.date
    px = px[(px["ohlcv_source"] == "tier1_kaggle")
            & (px["date"] >= pd.Timestamp(WIN_START).date())].copy()
    px = px.sort_values(["symbol", "date"]).reset_index(drop=True)
    calc = px["date"] <= pd.Timestamp(WIN_END).date()

    g = px.groupby("symbol", observed=True)
    px["ret"] = (px["close"] / g["close"].shift(1) - 1).where(calc)
    px["ret_fwd1"] = g["ret"].shift(-1)
    px["abs_ret_fwd1"] = px["ret_fwd1"].abs()
    px["parkinson_vol"] = (
        np.log(px["high"].astype(float) / px["low"].astype(float)).abs()
        / np.sqrt(4.0 * np.log(2.0))).where(calc)
    px["log_volume_ohlcv"] = np.log(px["volume"].astype(float).clip(lower=1.0))

    # ---- DC9 leave-one-out equal-weight market return ----
    # market for day t = mean ret across symbols WITH a valid back-to-back ret; the LOO
    # value for symbol i recomputes it without i's own row.
    day = px[calc].dropna(subset=["ret"])
    sums = day.groupby("date", observed=True)["ret"].agg(["sum", "count"])
    px = px.merge(sums.rename(columns={"sum": "ret_sum", "count": "ret_n"}),
                  left_on="date", right_index=True, how="left")
    own = px["ret"].where(calc)
    px["market_ret_loo"] = ((px["ret_sum"] - own) / (px["ret_n"] - 1)).where(
        px["ret_n"] >= 2)
    px["market_ret"] = (px["ret_sum"] / px["ret_n"]).where(px["ret_n"] >= 2)

    out_cols = ["date", "symbol", "close", "ret", "ret_fwd1", "abs_ret_fwd1",
                "parkinson_vol", "log_volume_ohlcv", "market_ret",
                "market_ret_loo", "volume", "turnover", "ohlcv_source"]
    out = px.loc[px["date"] <= pd.Timestamp(WIN_END).date(), out_cols].copy()
    cov = out[["ret", "ret_fwd1", "abs_ret_fwd1", "parkinson_vol",
               "market_ret_loo"]].notna().mean().rename("coverage")
    print("outcome coverage (window rows):")
    print(cov.map(lambda v: f"{v:.1%}").to_string())
    print(f"rows={len(out):,} symbols={out['symbol'].nunique()} days={out['date'].nunique()}")
    atomic_write_df(out, ROOT / "data/processed/daily_outcomes.parquet")
    atomic_write_df(out.head(200), ROOT / "outputs/tables/daily_outcomes_preview.csv",
                    index=False)

    prov.record({
        "ts_utc": utc_iso(),
        "artifact": "data/processed/daily_outcomes.parquet",
        "kind": "outcomes_panel_exp0003b",
        "source_path": "data/processed/daily_ohlcv.parquet (tier1 rows)",
        "source_url": "EXP-0002d sources", "sha256":
            sha256_file(ROOT / "data/processed/daily_outcomes.parquet"),
        "bytes": (ROOT / "data/processed/daily_outcomes.parquet").stat().st_size,
        "rows_sampled": len(out), "rows_total": len(out),
        "licence": "derived",
        "evidence": "; ".join(f"{k}={v:.1%}" for k, v in cov.items()),
    })
    print("OUTCOMES_DONE")


if __name__ == "__main__":
    main()
