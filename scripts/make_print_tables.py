#!/usr/bin/env python
"""Build print-ready thesis table CSVs from frozen artefacts.

Contract
--------
This script performs NO estimation, testing, re-fitting or robustness work.
Every output is either (a) a column/row projection of an existing frozen CSV,
(b) a unit conversion of an existing frozen column, or (c) a transcription of
values already stated in a frozen plan/handoff document.  It never writes to
`outputs/tables/`.

Run:
    nepse-msc/bin/python scripts/make_print_tables.py
"""
from __future__ import annotations

import hashlib
import io
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "chapter_assets" / "print_tables"
OUT.mkdir(parents=True, exist_ok=True)

MANIFEST: list[dict[str, str]] = []
GENERATED_UTC = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def src(*rel: str) -> list[Path]:
    paths = [ROOT / p for p in rel]
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(p)
    return paths


def read(rel: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / rel, **kwargs)


def table_number_key(test_id: str) -> int:
    return int(str(test_id).lstrip("H"))


def fmt_bp(x) -> str:
    return "" if pd.isna(x) else f"{float(x):.3f}"


def fmt_p(x) -> str:
    if pd.isna(x):
        return ""
    x = float(x)
    if x < 0.0001:
        return "<0.0001"
    return f"{x:.4f}"


def fmt_ratio(x, digits: int = 4) -> str:
    return "" if pd.isna(x) else f"{float(x):.{digits}f}"


def fmt_pct(x, digits: int = 2) -> str:
    return "" if pd.isna(x) else f"{float(x) * 100:.{digits}f}%"


def fmt_int(x) -> str:
    return "" if pd.isna(x) else str(int(round(float(x))))


def yesno(x) -> str:
    if pd.isna(x):
        return ""
    return "yes" if bool(x) else "no"


def sign_label(x) -> str:
    return {"pos": "+", "neg": "-", "amb": "ambiguous"}.get(str(x), str(x))


def order_label(x) -> str:
    return {
        "positive": "positive",
        "negative": "negative",
        "ambiguous": "ambiguous",
    }.get(str(x), str(x))


FEATURE_LABEL = {
    "self_loop_ratio": "Self-loop volume ratio",
    "anomaly_score": "IF anomaly score",
    "buyer_hhi": "Buyer HHI",
    "reciprocity": "Reciprocity",
    "end_of_day_concentration": "End-of-day concentration",
}
OUTCOME_LABEL = {
    "ret_fwd1": "Return (t+1)",
    "abs_ret_fwd1": "|Return| (t+1)",
}
STREAM_LABEL = {
    "NET": "Broker networks and intermediation",
    "LIQ": "Liquidity, concentration and microstructure",
    "MAN": "Manipulation and closing prices",
    "EM": "Emerging and frontier markets",
    "NP": "Nepal / NEPSE evidence",
}


def emit(
    table_id: str,
    title: str,
    chapter: str,
    filename: str,
    df: pd.DataFrame,
    sources: list[Path],
    transform: str,
    rounding: str,
    footnotes: str,
    status: str = "DERIVED_PROJECTION",
) -> None:
    out = OUT / filename
    df.to_csv(out, index=False, lineterminator="\n", encoding="utf-8")
    MANIFEST.append(
        {
            "table_id": table_id,
            "title": title,
            "chapter": chapter,
            "filename": filename,
            "source_artifacts": ";".join(str(p.relative_to(ROOT)) for p in sources),
            "source_sha256": ";".join(sha256(p) for p in sources),
            "output_sha256": sha256(out),
            "n_rows": str(len(df)),
            "n_cols": str(len(df.columns)),
            "transform": transform,
            "rounding": rounding,
            "footnotes": footnotes,
            "status": status,
            "generated_utc": GENERATED_UTC,
        }
    )
    print(f"{table_id:8s} {filename:48s} {len(df):4d} rows x {len(df.columns):2d} cols")


# ---------------------------------------------------------------------------
# Chapter 1
# ---------------------------------------------------------------------------
v2_grid = read("outputs/tables/hypothesis_grid_results_v2.csv")
final = read("outputs/tables/v2_final_headline_set.csv", keep_default_na=False)

m = v2_grid.merge(
    final[["hypothesis", "final_classification"]],
    left_on="test_id",
    right_on="hypothesis",
    validate="one_to_one",
)
t11 = pd.DataFrame(
    {
        "hypothesis": m["test_id"],
        "feature": m["feature"].map(FEATURE_LABEL),
        "outcome": m["outcome"].map(OUTCOME_LABEL),
        "predicted_direction": m["predicted_sign"].map(sign_label),
        "effect_bp_per_sd": m["bp"].map(fmt_bp),
        "dk_p": m["p_dk"].map(fmt_p),
        "bh_q": m["bh_adj_p"].map(fmt_p),
        "bh_pass_q10": m["bh_sig_q10"].map(yesno),
        "final_classification": m["final_classification"],
    }
).sort_values("hypothesis", key=lambda s: s.map(table_number_key))
emit(
    "Table 1.1",
    "Pre-declared hypothesis grid and final classification",
    "Ch.1 Introduction",
    "table_1_1_hypothesis_grid.csv",
    t11,
    src("outputs/tables/hypothesis_grid_results_v2.csv", "outputs/tables/v2_final_headline_set.csv"),
    "Projection: test_id, feature, outcome, predicted_sign, bp, p_dk, bh_adj_p, bh_sig_q10 from the v2 grid; final_classification merged one-to-one from the canonical headline set.",
    "bp 3 dp; p/q 4 dp with '<0.0001' floor; counts not present.",
    "bp = basis points per 1 TRAIN-fold standard deviation of the feature. DK = Driscoll-Kraay (bw=5). BH q = Benjamini-Hochberg adjusted p over the family of 10. Positive/negative signs are the pre-declared direction; H6 was declared ambiguous.",
)

t12 = pd.DataFrame(
    {
        "hypothesis": final["hypothesis"],
        "pre_declared_direction": final["pre_declared_direction"].map(order_label),
        "effect_bp_per_sd": final["estimated_beta"].map(fmt_bp),
        "dk_p": final["dk_p"].map(fmt_p),
        "rw_p": final["rw_p"].map(fmt_p),
        "wild_bootstrap_p": final["wild_bootstrap_p"].map(fmt_p),
        "se_concordance": final["se_concordance"],
        "final_classification": final["final_classification"],
    }
).sort_values("hypothesis", key=lambda s: s.map(table_number_key))
emit(
    "Table 1.2",
    "Canonical headline preview",
    "Ch.1 Introduction",
    "table_1_2_headline_preview.csv",
    t12,
    src("outputs/tables/v2_final_headline_set.csv"),
    "Projection: eight brief columns from the 11-column canonical headline set.",
    "beta 3 dp; p 4 dp with '<0.0001' floor.",
    "RW = Romano-Wolf stepdown p (B=999, family of 10); wild bootstrap = entity-clustered wild cluster bootstrap p (symbol clusters, B=999). Full 11-column version is Table 5.3.",
)

