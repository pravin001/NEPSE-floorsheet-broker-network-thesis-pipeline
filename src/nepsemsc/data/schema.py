"""Floorsheet schema — alias mapping, normalization, validation.

Source schema (socrateai archive, one CSV per day):
  transaction,symbol,buyer,seller,quantity,rate,amount,date

Buyer/seller broker NAMES are NOT in the archive — broker ids only; names are
optional columns (obtainable from the NEPSE broker list but not required for
any analysis: all network metrics key on ids).

CRITICAL (sibling-project validated): raw file order is NOT execution order —
reverse-pair rate up to 0.86 in 2024. ALWAYS sort by `transaction` before any
ordering-dependent statistic (end-of-day concentration, SV6).
"""
from __future__ import annotations

import pandas as pd

# raw column → canonical column
SOURCE_ALIASES: dict[str, str] = {
    "transaction": "contract_no",
    "symbol": "symbol",
    "buyer": "buyer_broker_id",
    "seller": "seller_broker_id",
    "quantity": "volume",
    "rate": "price",
    "amount": "amount",
    "date": "date",
    # optional name columns if present in other archives
    "buyer_broker_name": "buyer_broker_name",
    "seller_broker_name": "seller_broker_name",
    # legible long variants
    "buyer_broker_id": "buyer_broker_id",
    "seller_broker_id": "seller_broker_id",
    "contract_no": "contract_no",
    "volume": "volume",
    "price": "price",
}

CORE_COLUMNS = [
    "date",
    "contract_no",
    "symbol",
    "price",
    "volume",
    "amount",
    "buyer_broker_id",
    "seller_broker_id",
]

OPTIONAL_COLUMNS = ["buyer_broker_name", "seller_broker_name"]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map aliases → canonical names (case/space tolerant) and zero-pad ids."""
    out = df.copy()
    out.columns = [str(c).strip().lower().replace(" ", "_") for c in out.columns]
    out = out.rename(columns={k: v for k, v in SOURCE_ALIASES.items() if k in out.columns})
    for col in ("buyer_broker_id", "seller_broker_id"):
        if col in out.columns:
            # ids are issued as numeric codes ('01'..'99' plus a few 3-digit);
            # keep as zero-padded 2-digit strings for stable joining
            num = pd.to_numeric(out[col], errors="coerce")
            out[col] = num.map(lambda v: "" if pd.isna(v) else f"{int(v):02d}")
    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date
    if "contract_no" in out.columns:
        out["contract_no"] = pd.to_numeric(out["contract_no"], errors="coerce").astype("Int64")
    for num_col in ("volume", "price", "amount"):
        if num_col in out.columns:
            out[num_col] = pd.to_numeric(out[num_col], errors="coerce")
    return out


def validate_schema(df: pd.DataFrame, require_broker_names: bool = False) -> tuple[bool, list[str]]:
    """Return (schema_ok, problems). Core columns must exist and be non-identical."""
    problems: list[str] = []
    for col in CORE_COLUMNS:
        if col not in df.columns:
            problems.append(f"missing core column: {col}")
    if require_broker_names:
        for col in OPTIONAL_COLUMNS:
            if col not in df.columns:
                problems.append(f"missing optional column: {col}")
    if not problems:
        if (df["volume"] < 0).any():
            problems.append("negative volume")
        if (df["price"] <= 0).any():
            problems.append("non-positive price")
        if df["date"].isna().any():
            problems.append("unparseable date")
    return (len(problems) == 0), problems
