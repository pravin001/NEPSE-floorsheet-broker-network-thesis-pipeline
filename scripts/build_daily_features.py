"""EXP-0003a — DAILY (symbol,date) NETWORK FEATURES at corpus scale.

Pre-declared definitions (before ANY feature is computed; Phase 2 done
2026-11-09, plan §2 grid + brief Module-3):

UNIVERSE SCOPE  All corpus (symbol, date) pairs are computed (not only the
  top-12) so that Phase-4 per-fold re-selection (DC1) never re-runs features.
  DC2 (>=90% session presence) is applied at SELECTION time, not here.

ROW SCOPE (SV7 + Phase-2 gates)
  * source table = floorsheet_dedup (EXP-0002c; duplicates resolved
    deterministically, deviation logged);
  * DROP rows with NULL volume (junk scrape lines), volume <= 0, price <= 0,
    empty buyer/seller id or empty symbol. Drop accounting printed and saved
    (n_in, n_out, dropped_volume share) — SV7 "drop rows" policy, never switch.

FEATURES per (symbol, date)
  level aggregates (SQL):   total_volume, total_trades, unique_buyers,
                            unique_sellers, buyer_hhi, seller_hhi,
                            self_loop_volume_ratio, top_3_buyer_share,
                            top_3_seller_share
  graph metrics (networkx on aggregated BUYER→SELLER weighted edges):
                            density, reciprocity_volume (2*matched/total;
                            distinct-broker pairs only — self-loops stay in
                            the denominator, never the numerator),
                            max_betweenness (UNWEIGHTED, exact for
                            n_nodes <= precision_k=200; per-symbol-day
                            graphs are far smaller), n_nodes, n_edges
  core-periphery:           core_periphery_coeff (Borgatti-Everett sweep,
                            src/nepsemsc/network/core_periphery.py —
                            deterministic eigh, R12 interpretation guard)
  ordering-dependent:       end_of_day_concentration = share of daily volume
                            in the last ceil(5%) of trades BY contract_no
                            (sorted; gaps documented) — set to NULL with
                            flag contract_no_defect=1 for 2023-02-16 (ALL
                            rows share one id → ordering meaningless).
  provenance:               fs_source (MIN=MAX check inside [_REAL] scope)

OUTPUTS data/processed/daily_features.parquet (gitignored, rebuildable);
        outputs/tables/daily_features_preview.csv (tracked, head 200);
        drop-accounting  outputs/tables/feature_row_filter_accounting.csv.
"""
from __future__ import annotations

import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from nepsemsc.data.duckdb_loader import get_conn
from nepsemsc.network.core_periphery import borgatti_everett_score
from nepsemsc.network.graph_builder import build_directed_weighted_graph
from nepsemsc.network.metrics import reciprocity_volume
from nepsemsc.utils.io import atomic_write_df, sha256_file
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.tz import utc_iso

DEFECT_DATE = "2023-02-16"
BETWEENNESS_PRECISION_K = 200
OUT_PARQUET = ROOT / "data/processed/daily_features.parquet"

FILTER_SQL_GATES = """
    volume IS NOT NULL AND volume > 0
    AND price > 0
    AND COALESCE(buyer_broker_id, '') <> ''
    AND COALESCE(seller_broker_id, '') <> ''
    AND COALESCE(symbol, '') <> ''
"""