econ = read("outputs/tables/economic_magnitude.csv")
t13 = pd.DataFrame(
    {
        "hypothesis": econ["test_id"],
        "effect_bp_per_sd": econ["effect_bp_per_sd"].map(fmt_bp),
        "direction": econ["direction"],
        "cost_floor_low_bp": econ["cost_low_bp"].map(fmt_int),
        "cost_floor_high_bp": econ["cost_high_bp"].map(fmt_int),
        "multiple_below_floor_low": econ["cost_multiple_low"].map(lambda x: fmt_ratio(x, 2)),
        "multiple_below_floor_high": econ["cost_multiple_high"].map(lambda x: fmt_ratio(x, 2)),
        "standalone_tradable_at_1sd": econ["standalone_tradable_at_1sd"].map(yesno),
    }
)
emit(
    "Table 1.3",
    "Economic magnitude versus the declared cost floor",
    "Ch.1 Introduction",
    "table_1_3_economic_magnitude.csv",
    t13,
    src("outputs/tables/economic_magnitude.csv"),
    "Projection: eight columns from economic_magnitude.csv; no annualisation and no new cost calculation.",
    "effect 3 dp; multiples 2 dp; cost floor integer bp.",
    "Cost floor = 30-50 bp round-trip explicit cost, a floor that excludes brokerage, bid-ask spread and CNS carry. Effects are at 1 TRAIN-SD of the feature. H4 is opposite-sign post hoc.",
)


# ---------------------------------------------------------------------------
# Chapter 3 -- design tables (transcribed from frozen plans) and data tables
# ---------------------------------------------------------------------------
t30_rows = [
    ("Observation unit", "symbol-session (daily)", "docs/analysis_plan.md §1", "Floorsheet rows are aggregated to one row per symbol and session."),
    ("Window", "2021-01-03 to 2024-12-31", "docs/analysis_plan.md §1; docs/reproducibility.md", "940 DC3 calendar sessions; 938 have corpus coverage."),
    ("Headline panel", "12 symbols; 723 dates; 7,116 rows", "outputs/tables/hypothesis_grid_results_v2.csv", "The panel is the per-fold top-10 universe, not the 530-symbol market."),
    ("Effective N", "6,383", "outputs/tables/hypothesis_grid_results_v2.csv", "n_obs - (n_stocks - 1) - (n_dates - 1) = 7,116 - 11 - 722."),
    ("Network features", "self-loop ratio; buyer HHI; reciprocity; end-of-day concentration", "docs/analysis_plan.md §2", "Definitions in Table 3.3."),
    ("Anomaly feature", "Isolation Forest score (200 trees, TRAIN-fold fit)", "docs/analysis_plan.md §4", "Scored with -decision_function on both sides."),
    ("Outcomes", "ret_fwd1; abs_ret_fwd1", "docs/analysis_plan.md §2", "Next-session close-to-close return and its absolute value."),
    ("Baseline controls", "log_volume; market_ret_loo", "docs/analysis_plan.md §2", "Leave-one-out equal-weight market return."),
    ("v2 liquidity controls", "Amihud; Roll; Corwin-Schultz", "docs/analysis_plan_v2_extension.md §V2-2", "Three trailing proxies; no quoted spreads."),
    ("Fixed effects", "symbol + date", "docs/analysis_plan.md §3", "PanelOLS with absorbed entity and time effects."),
    ("Primary inference", "Driscoll-Kraay, Bartlett bandwidth 5", "docs/analysis_plan.md §3", "DK(bw=5) is the primary standard error."),
    ("Concordance inference", "DC-v2; Fama-MacBeth; wild cluster bootstrap", "docs/analysis_plan_v2_extension.md §V2-1", "Each is a concordance check, not a replacement primary."),
    ("Multiplicity", "BH q=.10 (v1); Romano-Wolf q=.10 (v2)", "docs/analysis_plan.md §2; docs/analysis_plan_v2_extension.md §V2-1", "BH is the v1 gate; RW is the family-wise v2 gate."),
    ("Validation design", "4 anchored folds; 6-session purge; 7,126 OOS rows; 686 events", "docs/analysis_plan.md §4", "Warm-up chunk is never tested."),
]
t30 = pd.DataFrame(t30_rows, columns=["item", "value", "source", "note"])
emit(
    "Table 3.0",
    "Design summary",
    "Ch.3 Methodology",
    "table_3_0_design_summary.csv",
    t30,
    src("docs/analysis_plan.md", "docs/analysis_plan_v2_extension.md", "docs/reproducibility.md", "outputs/tables/hypothesis_grid_results_v2.csv"),
    "Manual transcription of design constants already stated in the frozen plans and the v2 grid.",
    "Counts as integers; no statistical quantity is recomputed.",
    "This table is a typeset index of declared design choices. The binding sources remain docs/analysis_plan.md and docs/analysis_plan_v2_extension.md.",
    status="MANUAL_TRANSCRIPTION_FROM_FROZEN_PLAN",
)

t31_rows = [
    ("2026-11-08", "v1 analysis plan frozen before any test-fold data was scored", "docs/analysis_plan.md", "DC20; initial config fingerprint 29a43e8c."),
    ("2026-11-09", "Fold mode amended sequential -> anchored before scoring", "commit 26ad798; deviation #1", "Purge gap remains 6 sessions."),
    ("2026-11-10", "v2 extension pre-declared before any v2 result", "docs/analysis_plan_v2_extension.md", "Binding v2 protocols and seed ranges."),
    ("2026-11-11 to 2026-11-12", "v2 Stages 1-4 executed", "EXP-0008a to EXP-0011f", "Classification, dependence, distributional and heterogeneity checks."),
    ("2026-11-12", "Stage-5 canonical headline set and chapter skeletons", "EXP-0012", "Final composition rule applied."),
    ("2026-11-12/13", "Stage-6 clean rebuild and numerical-equivalence audit", "EXP-0013; docs/reproducibility.md", "21/21 steps exit 0; 3,749.9 s."),
    ("2026-11-13", "v2.0.1 verified chapter-to-artefact crosswalk", "EXP-0014; docs/chapter_artifact_map.md", "67 claims; hash audit."),
    ("2026-11-13", "v2.0.2 pre-write asset sprint", "this sprint", "No new analysis; assets, skeletons, tables, figures and checks only."),
]
t31 = pd.DataFrame(t31_rows, columns=["date", "event", "artifact", "note"])
emit(
    "Table 3.1",
    "Pre-declaration and freeze timeline",
    "Ch.3 Methodology",
    "table_3_1_predeclaration_timeline.csv",
    t31,
    src("docs/analysis_plan.md", "docs/analysis_plan_v2_extension.md", "docs/experiment_register.md", "docs/analysis_deviations.md"),
    "Manual timeline transcription from the frozen plan headers, experiment register and deviation log.",
    "Dates as ISO-8601 where known.",
    "The timeline is chronological, not a claim of priority over the experiment register. EXP rows are authoritative for experiment dates.",
    status="MANUAL_TRANSCRIPTION_FROM_FROZEN_PLAN",
)

fold = read("outputs/tables/anomaly_scoring_summary.csv")
t32 = pd.DataFrame(
    {
        "fold": fold["fold_id"].map(fmt_int),
        "mode": fold["mode"],
        "n_symbols": fold["n_universe"].map(fmt_int),
        "n_train_rows": fold["n_train_complete"].map(fmt_int),
        "n_test_rows": fold["n_test_complete"].map(fmt_int),
        "train_q90_threshold": fold["score_threshold_q90_train"].map(lambda x: fmt_ratio(x, 4)),
        "n_test_events": fold["n_test_events"].map(fmt_int),
        "test_event_share": fold["event_share_test"].map(lambda x: fmt_ratio(x, 4)),
        "train_window": fold["train_dates"],
        "test_window": fold["test_dates"],
        "universe_symbols": fold["universe"],
    }
)
emit(
    "Table 3.2",
    "Anchored walk-forward folds and out-of-sample counts",
    "Ch.3 Methodology",
    "table_3_2_fold_boundaries.csv",
    t32,
    src("outputs/tables/anomaly_scoring_summary.csv"),
    "Projection: fold_id, mode, universe counts/dates and OOS event counts from the frozen scoring summary.",
    "counts integer; threshold and share 4 dp.",
    "The q90 threshold is fitted on TRAIN rows only. Fold 0 is the warm-up train chunk and is never tested; the four scored folds are 0-3 in the source table's test rows. 12 unique symbols appear across the four fold universes. 2023-02-16 is excluded from ordering-dependent features.",
)

