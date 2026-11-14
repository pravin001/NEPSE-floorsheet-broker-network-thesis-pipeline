"""Independent Phase-A verification of the frozen H10 result (v2.0.2 sprint).

Purpose
-------
Re-derive the canonical H10 coefficient from the processed parquet inputs using
an estimation path that is INDEPENDENT of the production pipeline.  Nothing in
this script imports `nepsemsc.models.panel_regression`, `nepsemsc.ml.panel_data`,
or any other production estimation module.  The panel assembly, train-fold
winsor(1/99)+z standardization, liquidity proxies, and the PanelOLS/DK fit are
implemented here directly from the frozen protocol.

Canonical target
----------------
H10: reciprocity (design z) -> abs_ret_fwd1
     beta = +9.492266420621041 bp, DK p = .013754510527417598, n = 7,116
     n_effective = 6,383 (12 stocks, 723 dates)

Tolerances (Phase A, mandatory)
-------------------------------
|beta diff| < 0.5% of |canonical beta|
|p diff|    <= 0.005 absolute
n           exact
n_effective exact

On any primary-tolerance breach the script prints CRITICAL REPRODUCTION FAILURE
and exits non-zero.  It never tunes, patches, or explains away a mismatch.

Outputs
-------
outputs/tables/verification_h10_recompute.csv
outputs/tables/verification_spot_checks.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"

CANONICAL_FILE = TABLES / "v2_final_headline_set.csv"
GRID_V2_FILE = TABLES / "hypothesis_grid_results_v2.csv"
GRID_V1_FILE = TABLES / "hypothesis_grid_results.csv"
RW_FILE = TABLES / "hypothesis_grid_results_rw.csv"
LIQ_CONTROL_FILE = TABLES / "headline_with_liquidity_controls.csv"
EVENT_UPGRADED_FILE = TABLES / "event_study_upgraded.csv"
EVENT_CARS_FILE = TABLES / "event_study_cars.csv"

# Frozen design (docs/analysis_plan_v2_extension.md V2-2 / EXP-0004b).
BASE_FEATURES = [
    "anomaly_score",
    "buyer_hhi",
    "self_loop_ratio",
    "reciprocity",
    "end_of_day_concentration",
]
CONTROL_COLS = ["log_volume", "market_ret_loo"]
Z_SOURCE_COLS = BASE_FEATURES + CONTROL_COLS
LIQUIDITY_COLS = ["amihud", "roll_spread", "corwin_schultz", "effective_tick"]
LIQUIDITY_GAMMAS = ["amihud", "roll_spread", "corwin_schultz"]

H10_FEATURE = "reciprocity_z"
H10_OUTCOME = "abs_ret_fwd1"
H10_CONTROLS = ["log_volume_z", "market_ret_loo_z"]

BETA_RTOL = 0.005          # 0.5% of |canonical beta|
P_ATOL = 0.005             # absolute
DK_BANDWIDTH = 5


# ---------------------------------------------------------------------------
# Independent panel construction
# ---------------------------------------------------------------------------
def _as_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.date


def build_base_panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recreate the frozen OOS panel from processed parquets.

    Mirrors the declared construction: OOS test rows only; merge outcomes on
    (date, symbol); log_volume = log(total_volume clipped at 1); base complete-
    case filter on ret_fwd1 + every frozen regressor.  The train frame is the
    complement (is_train) and is used ONLY for fold constants.
    """
    scores = pd.read_parquet(PROCESSED / "anomaly_scores.parquet")
    outcomes = pd.read_parquet(PROCESSED / "daily_outcomes.parquet")

    sc = scores.copy()
    out = outcomes.copy()
    sc["date"] = _as_date(sc["date"])
    out["date"] = _as_date(out["date"])

    outcome_cols = ["date", "symbol", "ret_fwd1", "abs_ret_fwd1",
                    "market_ret_loo"]
    test = (sc.loc[~sc["is_train"]]
              .merge(out[outcome_cols], on=["date", "symbol"], how="left"))
    test["log_volume"] = np.log(test["total_volume"].clip(lower=1.0))
    test = test.dropna(subset=["ret_fwd1", *Z_SOURCE_COLS]).reset_index(drop=True)

    train = (sc.loc[sc["is_train"]]
               .merge(out[["date", "symbol", "market_ret_loo"]],
                      on=["date", "symbol"], how="left"))
    train["log_volume"] = np.log(train["total_volume"].clip(lower=1.0))
    return test, train


