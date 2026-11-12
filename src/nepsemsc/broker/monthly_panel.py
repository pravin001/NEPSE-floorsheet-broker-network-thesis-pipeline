"""Broker monthly panel + network snapshots (v2 Stage 4, PhD seed).

DESCRIPTIVE ONLY (R11): every output here is a measurement of the corpus, not
an inference about returns.  No p-values, no causal claims.

Pre-declared construction (docs/analysis_plan_v2_extension.md §V2-4):

  * unit = (broker, calendar month); value = floorsheet `amount`, converted to
    integer paisa (`round(amount*100)`) before aggregation so HHI is exact
    integer arithmetic rather than floating-point accumulation;
  * level aggregates KEEP 2023-02-16 (the contract-number defect only affects
    ordering-dependent features, not monthly value totals);
  * buy/sell value, net position (buy - sell), stock breadth (distinct
    symbols on either side), cross-stock HHI = sum of squared symbol shares of
    the broker's monthly traded value (buy+sell), exact rational evaluated in
    Python integers;
  * network = MONTHLY undirected broker graph from aggregated pair edges
    (self-loops excluded from the graph but retained in flows);
    betweenness = normalized, unweighted topology; eigenvector = weighted by
    monthly traded value; degree = distinct counterparties;
  * top-50 persistence = month-over-month Jaccard of the top-50 brokers by
    total traded value;
  * core = top decile of monthly betweenness (ceil(10% of active brokers),
    ties broken by total value then broker id) AND top-decile in >= 6 of the
    trailing up-to-12 calendar months (at least 6 observed months);
  * core<->periphery transitions among brokers active in CONSECUTIVE months;
    entries/exits counted separately;
  * snapshots 2021-10 vs 2023-06, spring layout (fixed seed), top-100 by
    monthly value (all active brokers when fewer than 100).

Known coverage caveat (recorded in the report): the Kaggle 2021-2023 source
exposes ~51 active brokers in most months, while the 2024 socrateai source
exposes ~90.  Cross-source network levels are therefore not comparable; the
two declared snapshots are both inside the Kaggle era.
"""
from __future__ import annotations

import math
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

# Broker identifiers arrive in two forms across source vintages: canonical
# two-digit strings ("58", "01") and float-rendered strings ("58.0", "1.0").
# Left uncorrected, the same broker becomes two graph nodes on the affected
# days (a source-format defect, not an economic entry).  The macro canonicalises
# the dotted form to the existing zero-padded two-digit convention.
BROKER_CANON_SQL = """
CASE
  WHEN regexp_matches({col}, '^[0-9]+[.]0$')
    THEN lpad(split_part({col}, '.', 1), 2, '0')
  ELSE {col}
END
"""


def canonical_broker_id(value: str) -> str:
    """Canonicalise one broker id (Python mirror of the DuckDB macro)."""
    v = str(value)
    if v.endswith(".0") and v[:-2].isdigit():
        return v[:-2].zfill(2)
    return v


def create_broker_macro(con) -> None:
    """Register the canonicalisation macro on a DuckDB connection."""
    con.execute(
        "CREATE OR REPLACE TEMP MACRO canon_broker(x) AS "
        + BROKER_CANON_SQL.format(col="x"))


TOP_FRAC = 0.10
PERSIST_MONTHS = 6
PERSIST_WINDOW = 12
TOP_N_PERSISTENCE = 50
SNAPSHOT_MONTHS = ("2021-10", "2023-06")
RENDER_TOP_N = 100
SNAPSHOT_SEED = 20211006


def load_trade_months(con) -> int:
    """Materialise the valid trade ledger as a temp table; return row count."""
    create_broker_macro(con)
    con.execute("""
        CREATE OR REPLACE TEMP TABLE _broker_trade AS
        SELECT CAST(date_trunc('month', date) AS DATE) AS month,
               symbol,
               canon_broker(buyer_broker_id) AS buyer,
               canon_broker(seller_broker_id) AS seller,
               CAST(round(amount * 100) AS BIGINT) AS paisa
        FROM floorsheet_dedup
        WHERE volume IS NOT NULL AND volume > 0
          AND price > 0
          AND amount IS NOT NULL AND amount > 0
          AND COALESCE(buyer_broker_id, '') <> ''
          AND COALESCE(seller_broker_id, '') <> ''
          AND COALESCE(symbol, '') <> ''
    """)
    return int(con.execute("SELECT COUNT(*) FROM _broker_trade").fetchone()[0])