feature_raw = (ROOT / "reports/chapter_assets/ch3_feature_dictionary.csv").read_text(encoding="utf-8")
# The audited source line 4 has an unquoted comma in its final `notes` field.
# Quote only that field so the print copy is valid CSV; no value is changed.
feature_fixed = feature_raw.replace(
    "EXP-0003a,2*sum(min(w_ij,w_ji))/sum(all weights)",
    'EXP-0003a,"2*sum(min(w_ij,w_ji))/sum(all weights)"',
)
t33 = pd.read_csv(io.StringIO(feature_fixed), keep_default_na=False)
emit(
    "Table 3.3",
    "Feature and outcome dictionary",
    "Ch.3 Methodology",
    "table_3_3_feature_dictionary.csv",
    t33,
    src("reports/chapter_assets/ch3_feature_dictionary.csv"),
    "Verbatim copy of the 13-row feature dictionary with the malformed final field of the reciprocity row correctly quoted. No definition, formula or note is edited.",
    "Text only; no numeric rounding.",
    "Source line 4 is not valid CSV as committed (an unquoted comma in `notes`). The print copy quotes that field only; the audited source is left untouched. `self_loop_ratio` is a self-loop volume share, not a wash-trading measure.",
    status="VERBATIM_COPY_WITH_CSV_QUOTING_FIX",
)

t34_rows = [
    ("Driscoll-Kraay (DK)", "Bartlett kernel HAC; bandwidth 5; entity and time FE absorbed", "Primary", "alpha=.05; BH q=.10", "EXP-0004b"),
    ("Two-way cluster (DC-v2)", "Entity and time two-way cluster covariance", "Concordance", "p<.10 in the four-estimator count", "EXP-0009d"),
    ("Fama-MacBeth (FM)", "Cross-sectional slope series; full-rank date slices only", "Concordance", "p<.10 in the four-estimator count", "EXP-0004b; EXP-0009d"),
    ("Wild cluster bootstrap (WB)", "Entity/symbol clusters; B=999; ReBWB", "Concordance", "p<.10; 12-cluster small-G caveat", "EXP-0009c"),
    ("Romano-Wolf (RW)", "Stepdown max-t over the family of 10; B=999", "Family-wise gate", "q=.10", "EXP-0008b"),
    ("Benjamini-Hochberg (BH)", "Step-up FDR over the family of 10", "v1 gate", "q=.10", "EXP-0004b"),
]
t34 = pd.DataFrame(t34_rows, columns=["estimator", "assumption_or_construction", "role", "decision_rule", "exp_id"])
emit(
    "Table 3.4",
    "Estimator and inference matrix",
    "Ch.3 Methodology",
    "table_3_4_estimator_matrix.csv",
    t34,
    src("docs/analysis_plan.md", "docs/analysis_plan_v2_extension.md", "docs/experiment_register.md"),
    "Manual transcription of estimator roles and decision rules from the frozen plans and register.",
    "Alpha/q values as declared.",
    "DK is primary. DC-v2, FM and WB are concordance checks. RW is the v2 family-wise gate; BH is retained as the v1 gate. WB has only 12 symbol clusters.",
    status="MANUAL_TRANSCRIPTION_FROM_FROZEN_PLAN",
)

t35_rows = [
    ("Event-study reconstruction", "Rebuild stored v1 ARs/CARs without re-estimation", "Integrity gate", "PASS: max |reconstructed - stored| = 0.0", "EXP-0011e"),
    ("BMP test", "Prediction-error variance; cross-sectional t", "Added inference", "Mean CAR null (p=.240)", "EXP-0011e"),
    ("Corrado rank test", "Rank each event-window AR among estimation + event ARs", "Added inference", "Rank z=3.158 (p=.0016); date-clustered z=2.522 (p=.0120)", "EXP-0011e"),
    ("Leave-one-stock-out", "Drop each of 12 symbols in turn", "Robustness", "5/5 headlines sign-stable 12/12", "EXP-0005a"),
    ("Alternative horizons", "t+2, t+3, t+5; BH per horizon", "Robustness", "BH pass 0/5, 0/5, 1/5 (H7 at t+5)", "EXP-0005b"),
    ("Alternative EoD thresholds", "Top 1% and top 10% by contract_no", "Robustness", "H7 robust; H8 collapses at 1%", "EXP-0005c"),
    ("Alternative anomaly scorers", "Mahalanobis; diag-z^2; LOF; OC-SVM", "Descriptive", "Rank correlation vs IF: +.83/+.95/+.60/+.54", "EXP-0005d"),
    ("Drop-bubble re-fit", "Normal era only (2023+)", "Robustness", "H4/H6/H7/H10 survive BH; H8 fails", "EXP-0005e"),
    ("External top-5", "Ranks 11-15 of the same TRAIN turnover ranking", "Falsification", "0/5 BH pass; raw p >= .23", "EXP-0005f"),
    ("Sequential fold variant", "Rolling pairs; 2021-07 to 2023-06 coverage", "Descriptive", "Pooled Spearman +.87 vs anchored", "EXP-0005g"),
]
t35 = pd.DataFrame(t35_rows, columns=["protocol", "declared_variant", "role", "verdict", "exp_id"])
emit(
    "Table 3.5",
    "Event-study and robustness protocol matrix",
    "Ch.3 Methodology",
    "table_3_5_protocol_matrix.csv",
    t35,
    src("docs/analysis_plan.md", "docs/analysis_plan_v2_extension.md", "docs/experiment_register.md"),
    "Manual transcription of protocol names, declared variants and verdicts from the frozen plans and register.",
    "Statistics as reported in the cited EXP rows.",
    "Verdicts are summaries of registered results, not new tests. The event-study p-values remain upper bounds because 68.2% of events share a date.",
    status="MANUAL_TRANSCRIPTION_FROM_FROZEN_PLAN",
)


# ---------------------------------------------------------------------------
# Chapter 4
# ---------------------------------------------------------------------------
timings = read("outputs/logs/v2_stage6_rebuild_timings.csv")
t40 = pd.DataFrame(
    {
        "step_order": range(1, len(timings) + 1),
        "step": timings["step"],
        "script": timings["script"],
        "duration_s": timings["duration_s"].map(lambda x: f"{float(x):.1f}"),
        "exit_code": timings["exit_code"].map(fmt_int),
    }
)
emit(
    "Table 4.0",
    "Stage-6 clean-rebuild steps and timings",
    "Ch.4 Data engineering",
    "table_4_0_pipeline_timings.csv",
    t40,
    src("outputs/logs/v2_stage6_rebuild_timings.csv", "docs/reproducibility.md"),
    "Projection: ordered step, script, duration and exit code from the local Stage-6 timing log. Step order is the driver's ordered STEPS list.",
    "Duration 1 dp; exit code integer.",
    "The timing log is local evidence and is gitignored; this CSV is the tracked print projection. Total wall time was 3,749.9 s (62.5 min), 21/21 steps exit 0. No step was re-run to make this table.",
)

