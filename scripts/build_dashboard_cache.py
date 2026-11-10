"""PHASE 6 — DASHBOARD CACHE BUILDER (extracts-only contract).

Builds the compact snapshot the Dash app serves at runtime, so the app itself
NEVER touches DuckDB, the 57.9M-row corpus, or large parquets:

  data/processed/dashboard_cache/
    top12_daily_features.csv   — 12 extract symbols × 938 sessions of daily
                                 network features (+ regime tag, defect tag)
    anomaly_test_rows.csv      — 7,126 OOS test rows (score/event/fold/feats)
    extract_monthly_summary.csv— per (symbol, month) aggregates from the 576
                                 top-12 extract CSVs (data/raw/floorsheet/)
    calendar.csv               — 940 DC3 sessions w/ in-corpus flag + regime

Everything else the dashboard shows comes straight from outputs/tables/*.csv
(register artifacts of record — single-sourced). Reasoning outputs live there.

NO experiment on this path — data engineering for presentation only; numbers
shown are the already-registered [REAL] numbers re-visualized (R11/R4).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import numpy as np

from nepsemsc.utils.io import atomic_write_df, sha256_file
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.tz import utc_iso

CACHE = ROOT / "data/processed/dashboard_cache"
DEFECT = "2023-02-16"
REGIME_END_BUBBLE = "2022-12-31"          # plan §5 calendar regimes
TOP12 = ["SHIVM", "API", "HDL", "AHPC", "NRIC", "NABIL", "NICA", "UPPER",
         "NLIC", "AKPL", "NHPC", "HIDCL"]


def regime_label(dates: pd.Series) -> pd.Series:
    return np.where(dates <= pd.Timestamp(REGIME_END_BUBBLE).date(),
                    "bubble 2021-22", "normal 2023-24")


def top12_features() -> pd.DataFrame:
    feat = pd.read_parquet(ROOT / "data/processed/daily_features.parquet")
    feat = feat.rename(columns={"self_loop_volume_ratio": "self_loop_ratio",
                                "reciprocity_volume": "reciprocity"})
    feat["date"] = pd.to_datetime(feat["date"]).dt.date
    feat = feat.loc[feat["symbol"].isin(TOP12)].copy()
    feat["regime"] = regime_label(feat["date"])
    feat["is_defect_session"] = (feat["date"].astype(str) == DEFECT)
    # end_of_day_concentration on the defect session is BY DEFINITION an
    # ordering-features exclusion (EXP-0002b/c) — keep the row, null the field
    feat.loc[feat["is_defect_session"],
             "end_of_day_concentration"] = np.nan
    keep = ["date", "symbol", "regime", "is_defect_session", "total_volume",
            "total_trades", "unique_buyers", "unique_sellers", "buyer_hhi",
            "seller_hhi", "top_3_buyer_share", "self_loop_ratio",
            "end_of_day_concentration", "reciprocity", "density",
            "max_betweenness", "core_periphery_coeff", "fs_source"]
    return feat[keep].sort_values(["symbol", "date"]).reset_index(drop=True)


def anomaly_test_rows() -> pd.DataFrame:
    sc = pd.read_parquet(ROOT / "data/processed/anomaly_scores.parquet")
    sc["date"] = pd.to_datetime(sc["date"]).dt.date
    te = sc.loc[~sc["is_train"]].copy()
    te["regime"] = regime_label(te["date"])
    keep = ["date", "symbol", "fold_id", "anomaly_score", "is_event",
            "buyer_hhi", "self_loop_ratio", "reciprocity",
            "end_of_day_concentration", "regime"]
    return te[keep].sort_values(["date", "symbol"]).reset_index(drop=True)


def extract_monthly_summary() -> pd.DataFrame:
    rows = []
    for month_file in sorted((ROOT / "data/raw/floorsheet").glob("*/*.csv")):
        symbol = month_file.parent.name
        df = pd.read_csv(month_file,
                         usecols=["date", "price", "volume", "amount"])
        num = df[["price", "volume", "amount"]].apply(pd.to_numeric,
                                                      errors="coerce")
        rows.append({
            "symbol": symbol,
            "month": month_file.stem,
            "n_files_covered_days": df["date"].nunique(),
            "n_trades": int(len(df)),
            "sum_volume": float(num["volume"].sum()),
            "sum_amount": float(num["amount"].sum()),
        })
    out = pd.DataFrame(rows)
    assert out["symbol"].isin(TOP12).all()
    return out.sort_values(["symbol", "month"]).reset_index(drop=True)


def calendar() -> pd.DataFrame:
    cal = pd.read_parquet(ROOT / "data/processed/nepse_calendar.parquet")
    dcol = "session_date"                     # gotcha: not `date`
    cal["date"] = pd.to_datetime(cal[dcol]).dt.date
    cal["regime"] = regime_label(cal["date"])
    # in-corpus flag: register-verified corpus coverage = 938/940 sessions;
    # the two documentable gaps are 2021-09-01 and 2023-11-27 (EXP-0002b)
    gaps = {pd.Timestamp("2021-09-01").date(), pd.Timestamp("2023-11-27").date()}
    cal["in_corpus"] = ~cal["date"].isin(gaps)
    keep = ["date", "regime", "in_corpus"]
    return cal[keep].drop_duplicates("date").reset_index(drop=True)


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    f12 = top12_features()
    atomic_write_df(f12, CACHE / "top12_daily_features.csv", index=False)
    tr = anomaly_test_rows()
    atomic_write_df(tr, CACHE / "anomaly_test_rows.csv", index=False)
    ems = extract_monthly_summary()
    atomic_write_df(ems, CACHE / "extract_monthly_summary.csv", index=False)
    cal = calendar()
    atomic_write_df(cal, CACHE / "calendar.csv", index=False)
    print(f"dashboard cache: {len(f12):,} feature rows · {len(tr):,} OOS rows"
          f" · {len(ems):,} symbol-months · {len(cal)} sessions → {CACHE}")

    # provenance (Phase-6 presentation-only build; no new inference)
    srcs = {"top12_daily_features.csv": "data/processed/daily_features.parquet"
                                         " (EXP-0003a)",
            "anomaly_test_rows.csv": "data/processed/anomaly_scores.parquet "
                                     "(EXP-0004a OOS rows)",
            "extract_monthly_summary.csv":
                "data/raw/floorsheet/<SYM>/*.csv (top-12 extracts, 576 files)",
            "calendar.csv": "data/processed/nepse_calendar.parquet (DC3)"}
    for name, source in srcs.items():
        path = CACHE / name
        prov.record({
            "ts_utc": utc_iso(),
            "artifact": f"data/processed/dashboard_cache/{name}",
            "kind": "dashboard_cache_exp0006",
            "source_path": source, "source_url": "derived",
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "rows_sampled": len(pd.read_csv(path)),
            "rows_total": len(pd.read_csv(path)),
            "licence": "derived",
            "evidence": "phase-6 extracts-only dashboard cache; "
                        "presentation of registered [REAL] numbers only "
                        "(EXP-0002b/0003a/0004a); re-builds append rows",
        })
    print("provenance rows appended for the 4 cache artifacts")


if __name__ == "__main__":
    main()