def monthly_edges(con) -> pd.DataFrame:
    """Aggregated buyer -> seller pair edges per month (value in paisa)."""
    return con.execute("""
        SELECT month, buyer, seller,
               CAST(SUM(paisa) AS BIGINT) AS value_paisa,
               COUNT(*) AS n_trades
        FROM _broker_trade
        GROUP BY 1, 2, 3
        ORDER BY 1, 2, 3
    """).df()


def broker_month_symbol(con) -> pd.DataFrame:
    """Broker x month x symbol traded value (buy and sell sides pooled)."""
    return con.execute("""
        SELECT month, broker, symbol,
               CAST(SUM(paisa) AS BIGINT) AS value_paisa
        FROM (
            SELECT month, buyer AS broker, symbol, paisa FROM _broker_trade
            UNION ALL
            SELECT month, seller AS broker, symbol, paisa FROM _broker_trade
        )
        GROUP BY 1, 2, 3
    """).df()


def broker_flows(con) -> pd.DataFrame:
    """Symmetric buy/sell monthly totals, trade counts and side breadths."""
    return con.execute("""
        WITH b AS (
            SELECT month, buyer AS broker,
                   CAST(SUM(paisa) AS BIGINT) AS buy_paisa,
                   COUNT(*) AS n_buy_trades,
                   COUNT(DISTINCT symbol) AS n_buy_symbols
            FROM _broker_trade GROUP BY 1, 2
        ), s AS (
            SELECT month, seller AS broker,
                   CAST(SUM(paisa) AS BIGINT) AS sell_paisa,
                   COUNT(*) AS n_sell_trades,
                   COUNT(DISTINCT symbol) AS n_sell_symbols
            FROM _broker_trade GROUP BY 1, 2
        )
        SELECT COALESCE(b.month, s.month) AS month,
               COALESCE(b.broker, s.broker) AS broker,
               COALESCE(b.buy_paisa, 0) AS buy_paisa,
               COALESCE(s.sell_paisa, 0) AS sell_paisa,
               COALESCE(b.n_buy_trades, 0) AS n_buy_trades,
               COALESCE(s.n_sell_trades, 0) AS n_sell_trades,
               COALESCE(b.n_buy_symbols, 0) AS n_buy_symbols,
               COALESCE(s.n_sell_symbols, 0) AS n_sell_symbols
        FROM b FULL OUTER JOIN s
          ON b.month = s.month AND b.broker = s.broker
    """).df()


def exact_concentration(bs: pd.DataFrame) -> pd.DataFrame:
    """Exact cross-stock HHI + top-symbol share from integer paisa.

    HHI = sum_i (v_i / V)^2 = (sum_i v_i^2) / V^2, evaluated with Python
    integers so no float accumulation enters the concentration measure.
    """
    rows = []
    for (month, broker), g in bs.groupby(["month", "broker"], observed=True):
        vals = [int(v) for v in g["value_paisa"].tolist()]
        total = sum(vals)
        if total <= 0:
            continue
        sq = sum(v * v for v in vals)
        rows.append({
            "month": month, "broker": broker,
            "n_symbols": len(vals),
            "hhi": sq / (total * total),
            "top_symbol_share": max(vals) / total,
        })
    return pd.DataFrame(rows)


def monthly_centrality(edges: pd.DataFrame) -> pd.DataFrame:
    """Betweenness + eigenvector centrality for every active broker-month."""
    rows = []
    for month, g in edges.groupby("month", observed=True):
        g = g.sort_values(["buyer", "seller"])
        G = nx.Graph()
        nodes = sorted(set(g["buyer"]) | set(g["seller"]))
        G.add_nodes_from(nodes)
        for b, s, w in zip(g["buyer"], g["seller"], g["value_paisa"]):
            if b == s:
                continue
            w = float(w)
            if G.has_edge(b, s):
                G[b][s]["weight"] += w
            else:
                G.add_edge(b, s, weight=w)
        bt = nx.betweenness_centrality(G, normalized=True)
        try:
            ev = nx.eigenvector_centrality_numpy(G, weight="weight")
        except Exception:
            ev = nx.eigenvector_centrality(G, weight="weight", max_iter=2000,
                                           tol=1e-10)
        deg = dict(G.degree())
        wdeg = dict(G.degree(weight="weight"))
        for node in nodes:
            # Quantized to 12 decimals: graph traversal order is not stable
            # across Python hash seeds, which moves the last 1-2 ULPs of the
            # centrality floats.  1e-12 is ~10 orders of magnitude below any
            # economically meaningful difference and makes the descriptive
            # artifacts byte-reproducible (Stage-4 determinism gate).
            rows.append({
                "month": month, "broker": node,
                "betweenness": round(float(bt.get(node, 0.0)), 12),
                "eigenvector": round(float(ev.get(node, 0.0)), 12),
                "degree": int(deg.get(node, 0)),
                "weighted_degree": round(float(wdeg.get(node, 0.0)), 12),
            })
    return pd.DataFrame(rows)