licence_rows = [
    (
        "viking303 floorsheets 2021-2023",
        "Primary floorsheet corpus",
        "CC0: Public Domain",
        "UNCERTAIN: merolagani",
        "Permitted",
        "Permitted",
        "Permitted on the dataset grant; upstream caution",
        "https://www.kaggle.com/api/v1/datasets/view/viking303/nepse-historical-floorsheet",
    ),
    (
        "socrateai 2024 floorsheets",
        "2024 floorsheet corpus",
        "MIT (modified wording; GitHub NOASSERTION)",
        "UNCERTAIN: NEPSE/merolagani",
        "Permitted with notice",
        "Permitted with notice",
        "Permitted with notice",
        "https://raw.githubusercontent.com/socrateai-official/nepse-open-data/main/LICENSE",
    ),
    (
        "Kaggle rohankasichhwa OHLCV (tier1)",
        "Prices / outcomes",
        "MIT (Kaggle metadata); description says educational/research",
        "UNCERTAIN: NEPSE Alpha",
        "Permitted",
        "Permitted for thesis; conditional for public redistribution",
        "Derived tables permitted; raw OHLCV not deposited",
        "https://www.kaggle.com/api/v1/datasets/view/rohankasichhwa/nepse-daily-stock-data-2012-2025",
    ),
    (
        "SamirWagle OHLCV (tier2)",
        "Gap-fill only",
        "None (license:null); README 'License: Educational'",
        "UNCERTAIN: ShareSansar/Merolagani",
        "Conditional: stated educational intent, no formal grant",
        "Uncertain; avoid material reliance",
        "Not permitted without permission",
        "https://api.github.com/repos/SamirWagle/Nepse-All-Scraper",
    ),
    (
        "menaceXnadin NEPSE index",
        "Secondary regime shading/benchmark",
        "None (license:null); 'unofficial mirror'",
        "UNCERTAIN: ShareHub/NEPSE",
        "Internal academic use only",
        "Uncertain; not used in F1-F10",
        "Not permitted without permission",
        "https://api.github.com/repos/menaceXnadin/nepse-historical-market-data-csv",
    ),
    (
        "Thesis code",
        "Analysis code and deposit",
        "MIT (repository LICENSE)",
        "Not applicable",
        "Permitted",
        "Not applicable",
        "Permitted with notice",
        "LICENSE",
    ),
]
t41 = pd.DataFrame(
    licence_rows,
    columns=[
        "source",
        "role",
        "licence_as_declared",
        "upstream_status",
        "academic_use",
        "thesis_figures",
        "deposit_redistribution",
        "evidence_url",
    ],
)
t41["retrieved_utc"] = "2026-11-13T10:21:13Z"
emit(
    "Table 4.1",
    "Source and licence matrix",
    "Ch.4 Data engineering",
    "table_4_1_licence_matrix.csv",
    t41,
    src("reports/licence_review.md", "LICENSE", "data/metadata/provenance_manifest.csv"),
    "Manual transcription of the live licence review into a six-source matrix; every quoted status is traceable to reports/licence_review.md.",
    "Text only; no numeric rounding.",
    "Supersedes the 'tier1 pending' wording in reports/limitations.md L4 and the Ch.4 pack: the live Kaggle metadata declares MIT, while upstream NEPSE Alpha remains UNCERTAIN. The provenance manifest remains authoritative per file. Retrieved 2026-11-13T10:21:13Z.",
    status="MANUAL_TRANSCRIPTION_FROM_VERIFIED_SOURCE",
)

audit_rows = [
    ("Raw floorsheet rows ingested", "57927926", "rows", "EXP-0002b", "36,706,934 Kaggle + 21,220,992 socrateai."),
    ("Rows after deduplication", "57892630", "rows", "EXP-0002c", "Page-split duplicates dropped."),
    ("Duplicate rows dropped", "35296", "rows", "EXP-0002c", "Dedupe key = (date, symbol, contract_no)."),
    ("Day files ingested", "1167", "files", "EXP-0002b", "576 raw-slice extracts plus archive files."),
    ("Distinct symbols", "530", "symbols", "EXP-0002c", "Corpus-wide, not the headline panel."),
    ("Calendar sessions covered", "938", "sessions of 940", "EXP-0002b", "Gaps: 2021-09-01 and 2023-11-27."),
    ("Duplicate keys", "752", "keys", "EXP-0002c", "Duplicate (date, symbol, contract_no) keys."),
    ("Exact duplicate keys dropped", "506", "keys", "EXP-0002c", "Full-signature duplicates."),
    ("Signature-conflict keys kept non-merged", "246", "keys", "EXP-0002c", "Deterministic full-signature pick."),
    ("Junk (symbol, date) pairs", "19", "pairs", "EXP-0002c", "All numerics empty; kept in raw with NULL volume."),
    ("Empty-symbol rows", "4", "rows", "EXP-0002c", "Junk scrape rows."),
    ("2023-02-16 contract-id defect rows", "35043", "rows", "EXP-0002c", "All share one transaction id; ordering features exclude the day."),
    ("Low-activity symbol-days", "114167", "pairs", "EXP-0002f", "Fewer than 100 trades; included by default."),
    ("Missing broker-ID symbol-days", "19", "pairs", "EXP-0002c", "NULL volume; no aggregation touches them."),
    ("Dotted broker-ID rows", "275590", "rows", "EXP-0011c", "15 days; canonicalised Xs.0 -> zero-padded integer."),
    ("Out-of-sample rows affected by dotted IDs", "37", "rows of 7116", "EXP-0011c", "0.52%; leave-out signs unchanged, H8 p .0563."),
]
t42 = pd.DataFrame(audit_rows, columns=["metric", "value", "unit", "exp_id", "note"])
emit(
    "Table 4.2",
    "Corpus quality audit summary",
    "Ch.4 Data engineering",
    "table_4_2_corpus_audit.csv",
    t42,
    src(
        "reports/chapter_assets/ch4_data_engineering_pack.md",
        "outputs/tables/corpus_daily_summary.csv",
        "outputs/tables/corpus_duplicate_keys.csv",
        "outputs/tables/corpus_missing_broker_ids.csv",
        "outputs/tables/corpus_low_activity_days.csv",
        "outputs/tables/corpus_symbol_coverage.csv",
    ),
    "Transcription of counts already reported in the Ch.4 handoff pack and experiment register; no audit is re-run.",
    "Counts as plain integers; no thousands separators.",
    "Counts are exact integers. 'Low-activity' means fewer than 100 trades on a symbol-day and is not an exclusion. The defect day remains in level aggregates but is excluded from ordering-dependent features.",
    status="DOCUMENTED_CONSTANTS",
)

