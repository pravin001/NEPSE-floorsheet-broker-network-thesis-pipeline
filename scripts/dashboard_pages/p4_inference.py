"""Page 4 — Inference grid + robustness battery (EXP-0004b/d, EXP-0005a–g).
All numbers straight from register artifacts; nothing recomputed.
"""
# pages load by file path under dash Pages: make sibling _shared importable
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))


import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from _shared import table, page_container

dash.register_page(__name__, name="4 · Inference & Robustness", order=3,
                   path="/inference")

_GRID = table("hypothesis_grid_results.csv")
_REG = table("regime_split_results.csv")
_SURV = table("robustness_headline_survival.csv")
_LOO = table("robustness_loo_stability.csv")
_DB = table("robustness_drop_bubble_grid.csv")
_T5 = table("robustness_top5_external_grid.csv")

# ---------- grid table (10 rows of record) -----------------------------------
_fmt = _GRID.copy()
_fmt["bh"] = np.where(_fmt["bh_sig_q10"],
                      "✓ q≤.10", "—")
_fmt["fm"] = np.where(_fmt["p_fm"].notna(),
                      _fmt["p_fm"].map("{:.4f}".format), "skipped")
_fmt["plcb"] = np.where(_fmt["placebo_share"].notna(),
                        _fmt["placebo_share"].map("{:.3f}".format), "n/a")
_fmt["sign"] = np.where(_fmt["sign_agrees"].notna(),
                        np.where(_fmt["sign_agrees"], "agrees",
                                 "OPPOSITE"), "amb")
_cols_show = ["test_id", "feature", "outcome", "predicted_sign", "n_obs",
              "bp", "p_dk", "bh", "fm", "plcb", "sign", "headline_significant"]
_fmt = _fmt[_cols_show].rename(columns={
    "predicted_sign": "pred. sign", "n_obs": "N", "p_dk": "DK p",
    "bh": "BH", "fm": "FM p", "plcb": "placebo", "sign": "sign vs decl.",
    "headline_significant": "headline"})
_fmt["bp"] = _fmt["bp"].map("{:+.2f}".format)
_grid_table = dbc.Table.from_dataframe(_fmt, striped=True, size="sm",
                                       className="table-hover")


def _survival_matrix() -> go.Figure:
    """variant × headline: cell value = BH-pass; hover shows p_dk."""
    surv = _SURV.copy()
    heads = ["H4", "H6", "H7", "H8", "H10"]
    surv["bh"] = pd.to_numeric(surv["bh_pass"], errors="coerce")
    variant_order = ["base t+1 (EXP-0004b)", "t+2", "t+3", "t+5",
                     "eod 10%", "eod 1%", "drop_bubble", "top5_external",
                     "loo_full_sample"]
    mat = (surv[surv["test_id"].isin(heads)]
           .pivot_table(index="variant", columns="test_id", values="bh",
                        aggfunc="first"))
    pmat = (surv[surv["test_id"].isin(heads)]
            .pivot_table(index="variant", columns="test_id", values="p_dk",
                         aggfunc="first"))
    mat = mat.reindex(index=[v for v in variant_order if v in mat.index],
                      columns=heads)
    z = mat.to_numpy(dtype=float)
    fig = go.Figure(go.Heatmap(
        z=z, x=mat.columns, y=mat.index,
        colorscale=[[0, "#fadbd8"], [1, "#d5f5e3"]], zmin=0, zmax=1,
        showscale=False, hovertext=pmat.reindex(index=mat.index,
                                                columns=mat.columns)
                .map(lambda p: "" if pd.isna(p) else f"p={p:.4f}").values,
        hovertemplate="%{y} · %{x}<br>%{hovertext}<extra></extra>",
        xgap=2, ygap=2))
    fig.update_layout(
        title="Headline survival across battery variants (green = "
              "BH q≤0.10 pass; grey/void = fail or not applicable — eod "
              "cells are sign-concordance flags by pre-declaration)",
        height=380, margin=dict(l=10, r=10, t=60, b=6))
    return fig


