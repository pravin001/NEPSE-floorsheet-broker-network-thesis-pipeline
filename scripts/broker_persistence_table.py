"""EXP-0003c — BROKER PERSISTENCE (descriptive, R11 PhD-seed appendix).

Definition (declared BEFORE computing): for each (symbol, date) rank brokers
by TOTAL volume traded through them = buy-side volume + sell-side volume
(self-loops contribute to both sides — a ranking-only convention, documented);
take top-10; Jaccard overlap with the previous SESSION's top-10 of the SAME
symbol (DC3 calendar adjacency: |A|, |B| > 0 required). Output:
  outputs/tables/broker_persistence_by_symbol.csv  (per symbol summary)
  outputs/tables/broker_persistence_transitions.csv (per symbol-day Jaccard)

DESCRIPTIVE ONLY (labels R11): persistence numbers are never hypothesis-tested
in the main grid; DC1 note — formal uses must re-run on train-fold days.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import duckdb
import pandas as pd

from nepsemsc.data.duckdb_loader import get_conn
from nepsemsc.network.persistence import jaccard
from nepsemsc.utils.io import atomic_write_df, sha256_file
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.tz import utc_iso

K = 10

TOPK_SQL = f"""
WITH fs AS (
    SELECT date, symbol, buyer_broker_id AS broker, volume
    FROM floorsheet_dedup
    WHERE volume IS NOT NULL AND volume > 0 AND COALESCE(buyer_broker_id,'') <> ''
      AND COALESCE(seller_broker_id,'') <> ''
    UNION ALL
    SELECT date, symbol, seller_broker_id AS broker, volume
    FROM floorsheet_dedup
    WHERE volume IS NOT NULL AND volume > 0 AND COALESCE(buyer_broker_id,'') <> ''
      AND COALESCE(seller_broker_id,'') <> ''
),
tot AS (
    SELECT date, symbol, broker, SUM(volume) AS v FROM fs GROUP BY 1, 2, 3
),
ranked AS (
    SELECT date, symbol, broker, v,
           ROW_NUMBER() OVER (PARTITION BY date, symbol ORDER BY v DESC, broker) AS rk
    FROM tot
)
SELECT date, symbol, broker FROM ranked WHERE rk <= {K}
"""


def main() -> None:
    con = get_conn()
    topk = con.execute(TOPK_SQL).df()
    print(f"top-{K} broker rows: {len(topk):,} "
          f"({topk.symbol.nunique():,} symbols, {topk.date.nunique():,} days)")

    topk = topk.sort_values(["symbol", "date"])
    transitions: list[dict] = []
    for symbol, gr in topk.groupby("symbol", observed=True):
        sets = gr.groupby("date", observed=True)["broker"].agg(set).sort_index()
        for (prev, cur) in zip(sets.index[:-1], sets.index[1:]):
            transitions.append({
                "symbol": symbol, "date": cur,
                "jaccard_topk": jaccard(sets[prev], sets[cur]),
            })
    tr = pd.DataFrame(transitions)
    atomic_write_df(tr, ROOT / "outputs/tables/broker_persistence_transitions.csv",
                    index=False)

    by_sym = (tr.groupby("symbol", observed=True)["jaccard_topk"]
                .agg(n_transitions="size", mean="mean",
                     p10=lambda s: s.quantile(0.10), p50="median",
                     p90=lambda s: s.quantile(0.90))
                .reset_index())
    atomic_write_df(by_sym, ROOT / "outputs/tables/broker_persistence_by_symbol.csv",
                    index=False)
    print(f"transitions: {len(tr):,} | market mean jaccard_top10 "
          f"{tr.jaccard_topk.mean():.4f} | median {tr.jaccard_topk.median():.4f} [REAL]")
    print(by_sym.sort_values("mean", ascending=False).head(12).to_string(index=False))

    prov.record({
        "ts_utc": utc_iso(),
        "artifact": "outputs/tables/broker_persistence_*.csv",
        "kind": "broker_persistence_exp0003c",
        "source_path": "floorsheet_dedup (EXP-0002c)",
        "source_url": "EXP-0002b sources", "sha256": "",
        "bytes": 0,
        "rows_sampled": len(tr), "rows_total": len(tr),
        "licence": "derived",
        "evidence": f"transitions={len(tr)} mean_j={tr.jaccard_topk.mean():.4f} "
                    f"median_j={tr.jaccard_topk.median():.4f}; DESCRIPTIVE ONLY (R11)",
    })
    print("PERSISTENCE_DONE")


if __name__ == "__main__":
    main()