recon_rows = [
    ("Reconciliation pairs in file", "11283", "pairs", "All symbol-days in the top-12 scope."),
    ("Both-side pairs with volume ratio", "10909", "pairs", "374 pairs lack one side."),
    ("Median volume ratio", "1.0000", "ratio", "Floorsheet volume counts the buyer side."),
    ("Pairs in [0.95, 1.25]", "10538", "pairs", "96.5991% of both-side pairs."),
    ("Pairs in [0.98, 1.02]", "10332", "pairs", "94.7108% of both-side pairs."),
    ("Median amount ratio", "1.0000", "ratio", "Rupee amount reconciliation."),
    ("Maximum volume ratio", "1597.020", "ratio", "Outlier; full-market ~2x ratio is a tier1 coverage artifact."),
]
t43 = pd.DataFrame(recon_rows, columns=["metric", "value", "unit", "note"])
emit(
    "Table 4.3",
    "Volume reconciliation summary",
    "Ch.4 Data engineering",
    "table_4_3_volume_reconciliation.csv",
    t43,
    src("outputs/tables/volume_reconciliation.csv", "reports/chapter_assets/ch4_data_engineering_pack.md"),
    "Descriptive summary of the frozen reconciliation table: counts, median ratios and band shares. No estimate or test is recomputed.",
    "Ratios 4 dp; counts integer; maximum ratio 3 dp.",
    "The ~2x full-market ratio is a 100/530 tier1 coverage artifact, not double counting. The top-12 median ratio of 1.0000 verifies buyer-side volume counting.",
    status="DERIVED_DESCRIPTIVE_SUMMARY",
)

univ = read("outputs/tables/universe_selected_top10.csv")
t44a = pd.DataFrame(
    {
        "rank": univ["rank"].map(fmt_int),
        "symbol": univ["rank_symbol"],
        "mean_daily_turnover_npr": univ["mean_daily_turnover"].map(lambda x: f"{float(x):.0f}"),
        "total_turnover_npr": univ["total_turnover"].map(lambda x: f"{float(x):.0f}"),
        "coverage": univ["coverage"].map(lambda x: fmt_ratio(x, 4)),
        "role": univ["role"],
    }
)
emit(
    "Table 4.4a",
    "Universe selection ranking",
    "Ch.4 Data engineering",
    "table_4_4a_universe_selection.csv",
    t44a,
    src("outputs/tables/universe_selected_top10.csv"),
    "Projection: all 50 ranked candidates with role and coverage.",
    "Turnover 0 dp; coverage 4 dp.",
    "Selection is TRAIN-fold turnover with a >=90% coverage rule (DC1/DC2). Ranks 1-10 are the headline universe; 11-15 are the external replication tier; the remainder are reserves.",
)

excl = read("outputs/tables/universe_exclusions.csv")
t44b = pd.DataFrame(
    {
        "symbol": excl["symbol"],
        "mean_daily_turnover_npr": excl["mean_daily_turnover"].map(lambda x: f"{float(x):.0f}"),
        "total_turnover_npr": excl["total_turnover"].map(lambda x: f"{float(x):.0f}"),
        "coverage": excl["coverage"].map(lambda x: fmt_ratio(x, 4)),
        "exclusion_reason": excl["exclusion_reason"],
    }
)
emit(
    "Table 4.4b",
    "Universe exclusions",
    "Ch.4 Data engineering",
    "table_4_4b_universe_exclusions.csv",
    t44b,
    src("outputs/tables/universe_exclusions.csv"),
    "Projection: all 24 excluded symbols with coverage and declared reason.",
    "Turnover 0 dp; coverage 4 dp.",
    "All exclusions are the pre-declared DC2 coverage rule (<90% of sessions). No symbol is excluded on the outcome or on a result.",
)

drift = read("outputs/tables/v2_clean_rebuild_audit.csv")
status_order = [
    "IDENTICAL",
    "NUMERIC_EPSILON",
    "REORDERED_ONLY",
    "OPTIMIZER_DRIFT",
    "FLOAT_AGGREGATION",
    "THRESHOLD_FLIP",
]
interpretation = {
    "IDENTICAL": "Byte-identical.",
    "NUMERIC_EPSILON": "Floating-point aggregation/computation order.",
    "REORDERED_ONLY": "Same row multiset; row order differs.",
    "OPTIMIZER_DRIFT": "Statsmodels QuantReg convergence path; labels/shapes identical.",
    "FLOAT_AGGREGATION": "11 symbol totals differ by 1 unit on ~1e8 sums.",
    "THRESHOLD_FLIP": "Descriptive sequential fold-0 events 146 -> 141; anchored 686 unchanged.",
}
summary = (
    drift.groupby("status", sort=False)
    .agg(
        n_artifacts=("artifact", "size"),
        max_abs_diff=("max_abs_diff", "max"),
        max_rel_diff=("max_rel_diff", "max"),
    )
    .reindex(status_order)
    .reset_index()
)
t45a = pd.DataFrame(
    {
        "status": summary["status"],
        "n_artifacts": summary["n_artifacts"].map(fmt_int),
        "max_abs_diff": summary["max_abs_diff"].map(lambda x: "" if pd.isna(x) else f"{float(x):.2e}"),
        "max_rel_diff": summary["max_rel_diff"].map(lambda x: "" if pd.isna(x) else f"{float(x):.2e}"),
        "interpretation": summary["status"].map(interpretation),
    }
)
emit(
    "Table 4.5a",
    "Clean-rebuild drift summary",
    "Ch.4 Data engineering",
    "table_4_5a_drift_summary.csv",
    t45a,
    src("outputs/tables/v2_clean_rebuild_audit.csv", "docs/reproducibility.md"),
    "Group-by summary of the frozen 73-artifact drift audit; no rebuild is re-run.",
    "Counts integer; max differences scientific notation with 2 significant digits.",
    "Largest relative drift among the 25 NUMERIC_EPSILON artifacts is 2.03e-12 (broker_id_defect_sensitivity.csv); among the regression-table subset it is 3.55e-14. Anchored classifications are unchanged.",
    status="DERIVED_DESCRIPTIVE_SUMMARY",
)

t45b = pd.DataFrame(
    {
        "artifact": drift["artifact"],
        "frozen_sha256_12": drift["frozen_sha256"].str[:12],
        "rebuilt_sha256_12": drift["rebuilt_sha256"].str[:12],
        "frozen_rows": drift["frozen_rows"].map(fmt_int),
        "rebuilt_rows": drift["rebuilt_rows"].map(fmt_int),
        "status": drift["status"],
        "max_abs_diff": drift["max_abs_diff"].map(lambda x: "" if pd.isna(x) else f"{float(x):.2e}"),
        "max_rel_diff": drift["max_rel_diff"].map(lambda x: "" if pd.isna(x) else f"{float(x):.2e}"),
        "notes": drift["notes"],
    }
)
emit(
    "Table 4.5b",
    "Clean-rebuild drift audit, artifact detail",
    "Ch.4 Data engineering",
    "table_4_5b_drift_detail.csv",
    t45b,
    src("outputs/tables/v2_clean_rebuild_audit.csv"),
    "Projection: 73 artifact rows with 12-hex hash prefixes for print; full hashes remain in the source artifact.",
    "Hashes truncated to 12 hex characters; differences scientific notation with 2 significant digits.",
    "Use the source artifact for full 64-character hashes. Reorder-only and drift rows are retained, not hidden.",
)


