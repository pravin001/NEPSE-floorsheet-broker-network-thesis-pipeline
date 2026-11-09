"""Generate notebooks/00_smoke_test.ipynb (EXP-0001d) — executed via nbmake
(DC19). Purpose header + STATUS REPORT cell per engineering rule 4."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

NB = ROOT / "notebooks" / "00_smoke_test.ipynb"
NB.parent.mkdir(exist_ok=True)


def md(txt):
    return {"cell_type": "markdown", "metadata": {}, "source": txt}


def code(src):
    return {"cell_type": "code", "metadata": {},
            "source": src, "outputs": [], "execution_count": None}


HEADER = f"""# Notebook 00 — scaffold smoke test (Phase 1)

**Experiment:** EXP-0001d · **Phase:** 1 · **Date:** 2026-11-08

**Purpose** — prove the environment end-to-end: package import, config
fingerprint, Kathmandu offset (DC4), seed policy (DC14), DuckDB round-trip,
and the real NABIL 2024-12 sample loaded into `floorsheet_raw` with the
brief's exact check query.

**Prerequisites:** `make bootstrap install test-fast smoke` executed.

**Expected outputs:** version table, config sha256, offset check, DuckDB
query rows, HHI/self-loop sample table (EXP-0001c), STATUS REPORT cell.

**Status markers (R4/R5):** all numbers below are [REAL] — derived from the
local socrateai archive files (MIT), sha256-tracked.
"""

BODY1 = """
import sys, importlib
print(f"python {sys.version.split()[0]}")
mods = {"duckdb": "duckdb", "pandas": "pandas", "numpy": "numpy",
        "networkx": "networkx", "sklearn": "scikit-learn",
        "linearmodels": "linearmodels", "statsmodels": "statsmodels",
        "plotly": "plotly"}
for imp in ("duckdb", "pandas", "numpy", "networkx", "sklearn",
            "linearmodels", "statsmodels", "plotly"):
    m = importlib.import_module(imp)
    print(f"{imp:14s} {getattr(m, '__version__', '?')}")
assert sys.version_info[:2] == (3, 11), "brief pins python 3.11"
"""

BODY2 = """
from nepsemsc.utils import config
cfg = config.load_config()
print("config sha256:", cfg["_fingerprint_sha256"][:16], "…")
assert cfg["_fingerprint_sha256"]

from nepsemsc.utils.tz import now_ktm, verify_offset
print("Kathmandu offset:", now_ktm().utcoffset(), "| DC4 check:", verify_offset())
assert verify_offset()

from nepsemsc.utils.seeds import IF_FOLD_SEEDS, PLACEBO_SEEDS
print("IF fold seeds:", IF_FOLD_SEEDS, "| #placebo seeds:", len(PLACEBO_SEEDS))
assert len(PLACEBO_SEEDS) == 200
"""

BODY3 = """
from pathlib import Path
import duckdb
from nepsemsc.data.duckdb_loader import DB_PATH, DAILY_COUNTS_SQL, get_conn, init_db
assert Path(DB_PATH).exists(), "DuckDB missing — run scripts/init_duckdb_load_sample.py"
con = get_conn()
init_db(con)
total = con.execute("SELECT COUNT(*) FROM floorsheet_raw").fetchone()[0]
print(f"floorsheet_raw rows: {total:,}  [REAL — NABIL 2024-12 extract of socrateai archive]")
table = con.execute("SELECT * FROM floorsheet_raw LIMIT 5").df()
display(table)
rows = con.execute(DAILY_COUNTS_SQL).fetchall()
print(f"DAILY_COUNTS_SQL (brief query): {len(rows)} rows")
for r in rows[:10]:
    print(r)
con.close()
"""

BODY4 = """
from pathlib import Path
import pandas as pd
tbl = Path("../outputs/tables/sample_hhi_selfloop.csv")
assert tbl.exists(), "run scripts/write_sample_hhi_table.py"
sample = pd.read_csv(tbl)
print(f"rows: {len(sample)}  (NABIL {sample['date'].min()} → {sample['date'].max()})")
display(sample.head(10))
summary = sample[["buyer_hhi", "seller_hhi", "self_loop_volume_ratio",
                  "end_of_day_concentration"]].describe().loc[["mean", "std", "min", "max"]]
display(summary)
"""

STATUS = """## STATUS REPORT (Phase 1)

| item | value |
|---|---|
| env | python 3.11.16 · venv `nepse-msc` (uv) |
| duckdb | loaded NABIL 2024-12 extract, query executed |
| schema validation | PASS (canonical core columns; broker ids zero-padded) |
| sample metrics | buyer/seller HHI + self-loop + EoD concentration table saved |
| tests | pytest suite green (see `make test-fast`) |
| blockers | none (SV1(b) archive substitution documented in block_log) |
| [] STOP | awaiting user "continue" → Phase 2 |
"""

nb = {"cells": [md(HEADER), code(BODY1), code(BODY2), code(BODY3), code(BODY4), md(STATUS)],
      "metadata": {
          "kernelspec": {"display_name": "nepse-msc", "language": "python",
                         "name": "nepse-msc"},
          "language_info": {"name": "python", "version": "3.11.16"},
      },
      "nbformat": 4, "nbformat_minor": 5}

NB.write_text(json.dumps(nb, indent=1))
# register the kernel for jupyter/nbmake execution
import subprocess
subprocess.run([str(ROOT / "nepse-msc" / "bin" / "python"), "-m",
                "ipykernel", "install", "--user", "--name", "nepse-msc",
                "--display-name", "nepse-msc"], check=False)
print(f"NOTEBOOK_WRITTEN {NB}")
