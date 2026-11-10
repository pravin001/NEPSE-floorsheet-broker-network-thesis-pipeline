"""PHASE 6 — Dash dashboard app (4 pages, EXTRACTS-ONLY).

Run:  nepse-msc/bin/python scripts/dashboard_app.py   →  http://127.0.0.1:8050

Pages (scripts/dashboard_pages/, dash.Pages):
  /            1 · Corpus & Provenance   — calendar, per-source load, licences
  /features    2 · Daily Network Features— top-12 explorer, regime shading
  /anomaly     3 · Anomaly Events & CARs — OOS scores/events + event study
  /inference   4 · Inference & Robustness— grid, battery survival, LOO, eras

Contract: the app serves ONLY (i) data/processed/dashboard_cache/*.csv
(small snapshots built by scripts/build_dashboard_cache.py) and (ii)
outputs/tables/*.csv (register artifacts of record). No DuckDB, no
full-corpus reads at runtime; every number traces to a registered
experiment [REAL]; descriptive aggregates only on page 2 (R11).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import dash
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, html

PAGE_COLOR_ACTIVE = "#1f618d"


def create_app() -> Dash:
    app = Dash(
        __name__, use_pages=True,
        pages_folder="dashboard_pages",
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="NEPSE Broker-Network Thesis Dashboard (extracts-only)",
        meta_tags=[{"name": "viewport",
                    "content": "width=device-width, initial-scale=1"}],
        suppress_callback_exceptions=True,
    )

    nav_links = []
    for page in sorted(dash.page_registry.values(), key=lambda p: p["order"]):
        nav_links.append(dbc.NavItem(dbc.NavLink(
            page["name"], href=page["path"], active="exact")))

    app.layout = html.Div([
        dbc.Navbar(dbc.Container([
            html.A(
                dbc.Row([dbc.Col(
                    html.Span("NEPSE broker-network microstructure — "
                              "thesis dashboard",
                              className="ms-2 navbar-brand"))],
                        align="center", className="g-0"),
                href="/", style={"textDecoration": "none",
                                 "color": "inherit"}),
            dbc.Nav(nav_links, navbar=True, className="ms-auto")
        ]), color="dark", dark=True, className="mb-3"),
        dbc.Container([dash.page_container], fluid=True,
                      className="pb-4"),
    ], className="app-body")

    return app


app = create_app()
server = app.server

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=False)