# ---------------------------------------------------------------------------
# Chapter 5
# ---------------------------------------------------------------------------
t51 = pd.DataFrame(
    {
        "hypothesis": v2_grid["test_id"],
        "feature": v2_grid["feature"].map(FEATURE_LABEL),
        "outcome": v2_grid["outcome"].map(OUTCOME_LABEL),
        "n_obs": v2_grid["n_obs"].map(fmt_int),
        "n_stocks": v2_grid["n_stocks"].map(fmt_int),
        "n_dates": v2_grid["n_dates"].map(fmt_int),
        "n_effective": v2_grid["n_effective"].map(fmt_int),
        "n_fm_cross_sections": v2_grid["n_cross_sections"].map(fmt_int),
    }
).sort_values("hypothesis", key=lambda s: s.map(table_number_key))
emit(
    "Table 5.1",
    "Sample, folds and effective N",
    "Ch.5 Results",
    "table_5_1_sample_effective_n.csv",
    t51,
    src("outputs/tables/hypothesis_grid_results_v2.csv"),
    "Projection: per-hypothesis sample counts and effective N from the v2 governance grid.",
    "Counts integer.",
    "n_effective = n_obs - (n_stocks - 1) - (n_dates - 1) = 7,116 - 11 - 722 = 6,383. FM cross-sections vary 712-714 because each date slice must clear the full-rank guard. The 10 rows lost from 7,126 OOS rows are missing outcome/feature rows.",
)

t52 = pd.DataFrame(
    {
        "hypothesis": v2_grid["test_id"],
        "feature": v2_grid["feature"].map(FEATURE_LABEL),
        "outcome": v2_grid["outcome"].map(OUTCOME_LABEL),
        "predicted_direction": v2_grid["predicted_sign"].map(sign_label),
        "effect_bp_per_sd": v2_grid["bp"].map(fmt_bp),
        "dk_p": v2_grid["p_dk"].map(fmt_p),
        "fm_p": v2_grid["p_fm"].map(fmt_p),
        "bh_q": v2_grid["bh_adj_p"].map(fmt_p),
        "bh_pass_q10": v2_grid["bh_sig_q10"].map(yesno),
        "placebo_share": v2_grid["placebo_share"].map(lambda x: fmt_ratio(x, 3)),
        "sign_agrees": v2_grid["sign_agrees"].map(yesno),
        "mde_bp_80pct": v2_grid["mde_bp_80pct"].map(fmt_bp),
        "stage1_classification": v2_grid["result_classification"],
    }
).sort_values("hypothesis", key=lambda s: s.map(table_number_key))
emit(
    "Table 5.2",
    "Main hypothesis grid",
    "Ch.5 Results",
    "table_5_2_main_grid.csv",
    t52,
    src("outputs/tables/hypothesis_grid_results_v2.csv"),
    "Projection: frozen v1 estimates plus v2 governance columns from hypothesis_grid_results_v2.csv.",
    "bp 3 dp; p/q 4 dp with '<0.0001' floor; placebo share 3 dp.",
    "bp = per 1 TRAIN-SD of the feature. DK is primary; FM is a concordance check. BH q=.10 is the v1 gate. Placebo shares apply only to H2/H3 by declaration; a blank cell is not applicable. 'Sign agrees' is blank for H6 because its direction was declared ambiguous.",
)

t53 = pd.DataFrame(
    {
        "hypothesis": final["hypothesis"],
        "pre_declared_direction": final["pre_declared_direction"].map(order_label),
        "estimated_beta_bp": final["estimated_beta"].map(fmt_bp),
        "dk_p": final["dk_p"].map(fmt_p),
        "rw_p": final["rw_p"].map(fmt_p),
        "wild_bootstrap_p": final["wild_bootstrap_p"].map(fmt_p),
        "se_concordance": final["se_concordance"],
        "survives_liquidity": final["survives_liquidity"].map(yesno),
        "survives_egarch": final["survives_egarch"].map(yesno),
        "tail_concentration": final["tail_concentration"],
        "final_classification": final["final_classification"],
    }
).sort_values("hypothesis", key=lambda s: s.map(table_number_key))
emit(
    "Table 5.3",
    "Canonical final headline set",
    "Ch.5 Results",
    "table_5_3_canonical_headline_set.csv",
    t53,
    src("outputs/tables/v2_final_headline_set.csv"),
    "Projection: all 11 canonical columns, formatted for print.",
    "beta 3 dp; p 4 dp with '<0.0001' floor; flags yes/no.",
    "H10 is the sole HEADLINE_MODERATE. H4 is EXPLORATORY_POST_HOC (opposite sign to pre-declaration). H6/H7/H8 are NULL_FRAGILE. H1/H2/H3/H5/H9 are NULL_POWERED. survives_liquidity = p<.10 under the three liquidity controls; survives_egarch = sign match AND p<.10.",
)

ev = read("outputs/tables/event_study_upgraded.csv")
t54 = pd.DataFrame(
    {
        "sample": ev["sample"],
        "n_events": ev["n_events"].map(fmt_int),
        "model": ev["model"],
        "mean_car_bp": ev["mean_car"].map(lambda x: f"{float(x) * 10000:.3f}"),
        "sd_car_bp": ev["sd_car"].map(lambda x: f"{float(x) * 10000:.3f}"),
        "test": ev["test"],
        "statistic": ev["statistic"].map(lambda x: f"{float(x):.3f}"),
        "p_value": ev["p_value"].map(fmt_p),
        "note": ev["note"],
    }
)
emit(
    "Table 5.4",
    "Event-study inference",
    "Ch.5 Results",
    "table_5_4_event_study.csv",
    t54,
    src("outputs/tables/event_study_upgraded.csv"),
    "Projection: all 12 rows; CAR and SD converted from decimal returns to basis points (x10,000).",
    "CAR 3 dp in bp; test statistic 3 dp; p 4 dp with '<0.0001' floor.",
    "686 events on 393 dates; 468 events (68.2%) share a date, so event-level p-values are upper bounds. The market-adjusted mean is a pre-window-alpha artifact, not an event effect. The 16-event illiquid appendix is not a headline.",
)

rob = read("outputs/tables/robustness_headline_survival.csv")
t55 = pd.DataFrame(
    {
        "variant": rob["variant"],
        "hypothesis": rob["test_id"],
        "effect_bp_per_sd": rob["bp"].map(fmt_bp),
        "dk_p": rob["p_dk"].map(fmt_p),
        "bh_pass_q10": rob["bh_pass"].map(yesno),
        "sign_agrees": rob["sign_agrees"].map(yesno),
    }
)
emit(
    "Table 5.5",
    "Robustness battery survival",
    "Ch.5 Results",
    "table_5_5_robustness_survival.csv",
    t55,
    src("outputs/tables/robustness_headline_survival.csv"),
    "Projection: all 46 variant-by-headline rows from the frozen survival table.",
    "bp 3 dp; p 4 dp with '<0.0001' floor; flags yes/no.",
    "Variants include horizons, leave-one-stock-out, drop-bubble, external top-5 and alternative EoD thresholds. BH is evaluated within each variant family as declared; this is not a new multiplicity family.",
)

se = read("outputs/tables/se_concordance.csv", keep_default_na=False)
for col in ["p_dk", "p_dc_v2", "p_wb", "rw_p", "n_sig_p_lt_10"]:
    se[col] = pd.to_numeric(se[col], errors="coerce")
