"""EXP-0003d — DESCRIPTIVE feature summary by calendar regime (R8 line).

Regime = calendar per plan §5 primary line: 2021-2022 = "bubble era",
2023-2024 = "normal". Summaries are DESCRIPTIVE (medians/means/extremes) —
NO inference here; hypotheses live in the Phase-4 grid.

Scope: (a) full corpus panel, (b) top-12 universe buffer (top-10 + NHPC,
HIDCL) from data/metadata/universe_selected.json; DC1 note: per-fold
re-selection at scoring time filters THESE rows, it does not re-derive them.

Columns: median/mean of the 5 grid features + core_periphery_coeff +
seller_hhi; n_pairs; contract_no_defect rows excluded from eod stats.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from nepsemsc.utils.io import atomic_write_df, sha256_file
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.tz import utc_iso


def regimes(year_series: pd.Series) -> pd.Series:
    yr = year_series.astype(int)
    return pd.Series(pd.Categorical(
        yr.map(lambda y: "bubble_2021_22" if y <= 2022 else "normal_2023_24"),
        categories=["bubble_2021_22", "normal_2023_24"]), index=year_series.index)


def main() -> None:
    feat = pd.read_parquet(ROOT / "data/processed/daily_features.parquet")
    feat["date"] = pd.to_datetime(feat["date"])
    feat["regime"] = regimes(feat["date"].dt.year)
    uni = json.loads((ROOT / "data/metadata/universe_selected.json").read_text())
    top12 = set(uni["top12_buffer"])

    rows = []
    for scope, frame in (("full_corpus", feat),
                         ("top12", feat.loc[feat["symbol"].isin(top12)])):
        for regime, g in frame.groupby("regime", observed=True):
            eod = g.loc[g["contract_no_defect"] == 0, "end_of_day_concentration"]
            rec = {
                "scope": scope, "regime": str(regime),
                "n_pairs": len(g), "n_symbols": g["symbol"].nunique(),
                "n_days": g["date"].nunique(),
                "buyer_hhi_median": g["buyer_hhi"].median(),
                "buyer_hhi_mean": g["buyer_hhi"].mean(),
                "seller_hhi_median": g["seller_hhi"].median(),
                "self_loop_median": g["self_loop_volume_ratio"].median(),
                "reciprocity_median": g["reciprocity_volume"].median(),
                "density_median": g["density"].median(),
                "max_betweenness_median": g["max_betweenness"].median(),
                "cp_median": g["core_periphery_coeff"].median(),
                "eod_median": eod.median() if len(eod) else float("nan"),
                "eod_p90": eod.quantile(0.90) if len(eod) else float("nan"),
                "total_volume_sum": float(g["total_volume"].sum()),
            }
            rows.append(rec)
    out = pd.DataFrame(rows)
    atomic_write_df(out, ROOT / "outputs/tables/feature_regime_summary.csv", index=False)
    print(out[["scope", "regime", "n_pairs", "buyer_hhi_median", "self_loop_median",
               "reciprocity_median", "eod_median", "cp_median"]].to_string(index=False))

    prov.record({
        "ts_utc": utc_iso(),
        "artifact": "outputs/tables/feature_regime_summary.csv",
        "kind": "regime_summary_exp0003d",
        "source_path": "data/processed/daily_features.parquet (EXP-0003a)",
        "source_url": "derived", "sha256": "", "bytes": 0,
        "rows_sampled": len(out), "rows_total": len(out),
        "licence": "derived",
        "evidence": "calendar regimes (plan §5 primary): bubble 2021-22 vs normal 2023-24; DESCRIPTIVE ONLY",
    })
    print("SUMMARY_DONE")


if __name__ == "__main__":
    main()
