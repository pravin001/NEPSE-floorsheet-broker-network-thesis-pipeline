# Data schema (floorsheet_raw, DuckDB) — v1

| column | duckdb type | source col (archive) | notes |
|---|---|---|---|
| date | DATE | date | Asia/Kathmandu trading session (DC4) |
| contract_no | BIGINT | transaction | daily-global trade sequence id |
| symbol | VARCHAR | symbol | upper-trimmed |
| price | DOUBLE | rate | |
| volume | BIGINT | quantity | shares |
| amount | DOUBLE | amount | rs |
| buyer_broker_id | VARCHAR | buyer | zero-padded 2-digit id string |
| seller_broker_id | VARCHAR | seller | zero-padded 2-digit id string |

Optional (absent in archive, for other sources): buyer/seller_broker_name.

CRITICAL facts archived from prior-project validation:
* file row order is NOT execution order (reverse-pair rate 0.79–0.86 in 2024) →
  ALWAYS sort by contract_no before ordering statistics;
* contract_no is daily-global → per-(symbol,date) gaps are expected and
  documented; monotonic-after-sort is asserted per (symbol, date).