liq = read("outputs/tables/headline_with_liquidity_controls.csv")
eg = read("outputs/tables/headline_with_egarch_outcome.csv")
base = v2_grid[["test_id", "feature", "outcome", "bp", "p_dk", "p_fm"]].copy()
base = base.rename(columns={"bp": "base_bp", "p_dk": "base_dk_p", "p_fm": "fm_p"})
se_cols = se[["test_id", "p_dc_v2", "p_wb", "rw_p", "n_sig_p_lt_10", "se_concordance"]]
liq_cols = liq.loc[
    liq["spec"] == "single_feature_liquidity",
    ["test_id", "bp", "p_dk", "pct_delta", "survives_liquidity"],
].rename(
    columns={
        "bp": "liquidity_bp",
        "p_dk": "liquidity_dk_p",
        "pct_delta": "liquidity_pct_change",
        "survives_liquidity": "survives_liquidity",
    }
)
eg_cols = eg.loc[
    (eg["spec"] == "egarch_primary") & (eg["subset"] == "full"),
    ["test_id", "beta_sd_units", "p_dk", "sign_match_base", "survives_egarch"],
].rename(
    columns={
        "beta_sd_units": "egarch_beta_sd_units",
        "p_dk": "egarch_dk_p",
        "sign_match_base": "egarch_sign_match",
    }
)
comp = (
    base.merge(se_cols, on="test_id", validate="one_to_one")
    .merge(liq_cols, on="test_id", validate="one_to_one")
    .merge(eg_cols, on="test_id", validate="one_to_one")
    .sort_values("test_id", key=lambda s: s.map(table_number_key))
)
t56 = pd.DataFrame(
    {
        "hypothesis": comp["test_id"],
        "feature": comp["feature"].map(FEATURE_LABEL),
        "outcome": comp["outcome"].map(OUTCOME_LABEL),
        "base_bp_per_sd": comp["base_bp"].map(fmt_bp),
        "dk_p": comp["base_dk_p"].map(fmt_p),
        "dc_v2_p": comp["p_dc_v2"].map(fmt_p),
        "fm_p": comp["fm_p"].map(fmt_p),
        "wb_p": comp["p_wb"].map(fmt_p),
        "rw_p": comp["rw_p"].map(fmt_p),
        "n_se_significant": comp["n_sig_p_lt_10"].map(fmt_int),
        "se_concordance": comp["se_concordance"],
        "liquidity_bp": comp["liquidity_bp"].map(fmt_bp),
        "liquidity_dk_p": comp["liquidity_dk_p"].map(fmt_p),
        "liquidity_pct_change": comp["liquidity_pct_change"].map(fmt_pct),
        "survives_liquidity": comp["survives_liquidity"].map(yesno),
        "egarch_beta_sd_units": comp["egarch_beta_sd_units"].map(lambda x: fmt_ratio(x, 4)),
        "egarch_dk_p": comp["egarch_dk_p"].map(fmt_p),
        "egarch_survives": comp["survives_egarch"].map(yesno),
    }
)
emit(
    "Table 5.6",
    "Inference concordance across v2 checks",
    "Ch.5 Results",
    "table_5_6_inference_concordance.csv",
    t56,
    src(
        "outputs/tables/hypothesis_grid_results_v2.csv",
        "outputs/tables/se_concordance.csv",
        "outputs/tables/headline_with_liquidity_controls.csv",
        "outputs/tables/headline_with_egarch_outcome.csv",
    ),
    "Merge of four frozen tables on test_id: base grid; four-estimator concordance and Romano-Wolf; three-control liquidity specification; primary EGARCH outcome (full sample). No estimate is recomputed.",
    "bp 3 dp; p 4 dp with '<0.0001' floor; n integer; EGARCH beta 4 dp; liquidity percent change 2 dp.",
    "DK = Driscoll-Kraay bw=5; DC-v2 = two-way cluster; FM = Fama-MacBeth; WB = wild cluster bootstrap (symbol clusters, B=999); RW = Romano-Wolf stepdown (B=999). Liquidity columns use the three-control single-feature specification; EGARCH uses the primary symmetric EGARCH(1,1) outcome on the full sample and is expressed in outcome-SD units per feature-SD. 'Survives' flags are the frozen columns, not new gates.",
)

q = read("outputs/tables/quantile_tail_summary.csv")
q = q.sort_values("test_id", key=lambda s: s.map(table_number_key))
t57a = pd.DataFrame(
    {
        "hypothesis": q["test_id"],
        "base_bp": q["base_bp_v1"].map(fmt_bp),
        "tau10_bp": q["bp_tau10"].map(fmt_bp),
        "tau10_p": q["p_tau10"].map(fmt_p),
        "tau50_bp": q["bp_tau50"].map(fmt_bp),
        "tau90_bp": q["bp_tau90"].map(fmt_bp),
        "tau90_p": q["p_tau90"].map(fmt_p),
        "ratio_tau90_tau10": q["beta_ratio_90_10"].map(lambda x: fmt_ratio(x, 3)),
        "tail_shape": q["tail_shape"],
        "tail_classification": q["tail_classification"],
    }
)
emit(
    "Table 5.7a",
    "Quantile tail estimates",
    "Ch.5 Results",
    "table_5_7a_quantile_tails.csv",
    t57a,
    src("outputs/tables/quantile_tail_summary.csv"),
    "Projection: five quantile points, ratio and tail labels from the frozen quantile summary; rows sorted by hypothesis number.",
    "bp 3 dp; p 4 dp with '<0.0001' floor; ratio 3 dp.",
    "Quantile standard errors are Koenker heteroskedasticity-robust, not cluster-robust; panel dependence is a limitation. The 20 extreme-tail checks are unadjusted for multiplicity, so null-tail labels are descriptive only. H10: +3.083 bp at tau=.10 to +18.696 bp at tau=.90, ratio 6.064, both tails increasing.",
)

ts = read("outputs/tables/trade_size_heterogeneity.csv")
ts = ts[ts["spec"] == "primary"].copy()
ts["test_order"] = ts["test_id"].map(table_number_key)
metric_order = {"buyer_hhi": 0, "top3_buyer_share": 1, "eod_concentration": 2}
bucket_order = {"small": 0, "medium": 1, "large": 2}
ts["metric_order"] = ts["metric"].map(metric_order)
ts["bucket_order"] = ts["bucket"].map(bucket_order)
ts = ts.sort_values(["test_order", "metric_order", "bucket_order"])
t57b = pd.DataFrame(
    {
        "hypothesis": ts["test_id"],
        "metric": ts["metric"],
        "bucket": ts["bucket"],
        "base_bp": ts["base_bp_v1"].map(fmt_bp),
        "bucket_bp": ts["beta_bp"].map(fmt_bp),
        "dk_p": ts["p_dk"].map(fmt_p),
        "dc_v2_p": ts["p_dc_v2"].map(fmt_p),
        "n_obs": ts["n_obs"].map(fmt_int),
        "sign_matches_base": ts["sign_match_base"].map(yesno),
    }
)
emit(
    "Table 5.7b",
    "Trade-size heterogeneity, primary specification",
    "Ch.5 Results",
    "table_5_7b_trade_size.csv",
    t57b,
    src("outputs/tables/trade_size_heterogeneity.csv"),
    "Projection: 18 primary-specification rows (2 hypotheses x 3 metrics x 3 buckets); sensitivity min-1/min-10 rows omitted from the print copy but retained in the source.",
    "bp 3 dp; p 4 dp with '<0.0001' floor; n integer.",
    "Buckets use TRAIN-fold p10/p90 trade size per (fold, symbol) with a minimum-5-trades guard. The sign-aware criterion is the honest adjudication: only H7 EoD large-ticket passes. The small bucket is only 0.35% of volume.",
)