FEATURE_SQL = f"""
WITH fs AS (
    SELECT date, symbol, contract_no, volume, amount,
           buyer_broker_id, seller_broker_id, source
    FROM floorsheet_dedup
    WHERE {FILTER_SQL_GATES}
),
vol AS (
    SELECT date, symbol, SUM(volume) AS total_volume, COUNT(*) AS total_trades,
           COUNT(DISTINCT buyer_broker_id) AS unique_buyers,
           COUNT(DISTINCT seller_broker_id) AS unique_sellers,
           MIN(source) AS src_min, MAX(source) AS src_max
    FROM fs GROUP BY 1, 2
),
buy AS (
    SELECT date, symbol, buyer_broker_id AS broker, SUM(volume) AS bv
    FROM fs GROUP BY 1, 2, 3
),
sell AS (
    SELECT date, symbol, seller_broker_id AS broker, SUM(volume) AS sv
    FROM fs GROUP BY 1, 2, 3
),
buy_hhi AS (
    SELECT date, symbol, SUM(pow(bv / total_volume, 2)) AS buyer_hhi
    FROM buy JOIN vol USING (date, symbol) GROUP BY 1, 2
),
sell_hhi AS (
    SELECT date, symbol, SUM(pow(sv / total_volume, 2)) AS seller_hhi
    FROM sell JOIN vol USING (date, symbol) GROUP BY 1, 2
),
self_loop AS (
    SELECT date, symbol,
           SUM(CASE WHEN buyer_broker_id = seller_broker_id THEN volume ELSE 0 END)
               / SUM(volume) AS self_loop_volume_ratio
    FROM fs GROUP BY 1, 2
),
top_buy AS (
    SELECT date, symbol, SUM(bv) AS top3_bv FROM (
        SELECT date, symbol, bv,
               ROW_NUMBER() OVER (PARTITION BY date, symbol ORDER BY bv DESC) AS rk
        FROM buy) WHERE rk <= 3 GROUP BY 1, 2
),
top_sell AS (
    SELECT date, symbol, SUM(sv) AS top3_sv FROM (
        SELECT date, symbol, sv,
               ROW_NUMBER() OVER (PARTITION BY date, symbol ORDER BY sv DESC) AS rk
        FROM sell) WHERE rk <= 3 GROUP BY 1, 2
),
ranked AS (
    -- 2023-02-16 EXCLUDED: every row shares one contract id (EXP-0002c) so
    -- "last 5% of trades" is undefined; ordering-safe days only.
    SELECT date, symbol, volume,
           ROW_NUMBER() OVER (PARTITION BY date, symbol ORDER BY contract_no DESC) AS rn_desc,
           COUNT(*) OVER (PARTITION BY date, symbol) AS n_t
    FROM fs
    WHERE CAST(date AS VARCHAR) <> '{DEFECT_DATE}'
),
eod AS (
    SELECT date, symbol,
           SUM(CASE WHEN rn_desc <= CAST(ceil(0.05 * n_t) AS BIGINT)
                    THEN volume ELSE 0 END) / SUM(volume) AS end_of_day_concentration
    FROM ranked GROUP BY 1, 2
)
SELECT v.date, v.symbol, v.total_volume, v.total_trades,
       v.unique_buyers, v.unique_sellers, v.src_min, v.src_max,
       bh.buyer_hhi, sh.seller_hhi, sl.self_loop_volume_ratio,
       tb.top3_bv / v.total_volume AS top_3_buyer_share,
       ts.top3_sv / v.total_volume AS top_3_seller_share,
       e.end_of_day_concentration
FROM vol v
LEFT JOIN buy_hhi bh USING (date, symbol)
LEFT JOIN sell_hhi sh USING (date, symbol)
LEFT JOIN self_loop sl USING (date, symbol)
LEFT JOIN top_buy tb USING (date, symbol)
LEFT JOIN top_sell ts USING (date, symbol)
LEFT JOIN eod e USING (date, symbol)
ORDER BY v.symbol, v.date
"""

EDGES_SQL = f"""
SELECT date, symbol, buyer_broker_id, seller_broker_id, SUM(volume) AS pair_volume
FROM floorsheet_dedup
WHERE {FILTER_SQL_GATES}
GROUP BY 1, 2, 3, 4
"""


def graph_metrics_for_date(day_edges: pd.DataFrame) -> pd.DataFrame:
    """Per-symbol graphs for ONE date; networkx metrics + Borgatti-Everett CP."""
    import networkx as nx

    rows: list[dict] = []
    for symbol, g in day_edges.groupby("symbol", observed=True):
        G = build_directed_weighted_graph(g)
        m = {
            "symbol": symbol,
            "n_nodes": G.number_of_nodes(),
            "n_edges": G.number_of_edges(),
            "density": nx.density(G),
            "reciprocity_volume": reciprocity_volume(G),
        }
        m["max_betweenness"] = (
            0.0 if G.number_of_nodes() < 3 else _betweenness(G))
        m["core_periphery_coeff"] = borgatti_everett_score(G)
        rows.append(m)
    return pd.DataFrame(rows)


def _betweenness(G) -> float:
    from nepsemsc.network.metrics import max_betweenness
    return max_betweenness(G, unweighted=True, precision_k=BETWEENNESS_PRECISION_K)


def _day_worker(args):
    date, slice_bytes = args
    import io as _io
    day_edges = pd.read_parquet(_io.BytesIO(slice_bytes))
    gm = graph_metrics_for_date(day_edges)
    gm.insert(0, "date", date)
    return gm


