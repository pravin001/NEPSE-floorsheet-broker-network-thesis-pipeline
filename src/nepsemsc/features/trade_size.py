"""Trade-size bucket features (v2 Stage 3, plan V2-3.3).

Pre-declared construction:
  * thresholds: per (fold_id, symbol), p10 / p90 of TRADE SIZE (floorsheet
    ``volume``, buyer-side counted) computed on TRAIN-FOLD session rows ONLY —
    the declared anti-leakage choice.
  * buckets: small (<p10), medium (p10-p90), large (>p90) by trade size.
  * per (fold_id, date, symbol, bucket): buyer-side HHI, top-3 buyer share,
    EoD-style contracted-order concentration (last ceil(5%) trades by
    contract_no DESC; 2023-02-16 excluded for ordering features, matching the
    v1 EoD definition).
  * ``MIN_BUCKET_TRADES = 5`` primary: concentration measures are mechanically
    1.0 when a bucket-day has 1 trade/1 buyer (23.7% of small-bucket days
    before the guard; mean small HHI 0.245 -> 0.122 at n>=5). The guard is
    declared in deviation #19 with 1/10 sensitivity.

The SQL is exposed as a template so tests can run it against an in-memory
DuckDB table with synthetic trades.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

BUCKETS = ("small", "medium", "large")
BUCKET_FEATURES = ("buyer_hhi", "top3_buyer_share", "eod_concentration")
BUCKET_COLS = tuple(f"{m}_{b}" for m in BUCKET_FEATURES for b in BUCKETS)
DEFECT_DATE = "2023-02-16"
MIN_BUCKET_TRADES = 5

TRADE_SIZE_SQL = """
WITH tr AS (
    SELECT sc.fold_id, sc.symbol, f.volume
    FROM sc
    JOIN {table} f
      ON CAST(f.date AS DATE) = sc.date AND f.symbol = sc.symbol
    WHERE sc.is_train
      AND f.volume IS NOT NULL AND f.volume > 0
      AND f.price > 0
      AND COALESCE(f.buyer_broker_id, '') <> ''
      AND COALESCE(f.seller_broker_id, '') <> ''
      AND COALESCE(f.symbol, '') <> ''
),
thr AS (
    SELECT fold_id, symbol,
           quantile_cont(volume, 0.10) AS p10,
           quantile_cont(volume, 0.90) AS p90,
           COUNT(*) AS n_train_trades
    FROM tr GROUP BY 1, 2
),
j AS (
    SELECT sc.fold_id, sc.date, sc.symbol, f.contract_no, f.volume,
           f.buyer_broker_id AS buyer, f.seller_broker_id AS seller
    FROM sc
    JOIN {table} f
      ON CAST(f.date AS DATE) = sc.date AND f.symbol = sc.symbol
    WHERE f.volume IS NOT NULL AND f.volume > 0
      AND f.price > 0
      AND COALESCE(f.buyer_broker_id, '') <> ''
      AND COALESCE(f.seller_broker_id, '') <> ''
      AND COALESCE(f.symbol, '') <> ''
),
b AS (
    SELECT j.*, t.p10, t.p90,
           CASE WHEN j.volume < t.p10 THEN 'small'
                WHEN j.volume > t.p90 THEN 'large'
                ELSE 'medium' END AS bucket
    FROM j JOIN thr t USING (fold_id, symbol)
),
tot AS (
    SELECT fold_id, date, symbol, bucket,
           SUM(volume) AS bucket_volume, COUNT(*) AS n_trades
    FROM b GROUP BY 1, 2, 3, 4
),
bv AS (
    SELECT fold_id, date, symbol, bucket, buyer, SUM(volume) AS bvol
    FROM b GROUP BY 1, 2, 3, 4, 5
),
hhi AS (
    -- exact integer ratio: SUM(bvol^2) / (SUM(bvol))^2.  Summing squared
    -- integer volumes is order-independent, so the artifact is byte-stable
    -- across DuckDB runs (summing float shares is not).
    SELECT bv.fold_id, bv.date, bv.symbol, bv.bucket,
           SUM(bv.bvol * bv.bvol)
             / (tot.bucket_volume * tot.bucket_volume) AS buyer_hhi
    FROM bv JOIN tot USING (fold_id, date, symbol, bucket)
    GROUP BY 1, 2, 3, 4, tot.bucket_volume
),
ranked AS (
    SELECT fold_id, date, symbol, bucket, buyer, bvol,
           ROW_NUMBER() OVER (PARTITION BY fold_id, date, symbol, bucket
                              ORDER BY bvol DESC) AS rk
    FROM bv
),
top3 AS (
    SELECT fold_id, date, symbol, bucket, SUM(bvol) AS top3_volume
    FROM ranked WHERE rk <= 3 GROUP BY 1, 2, 3, 4
),
eod_ranked AS (
    SELECT fold_id, date, symbol, bucket, volume, contract_no,
           ROW_NUMBER() OVER (PARTITION BY fold_id, date, symbol, bucket
                              ORDER BY contract_no DESC) AS rn_desc,
           COUNT(*) OVER (PARTITION BY fold_id, date, symbol, bucket) AS n_t
    FROM b
),
eod AS (
    SELECT fold_id, date, symbol, bucket,
           CASE WHEN CAST(date AS VARCHAR) = '{defect_date}' THEN NULL
                ELSE SUM(CASE WHEN rn_desc <= CAST(ceil(0.05 * n_t) AS BIGINT)
                              THEN volume ELSE 0 END) / SUM(volume) END
               AS eod_concentration
    FROM eod_ranked GROUP BY 1, 2, 3, 4
)
SELECT tot.fold_id, tot.date, tot.symbol, tot.bucket,
       tot.bucket_volume, tot.n_trades,
       hhi.buyer_hhi,
       top3.top3_volume / tot.bucket_volume AS top3_buyer_share,
       eod.eod_concentration,
       thr.p10, thr.p90, thr.n_train_trades