spec = read("outputs/tables/specification_curve_h7_summary.csv")
t57c = pd.DataFrame(
    {
        "group": spec["group"],
        "n_specs": spec["n_specs"].map(fmt_int),
        "median_bp": spec["median_bp"].map(fmt_bp),
        "mean_bp": spec["mean_bp"].map(fmt_bp),
        "min_bp": spec["min_bp"].map(fmt_bp),
        "max_bp": spec["max_bp"].map(fmt_bp),
        "share_ci_excludes_0": spec["share_ci_excludes_0"].map(lambda x: fmt_ratio(x, 3)),
        "share_p_lt_05": spec["share_p_lt_05"].map(lambda x: fmt_ratio(x, 3)),
        "share_positive": spec["share_positive"].map(lambda x: fmt_ratio(x, 3)),
        "robustness_ratio": spec["robustness_ratio_abs"].map(lambda x: fmt_ratio(x, 2)),
    }
)
emit(
    "Table 5.7c",
    "H7 specification-curve summary",
    "Ch.5 Results",
    "table_5_7c_specification_curve.csv",
    t57c,
    src("outputs/tables/specification_curve_h7_summary.csv"),
    "Projection: overall and outcome-split summary rows from the frozen specification curve; the 144-row curve itself is Appendix material.",
    "bp 3 dp; shares 3 dp; robustness ratio 2 dp (absolute value).",
    "144 executed specifications / 72 unique design betas. H7 is 72/72 positive for abs_ret but 66/72 negative for ret; the 1% EoD cutoff collapses the CI-exclusion share to zero. This is a volatility/absolute-return association, not a directional-return effect.",
)

sub = read("outputs/tables/heterogeneity_subgroups.csv")
sub["test_order"] = sub["test_id"].map(table_number_key)
sub = sub.sort_values(["test_order", "row_type", "split", "group"])
t57d = pd.DataFrame(
    {
        "hypothesis": sub["test_id"],
        "split": sub["split"],
        "group": sub["group"],
        "row_type": sub["row_type"],
        "effect_bp": sub["beta_bp"].map(fmt_bp),
        "dk_p": sub["p_dk"].map(fmt_p),
        "dc_v2_p": sub["p_dc_v2"].map(fmt_p),
        "n_obs": sub["n_obs"].map(fmt_int),
        "bonferroni_family": sub["bonferroni_family"].map(fmt_int),
        "p_bonf": sub["p_bonf"].map(fmt_p),
        "status": sub["status"],
        "note": sub["note"],
    }
)
emit(
    "Table 5.7d",
    "Subgroup heterogeneity grid",
    "Ch.5 Results",
    "table_5_7d_subgroups.csv",
    t57d,
    src("outputs/tables/heterogeneity_subgroups.csv"),
    "Projection: all 40 rows including the four NOT_EXECUTED circuit-breaker rows. No cell is dropped or re-labelled.",
    "bp 3 dp; p 4 dp with '<0.0001' floor; n integer.",
    "36 estimated cells/interactions plus 4 NOT_EXECUTED circuit-breaker rows. No Bonferroni survivor; minimum p_bonf .1434 (H10 bottom-7). The circuit-breaker split is not implementable: no limit-hit flag exists in the corpus or verified archives.",
)

econ5 = read("outputs/tables/economic_magnitude.csv")
t57e = pd.DataFrame(
    {
        "hypothesis": econ5["test_id"],
        "effect_bp_per_sd": econ5["effect_bp_per_sd"].map(fmt_bp),
        "direction": econ5["direction"],
        "cost_floor_low_bp": econ5["cost_low_bp"].map(fmt_int),
        "cost_floor_high_bp": econ5["cost_high_bp"].map(fmt_int),
        "multiple_below_floor_low": econ5["cost_multiple_low"].map(lambda x: fmt_ratio(x, 2)),
        "multiple_below_floor_high": econ5["cost_multiple_high"].map(lambda x: fmt_ratio(x, 2)),
        "standalone_tradable_at_1sd": econ5["standalone_tradable_at_1sd"].map(yesno),
        "note": econ5["note"],
    }
)
emit(
    "Table 5.7e",
    "Economic magnitude versus the cost floor",
    "Ch.5 Results",
    "table_5_7e_cost_floor.csv",
    t57e,
    src("outputs/tables/economic_magnitude.csv"),
    "Projection: all nine columns from the frozen economic-magnitude table.",
    "effect 3 dp; multiples 2 dp; cost floor integer bp.",
    "Declared floor = 30-50 bp round-trip explicit cost, excluding brokerage, bid-ask spread and CNS carry. At 1 SD of engagement none is standalone tradable. H4 is opposite-sign post hoc.",
)


# ---------------------------------------------------------------------------
# manifest + README
# ---------------------------------------------------------------------------
manifest = pd.DataFrame(MANIFEST)
manifest.to_csv(OUT / "table_manifest.csv", index=False, lineterminator="\n", encoding="utf-8")

readme_lines = [
    "# Print-ready thesis tables (v2.0.2 pre-write)",
    "",
    f"Generated: {GENERATED_UTC}",
    "",
    "Every CSV in this directory is a **projection or transcription of a frozen",
    "artefact**. No regression, test, re-fit, robustness check, simulation or",
    "new estimate is performed here. Values are formatted for print; the",
    "authoritative numeric sources remain under `outputs/tables/`.",
    "",
    "## How to use",
    "",
    "- Open the CSV for the table number you need. Column names are already",
    "  print labels; replace `_` with spaces in the thesis tool if desired.",
    "- Blank cells mean *not applicable*, not zero.",
    "- Keep the footnotes from `table_manifest.csv` with the table. They define",
    "  units, gates, and the frozen caveats.",
    "- Do not edit a CSV by hand. Change the source or the generator and rerun",
    "  `nepse-msc/bin/python scripts/make_print_tables.py`.",
    "- `table_manifest.csv` records the SHA-256 of every source and output, the",
    "  transform, the rounding rule and the status of each table.",
    "",
    "## Table index",
    "",
    "| table | title | rows | source status |",
    "|---|---|---:|---|",
]
for row in MANIFEST:
    readme_lines.append(
        f"| {row['table_id']} | {row['title']} | {row['n_rows']} | {row['status']} |"
    )
readme_lines += [
    "",
    "## Status vocabulary",
    "",
    "| status | meaning |",
    "|---|---|",
    "| DERIVED_PROJECTION | Column/row projection or unit conversion of a frozen CSV. |",
    "| DERIVED_DESCRIPTIVE_SUMMARY | Counts, medians or shares already present in a frozen table, regrouped for print. |",
    "| DOCUMENTED_CONSTANTS | Counts transcribed from the Ch.4 handoff pack and experiment register; no audit re-run. |",
    "| MANUAL_TRANSCRIPTION_FROM_FROZEN_PLAN | Design/protocol table transcribed from a frozen plan; no numeric estimate. |",
    "| MANUAL_TRANSCRIPTION_FROM_VERIFIED_SOURCE | Licence matrix transcribed from the live, timestamped licence review. |",
    "| VERBATIM_COPY_WITH_CSV_QUOTING_FIX | Content-identical copy with one malformed CSV field correctly quoted. |",
    "",
    "## Known source quirk",
    "",
    "`reports/chapter_assets/ch3_feature_dictionary.csv` is not valid CSV as",
    "committed: line 4 has an unquoted comma in its final `notes` field. Its",
    "chapter-map hash is audited, so the source is left untouched; the print",
    "copy quotes that one field and changes nothing else.",
    "",
]
(OUT / "README.md").write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

print(f"\nWrote {len(MANIFEST)} tables to {OUT.relative_to(ROOT)}")
print(f"Manifest: {(OUT / 'table_manifest.csv').relative_to(ROOT)}")