def add_core_flags(panel: pd.DataFrame,
                   rank_col: str = "betweenness") -> pd.DataFrame:
    """Add monthly top-decile flag, 12-month persistence and core status.

    `rank_col` is the declared ranking variable (betweenness).  A sensitivity
    runner may pass `eigenvector` or `total_value_paisa`; the tie-break order
    (rank variable desc, total value desc, broker id) is unchanged.
    """
    p = panel.sort_values(["month", "broker"]).copy()
    p["n_active_brokers"] = p.groupby("month")["broker"].transform("size")
    # deterministic tie-break: rank variable desc, total value desc, broker id
    p = p.sort_values(["month", rank_col, "total_value_paisa", "broker"],
                      ascending=[True, False, False, True])
    p["betweenness_rank"] = (p.groupby("month").cumcount().to_numpy() + 1)
    k = np.ceil(TOP_FRAC * p["n_active_brokers"].to_numpy()).astype(int)
    p["core_month"] = p["betweenness_rank"].to_numpy() <= k

    months = sorted(p["month"].unique())
    brokers = sorted(p["broker"].unique())
    idx = pd.MultiIndex.from_product([brokers, months],
                                     names=["broker", "month"])
    grid = p.set_index(["broker", "month"]).reindex(idx)
    active = grid["n_buy_trades"].notna() | grid["n_sell_trades"].notna()
    core_month = grid["core_month"].fillna(False).astype(bool)
    n_core_12 = core_month.groupby(level="broker").transform(
        lambda s: s.rolling(PERSIST_WINDOW, min_periods=PERSIST_MONTHS).sum())
    persistent = (n_core_12 >= PERSIST_MONTHS) & active
    grid["n_core_months_12"] = n_core_12
    grid["persistent_core"] = persistent
    grid["core"] = core_month & persistent
    grid = grid.dropna(subset=["n_buy_trades"]).reset_index()
    return grid.sort_values(["month", "broker"]).reset_index(drop=True)


def top50_persistence(panel: pd.DataFrame) -> pd.DataFrame:
    """Month-over-month Jaccard of top-50 brokers by total traded value."""
    rows = []
    prev = None
    prev_month = None
    for month, g in panel.groupby("month", observed=True):
        n_active = len(g)
        top = set(g.nlargest(min(TOP_N_PERSISTENCE, n_active),
                             "total_value_paisa")["broker"])
        if prev is None:
            rows.append({"month": month, "prev_month": pd.NaT,
                         "n_active": n_active, "n_top": len(top),
                         "overlap": np.nan, "jaccard": np.nan})
        else:
            inter = len(top & prev)
            union = len(top | prev)
            rows.append({"month": month, "prev_month": prev_month,
                         "n_active": n_active, "n_top": len(top),
                         "overlap": inter,
                         "jaccard": inter / union if union else np.nan})
        prev, prev_month = top, month
    return pd.DataFrame(rows)


def transition_counts(panel: pd.DataFrame) -> pd.DataFrame:
    """Core <-> periphery transitions across consecutive calendar months."""
    months = sorted(panel["month"].unique())
    by_month = {m: g.set_index("broker") for m, g in
                panel.groupby("month", observed=True)}
    rows = []
    for prev_m, now_m in zip(months[:-1], months[1:]):
        a, b = by_month[prev_m], by_month[now_m]
        both = set(a.index) & set(b.index)
        ac, bc = set(a.index[a["core"]]), set(b.index[b["core"]])
        rows.append({
            "prev_month": prev_m, "month": now_m,
            "n_core_prev": len(ac), "n_core_now": len(bc),
            "n_active_both": len(both),
            "core_to_core": len((ac & bc) & both),
            "core_to_periphery": len((ac - bc) & both),
            "periphery_to_core": len((bc - ac) & both),
            "periphery_to_periphery": len(both - ac - bc),
            "entries": len(set(b.index) - set(a.index)),
            "exits": len(set(a.index) - set(b.index)),
            "entries_core": len(bc - set(a.index)),
            "exits_core": len(ac - set(b.index)),
        })
    return pd.DataFrame(rows)