FROM tot
JOIN hhi USING (fold_id, date, symbol, bucket)
JOIN top3 USING (fold_id, date, symbol, bucket)
JOIN eod USING (fold_id, date, symbol, bucket)
JOIN thr USING (fold_id, symbol)
ORDER BY tot.fold_id, tot.date, tot.symbol, tot.bucket
"""


def build_trade_size_features(con, scores: pd.DataFrame,
                              table: str = "floorsheet_dedup",
                              defect_date: str = DEFECT_DATE,
                              min_trades: int = MIN_BUCKET_TRADES
                              ) -> pd.DataFrame:
    """Run the bucket aggregation; returns one row per (fold,date,symbol,bucket).

    Rows with ``n_trades < min_trades`` keep their volume/trade counts (for the
    descriptive summary) but the three concentration features are set NaN.
    """
    sc = scores[["date", "symbol", "fold_id", "is_train"]].copy()
    sc["date"] = pd.to_datetime(sc["date"]).dt.date
    if sc.duplicated(["fold_id", "date", "symbol"]).any():
        raise ValueError("scores has duplicate (fold_id,date,symbol) rows")
    con.register("sc", sc)
    try:
        df = con.execute(TRADE_SIZE_SQL.format(
            table=table, defect_date=defect_date)).fetchdf()
    finally:
        con.unregister("sc")
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["suppressed_min_trades"] = df["n_trades"] < int(min_trades)
    for c in BUCKET_FEATURES:
        df.loc[df["suppressed_min_trades"], c] = np.nan
    return df


def pivot_bucket_features(df: pd.DataFrame) -> pd.DataFrame:
    """Wide frame: one row per (fold,date,symbol), 3 buckets x 3 features."""
    w = df.pivot_table(index=["fold_id", "date", "symbol"],
                       columns="bucket", values=list(BUCKET_FEATURES),
                       aggfunc="first", dropna=False)
    w.columns = [f"{metric}_{bucket}" for metric, bucket in w.columns]
    w = w.reindex(columns=list(BUCKET_COLS))
    return w.reset_index()


def thresholds_table(df: pd.DataFrame) -> pd.DataFrame:
    return (df[["fold_id", "symbol", "p10", "p90", "n_train_trades"]]
            .drop_duplicates(["fold_id", "symbol"])
            .sort_values(["fold_id", "symbol"]).reset_index(drop=True))


def bucket_summary(df: pd.DataFrame,
                   min_trades: int = MIN_BUCKET_TRADES) -> pd.DataFrame:
    d = df.copy()
    d["suppressed"] = d["n_trades"] < int(min_trades)
    used = d[~d["suppressed"]]
    g = d.groupby("bucket").agg(
        bucket_days=("n_trades", "size"),
        trades=("n_trades", "sum"),
        volume=("bucket_volume", "sum"),
        suppressed_days=("suppressed", "sum"),
    )
    u = used.groupby("bucket").agg(
        used_days=("n_trades", "size"),
        median_trades=("n_trades", "median"),
        hhi_mean=("buyer_hhi", "mean"),
        hhi_median=("buyer_hhi", "median"),
        top3_mean=("top3_buyer_share", "mean"),
        eod_mean=("eod_concentration", "mean"),
        eod_median=("eod_concentration", "median"),
    )
    g = g.join(u, how="left")
    g["volume_share"] = g["volume"] / g["volume"].sum()
    g["trade_share"] = g["trades"] / g["trades"].sum()
    return g.reset_index()[["bucket", "bucket_days", "used_days",
                            "suppressed_days", "trades", "volume",
                            "volume_share", "trade_share", "median_trades",
                            "hhi_mean", "hhi_median", "top3_mean",
                            "eod_mean", "eod_median"]]


def success_criterion(ts: pd.DataFrame, base_bp: dict[str, float],
                      metrics: tuple[str, ...] = BUCKET_FEATURES,
                      tests: tuple[str, ...] = ("H7", "H8"),
                      spec: str = "primary") -> pd.DataFrame:
    """Large-vs-small bucket success rule for the Stage-3 trade-size analysis.

    Pre-declared rule: success iff |beta_large| >= |beta_small| AND
    p_large <= p_small (raw DK p).  Because this raw rule can pass on a
    large-bucket estimate whose sign contradicts the v1 effect, a **sign-aware**
    companion is co-reported (`success_criterion_sign_aware`), which additionally
    requires the large-bucket sign to match the v1 DK sign.  Both columns are
    reported; the sign-aware one is the honest adjudication (deviation #19).
    """
    out = []
    for metric in metrics:
        for hid in tests:
            d = ts[(ts.spec == spec) & (ts.metric == metric) &
                   (ts.test_id == hid)].set_index("bucket")
            if not {"small", "large"}.issubset(d.index):
                continue
            big, sml = d.loc["large"], d.loc["small"]
            mag = abs(big.beta_bp) >= abs(sml.beta_bp)
            p_ok = big.p_dk <= sml.p_dk
            v1_bp = float(base_bp[hid])
            sign_big = bool(np.sign(big.beta_bp) == np.sign(v1_bp))
            sign_sml = bool(np.sign(sml.beta_bp) == np.sign(v1_bp))
            out.append({
                "test_id": hid, "metric": metric,
                "beta_large_bp": big.beta_bp, "p_large": big.p_dk,
                "beta_small_bp": sml.beta_bp, "p_small": sml.p_dk,
                "sign_large_matches_v1": sign_big,
                "sign_small_matches_v1": sign_sml,
                "magnitude_large_ge_small": bool(mag),
                "p_large_le_small": bool(p_ok),
                "success_criterion": bool(mag and p_ok),
                "success_criterion_sign_aware": bool(mag and p_ok and sign_big),
            })
    return pd.DataFrame(out)