def _loo_fig() -> go.Figure:
    loo = _LOO.loc[_LOO["test_id"].isin(["H4", "H6", "H7", "H8", "H10"])]
    fig = go.Figure()
    for _, r in loo.iterrows():
        lo_b, hi_b = r["beta_min"] * 1e4, r["beta_max"] * 1e4
        fig.add_trace(go.Scatter(
            x=[lo_b, hi_b], y=[r["test_id"], r["test_id"]], mode="lines",
            line=dict(width=10, color="#b8a6d9"), showlegend=False,
            name=r["test_id"]))
        decl = {"H4": "ret (decl. −)", "H6": "ret (amb.)",
                "H7": "|ret| (+)", "H8": "ret (decl. −)",
                "H10": "|ret| (+)"}[r["test_id"]]
        fig.add_trace(go.Scatter(
            x=[r["beta_full"] * 1e4], y=[r["test_id"]], mode="markers+text",
            text=[f"{r['beta_full'] * 1e4:+.2f} bp"],
            textposition="middle right",
            marker=dict(size=11, symbol="diamond", color="#6c3483"),
            showlegend=False,
            hovertemplate=(f"{r['test_id']} ({decl})<br>full "
                           f"{r['beta_full'] * 1e4:+.2f} bp · "
                           f"p {r['p_full']:.4f}<br>"
                           f"sign-stable {int(r['n_same_sign'])}"
                           f"/{int(r['n_symbols'])}; "
                           f"p<.10 in {int(r['n_p_dk_lt_10'])} refits"
                           "<extra></extra>")))
    fig.update_layout(
        title="Leave-one-stock-out β ranges (bp) — all five headlines "
              "sign-stable 12/12",
        xaxis_title="β (bp per 1 SD)", height=340,
        margin=dict(l=10, r=10, t=42, b=40))
    return fig


def _base_vs_variants() -> go.Figure:
    heads = ["H4", "H6", "H7", "H8", "H10"]
    base = _SURV.loc[_SURV["variant"].str.startswith("base")].set_index(
        "test_id")["bp"].reindex(heads)
    variants = {
        "drop_bubble (normal era)": _DB.set_index("test_id")["bp"].reindex(heads),
        "top5_external (ranks 11-15)": _T5.set_index("test_id")["bp"].reindex(heads),
    }
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=heads, y=base.values, name="base t+1 EXP-0004b",
        marker_color="#5d6d7e"))
    for lv_bp, (label, series) in enumerate(variants.items()):
        fig.add_trace(go.Bar(x=heads, y=series.values, name=label,
                             marker_color=["#48c9b0", "#f5b041"][lv_bp]))
    fig.update_layout(barmode="group", height=360,
                      yaxis_title="β (bp per 1 SD)",
                      title="β magnitude: base vs normal-era vs BELOW the "
                            "top-10 tier (top-5 external) — transfer fails "
                            "outside the flagship tier",
                      legend=dict(orientation="h", y=-0.25),
                      margin=dict(l=10, r=10, t=42, b=60))
    return fig


def layout() -> html.Div:
    reg_rows = []
    for _, r in _REG.iterrows():
        reg_rows.append(html.Tr([
            html.Td(html.B(r["test_id"]) if r["test_id"] in
                    ("H4", "H6", "H7", "H8", "H10") else r["test_id"]),
            html.Td(f"{r['interaction_p']:.4f}"),
            html.Td(f"{r['beta_bubble']:+.2f}"), html.Td(f"{r['p_bubble']:.4f}"),
            html.Td(f"{r['beta_normal']:+.2f}"),
            html.Td(f"{r['p_normal']:.4f}"),
            html.Td("—" if pd.isna(r["interaction_p"]) else
                    ("SIG" if r["interaction_p"] < 0.05 else "n.s.")),
        ]))
    return page_container(
        "Inference & robustness — 10-test grid (EXP-0004b), regime split "
        "(EXP-0004d) + the 7-part battery (EXP-0005a–g)",
        html.H6("Numbers-of-record grid — DK(bw=5) primary, BH q0.10 "
                "family of 10; 5/10 HEADLINES: H4 H6 H7 H8 H10"),
        _grid_table,
        dbc.Row([
            dbc.Col(dcc.Graph(figure=_survival_matrix()), width=6),
            dbc.Col(dcc.Graph(figure=_loo_fig()), width=6),
        ]),
        dcc.Graph(figure=_base_vs_variants()),
        html.H6("Regime interaction (plan §5): bubble main effect absorbed "
                "by time FE; INTERACTION is the identified object — "
                "no interaction significant (min p .1171)"),
        dbc.Table([
            html.Thead(html.Tr([html.Th(m) for m in [
                "test", "interaction p", "β bubble (bp)", "p bubble",
                "β normal (bp)", "p normal", "verdict"]])),
            html.Tbody(reg_rows)], striped=True, size="sm"),
        html.P("Reading preserved from Phase 5: headline set survives LOO/"
               "thresholds/normal-era drop; H8 fragile twice (top-1% "
               "cutoff + bubble era); concentration effects DO NOT "
               "transfer below the most-traded tier (0/5 pass). The IF "
               "anomaly score itself has NO OOS return content "
               "(placebo ≈ random).", className="text-muted"),
    )