def main() -> None:
    t0 = time.time()
    con = get_conn()

    # ---------- 0. accounting: SV7 drop scope ----------
    acc = con.execute(f"""
        SELECT COUNT(*) AS n_rows_in, COALESCE(SUM(volume), 0) AS vol_in
        FROM floorsheet_dedup
    """).df().iloc[0]
    acc2 = con.execute(f"""
        SELECT COUNT(*) AS n_rows_kept, COALESCE(SUM(volume), 0) AS vol_kept
        FROM floorsheet_dedup WHERE {FILTER_SQL_GATES}
    """).df().iloc[0]
    accounting = pd.DataFrame([{
        "n_rows_raw": int(acc.n_rows_in), "n_rows_after_filters": int(acc2.n_rows_kept),
        "dropped_rows": int(acc.n_rows_in - acc2.n_rows_kept),
        "volume_kept_share": float(acc2.vol_kept / acc.vol_in) if acc.vol_in else None,
        "policy": "SV7: DROP rows (junk/NULL-volume; missing broker id); pre-declared, never switch",
    }])
    atomic_write_df(accounting, ROOT / "outputs/tables/feature_row_filter_accounting.csv", index=False)
    print("drop accounting:", accounting.to_dict("records")[0])

    # ---------- 1. SQL daily features ----------
    feat_sql = con.execute(FEATURE_SQL).df()
    src_mismatch = int((feat_sql.src_min != feat_sql.src_max).sum())
    assert src_mismatch == 0, "source must be constant within a (symbol,date) group"
    feat_sql["fs_source"] = feat_sql["src_min"]
    feat_sql = feat_sql.drop(columns=["src_min", "src_max"])
    feat_sql["contract_no_defect"] = (
        feat_sql["date"].astype(str) == DEFECT_DATE).astype("int8")
    n_pairs = len(feat_sql)
    print(f"SQL features: {n_pairs:,} (symbol,date) pairs "
          f"[{feat_sql.date.min()} → {feat_sql.date.max()}] in {time.time() - t0:.0f}s")

    # ---------- 2. edges → parquet bytes per date ----------
    edges = con.execute(EDGES_SQL).df()
    print(f"edges: {len(edges):,} broker-pair rows "
          f"({edges.date.nunique()} dates, {edges.symbol.nunique()} symbols)")
    date_slices = []
    for d, g in edges.groupby("date", observed=True):
        buf = g.to_parquet(index=False, engine="pyarrow")  # bytes
        date_slices.append((d, buf))
    del edges
    print(f"date slices prepared: {len(date_slices)}")

    # ---------- 3. graph stage (24 workers) ----------
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    gm_parts = []
    with ProcessPoolExecutor(max_workers=24, mp_context=ctx) as pool:
        for i, part in enumerate(pool.map(_day_worker, date_slices, chunksize=8)):
            gm_parts.append(part)
            if (i + 1) % 200 == 0:
                print(f"  graph stage {i + 1}/{len(date_slices)} dates "
                      f"({time.time() - t0:.0f}s)")
    gm = pd.concat(gm_parts, ignore_index=True)
    del gm_parts, date_slices
    print(f"graph metrics rows: {len(gm):,} in {time.time() - t0:.0f}s")

    # ---------- 4. join + save ----------
    import duckdb
    dd = duckdb.connect()
    feat_sql["date"] = pd.to_datetime(feat_sql["date"]).dt.date
    gm["date"] = pd.to_datetime(gm["date"]).dt.date
    dd.register("feat", feat_sql)
    dd.register("gm", gm)
    out = dd.execute("""
        SELECT f.*, g.n_nodes, g.n_edges, g.density, g.reciprocity_volume,
               g.max_betweenness, g.core_periphery_coeff
        FROM feat f LEFT JOIN gm g USING (date, symbol)
    """).df()
    dd.close()
    atomic_write_df(out, OUT_PARQUET)
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    preview_cols = ["date", "symbol", "total_volume", "total_trades", "buyer_hhi",
                    "seller_hhi", "self_loop_volume_ratio", "end_of_day_concentration",
                    "density", "reciprocity_volume", "max_betweenness",
                    "core_periphery_coeff", "fs_source", "contract_no_defect"]
    atomic_write_df(out[preview_cols].head(200),
                    ROOT / "outputs/tables/daily_features_preview.csv", index=False)

    # sanity: no NaN in the 5 grid features beyond declared defects
    for col in ("buyer_hhi", "seller_hhi", "self_loop_volume_ratio"):
        bad = int(out[col].isna().sum())
        assert bad == 0, f"{col} NaNs: {bad}"
    eod_nan = int(out["end_of_day_concentration"].isna().sum())
    eod_nan_defect = int(out.loc[out.contract_no_defect == 1,
                                 "end_of_day_concentration"].isna().sum())
    print(f"eod NaN: {eod_nan} (defect days: {eod_nan_defect}) — "
          f"expected {n_pairs and int((out.contract_no_defect == 1).sum())}")

    prov.record({
        "ts_utc": utc_iso(),
        "artifact": "data/processed/daily_features.parquet",
        "kind": "daily_features_exp0003a",
        "source_path": "floorsheet_dedup (EXP-0002c) + network stack",
        "source_url": "EXP-0002b sources", "sha256": sha256_file(OUT_PARQUET),
        "bytes": OUT_PARQUET.stat().st_size,
        "rows_sampled": len(out), "rows_total": len(out),
        "licence": "derived",
        "evidence": f"pairs={n_pairs} graph_rows={len(gm)} "
                    f"dropped_rows={accounting.dropped_rows.iloc[0]}",
    })
    print(f"FEATURES_DONE rows={len(out):,} total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