def train_fold_stats(train: pd.DataFrame,
                     cols: list[str]) -> dict[int, dict[str, dict[str, float]]]:
    """Per fold: winsor bounds q01/q99 then mean/sd (ddof=0) of clipped train."""
    stats: dict[int, dict[str, dict[str, float]]] = {}
    for fold_id, g in train.groupby("fold_id", observed=True):
        fold: dict[str, dict[str, float]] = {}
        for col in cols:
            q1 = float(g[col].quantile(0.01))
            q99 = float(g[col].quantile(0.99))
            clipped = g[col].clip(q1, q99)
            fold[col] = {
                "q1": q1,
                "q99": q99,
                "mu": float(clipped.mean()),
                "sd": float(clipped.std(ddof=0)),
            }
        stats[int(fold_id)] = fold
    return stats


def apply_train_z(panel: pd.DataFrame,
                  stats: dict[int, dict[str, dict[str, float]]],
                  cols: list[str]) -> pd.DataFrame:
    """Add <col>_z using each row's own fold's TRAIN constants."""
    out = panel.copy()
    for fold_id, fold in stats.items():
        mask = out["fold_id"] == fold_id
        for col in cols:
            s = fold[col]
            out.loc[mask, col + "_z"] = (
                (out.loc[mask, col].clip(s["q1"], s["q99"]) - s["mu"]) / s["sd"]
            )
    return out


# ---------------------------------------------------------------------------
# Independent Stage-2 liquidity proxies (published formulas, frozen details)
# ---------------------------------------------------------------------------
_ROLL_WINDOW = 20
_ROLL_MIN_PERIODS = 10
_CS_WINDOW = 20
_CS_MIN_PERIODS = 10
_CS_DEN = 3.0 - 2.0 * np.sqrt(2.0)


def _roll_relative(close: pd.Series) -> np.ndarray:
    c = close.reset_index(drop=True).astype(float)
    dp = c.diff()
    cov = dp.rolling(_ROLL_WINDOW, min_periods=_ROLL_MIN_PERIODS).cov(dp.shift(1))
    spread = 2.0 * np.sqrt(np.clip(-cov.to_numpy(dtype=float), 0.0, None))
    spread = np.where(np.isfinite(spread), spread, np.nan)
    return spread / c.to_numpy(dtype=float)


def _corwin_schultz(high: pd.Series, low: pd.Series) -> np.ndarray:
    h = high.reset_index(drop=True).astype(float)
    lo = low.reset_index(drop=True).astype(float)
    hl = np.log(h / lo)
    beta = hl.pow(2) + hl.shift(1).pow(2)
    h_max = h.combine(h.shift(1), max)
    l_min = lo.combine(lo.shift(1), min)
    gamma = np.log(h_max / l_min).pow(2)
    with np.errstate(invalid="ignore", divide="ignore"):
        alpha = ((np.sqrt(2.0 * beta) - np.sqrt(beta)) / _CS_DEN
                 - np.sqrt(gamma / _CS_DEN))
    s = 2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))
    s = s.where(alpha > 0.0, 0.0)
    s = s.where(beta.notna() & gamma.notna(), np.nan)
    s = s.clip(lower=0.0, upper=1.0)
    return s.rolling(_CS_WINDOW, min_periods=_CS_MIN_PERIODS).mean().to_numpy()


