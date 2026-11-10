"""Shared loaders for the Phase-6 dashboard pages (extracts-only contract).

Every number shown by the dashboard is either
  (a) read from `outputs/tables/*.csv` — REGISTER artifacts of record [REAL],
  (b) read from `data/processed/dashboard_cache/*.csv` — compact snapshot
      built once by `scripts/build_dashboard_cache.py`, or
  (c) a plain descriptive aggregate (mean/median/p90) of the frames in (a)/(b)
      computed at request time without any statistics claim (R11).

The app NEVER opens DuckDB or a >10 MB parquet at runtime.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

TABLES = ROOT / "outputs/tables"
CACHE = ROOT / "data/processed/dashboard_cache"

DEFECT = "2023-02-16"
REGIME_END_BUBBLE = "2022-12-31"

FEATURE_METRICS = [
    ("buyer_hhi", "Buyer-broker HHI (concentration)"),
    ("seller_hhi", "Seller-broker HHI"),
    ("self_loop_ratio", "Self-loop volume ratio"),
    ("end_of_day_concentration", "End-of-day concentration (5%)"),
    ("reciprocity", "Reciprocity volume (buyer=seller pair share)"),
    ("density", "Day-graph density"),
    ("max_betweenness", "Max betweenness"),
    ("core_periphery_coeff", "Core-periphery coefficient"),
    ("top_3_buyer_share", "Top-3 buyer share"),
]

VICTIM_HIGHLIGHT = ["H4", "H6", "H7", "H8", "H10"]


def table(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLES / name)


def cache(name: str) -> pd.DataFrame:
    return pd.read_csv(CACHE / name)


def regime_vrects(fig):
    """Shade the bubble era 2021-01..2022-12-31 on a date-axis figure."""
    import plotly.graph_objects as go
    fig.add_vrect(x0="2021-01-01", x1=REGIME_END_BUBBLE,
                  fillcolor="rgba(230, 126, 34, 0.10)", line_width=0,
                  annotation_text="bubble era (descriptive)",
                  annotation_position="top left",
                  annotation_font_size=10)
    fig.add_vline(x=DEFECT, line_width=1, line_dash="dot",
                  line_color="#c0392b",
                  annotation_text="2023-02-16 contract_no_defect "
                                  "(ordering features excluded)",
                  annotation_position="bottom right",
                  annotation_font_size=10)
    return fig


def descriptives(s: pd.Series) -> pd.DataFrame:
    s = pd.to_numeric(s, errors="coerce").dropna()
    return pd.DataFrame({
        "n": [len(s)], "mean": [s.mean()], "median": [s.median()],
        "p90": [s.quantile(0.90)], "sd": [s.std(ddof=0)],
        "min": [s.min()], "max": [s.max()],
    }).round(6)


def footer_note() -> str:
    from dash import html
    return html.Div(
        "Extracts-only build (Phase 6): no DuckDB or full-corpus reads at "
        "runtime — serves dashboard_cache snapshots + register artifacts in "
        "outputs/tables. Every plotted number traces to EXP-0002a–e, "
        "EXP-0003a–d, EXP-0004a–e, EXP-0005a–g [REAL]; descriptive-only per "
        "R11. Thesis: 'Broker Networks, Concentration, and Market Integrity "
        "in a Frontier Exchange'.",
        style={"fontSize": 11, "color": "#777", "marginTop": 30})


def page_container(title: str, *children):
    from dash import html
    return html.Div([
        html.H2(title, style={"marginTop": 8, "marginBottom": 4}),
        html.Hr(style={"margin": "4px 0 14px"}),
        *children,
        footer_note(),
    ], className="page-body")
