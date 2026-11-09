"""EXP-0002a — Universe selection (DC1/DC2), declared BEFORE any floorsheet ingestion.

Method (pre-declared in analysis_plan §1):
  * NEPSE session calendar = dates where ANY of the 100 tier1_kaggle symbols
    has non-null (volume > 0) in 2021-01-01 → 2024-12-31 (DC3, data-derived).
  * Candidates = the 100 tier1_kaggle symbols; turnover = daily Turnover column.
  * Headline top-10 by mean WINDOW turnover among stocks that pass the DC2
    inclusion rule (≥90% of calendar sessions present in window).
  * We also extract per-stock-month floorsheet raws for top-12 (= top-10 +
    two boundary buffer) so per-fold DC1 re-selection has room to shift.
  * FINAL analysis universe is re-selected per fold on TRAINING turnover only
    inside the Module-2/3 pipeline (DC1) — the DuckDB store keeps the full
    market so no stock is unreachable.

Outputs:
  data/processed/nepse_calendar.parquet         (session list, window)
  outputs/tables/universe_selected_top10.csv    (ranked table + buffer)
  outputs/tables/universe_exclusions.csv        (DC2 exclusions with reason)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from nepsemsc.utils import config as cfgmod
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.io import atomic_write_df
from nepsemsc.utils.tz import utc_iso

K1 = Path("/home/whacko/research/nepse-kronos-thesis/data/raw/tier1_kaggle")
WIN_START, WIN_END = "2021-01-01", "2024-12-31"


def main() -> None:
    cfg = cfgmod.load_config()
    assert cfg["universe"]["inclusion_min_days_present"] == 0.90

    frames = []
    for p in sorted(K1.glob("*.csv")):
        df = pd.read_csv(p, usecols=["Symbol", "Date", "Volume", "Turnover"])
        df = df.rename(columns={"Symbol": "symbol", "Date": "date",
                                "Volume": "volume", "Turnover": "turnover"})
        frames.append(df)
    px = pd.concat(frames, ignore_index=True)
    px["date"] = pd.to_datetime(px["date"])
    px = px[(px["date"] >= WIN_START) & (px["date"] <= WIN_END)]

    # --- calendar (DC3): any symbol non-null volume>0 ---
    sessions = sorted(px.loc[px["volume"] > 0, "date"].dt.date.unique())
    n_sessions = len(sessions)
    calendar = pd.DataFrame({"session_date": sessions})
    atomic_write_df(calendar, ROOT / "data/processed/nepse_calendar.parquet")
    print(f"calendar sessions 2021-01-01→2024-12-31: {n_sessions}")

    # --- per-symbol coverage + mean window turnover ---
    px["session_date"] = px["date"].dt.date
    sess_idx = set(sessions)
    px = px[px["session_date"].isin(sess_idx) & (px["volume"] > 0)]
    cov = (px.groupby("symbol")["session_date"].nunique() / n_sessions).rename("coverage")
    tr = px.groupby("symbol")["turnover"].agg(["mean", "sum"]).rename(
        columns={"mean": "mean_daily_turnover", "sum": "total_turnover"})
    uni = tr.join(cov).sort_values("mean_daily_turnover", ascending=False)

    # DC2 exclusions (pre-results): coverage < 0.90
    excluded = uni[uni["coverage"] < 0.90].reset_index()
    excluded["exclusion_reason"] = "coverage_lt_90pct_of_sessions (DC2)"
    atomic_write_df(excluded, ROOT / "outputs/tables/universe_exclusions.csv")

    eligible = uni[uni["coverage"] >= 0.90].reset_index()
    eligible = eligible.rename(columns={"symbol": "rank_symbol"}).reset_index(drop=True)
    eligible.insert(0, "rank", range(1, len(eligible) + 1))
    eligible["role"] = ["headline_top10" if r <= 10 else
                        ("top12_buffer" if r <= 12 else "reserve") for r in eligible["rank"]]
    top12 = eligible.head(12)
    atomic_write_df(eligible.head(50), ROOT / "outputs/tables/universe_selected_top10.csv")

    top10 = top12[top12["role"] == "headline_top10"]["rank_symbol"].tolist()
    top12buf = top12["rank_symbol"].tolist()
    print("\nHEADLINE TOP-10 (declared, mean window turnover, DC2-passed):")
    for i, s in enumerate(top10, 1):
        row = top12.iloc[i - 1]
        print(f"{i:2d}. {s:8s} mean_turnover={row['mean_daily_turnover']:>14,.0f} "
              f"coverage={row['coverage']:.3f}")
    print("buffer (11-12):", top12buf[10:12])

    prov.record({
        "ts_utc": utc_iso(),
        "artifact": "outputs/tables/universe_selected_top10.csv",
        "kind": "universe_selection_exp0002a",
        "source_path": "tier1_kaggle (local, sibling-project archive)",
        "source_url": "kaggle rohankasichhwa/nepse-daily-stock-data-2012-2025 (licence pending user UI check)",
        "sha256": "", "bytes": 0,
        "rows_sampled": len(top12), "rows_total": len(uni),
        "licence": "pending_user_ui_check (OHLCV secondary)",
        "evidence": "cal derived from OHLCV (DC3); window turnover mean; DC2 90% rule",
    })

    # persist the selection for downstream jobs
    (ROOT / "data/metadata").mkdir(exist_ok=True)
    atomic_write_df(top12, ROOT / "data/metadata/universe_selected.csv", index=False)
    import json
    prov.atomic_write_json(ROOT / "data/metadata/universe_selected.json", {
        "top10": top10, "top12_buffer": top12buf,
        "n_sessions_window": n_sessions,
        "window": [WIN_START, WIN_END],
        "config_fingerprint": cfg["_fingerprint_sha256"],
    })
    print(f"UNIVERSE_DECLARED top10={len(top10)} top12={len(top12buf)} sessions={n_sessions}")


if __name__ == "__main__":
    main()
