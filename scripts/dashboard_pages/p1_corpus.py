"""Page 1 — Corpus & provenance (calendar coverage, per-source load,
top-12 extract load, source/licence provenance). Serves corpus_daily_summary,
cache:extract_monthly_summary, cache:calendar.
"""
# pages load by file path under dash Pages: make sibling _shared importable
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))


import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from _shared import cache, table, regime_vrects, page_container

dash.register_page(__name__, path="/", name="1 · Corpus & Provenance",
                   order=0)

SOURCES = [
    ("Kaggle viking303 NEPSE historical floorsheet (2021–2023)", "CC0",
     "PRIMARY 2021-01-03 → 2023-12-28 (708/710 sessions)"),
    ("socrateai daily floorsheets (2024)", "MIT",
     "PRIMARY 2024 (232/232 sessions); SV1(b) adoption"),
    ("tier1_kaggle OHLCV (100 scrips)", "licence pending student UI check",
     "OHLCV/outcome panel (EXP-0002d); figures RESTRICTED until confirmed"),
    ("tier2 SamirWagle prices", "attribution",
     "OHLCV gap-fill only (overlap Δclose median 0.0000%)"),
    ("NEPSE composite index (menaceXnadin)", "unstated_in_repo",
     "SECONDARY: regime shading/benchmark only (R8); swap-able"),
]

_daily_summary = table("corpus_daily_summary.csv")
_monthly = cache("extract_monthly_summary.csv")
_cal = cache("calendar.csv")
_gaps = sorted(_cal.loc[~_cal["in_corpus"], "date"].tolist())

_kpis = dbc.Row([
    dbc.Col(dbc.Card(dbc.CardBody([
        html.H5(f"{_daily_summary['n_rows'].sum():,}"),
        html.Small("raw floorsheet rows (57,927,926 total in DuckDB — "
                   "extracts-only dashboard)")])), width=3),
    dbc.Col(dbc.Card(dbc.CardBody([
        html.H5("938 / 940"), html.Small("corpus sessions (99.79%)")])),
        width=3),
    dbc.Col(dbc.Card(dbc.CardBody([
        html.H5(f"{_monthly['n_trades'].sum():,}"),
        html.Small("top-12 extract rows served here")])), width=3),
    dbc.Col(dbc.Card(dbc.CardBody([
        html.H5("530 / 12"), html.Small(
            "symbols in corpus / in these extracts")])), width=3),
], className="mb-3")

_src_table = dbc.Table.from_dataframe(
    pd.DataFrame(SOURCES, columns=["source", "licence", "role / scope"]),
    striped=True, size="sm")


def chart_corpus_daily():
    fig = px.line(_daily_summary, x="date", y="n_rows", color="source",
                  title="Raw floorsheet rows per session by source "
                        "(kaggle 2021-23 · socrateai 2024)")
    fig = regime_vrects(fig)
    fig.update_layout(height=340, legend=dict(orientation="h", y=-0.15),
                      margin=dict(l=10, r=10, t=42, b=50))
    return fig


def chart_calendar():
    fig = px.strip(_cal, x="date", y="regime", color="in_corpus",
                   category_orders={"regime": ["bubble 2021-22",
                                               "normal 2023-24"]},
                   title="DC3 window calendar — 940 sessions"
                         " (known gaps: 2021-09-01, 2023-11-27)")
    fig = regime_vrects(fig)
    fig.update_layout(height=230, margin=dict(l=10, r=10, t=42, b=6))
    fig.update_yaxes(showgrid=False)
    fig.update_traces(marker=dict(size=3))
    return fig


@dash.callback(Output("p1-load-chart", "figure"),
               Input("p1-metric", "value"))
def update_load_chart(metric):
    if metric == "sum_volume":
        y, ttl = "sum_volume", "Monthly extract VOLUME per symbol"
    else:
        y, ttl = "n_trades", "Monthly extract TRADE COUNT per symbol"
    fig = px.line(_monthly, x="month", y=y, color="symbol",
                  title=ttl + " (log y; descriptive)")
    fig.update_yaxes(type="log")
    fig.update_layout(height=400, legend=dict(orientation="h", y=-0.3),
                      margin=dict(l=10, r=10, t=42, b=70))
    return fig


def layout() -> html.Div:
    return page_container(
        "Corpus & provenance — what was ingested, from where, under which "
        "licence",
        _kpis,
        dcc.Graph(figure=chart_corpus_daily()),
        dcc.Graph(figure=chart_calendar()),
        html.H6("Top-12 extract load (data/raw/floorsheet/<SYM>/<YYYY-MM>"
                ".csv — 576 files)"),
        dcc.Dropdown(
            id="p1-metric",
            options=[{"label": "Trade count", "value": "n_trades"},
                     {"label": "Volume", "value": "sum_volume"}],
            value="n_trades", clearable=False, style={"width": 280}),
        dcc.Graph(id="p1-load-chart"),
        html.H6("Source / licence / role (ai_use_policy table)"),
        _src_table,
        html.Div([html.B("Documented gaps: "),
                  ", ".join(_gaps) or "none",
                  " — non-imputable; no source in any verified archive."],
                 className="mt-2"),
    )
