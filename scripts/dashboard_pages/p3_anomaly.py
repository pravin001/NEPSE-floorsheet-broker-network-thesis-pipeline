"""Page 3 — OOS anomaly scoring & event study (EXP-0004a/EXP-0004e).
Serves anomaly_scoring_summary + event_study_summary + event_study_cars
+ cache:anomaly_test_rows (OOS rows only; train rows never shown here).
"""
# pages load by file path under dash Pages: make sibling _shared importable
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))


import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

from _shared import cache, table, regime_vrects, page_container

dash.register_page(__name__, name="3 · Anomaly Events & CARs", order=2,
                   path="/anomaly")

_summ = table("anomaly_scoring_summary.csv")
_es = table("event_study_summary.csv")
_cars = table("event_study_cars.csv")
_test = cache("anomaly_test_rows.csv")
_test["date"] = pd.to_datetime(_test["date"])

_fold_table = dbc.Table.from_dataframe(
    _summ.rename(columns={"score_threshold_q90_train": "train q90 thr."})[
        ["fold_id", "universe", "n_train_complete", "n_test_complete",
         "train q90 thr.", "n_test_events", "event_share_test",
         "test_dates"]],
    striped=True, size="sm")

_kpis = dbc.Row([
    dbc.Col(dbc.Card(dbc.CardBody([
        html.H5(f"{int(_test['is_event'].sum()):,} / {len(_test):,}"),
        html.Small("OOS events / scored rows (train-q90 thresholds, DC7)")])),
        width=4),
    dbc.Col(dbc.Card(dbc.CardBody([
        html.H5(f"{_test['is_event'].mean() * 100:.1f}%"),
        html.Small("OOS event share (q90 ⇒ ≈10% by construction)")])),
        width=4),
    dbc.Col(dbc.Card(dbc.CardBody([
        html.H5("ALL-CAR ≈ NULL"), html.Small(
            "overall +0.13% (p .569); market-model +0.19% (p .409); "
            "illiquid n=16 −2.45% (p .0018 caveat)")])), width=4),
], className="mb-3")


def _hist():
    fig = px.histogram(_test, x="anomaly_score", color="is_event",
                       nbins=70, barmode="overlay",
                       title="OOS anomaly-score distribution — events "
                             "(score ≥ fold's train-q90) overlay")
    fig.update_layout(height=360, legend=dict(orientation="h", y=-0.15),
                      margin=dict(l=10, r=10, t=42, b=40))
    return fig


def _event_timeline():
    ev = _test.loc[_test["is_event"]]
    daily = ev.groupby("date").size().reset_index(name="n_events")
    fig = px.bar(daily, x="date", y="n_events",
                 color_discrete_sequence=["#c0392b"],
                 title="Events per session — OOS anomaly events "
                       "(bubble-era concentration; descriptive)")
    fig = regime_vrects(fig)
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=42, b=6))
    return fig


def _car_bars():
    agg = (_cars.groupby("method")["car"]
           .agg(["mean", "count"]).reset_index())
    fig = px.bar(agg, x="method", y="mean",
                 color_discrete_sequence=["#2471a3"],
                 title="Mean CAR (t−5..t+5) by event-study method — "
                       "null overall; small-n market-adjusted caveat",
                 text_auto=".2%")
    fig.update_layout(height=330, yaxis_title="mean CAR",
                      margin=dict(l=10, r=10, t=42, b=6))
    fig.update_traces(textposition="outside")
    return fig


def _es_table() -> html.Table:
    head = html.Thead(html.Tr([html.Th(m) for m in
                               ["method", "n", "mean CAR", "median",
                                "p"]]))
    rows = [html.Tr([html.Td(r["method"]),
                     html.Td(f"{int(r['n']):,}"),
                     html.Td(f"{r['mean']:+.4f}"),
                     html.Td(f"{r['median']:+.4f}"),
                     html.Td(f"{r['t_p']:.4f}")])
             for _, r in _es.iterrows()]
    return html.Table([head, html.Tbody(rows)], className="table-sm")


def layout() -> html.Div:
    return page_container(
        "Out-of-sample anomaly events & event study — IF walk-forward "
        "scores (EXP-0004a) + CAR analysis (EXP-0004e)",
        _kpis,
        dbc.Row([
            dbc.Col(dcc.Graph(figure=_hist()), width=7),
            dbc.Col([html.H6("Event-study summary"),
                     _es_table(),
                     dcc.Graph(figure=_car_bars())], width=5),
        ]),
        dcc.Graph(figure=_event_timeline()),
        html.H6("Fold diagnostics (anchored, 4 folds; train rows are "
                "EDA-only and NOT shown)"),
        _fold_table,
        html.P("Headline context: the anomaly score has NO OOS "
               "forward-return content — placebo shares H2 0.800 / H3 0.640 "
               "≈ random (page 4), and ALL-events CAR is null. Events "
               "label unusual broker-graph behaviour, not profitable "
               "signals.", className="text-muted"),
    )
