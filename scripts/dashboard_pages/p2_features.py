"""Page 2 — Daily network features explorer for the 12 extract symbols
(cache:top12_daily_features). Descriptive only (R11); regime shading;
2023-02-16 defect-day EoD exclusion honoured at build time.
"""
# pages load by file path under dash Pages: make sibling _shared importable
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))


import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px

from _shared import (cache, regime_vrects, page_container, descriptives,
                     FEATURE_METRICS)

dash.register_page(__name__, name="2 · Daily Network Features", order=1,
                   path="/features")

_feats = cache("top12_daily_features.csv")
_SYMBOLS = sorted(_feats["symbol"].unique())
_METRIC_OPTS = [{"label": lbl, "value": col} for col, lbl in FEATURE_METRICS]


@dash.callback(
    Output("p2-metric-info", "children"),
    Output("p2-chart", "figure"),
    Output("p2-stats", "children"),
    Input("p2-symbol", "value"),
    Input("p2-metric", "value"),
)
def update(symbol, metric):
    g = _feats.loc[_feats["symbol"] == symbol]
    lbl = dict(FEATURE_METRICS)[metric]
    fig = px.line(g, x="date", y=metric,
                  title=f"{symbol} — {lbl} (daily, descriptive; "
                        f"{int(g[metric].notna().sum()):,}/{len(g):,} rows)")
    fig = regime_vrects(fig)
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=42, b=6))

    info = html.Div([
        html.Span("rows: ", className="text-muted"),
        f"{len(g):,} (sessions for symbol) · ",
        html.Span("source mix: "),
        ", ".join(f"{s} = {int(n):,}"
                  for s, n in g.groupby("fs_source")["date"].size().items())
    ])

    d = descriptives(g[metric]).iloc[0]
    stats = dbc.Card(dbc.CardBody(dbc.Row([
        dbc.Col([html.Small("mean"), html.H6(f"{d['mean']:.4f}")]),
        dbc.Col([html.Small("median"), html.H6(f"{d['median']:.4f}")]),
        dbc.Col([html.Small("p90"), html.H6(f"{d['p90']:.4f}")]),
        dbc.Col([html.Small("sd"), html.H6(f"{d['sd']:.4f}")]),
        dbc.Col([html.Small("min–max"),
                 html.H6(f"{d['min']:.3g}–{d['max']:.3g}")]),
        dbc.Col([html.Small("n"), html.H6(f"{int(d['n']):,}")]),
    ])))

    return info, fig, stats


def layout() -> html.Div:
    defaults = dict(symbol=_SYMBOLS[0], metric=FEATURE_METRICS[0][0])
    return page_container(
        "Daily network features — top-12 extract symbols (bubble era shaded; "
        "dot = 2023-02-16 contract_no_defect, EoD feeld excluded there)",
        html.P("Descriptive only (R11): no inference on this page. "
               "corpus-scale inference lives on page 4 "
               "(EXP-0004b/d + EXP-0005 battery).",
               className="text-muted"),
        dbc.Row([
            dbc.Col(dcc.Dropdown(id="p2-symbol", options=_SYMBOLS,
                                 value=defaults["symbol"], clearable=False),
                    width=3),
            dbc.Col(dcc.Dropdown(id="p2-metric", options=_METRIC_OPTS,
                                 value=defaults["metric"], clearable=False),
                    width=7),
        ]),
        html.Div(id="p2-metric-info", className="text-muted small mb-1"),
        dcc.Graph(id="p2-chart"),
        html.Div(id="p2-stats", className="mt-2"),
    )