def build_liquidity_features(outcomes: pd.DataFrame,
                             ohlcv: pd.DataFrame) -> pd.DataFrame:
    o = outcomes[["date", "symbol", "close", "ret", "turnover"]].copy()
    o["date"] = _as_date(o["date"])
    h = ohlcv[["date", "symbol", "high", "low"]].copy()
    h["date"] = _as_date(h["date"])
    o = o.merge(h, on=["date", "symbol"], how="left")

    parts: list[pd.DataFrame] = []
    for sym, g in o.groupby("symbol", sort=False):
        g = g.sort_values("date")
        close = g["close"].to_numpy(dtype=float)
        ret = g["ret"].to_numpy(dtype=float)
        turnover = g["turnover"].to_numpy(dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            amihud = 1e6 * np.abs(ret) / turnover
        amihud = np.where(np.isfinite(amihud) & (turnover > 0), amihud, np.nan)

        tick = np.where(close < 100.0, 0.1, 1.0)
        parts.append(pd.DataFrame({
            "date": g["date"].to_numpy(),
            "symbol": sym,
            "amihud": amihud,
            "roll_spread": _roll_relative(g["close"]),
            "corwin_schultz": _corwin_schultz(g["high"], g["low"]),
            "effective_tick": tick / close,
        }))
    return pd.concat(parts, ignore_index=True)


# ---------------------------------------------------------------------------
# Independent estimation
# ---------------------------------------------------------------------------
def fit_panel_dk(panel: pd.DataFrame, outcome: str,
                 regressors: list[str]) -> tuple[object, pd.DataFrame]:
    """PanelOLS entity+time FE, Driscoll-Kraay kernel bandwidth=5."""
    d = (panel.dropna(subset=[outcome, *regressors])
              .sort_values(["symbol", "date"])
              .reset_index(drop=True))
    index = pd.MultiIndex.from_arrays(
        [d["symbol"].astype("category"), pd.to_datetime(d["date"])],
        names=["symbol", "date"])
    y = d[outcome].astype(float).copy()
    y.index = index
    x = d[regressors].astype(float).copy()
    x.insert(0, "const", 1.0)
    x.index = index
    res = PanelOLS(y, x, entity_effects=True, time_effects=True,
                   drop_absorbed=True).fit(cov_type="kernel",
                                           bandwidth=DK_BANDWIDTH)
    return res, d


def effective_n(d: pd.DataFrame) -> dict[str, int]:
    n_obs = int(len(d))
    n_stocks = int(d["symbol"].nunique())
    n_dates = int(d["date"].nunique())
    return {
        "n_obs": n_obs,
        "n_stocks": n_stocks,
        "n_dates": n_dates,
        "n_effective": int(n_obs - max(n_stocks - 1, 0)
                           - max(n_dates - 1, 0)),
    }


def _row(check: str, metric: str, recomputed: float, frozen: float,
         tolerance: str, passed: bool, source: str,
         note: str = "") -> dict:
    abs_diff = abs(float(recomputed) - float(frozen))
    rel_diff = (abs_diff / abs(float(frozen))) if float(frozen) != 0 else np.nan
    return {
        "check": check,
        "metric": metric,
        "recomputed": float(recomputed),
        "frozen": float(frozen),
        "abs_diff": abs_diff,
        "rel_diff": rel_diff,
        "tolerance": tolerance,
        "passed": bool(passed),
        "frozen_source": source,
        "note": note,
    }


def main() -> int:
    print("=" * 78)
    print("PHASE A — INDEPENDENT H10 VERIFICATION")
    print("=" * 78)

    canonical = pd.read_csv(CANONICAL_FILE).set_index("hypothesis")
    grid_v2 = pd.read_csv(GRID_V2_FILE).set_index("test_id")
    grid_v1 = pd.read_csv(GRID_V1_FILE).set_index("test_id")
    rw = pd.read_csv(RW_FILE).set_index("test_id")

    base_row = canonical.loc["H10"]
    frozen_bp = float(base_row["estimated_beta"])
    frozen_p = float(base_row["dk_p"])
    frozen_n = int(grid_v2.loc["H10", "n_obs"])
    frozen_neff = int(grid_v2.loc["H10", "n_effective"])
    frozen_stocks = int(grid_v2.loc["H10", "n_stocks"])
    frozen_dates = int(grid_v2.loc["H10", "n_dates"])

    # ---------------- primary H10: frozen base design ----------------------
    test, train = build_base_panel()
    stats = train_fold_stats(train, Z_SOURCE_COLS)
    panel = apply_train_z(test, stats, Z_SOURCE_COLS)
    z_cols = [c + "_z" for c in Z_SOURCE_COLS]
    panel = panel.dropna(subset=z_cols).reset_index(drop=True)

    res, used = fit_panel_dk(panel, H10_OUTCOME,
                             [H10_FEATURE, *H10_CONTROLS])
    beta = float(res.params[H10_FEATURE])
    se = float(res.std_errors[H10_FEATURE])
    p = float(res.pvalues[H10_FEATURE])
    tstat = float(res.tstats[H10_FEATURE])
    beta_bp = 1e4 * beta
    eff = effective_n(used)

    beta_ok = abs(beta_bp - frozen_bp) < BETA_RTOL * abs(frozen_bp)
    p_ok = abs(p - frozen_p) <= P_ATOL
    n_ok = eff["n_obs"] == frozen_n
    neff_ok = eff["n_effective"] == frozen_neff
    stocks_ok = eff["n_stocks"] == frozen_stocks
    dates_ok = eff["n_dates"] == frozen_dates

    rows = [
        _row("H10_PRIMARY", "beta_bp", beta_bp, frozen_bp,
             "< 0.5% of |beta|", beta_ok, "v2_final_headline_set.csv:H10"),
        _row("H10_PRIMARY", "beta_raw", beta, frozen_bp / 1e4,
             "< 0.5% of |beta|", beta_ok, "v2_final_headline_set.csv:H10"),
        _row("H10_PRIMARY", "dk_p", p, frozen_p,
             "<= 0.005 absolute", p_ok, "v2_final_headline_set.csv:H10"),
        {
            "check": "H10_PRIMARY", "metric": "n_obs",
            "recomputed": eff["n_obs"], "frozen": frozen_n,
            "abs_diff": abs(eff["n_obs"] - frozen_n),
            "rel_diff": abs(eff["n_obs"] - frozen_n) / frozen_n,
            "tolerance": "exact", "passed": bool(n_ok),
            "frozen_source": "hypothesis_grid_results_v2.csv:H10",
            "note": "v2_final_headline_set.csv has no n column; n taken "
                    "from the same frozen H10 row lineage",
        },
        {
            "check": "H10_PRIMARY", "metric": "n_effective",
            "recomputed": eff["n_effective"], "frozen": frozen_neff,
            "abs_diff": abs(eff["n_effective"] - frozen_neff),
            "rel_diff": abs(eff["n_effective"] - frozen_neff) / frozen_neff,
            "tolerance": "exact", "passed": bool(neff_ok),
            "frozen_source": "hypothesis_grid_results_v2.csv:H10",
            "note": "n - (n_stocks-1) - (n_dates-1)",
        },
        {
            "check": "H10_PRIMARY", "metric": "n_stocks",
            "recomputed": eff["n_stocks"], "frozen": frozen_stocks,
            "abs_diff": abs(eff["n_stocks"] - frozen_stocks),
            "rel_diff": 0.0, "tolerance": "exact",
            "passed": bool(stocks_ok),
            "frozen_source": "hypothesis_grid_results_v2.csv:H10", "note": "",
        },
        {
            "check": "H10_PRIMARY", "metric": "n_dates",
            "recomputed": eff["n_dates"], "frozen": frozen_dates,
            "abs_diff": abs(eff["n_dates"] - frozen_dates),
            "rel_diff": 0.0, "tolerance": "exact",
            "passed": bool(dates_ok),
            "frozen_source": "hypothesis_grid_results_v2.csv:H10", "note": "",
        },
        _row("H10_PRIMARY", "se_raw", se, float(grid_v2.loc["H10", "se"]),
             "report only", True, "hypothesis_grid_results_v2.csv:H10"),
        _row("H10_PRIMARY", "t_stat", tstat, float(grid_v2.loc["H10", "t"]),
             "report only", True, "hypothesis_grid_results_v2.csv:H10"),
    ]

    # ---------------- secondary: Stage-2 liquidity-controlled spec ---------
    sec_ok = None
    try:
        outcomes = pd.read_parquet(PROCESSED / "daily_outcomes.parquet")
        ohlcv = pd.read_parquet(PROCESSED / "daily_ohlcv.parquet")
        liq = build_liquidity_features(outcomes, ohlcv)

        panel_l = test.merge(liq, on=["date", "symbol"], how="left")
        train_l = train.merge(liq, on=["date", "symbol"], how="left")
        z_cols_l = Z_SOURCE_COLS + LIQUIDITY_COLS
        stats_l = train_fold_stats(train_l, z_cols_l)
        panel_l = apply_train_z(panel_l, stats_l, z_cols_l)
        panel_l = panel_l.dropna(
            subset=[c + "_z" for c in z_cols_l]).reset_index(drop=True)

        res_l, used_l = fit_panel_dk(
            panel_l, H10_OUTCOME,
            [H10_FEATURE, *H10_CONTROLS, *[g + "_z" for g in LIQUIDITY_GAMMAS]])
        beta_l = 1e4 * float(res_l.params[H10_FEATURE])
        p_l = float(res_l.pvalues[H10_FEATURE])
        eff_l = effective_n(used_l)

        lc = pd.read_csv(LIQ_CONTROL_FILE)
        lc_row = lc[(lc["test_id"] == "H10")
                    & (lc["spec"] == "single_feature_liquidity")].iloc[0]
        frozen_l_bp = float(lc_row["bp"])
        frozen_l_p = float(lc_row["p_dk"])
        frozen_l_n = int(lc_row["n_obs"])

        l_beta_ok = abs(beta_l - frozen_l_bp) < BETA_RTOL * abs(frozen_l_bp)
        l_p_ok = abs(p_l - frozen_l_p) <= P_ATOL
        l_n_ok = eff_l["n_obs"] == frozen_l_n
        sec_ok = bool(l_beta_ok and l_p_ok and l_n_ok)
        rows += [
            _row("H10_SECONDARY_LIQUIDITY", "beta_bp", beta_l, frozen_l_bp,
                 "< 0.5% of |beta|", l_beta_ok,
                 "headline_with_liquidity_controls.csv:H10:"
                 "single_feature_liquidity",
                 "Stage-2 three-gamma controlled specification; informational "
                 "cross-check, not the canonical H10 base row"),
            _row("H10_SECONDARY_LIQUIDITY", "dk_p", p_l, frozen_l_p,
                 "<= 0.005 absolute", l_p_ok,
                 "headline_with_liquidity_controls.csv:H10:"
                 "single_feature_liquidity"),
            {
                "check": "H10_SECONDARY_LIQUIDITY", "metric": "n_obs",
                "recomputed": eff_l["n_obs"], "frozen": frozen_l_n,
                "abs_diff": abs(eff_l["n_obs"] - frozen_l_n),
                "rel_diff": abs(eff_l["n_obs"] - frozen_l_n) / frozen_l_n,
                "tolerance": "exact", "passed": bool(l_n_ok),
                "frozen_source": "headline_with_liquidity_controls.csv:H10",
                "note": "",
            },
        ]
    except Exception as exc:  # report, never fabricate a pass
        sec_ok = False
        rows.append({
            "check": "H10_SECONDARY_LIQUIDITY", "metric": "reconstruction",
            "recomputed": np.nan, "frozen": np.nan, "abs_diff": np.nan,
            "rel_diff": np.nan, "tolerance": "reconstruct",
            "passed": False,
            "frozen_source": "headline_with_liquidity_controls.csv:H10",
            "note": f"secondary reconstruction error: {type(exc).__name__}: {exc}",
        })
        beta_l = p_l = np.nan
        eff_l = {"n_obs": -1}

    recompute = pd.DataFrame(rows)
    recompute.to_csv(TABLES / "verification_h10_recompute.csv", index=False)

    # ---------------- spot checks -----------------------------------------
    spot: list[dict] = []

    def add_spot(check: str, item: str, quoted: float, source_file: str,
                 source_value: float, tolerance: float, note: str = "") -> bool:
        diff = abs(float(source_value) - float(quoted))
        ok = bool(diff <= tolerance)
        spot.append({
            "spot_check": check,
            "item": item,
            "quoted_value": float(quoted),
            "source_file": source_file,
            "source_value": float(source_value),
            "abs_diff": diff,
            "tolerance": tolerance,
            "match": ok,
            "note": note,
        })
        return ok

    # H7 beta: canonical bp -> frozen grid bp -> register EXP-0011f quote
    h7_canon = float(canonical.loc["H7", "estimated_beta"])
    h7_grid = float(grid_v1.loc["H7", "bp"])
    h7_register = 3.952  # EXP-0011f / EXP-0004b rounded quote
    h7_ok = True
    h7_ok &= add_spot("H7_BETA", "canonical vs frozen v1 grid bp",
                      h7_canon, "hypothesis_grid_results.csv:H7:bp",
                      h7_grid, 1e-12)
    h7_ok &= add_spot("H7_BETA", "register quote (3 dp) vs canonical",
                      h7_register, "docs/experiment_register.md:EXP-0011f",
                      round(h7_canon, 3), 1e-12,
                      "register quotes +3.952 bp/SD; canonical = "
                      f"{h7_canon:.15g}")

    # H10 RW p
    rw_canon = float(canonical.loc["H10", "rw_p"])
    rw_grid = float(rw.loc["H10", "rw_p"])
    rw_ok = add_spot("H10_RW_P", "canonical vs frozen RW table",
                     rw_canon, "hypothesis_grid_results_rw.csv:H10:rw_p",
                     rw_grid, 1e-12,
                     "register EXP-0008b quotes rw_p .081")

    # Event-study mean CAR + p: event_study_upgraded.csv is the register-cited
    # row of record for EXP-0011e; event_study_cars.csv is the v1 event record.
    ev = pd.read_csv(EVENT_UPGRADED_FILE)
    ev_row = ev[(ev["sample"] == "all_686")
                & (ev["model"] == "v1_method")
                & (ev["test"] == "mean_car_t")].iloc[0]
    ev_bp = 1e4 * float(ev_row["mean_car"])
    ev_p = float(ev_row["p_value"])
    cars = pd.read_csv(EVENT_CARS_FILE)
    cars_bp = 1e4 * float(cars["car"].mean())
    ev_ok = True
    ev_ok &= add_spot("EVENT_STUDY_CAR", "mean CAR bp: upgraded table vs "
                      "686-event cars reconstruction",
                      12.86, "event_study_upgraded.csv:all_686:v1_method",
                      ev_bp, 0.005,
                      f"full-precision {ev_bp:.15g} bp; "
                      f"event_study_cars.csv mean = {cars_bp:.15g} bp")
    ev_ok &= add_spot("EVENT_STUDY_CAR", "p-value: upgraded table vs quoted "
                      ".569", 0.569,
                      "event_study_upgraded.csv:all_686:v1_method",
                      ev_p, 5e-4, f"full precision {ev_p:.15g}")
    ev_ok &= add_spot("EVENT_STUDY_CAR", "686-event car mean vs upgraded "
                      "table", cars_bp,
                      "event_study_cars.csv:car:mean", ev_bp, 1e-12,
                      "v1 event_study_cars.csv reconstructs the upgraded "
                      "v1_method row exactly")

    spot_df = pd.DataFrame(spot)
    spot_df.to_csv(TABLES / "verification_spot_checks.csv", index=False)

    # ---------------- report ----------------------------------------------
    primary_ok = bool(beta_ok and p_ok and n_ok and neff_ok)
    spot_group_ok = {
        "H7_BETA": bool(spot_df.loc[spot_df.spot_check == "H7_BETA",
                                    "match"].all()),
        "H10_RW_P": bool(spot_df.loc[spot_df.spot_check == "H10_RW_P",
                                    "match"].all()),
        "EVENT_STUDY_CAR": bool(
            spot_df.loc[spot_df.spot_check == "EVENT_STUDY_CAR", "match"].all()),
    }
    spot_all_ok = all(spot_group_ok.values())

    print("\nH10 RECOMPUTE (base design: reciprocity_z + log_volume_z + "
          "market_ret_loo_z)")
    print(f"  beta        : {beta_bp:+.15g} bp  (frozen {frozen_bp:+.15g})")
    print(f"  abs diff    : {abs(beta_bp - frozen_bp):.3e} bp  "
          f"({abs(beta_bp - frozen_bp) / abs(frozen_bp):.3e} relative)")
    print(f"  DK p        : {p:.15g}  (frozen {frozen_p:.15g}; "
          f"diff {abs(p - frozen_p):.3e})")
    print(f"  n           : {eff['n_obs']:,}  (frozen {frozen_n:,})")
    print(f"  n_effective : {eff['n_effective']:,}  "
          f"(frozen {frozen_neff:,})")
    print(f"  stocks/dates: {eff['n_stocks']} / {eff['n_dates']}  "
          f"(frozen {frozen_stocks} / {frozen_dates})")
    print(f"  SE / t      : {se:.6e} / {tstat:.6f}")

    if sec_ok is not None:
        print("\nH10 STAGE-2 LIQUIDITY-CONTROLLED CROSS-CHECK (informational)")
        print(f"  beta        : {beta_l:+.15g} bp  (frozen {frozen_l_bp:+.15g})")
        print(f"  DK p        : {p_l:.15g}  (frozen {frozen_l_p:.15g})")
        print(f"  n           : {eff_l['n_obs']:,}  (frozen {frozen_l_n:,})")
        print(f"  match       : {'YES' if sec_ok else 'NO'}")

    print("\nSPOT CHECKS")
    for check, ok in spot_group_ok.items():
        print(f"  {check:<18}: {'MATCH' if ok else 'MISMATCH'}")
    if not spot_all_ok:
        print(spot_df.loc[~spot_df["match"]].to_string(index=False))

    print("\n" + "-" * 78)
    print(f"H10 PRIMARY: {'PASS' if primary_ok else 'FAIL'}")
    print(f"SPOT CHECKS: {sum(spot_group_ok.values())}/3")
    if not primary_ok:
        print("CRITICAL REPRODUCTION FAILURE")
        print("-" * 78)
        return 1
    if not spot_all_ok:
        print("CRITICAL REPRODUCTION FAILURE (spot check mismatch)")
        print("-" * 78)
        return 1
    if sec_ok is False:
        print("SECONDARY LIQUIDITY CROSS-CHECK MISMATCH — reported, not gating "
              "the canonical H10 row")
    print("PHASE A VERIFICATION: PASS")
    print("-" * 78)
    print(f"wrote {TABLES / 'verification_h10_recompute.csv'}")
    print(f"wrote {TABLES / 'verification_spot_checks.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
