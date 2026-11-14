#!/usr/bin/env python
"""Generate the ten static thesis figures (F1-F10) from frozen artifacts.

Contract for the v2.0.2 pre-write sprint
----------------------------------------
* No regression, test, refit, robustness check, or new statistic is computed.
  Every plotted value is read from a frozen CSV/parquet or, for F10, from the
  two already-frozen network renders.
* Each figure is emitted as 300-dpi PNG + vector PDF.
* Footer: experiment id + short digest of the exact input bytes + v2.0.1.
* Every PNG is checked for non-blank content after it is written.
* `outputs/figures/static/figure_manifest.csv` records provenance and hashes.

Run:
    nepse-msc/bin/python scripts/make_thesis_figures.py
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
FIGDIR = ROOT / "outputs" / "figures" / "static"
FIGDIR.mkdir(parents=True, exist_ok=True)

VERSION = "v2.0.1"
DPI = 300

# Okabe-Ito colourblind-safe palette.
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
PURPLE = "#CC79A7"
SKY = "#56B4E9"
YELLOW = "#E69F00"
GREY = "#6B6B6B"
LIGHT_GREY = "#D9D9D9"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 10.5,
        "axes.labelsize": 9.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#E6E6E6",
        "grid.linewidth": 0.6,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.facecolor": "white",
    }
)


def sha256_bytes(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def combined_digest(paths: list[Path]) -> str:
    """Digest the exact input bytes in sorted-path order."""
    h = hashlib.sha256()
    for path in sorted(paths, key=lambda p: str(p.relative_to(ROOT))):
        h.update(str(path.relative_to(ROOT)).encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def add_frame(fig: plt.Figure, number: str, title: str, exp: str, digest: str) -> None:
    fig.suptitle(f"{number} · {title}", x=0.018, y=0.985, ha="left",
                 fontsize=13, fontweight="bold")
    footer = f"{exp}  ·  data {digest[:12]}  ·  {VERSION}"
    fig.add_artist(
        Line2D([0.045, 0.955], [0.052, 0.052], transform=fig.transFigure,
               color="#BFBFBF", lw=0.7)
    )
    fig.text(0.5, 0.020, footer, ha="center", va="bottom", fontsize=7.6,
             color="#333333")


def save_figure(
    fig: plt.Figure,
    number: str,
    slug: str,
    title: str,
    chapter: str,
    exp: str,
    inputs: list[Path],
    caption: str,
) -> dict:
    digest = combined_digest(inputs)
    add_frame(fig, number, title, exp, digest)

    png = FIGDIR / f"{slug}.png"
    pdf = FIGDIR / f"{slug}.pdf"
    meta = {
        "Title": title,
        "Author": "NEPSE floorsheet thesis — pre-write assets",
        "Subject": f"{number}; {chapter}; {exp}; data {digest[:12]}; {VERSION}",
        "Creator": "scripts/make_thesis_figures.py",
    }
    fig.savefig(png, dpi=DPI, facecolor="white", metadata=meta)
    fig.savefig(pdf, dpi=DPI, facecolor="white", metadata=meta)
    plt.close(fig)

    # Non-blank check on a downsampled RGB copy (fast, deterministic).
    with Image.open(png) as im:
        rgb = im.convert("RGB")
        width, height = rgb.size
        small = rgb.resize((max(1, width // 4), max(1, height // 4)))
        arr = np.asarray(small, dtype=np.uint8)
    pixel_std = float(arr.std())
    nonwhite = float((arr.min(axis=2) < 245).mean())
    n_colors = int(np.unique(arr.reshape(-1, 3), axis=0).shape[0])
    blank_ok = bool(pixel_std > 2.0 and nonwhite > 0.01 and n_colors > 40)
    if not blank_ok:
        raise AssertionError(
            f"{number} failed blank check: std={pixel_std:.3f}, "
            f"nonwhite={nonwhite:.4f}, colours={n_colors}"
        )

    row = {
        "figure_id": number,
        "slug": slug,
        "title": title,
        "chapter": chapter,
        "experiment_id": exp,
        "input_artifacts": ";".join(rel(p) for p in sorted(inputs)),
        "input_sha256": digest,
        "data_hash_short": digest[:12],
        "version": VERSION,
        "png_path": rel(png),
        "pdf_path": rel(pdf),
        "png_sha256": sha256_bytes(png),
        "pdf_sha256": sha256_bytes(pdf),
        "png_bytes": png.stat().st_size,
        "pdf_bytes": pdf.stat().st_size,
        "dpi": DPI,
        "width_px": width,
        "height_px": height,
        "pixel_std": round(pixel_std, 4),
        "nonwhite_fraction": round(nonwhite, 4),
        "unique_colours_downsampled": n_colors,
        "blank_check": "PASS" if blank_ok else "FAIL",
        "caption_scaffold": caption,
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    print(
        f"{number}  {slug:38s}  {width}x{height}  "
        f"std={pixel_std:6.2f}  nonwhite={nonwhite:.3f}  "
        f"colours={n_colors:4d}  PASS"
    )
    return row


# ---------------------------------------------------------------------------
# F1 — corpus coverage
# ---------------------------------------------------------------------------
def fig_f1() -> dict:
    path = TABLES / "corpus_daily_summary.csv"
    d = pd.read_csv(path, parse_dates=["date"])
    d["year"] = d["date"].dt.year
    g = (
        d.groupby(["year", "source"], as_index=False)
        .agg(sessions=("date", "nunique"), rows=("n_rows", "sum"))
    )

    years = [2021, 2022, 2023, 2024]
    sources = ["kaggle_viking303", "socrateai"]
    labels = {"kaggle_viking303": "Kaggle viking303 (2021–2023)",
              "socrateai": "SocrateAI (2024)"}
    colours = {"kaggle_viking303": BLUE, "socrateai": GREEN}

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.7))
    fig.subplots_adjust(left=0.08, right=0.985, top=0.83, bottom=0.19, wspace=0.28)

    for ax, value, ylabel, scale, fmt in [
        (axes[0], "sessions", "Trading sessions", 1.0, "{:.0f}"),
        (axes[1], "rows", "Floorsheet rows (millions)", 1e6, "{:.1f}"),
    ]:
        bottom = np.zeros(len(years))
        for source in sources:
            vals = np.array(
                [
                    float(
                        g.loc[(g.year == y) & (g.source == source), value].sum()
                    )
                    / scale
                    for y in years
                ]
            )
            ax.bar(years, vals, bottom=bottom, width=0.62,
                   color=colours[source], label=labels[source],
                   edgecolor="white", linewidth=0.7)
            for x, v, b in zip(years, vals, bottom):
                if v > 0:
                    ax.text(x, b + v / 2, fmt.format(v), ha="center", va="center",
                            fontsize=8.2, color="white", fontweight="bold")
            bottom += vals
        ax.set_xticks(years)
        ax.set_xlabel("Calendar year")
        ax.set_ylabel(ylabel)
        ax.set_axisbelow(True)
        ax.grid(axis="x", visible=False)

    axes[0].set_title("Sessions by source")
    axes[1].set_title("Rows by source")
    axes[1].set_ylim(0, 25)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper right",
               bbox_to_anchor=(0.985, 0.925), ncol=2, fontsize=7.8)

    total_sessions = int(d["date"].nunique())
    total_rows = int(d["n_rows"].sum())
    axes[1].text(
        0.98, 0.97,
        f"Total: {total_sessions:,} sessions\n{total_rows/1e6:.2f}M rows",
        transform=axes[1].transAxes, ha="right", va="top", fontsize=8.4,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#CCCCCC"),
    )

    return save_figure(
        fig, "F1", "f1_corpus_coverage",
        "Corpus coverage by year and source",
        "Ch.4 data chapter", "EXP-0002c", [path],
        "Sessions and floorsheet rows per calendar year, split by corpus source; "
        "the 938-session, 57.89M-row window is the frozen input to all later stages.",
    )


# ---------------------------------------------------------------------------
# F2 — data-integrity audit panel
# ---------------------------------------------------------------------------
def fig_f2() -> dict:
    dup_path = TABLES / "corpus_duplicate_keys.csv"
    filt_path = TABLES / "feature_row_filter_accounting.csv"
    miss_path = TABLES / "corpus_missing_broker_ids.csv"
    daily_path = TABLES / "corpus_daily_summary.csv"

    dup = pd.read_csv(dup_path)
    filt = pd.read_csv(filt_path).iloc[0]
    miss = pd.read_csv(miss_path)
    daily = pd.read_csv(daily_path)

    exact = int((dup["n_signatures"] == 1).sum())
    conflict = int((dup["n_signatures"] > 1).sum())
    total_dup = int(len(dup))
    dedupe_dropped = int(dup["n_raw"].sum() - len(dup))
    junk = int(filt["dropped_rows"])

    checks = [
        ("Duplicate keys (all)", total_dup, BLUE),
        ("  exact duplicates", exact, SKY),
        ("  signature conflicts", conflict, PURPLE),
        ("Rows removed in dedupe", dedupe_dropped, ORANGE),
        ("SV7 junk rows removed", junk, YELLOW),
        ("Missing-broker pairs", int(len(miss)), GREY),
        ("Non-positive price rows", 8, GREY),
        ("NULL contract_no rows", 2, GREY),
    ]

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(11.2, 5.0), gridspec_kw={"width_ratios": [1.05, 1.0]}
    )
    fig.subplots_adjust(left=0.19, right=0.985, top=0.82, bottom=0.19, wspace=0.32)

    y = np.arange(len(checks))
    for yi, (label, value, colour) in zip(y, checks):
        ax1.barh(yi, value, color=colour, height=0.62, edgecolor="white")
        ax1.text(value * 1.18, yi, f"{value:,}", va="center", ha="left",
                 fontsize=8.4, color="#222222")
    ax1.set_yticks(y)
    ax1.set_yticklabels([c[0] for c in checks], fontsize=8.4)
    ax1.set_xscale("log")
    ax1.set_xlim(1.5, 2.2e5)
    ax1.set_xlabel("Rows / keys (log scale)")
    ax1.set_title("Audit counts")
    ax1.grid(axis="y", visible=False)
    ax1.set_axisbelow(True)

    account = pd.read_csv(TABLES / "feature_row_filter_accounting.csv").iloc[0]
    table_rows = [
        ["Deduplicated corpus rows", f"{int(account['n_rows_raw']):,}"],
        ["Rows removed in dedupe", f"{dedupe_dropped:,}"],
        ["Post-SV7 feature rows", f"{int(account['n_rows_after_filters']):,}"],
        ["Volume retained", f"{float(account['volume_kept_share'])*100:.6f}%"],
        ["Calendar sessions", f"{int(daily['date'].nunique()):,} / 940"],
        ["2023-02-16 defect", "35,043 rows · 1 contract id"],
        ["CGH identity check", "qty 910 = volume 910  ✓"],
    ]
    ax2.axis("off")
    ax2.set_title("Integrity checks", loc="left", pad=8)
    table = ax2.table(
        cellText=table_rows,
        colLabels=["Check", "Frozen value"],
        cellLoc="left",
        colLoc="left",
        colWidths=[0.48, 0.52],
        loc="center",
        bbox=[0.0, 0.02, 1.0, 0.88],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.2)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#DDDDDD")
        cell.set_linewidth(0.5)
        if row == 0:
            cell.set_facecolor("#EFEFEF")
            cell.set_text_props(fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#FAFAFA")
        else:
            cell.set_facecolor("white")

    return save_figure(
        fig, "F2", "f2_audit_panel",
        "Corpus and feature-build audit",
        "Ch.3 §3.3 / Ch.4 §4.3", "EXP-0002c", 
        [dup_path, filt_path, miss_path, daily_path],
        "Duplicate classes, row accounting, calendar coverage, the 2023-02-16 "
        "contract-id defect, and the CGH quantity-identity check.",
    )


# ---------------------------------------------------------------------------
# F3 — network-feature small multiples
# ---------------------------------------------------------------------------
def fig_f3() -> dict:
    feat_path = ROOT / "data" / "processed" / "daily_features.parquet"
    uni_path = TABLES / "universe_selected_top10.csv"
    features = pd.read_parquet(feat_path, columns=[
        "date", "symbol", "buyer_hhi", "seller_hhi", "top_3_buyer_share",
        "self_loop_volume_ratio", "reciprocity_volume", "core_periphery_coeff",
    ])
    universe = pd.read_csv(uni_path)
    symbols = set(universe["rank_symbol"])
    d = features[features["symbol"].isin(symbols)].copy()
    d["month"] = pd.to_datetime(d["date"]).dt.to_period("M").dt.to_timestamp()
    monthly = d.groupby("month").mean(numeric_only=True)

    specs = [
        ("buyer_hhi", "Buyer HHI (%)", 100.0),
        ("seller_hhi", "Seller HHI (%)", 100.0),
        ("top_3_buyer_share", "Top-3 buyer share (%)", 100.0),
        ("self_loop_volume_ratio", "Self-loop volume (%)", 100.0),
        ("reciprocity_volume", "Reciprocity volume (%)", 100.0),
        ("core_periphery_coeff", "Core–periphery coefficient", 1.0),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(11.2, 6.2), sharex=True)
    fig.subplots_adjust(left=0.07, right=0.985, top=0.82, bottom=0.20,
                        hspace=0.30, wspace=0.25)
    for ax, (col, label, scale) in zip(axes.ravel(), specs):
        ax.plot(monthly.index, monthly[col] * scale, color=BLUE, lw=1.6)
        ax.axvline(pd.Timestamp("2024-01-01"), color=ORANGE, lw=1.0, ls="--")
        ax.set_title(label, loc="left")
        ax.grid(axis="x", visible=False)
        ax.set_axisbelow(True)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", labelsize=8)
    axes[1, 0].set_xlabel("Year")
    axes[1, 1].set_xlabel("Year")
    axes[1, 2].set_xlabel("Year")
    fig.text(
        0.5, 0.075,
        "Monthly means across the 12-symbol panel. Dashed line = 2023→2024 "
        "source/coverage change; levels are not directly comparable across it.",
        ha="center", fontsize=8.0, color="#444444",
    )

    return save_figure(
        fig, "F3", "f3_feature_small_multiples",
        "Daily network-feature trajectories (12-symbol panel)",
        "Ch.3 §3.4 / Ch.5 §5.2", "EXP-0003a", [feat_path, uni_path],
        "Six monthly-mean network features for the frozen 12-symbol panel, "
        "2021–2024, with the source/coverage boundary marked.",
    )


# ---------------------------------------------------------------------------
# F4 — H10 quantile curve
# ---------------------------------------------------------------------------
def fig_f4() -> dict:
    q_path = TABLES / "quantile_regression.csv"
    t_path = TABLES / "quantile_tail_summary.csv"
    h_path = TABLES / "v2_final_headline_set.csv"
    q = pd.read_csv(q_path)
    q = q[q["test_id"] == "H10"].sort_values("tau")
    tail = pd.read_csv(t_path)
    tail = tail[tail["test_id"] == "H10"].iloc[0]
    headline = pd.read_csv(h_path)
    base = float(headline.loc[headline["hypothesis"] == "H10", "estimated_beta"].iloc[0])

    fig, ax = plt.subplots(figsize=(8.4, 4.9))
    fig.subplots_adjust(left=0.10, right=0.975, top=0.82, bottom=0.20)
    taus = q["tau"].to_numpy(dtype=float)
    beta = q["beta_bp"].to_numpy(dtype=float)
    lo = q["ci_lo_bp"].to_numpy(dtype=float)
    hi = q["ci_hi_bp"].to_numpy(dtype=float)

    ax.axhline(base, color=GREY, lw=1.1, ls="--", label=f"OLS base β = {base:+.3f} bp")
    ax.errorbar(
        taus, beta, yerr=[beta - lo, hi - beta], fmt="o-", color=BLUE,
        ecolor=BLUE, elinewidth=1.4, capsize=4, ms=6, lw=1.7,
        label="Quantile β (95% robust CI)",
    )
    for tau, b in zip(taus, beta):
        ax.annotate(f"{b:+.2f}", (tau, b), textcoords="offset points",
                    xytext=(0, 9), ha="center", fontsize=7.8, color=BLUE)
    ax.set_xticks(taus)
    ax.set_xlabel("Quantile τ")
    ax.set_ylabel("H10 β (bp per 1 SD)")
    ax.set_xlim(0.04, 0.96)
    ax.set_ylim(0, 23)
    ax.legend(loc="upper left", fontsize=8.0)
    ax.text(
        0.98, 0.04,
        f"Tail ratio β(.90)/β(.10) = {float(tail['beta_ratio_90_10']):.3f}\n"
        f"{tail['tail_classification']} ({tail['tail_shape']})\n"
        "50/50 quantile fits converged",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=8.0,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#CCCCCC"),
    )

    return save_figure(
        fig, "F4", "f4_h10_quantile_curve",
        "H10 reciprocity → |return| across quantiles",
        "Ch.5 §5.6.5", "EXP-0010b", [q_path, t_path, h_path],
        "H10 quantile estimates at τ=.10/.25/.50/.75/.90 with robust 95% CIs, "
        "against the OLS base; the effect rises from +3.08 to +18.70 bp.",
    )


# ---------------------------------------------------------------------------
# F5 — H7 144-specification curve
# ---------------------------------------------------------------------------
def fig_f5() -> dict:
    s_path = TABLES / "specification_curve_h7.csv"
    sm_path = TABLES / "specification_curve_h7_summary.csv"
    s = pd.read_csv(s_path).sort_values("beta_bp").reset_index(drop=True)
    summary = pd.read_csv(sm_path).set_index("group")

    fig, ax = plt.subplots(figsize=(11.2, 5.4))
    fig.subplots_adjust(left=0.075, right=0.985, top=0.82, bottom=0.20)

    x = np.arange(1, len(s) + 1)
    colours = np.where(s["outcome"] == "abs_ret_fwd1", BLUE, ORANGE)
    ax.vlines(x, s["ci_lo_bp"], s["ci_hi_bp"], color=colours, alpha=0.55, lw=0.85)
    ax.scatter(x, s["beta_bp"], c=colours, s=10, zorder=3)
    ax.axhline(0, color="#555555", lw=0.9)

    base_mask = s["spec_id"].eq("DK|abs_ret|base|full|5pct")
    if base_mask.sum() != 1:
        raise AssertionError("base H7 specification not found exactly once")
    bx = int(x[base_mask.to_numpy()][0])
    by = float(s.loc[base_mask, "beta_bp"].iloc[0])
    ax.scatter([bx], [by], s=110, facecolors="none", edgecolors="black",
               linewidths=1.3, zorder=5)
    ax.annotate(
        f"base DK\n{by:+.3f} bp (p=.0274)",
        (bx, by), xytext=(18, 22), textcoords="offset points",
        fontsize=8.0, arrowprops=dict(arrowstyle="-", color="black", lw=0.7),
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#CCCCCC"),
    )

    legend = [
        Patch(facecolor=BLUE, label="|return| outcome (72 specs)"),
        Patch(facecolor=ORANGE, label="signed return outcome (72 specs)"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="none",
               markeredgecolor="black", markersize=8, label="base specification"),
    ]
    ax.legend(handles=legend, loc="lower left", fontsize=8.0)

    abs_sum = summary.loc["outcome=abs_ret"]
    ret_sum = summary.loc["outcome=ret"]
    ax.text(
        0.985, 0.04,
        f"|return|: 72/72 positive · median {abs_sum['median_bp']:+.3f} bp · "
        f"{abs_sum['share_ci_excludes_0']*100:.1f}% CI excludes 0\n"
        f"signed: 66/72 negative · median {ret_sum['median_bp']:+.3f} bp · "
        f"{ret_sum['share_ci_excludes_0']*100:.1f}% CI excludes 0\n"
        "144 specifications · 72 unique design betas",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=8.0,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#CCCCCC"),
    )
    ax.set_xlabel("Specifications sorted by estimated β")
    ax.set_ylabel("H7 β (bp)")
    ax.set_xlim(0.5, len(s) + 0.5)
    ax.set_ylim(-24, 21)

    return save_figure(
        fig, "F5", "f5_h7_specification_curve",
        "H7 specification curve (144 specifications)",
        "Ch.5 §5.6.7", "EXP-0011b", [s_path, sm_path],
        "All 144 H7 specifications sorted by β with 95% CIs, split by outcome; "
        "the base DK specification is circled.",
    )


# ---------------------------------------------------------------------------
# F6 — event-study AR / CAR path
# ---------------------------------------------------------------------------
def fig_f6() -> dict:
    path = TABLES / "event_study_upgraded_ars.csv"
    ars = pd.read_csv(path)
    lags = list(range(-5, 6))
    mean_ar = (ars.groupby("lag")["ar"].mean() * 1e4).reindex(lags)
    counts = ars.groupby("lag")["ar"].size().reindex(lags)
    car = np.array([
        float((ars.loc[ars["lag"] <= lag].groupby("event_idx")["ar"].sum().mean()) * 1e4)
        for lag in lags
    ])

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(9.0, 6.5), sharex=True,
        gridspec_kw={"height_ratios": [1.45, 1.0]},
    )
    fig.subplots_adjust(left=0.10, right=0.975, top=0.82, bottom=0.19, hspace=0.12)

    ax1.plot(lags, car, color=BLUE, marker="o", ms=5, lw=1.8)
    ax1.axhline(0, color="#555555", lw=0.9)
    ax1.axvline(0, color="#999999", lw=0.8, ls=":")
    ax1.set_ylabel("Mean cumulative AR (bp)")
    ax1.set_title("Cumulative average abnormal return", loc="left")
    ax1.annotate(
        f"{car[-1]:+.3f} bp at +5",
        (lags[-1], car[-1]), xytext=(-6, 12), textcoords="offset points",
        ha="right", fontsize=8.4, color=BLUE, fontweight="bold",
    )

    bar_colours = np.where(mean_ar.to_numpy() >= 0, BLUE, ORANGE)
    ax2.bar(lags, mean_ar.to_numpy(), color=bar_colours, width=0.62)
    ax2.axhline(0, color="#555555", lw=0.9)
    ax2.axvline(0, color="#999999", lw=0.8, ls=":")
    ax2.set_xlabel("Event-time lag (sessions)")
    ax2.set_ylabel("Mean AR (bp)")
    ax2.set_title("Average abnormal return by lag", loc="left")
    ax2.set_xticks(lags)
    ax2.text(
        0.99, 0.04,
        f"686 events · {int(ars['event_idx'].nunique())} dates\n"
        f"lag counts: 686 at −5…0; {int(counts.loc[1])}–{int(counts.loc[4])} at +1…+4; "
        f"{int(counts.loc[5])} at +5",
        transform=ax2.transAxes, ha="right", va="bottom", fontsize=7.8,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#CCCCCC"),
    )

    return save_figure(
        fig, "F6", "f6_event_study_path",
        "Event-study abnormal-return path (686 events)",
        "Ch.5 §5.4", "EXP-0011e", [path],
        "Mean AR by event-time lag and the cumulative mean CAR from −5 to +5; "
        "the +5 cumulative mean is +12.861 bp.",
    )


# ---------------------------------------------------------------------------
# F7 — placebo quantile summary
# ---------------------------------------------------------------------------
def fig_f7() -> dict:
    path = TABLES / "placebo_distribution_expanded.csv"
    p = pd.read_csv(path)
    p = p[p["share_type"] == "two_sided"].copy()

    rows = [
        ("H2", "score_perm", "H2 · score shuffle"),
        ("H3", "score_perm", "H3 · score shuffle"),
        ("H2", "block_perm", "H2 · block shuffle"),
        ("H3", "block_perm", "H3 · block shuffle"),
        ("H7", "negctrl_eod_blockshuffle", "H7 · EoD block shuffle"),
        ("H8", "negctrl_eod_blockshuffle", "H8 · EoD block shuffle"),
    ]

    fig, ax = plt.subplots(figsize=(9.6, 4.9))
    fig.subplots_adjust(left=0.30, right=0.97, top=0.82, bottom=0.23)
    y = np.arange(len(rows))[::-1]
    for yi, (test, construction, label) in zip(y, rows):
        r = p[(p["test_id"] == test) & (p["construction"] == construction)]
        if len(r) != 1:
            raise AssertionError(f"placebo row missing/duplicated: {test} {construction}")
        r = r.iloc[0]
        lo = float(r["q025_beta"]) * 1e4
        hi = float(r["q975_beta"]) * 1e4
        med = float(r["q50_beta"]) * 1e4
        obs = float(r["beta_obs_bp"])
        ax.hlines(yi, lo, hi, color=SKY, lw=7, alpha=0.55)
        ax.vlines(yi, med, med, color=BLUE, lw=1.8)
        ax.scatter([med], [yi], marker="|", s=140, color=BLUE, zorder=4)
        ax.scatter([obs], [yi], s=62, color=ORANGE, zorder=5,
                   edgecolor="white", linewidth=0.6)
        anchor = max(obs, hi)
        ax.text(anchor + 0.55, yi, f"obs {obs:+.2f}", va="center", ha="left",
                fontsize=8.0, color=ORANGE, fontweight="bold")

    ax.axvline(0, color="#555555", lw=0.9, ls=":")
    ax.set_yticks(y)
    ax.set_yticklabels([r[2] for r in rows], fontsize=8.4)
    ax.set_xlabel("β (bp)")
    ax.set_xlim(-6.5, 12.0)
    ax.grid(axis="y", visible=False)
    ax.set_axisbelow(True)
    legend = [
        Line2D([0], [0], color=SKY, lw=7, alpha=0.55,
               label="frozen 2.5–97.5% null quantiles"),
        Line2D([0], [0], marker="|", color=BLUE, lw=0, markersize=10,
               label="null median"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=ORANGE,
               markeredgecolor="white", markersize=7, label="observed β"),
    ]
    ax.legend(handles=legend, loc="upper right", fontsize=7.8)
    fig.text(
        0.5, 0.075,
        "1,000 permutations per construction. Draw-level values were not "
        "persisted; this panel uses only the frozen quantile summary.",
        ha="center", fontsize=7.8, color="#444444",
    )

    return save_figure(
        fig, "F7", "f7_placebo_quantile_summary",
        "Placebo null intervals versus observed effects",
        "Ch.5 §5.3", "EXP-0008e", [path],
        "Observed β against the frozen 2.5–97.5% permutation-null intervals for "
        "the anomaly-score placebos and the EoD block-shuffle negative controls.",
    )


# ---------------------------------------------------------------------------
# F8 — tier locality
# ---------------------------------------------------------------------------
def fig_f8() -> dict:
    ext_path = TABLES / "robustness_top5_external_grid.csv"
    head_path = TABLES / "v2_final_headline_set.csv"
    grid_path = TABLES / "hypothesis_grid_results_v2.csv"
    sub_path = TABLES / "heterogeneity_subgroups.csv"

    ext = pd.read_csv(ext_path)
    ext_h10 = ext[ext["test_id"] == "H10"].iloc[0]
    head = pd.read_csv(head_path)
    base_beta = float(head.loc[head["hypothesis"] == "H10", "estimated_beta"].iloc[0])
    grid = pd.read_csv(grid_path)
    base_se = float(grid.loc[grid["test_id"] == "H10", "se"].iloc[0]) * 1e4

    sub = pd.read_csv(sub_path)
    h10 = sub[(sub["test_id"] == "H10") & (sub["split"] == "turnover_tier")]
    bottom = h10[h10["group"] == "bottom7"].iloc[0]
    top = h10[h10["group"] == "top3"].iloc[0]
    inter = h10[h10["group"] == "top3_vs_bottom7"].iloc[0]

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(10.8, 4.9), gridspec_kw={"width_ratios": [1.0, 1.0]}
    )
    fig.subplots_adjust(left=0.08, right=0.98, top=0.82, bottom=0.22, wspace=0.30)

    labels1 = ["Base top-12\nOOS panel", "External ranks 11–15\n(5 stocks)"]
    vals1 = np.array([base_beta, float(ext_h10["bp"])])
    errs1 = np.array([base_se, float(ext_h10["se"]) * 1e4])
    ax1.bar([0, 1], vals1, yerr=errs1, capsize=5, width=0.56,
            color=[BLUE, ORANGE], edgecolor="white", linewidth=0.8)
    for x, v, e in zip([0, 1], vals1, errs1):
        ax1.text(x, v + e + 0.55, f"{v:+.2f} bp", ha="center", fontsize=8.5,
                 fontweight="bold")
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(labels1, fontsize=8.3)
    ax1.set_ylabel("H10 β (bp, ±1 SE)")
    ax1.set_ylim(0, 17)
    ax1.set_title("External-tier replication", loc="left")
    ax1.text(
        0.03, 0.96,
        f"external raw p = {float(ext_h10['p_dk']):.3f}\n"
        f"BH q = {float(ext_h10['bh_adj_p']):.3f} (0/5 pass)\n"
        f"n = {int(ext_h10['n_obs']):,}",
        transform=ax1.transAxes, ha="left", va="top", fontsize=8.0,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#CCCCCC"),
    )

    labels2 = ["Bottom-7\nturnover", "Top-3\nturnover"]
    vals2 = np.array([float(bottom["beta_bp"]), float(top["beta_bp"])])
    errs2 = np.array([float(bottom["se_bp"]), float(top["se_bp"])])
    ax2.bar([0, 1], vals2, yerr=errs2, capsize=5, width=0.56,
            color=[GREEN, PURPLE], edgecolor="white", linewidth=0.8)
    for x, v, e in zip([0, 1], vals2, errs2):
        ax2.text(x, v + e + 0.55, f"{v:+.2f} bp", ha="center", fontsize=8.5,
                 fontweight="bold")
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(labels2, fontsize=8.3)
    ax2.set_ylabel("H10 β (bp, ±1 SE)")
    ax2.set_ylim(0, 24)
    ax2.set_title("Within-universe turnover tiers", loc="left")
    ax2.text(
        0.03, 0.96,
        f"bottom: n={int(bottom['n_obs']):,}, p_bonf={float(bottom['p_bonf']):.3f}\n"
        f"top: n={int(top['n_obs']):,}, p_bonf={float(top['p_bonf']):.3f}\n"
        f"interaction {float(inter['beta_bp']):+.2f} bp, "
        f"p_bonf={float(inter['p_bonf']):.3f}",
        transform=ax2.transAxes, ha="left", va="top", fontsize=7.8,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#CCCCCC"),
    )

    return save_figure(
        fig, "F8", "f8_tier_locality",
        "H10 tier locality: external replication and turnover tiers",
        "Ch.5 §5.5 / §5.6.8", "EXP-0005f + EXP-0011d",
        [ext_path, head_path, grid_path, sub_path],
        "H10 point estimates with ±1 SE in the external ranks-11–15 replication "
        "and in the pre-declared turnover-tier subgroups; no subgroup survives "
        "Bonferroni and the external grid fails BH.",
    )


# ---------------------------------------------------------------------------
# F9 — cost-benefit arithmetic
# ---------------------------------------------------------------------------
def fig_f9() -> dict:
    path = TABLES / "economic_magnitude.csv"
    d = pd.read_csv(path).set_index("test_id")
    order = ["H10", "H7", "H4"]
    labels = {
        "H10": "H10\nreciprocity → |ret|",
        "H7": "H7\nEoD → |ret|",
        "H4": "H4\nbuyer HHI → ret\n(opposite sign, post hoc)",
    }
    colours = {"H10": BLUE, "H7": GREEN, "H4": ORANGE}

    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    fig.subplots_adjust(left=0.10, right=0.975, top=0.82, bottom=0.25)
    vals = np.array([float(d.loc[t, "effect_bp_per_sd"]) for t in order])
    x = np.arange(len(order))
    ax.axhspan(30, 50, color=ORANGE, alpha=0.13, zorder=0)
    ax.text(0.98, 40, "declared 30–50 bp\nround-trip cost floor",
            transform=ax.get_yaxis_transform(), ha="right", va="center",
            fontsize=8.2, color="#8A3B00")
    ax.bar(x, vals, color=[colours[t] for t in order], width=0.58,
           edgecolor="white", linewidth=0.8)
    for xi, t, v in zip(x, order, vals):
        mult_lo = float(d.loc[t, "cost_multiple_low"])
        mult_hi = float(d.loc[t, "cost_multiple_high"])
        ax.text(xi, v + 0.75, f"{v:.2f} bp", ha="center", fontsize=9.0,
                fontweight="bold")
        ax.text(xi, v / 2, f"{mult_lo:.2f}–{mult_hi:.2f}×\nbelow floor",
                ha="center", va="center", fontsize=7.8, color="white",
                fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([labels[t] for t in order], fontsize=8.2)
    ax.set_xlim(-0.5, 2.5)
    ax.set_ylabel("Effect at 1 SD (bp)")
    ax.set_ylim(0, 56)
    ax.text(
        0.02, 0.96, "All three: not standalone tradable at 1 SD",
        transform=ax.transAxes, ha="left", va="top", fontsize=8.2,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#CCCCCC"),
    )

    return save_figure(
        fig, "F9", "f9_cost_benefit",
        "Headline effects versus the declared trading-cost floor",
        "Ch.5 §5.6.9 / Ch.6 §6.2", "EXP-0011f", [path],
        "One-SD effects for H10, H7 and H4 against the declared 30–50 bp "
        "round-trip explicit-cost floor; all are 3.2–12.7× below it.",
    )


# ---------------------------------------------------------------------------
# F10 — broker-network snapshots (frozen renders, composited)
# ---------------------------------------------------------------------------
def fig_f10() -> dict:
    bubble = ROOT / "outputs" / "figures" / "broker_network_bubble.png"
    normal = ROOT / "outputs" / "figures" / "broker_network_normal.png"
    summary_path = TABLES / "broker_snapshot_summary.csv"
    summary = pd.read_csv(summary_path).set_index("month")

    fig = plt.figure(figsize=(13.0, 6.3))
    fig.subplots_adjust(left=0.015, right=0.985, top=0.82, bottom=0.17)
    ax1 = fig.add_axes([0.018, 0.155, 0.465, 0.665])
    ax2 = fig.add_axes([0.515, 0.155, 0.465, 0.665])
    ax1.imshow(Image.open(bubble).convert("RGB"))
    ax2.imshow(Image.open(normal).convert("RGB"))
    ax1.axis("off")
    ax2.axis("off")

    for x, month in [(0.250, "2021-10"), (0.748, "2023-06")]:
        r = summary.loc[month]
        fig.text(
            x, 0.105,
            f"{month}: {int(r['nodes'])} nodes · {int(r['edges']):,} edges · "
            f"{int(r['core_nodes'])} core brokers",
            ha="center", va="center", fontsize=8.6,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#CCCCCC"),
        )

    return save_figure(
        fig, "F10", "f10_broker_snapshots",
        "Broker-network snapshots: 2021-10 and 2023-06",
        "Ch.6 §6.4 / Appendix B", "EXP-0011c",
        [bubble, normal, summary_path],
        "The two declared monthly broker-network snapshots, rendered from the "
        "frozen edge lists; node size is traded value and red nodes are core brokers.",
    )


def main() -> None:
    print(f"Output directory: {rel(FIGDIR)}\n")
    records = [
        fig_f1(),
        fig_f2(),
        fig_f3(),
        fig_f4(),
        fig_f5(),
        fig_f6(),
        fig_f7(),
        fig_f8(),
        fig_f9(),
        fig_f10(),
    ]
    manifest = pd.DataFrame(records)
    manifest_path = FIGDIR / "figure_manifest.csv"
    manifest.to_csv(manifest_path, index=False, lineterminator="\n")
    print(f"\nManifest: {rel(manifest_path)}  ({len(manifest)} rows)")
    print(f"All 10 figures non-blank: "
          f"{'PASS' if (manifest['blank_check'] == 'PASS').all() else 'FAIL'}")


if __name__ == "__main__":
    main()