def build_broker_panel(con) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame,
                                     pd.DataFrame, int]:
    """Return (panel, edges, jaccard, transitions, n_valid_trades)."""
    n = load_trade_months(con)
    edges = monthly_edges(con)
    bs = broker_month_symbol(con)
    flows = broker_flows(con)
    conc = exact_concentration(bs)
    cent = monthly_centrality(edges)

    panel = flows.merge(conc, on=["month", "broker"], how="left")
    panel = panel.merge(cent, on=["month", "broker"], how="left")
    panel["total_value_paisa"] = panel["buy_paisa"] + panel["sell_paisa"]
    panel["n_trades"] = panel["n_buy_trades"] + panel["n_sell_trades"]
    panel["breadth"] = panel[["n_buy_symbols", "n_sell_symbols"]].max(axis=1)
    panel = panel.sort_values(["month", "broker"]).reset_index(drop=True)
    panel = add_core_flags(panel)

    panel["buy_value_npr"] = panel["buy_paisa"] / 100.0
    panel["sell_value_npr"] = panel["sell_paisa"] / 100.0
    panel["total_value_npr"] = panel["total_value_paisa"] / 100.0
    panel["net_position_npr"] = (panel["buy_paisa"] - panel["sell_paisa"]) / 100.0

    jac = top50_persistence(panel)
    trans = transition_counts(panel)
    return panel, edges, jac, trans, n


def snapshot_figure(panel: pd.DataFrame, edges: pd.DataFrame, month: str,
                    path: str | Path, top_n: int = RENDER_TOP_N,
                    seed: int = SNAPSHOT_SEED) -> dict:
    """Render the declared spring-layout snapshot for one month."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    m = pd.Timestamp(month)
    p = panel.loc[panel.month == m].nlargest(min(top_n, int(
        (panel.month == m).sum())), "total_value_paisa")
    keep = set(p["broker"])
    core = set(p.loc[p["core"], "broker"])
    em = edges[(edges.month == m)
               & edges.buyer.isin(keep) & edges.seller.isin(keep)
               & (edges.buyer != edges.seller)]

    G = nx.Graph()
    G.add_nodes_from(sorted(keep))
    for b, s, w in zip(em.buyer, em.seller, em.value_paisa):
        w = float(w)
        if G.has_edge(b, s):
            G[b][s]["weight"] += w
        else:
            G.add_edge(b, s, weight=w)
    pos = nx.spring_layout(G, seed=seed, weight="weight", iterations=300)
    # Quantized render positions: layout arithmetic can differ in the last
    # ULP across runs, which changes antialiasing but not the visible graph.
    pos = {n_: (round(float(xy[0]), 8), round(float(xy[1]), 8))
           for n_, xy in pos.items()}

    vals = p.set_index("broker")["total_value_paisa"]
    vmax = max(float(vals.max()), 1.0)
    sizes = [30 + 900 * math.sqrt(float(vals.get(n_, 0.0)) / vmax)
             for n_ in G.nodes()]
    colors = ["#c0392b" if n_ in core else "#7f8c8d" for n_ in G.nodes()]
    # Canonical edge order: alpha blending makes draw order observable at
    # the last couple of pixel levels, so sort edges before rendering.
    edge_order = sorted(G.edges())
    widths = [0.2 + 2.0 * math.sqrt(float(G[u][v]["weight"]) / vmax)
              for u, v in edge_order]

    fig, ax = plt.subplots(figsize=(10, 8))
    nx.draw_networkx_edges(G, pos, ax=ax, edgelist=edge_order, width=widths,
                           alpha=0.25, edge_color="#34495e")
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=sizes, node_color=colors,
                           linewidths=0.3, edgecolors="white")
    top_labels = {n_: n_ for n_ in
                  vals.nlargest(min(12, len(vals))).index if n_ in pos}
    nx.draw_networkx_labels(G, pos, labels=top_labels, font_size=8, ax=ax)
    ax.set_title(f"Broker network {month} — top {len(keep)} by value "
                 f"({len(core)} core brokers)", fontsize=11)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return {"month": month, "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(), "core_nodes": len(core & keep)}
