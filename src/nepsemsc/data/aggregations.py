"""Module 1 aggregation SQL — daily concentration + broker-pair edges.

All heavy aggregation happens in DuckDB; NetworkX receives only aggregated
(pair, volume) edges (brief: NEVER raw trades into the graph builder).
"""
from __future__ import annotations

# Per (symbol, date) concentration features. contract_no ordering is AFTER
# sort (the ROW_NUMBER window sorts explicitly — file order is not trusted).
DAILY_CONCENTRATION_SQL = """
WITH vol AS (
    SELECT date, symbol, SUM(volume) AS total_volume, COUNT(*) AS total_trades,
           COUNT(DISTINCT buyer_broker_id) AS unique_buyers,
           COUNT(DISTINCT seller_broker_id) AS unique_sellers
    FROM floorsheet_raw
    GROUP BY 1, 2
),
buy AS (
    SELECT r.date, r.symbol, r.buyer_broker_id AS broker, SUM(r.volume) AS bv
    FROM floorsheet_raw r GROUP BY 1, 2, 3
),
sell AS (
    SELECT r.date, r.symbol, r.seller_broker_id AS broker, SUM(r.volume) AS sv
    FROM floorsheet_raw r GROUP BY 1, 2, 3
),
buy_hhi AS (
    SELECT b.date, b.symbol, SUM(pow(b.bv / v.total_volume, 2)) AS buyer_hhi
    FROM buy b JOIN vol v USING (date, symbol) GROUP BY 1, 2
),
sell_hhi AS (
    SELECT s.date, s.symbol, SUM(pow(s.sv / v.total_volume, 2)) AS seller_hhi
    FROM sell s JOIN vol v USING (date, symbol) GROUP BY 1, 2
),
self_loop AS (
    SELECT date, symbol,
           SUM(CASE WHEN buyer_broker_id = seller_broker_id THEN volume ELSE 0 END) AS selfloop_vol,
           SUM(volume) AS total_volume
    FROM floorsheet_raw GROUP BY 1, 2
),
top_buy AS (
    SELECT date, symbol, SUM(bv) AS top3_bv
    FROM (
        SELECT date, symbol, bv,
               ROW_NUMBER() OVER (PARTITION BY date, symbol ORDER BY bv DESC) AS rk
        FROM buy
    ) WHERE rk <= 3 GROUP BY 1, 2
),
top_sell AS (
    SELECT date, symbol, SUM(sv) AS top3_sv
    FROM (
        SELECT date, symbol, sv,
               ROW_NUMBER() OVER (PARTITION BY date, symbol ORDER BY sv DESC) AS rk
        FROM sell
    ) WHERE rk <= 3 GROUP BY 1, 2
),
ranked AS (
    SELECT date, symbol, volume,
           ROW_NUMBER() OVER (PARTITION BY date, symbol ORDER BY contract_no DESC) AS rn_desc,
           COUNT(*) OVER (PARTITION BY date, symbol) AS n_t
    FROM floorsheet_raw
),
eod AS (
    SELECT date, symbol,
           SUM(CASE WHEN rn_desc <= CAST(ceil(0.05 * n_t) AS BIGINT) THEN volume ELSE 0 END)
             / SUM(volume) AS end_of_day_concentration
    FROM ranked GROUP BY 1, 2
)
SELECT v.date, v.symbol, v.total_volume, v.total_trades,
       v.unique_buyers, v.unique_sellers,
       COALESCE(bh.buyer_hhi,   NULL) AS buyer_hhi,
       COALESCE(sh.seller_hhi,  NULL) AS seller_hhi,
       COALESCE(sl.selfloop_vol / NULLIF(sl.total_volume, 0), 0.0) AS self_loop_volume_ratio,
       COALESCE(e.end_of_day_concentration, NULL) AS end_of_day_concentration,
       COALESCE(tb.top3_bv / v.total_volume, NULL) AS top_3_buyer_share,
       COALESCE(ts.top3_sv / v.total_volume, NULL) AS top_3_seller_share
FROM vol v
LEFT JOIN buy_hhi bh USING (date, symbol)
LEFT JOIN sell_hhi sh USING (date, symbol)
LEFT JOIN self_loop sl USING (date, symbol)
LEFT JOIN eod e USING (date, symbol)
LEFT JOIN top_buy tb USING (date, symbol)
LEFT JOIN top_sell ts USING (date, symbol)
ORDER BY v.symbol, v.date
"""

# Broker-pair daily volume = the weighted directed edge list for NetworkX.
BROKER_PAIR_DAILY_SQL = """
SELECT date, symbol, buyer_broker_id, seller_broker_id,
       SUM(volume) AS pair_volume,
       COUNT(*) AS pair_trades,
       SUM(amount) AS pair_amount
FROM floorsheet_raw
GROUP BY 1, 2, 3, 4
ORDER BY date, symbol, pair_volume DESC
"""
