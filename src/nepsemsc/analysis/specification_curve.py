"""H7 specification curve (v2 Stage 4, plan V2-4).

Declared factor grid (4 x 2 x 2 x 3 x 3 = 144 specs).

Arithmetic note (deviation #20): the binding plan writes "4x2x2x3x3 = 72",
but the declared factors multiply to 144. Dropping a declared factor would be
an unregistered design change, so the full declared factorial is executed and
the count discrepancy is logged rather than silently resolved.

    SE family        DK | DC-v2 | FM | WB-as-SE
    outcome          abs_ret_fwd1 | ret_fwd1
    controls         base (log_volume_z + market_ret_loo_z) | gamma-all
                     (base + amihud_z + roll_spread_z + corwin_schultz_z)
    subsample        full | bubble (calendar year <= 2022) | normal (>= 2023)
    EoD cutoff       5% (base) | 1% | 10%

The H7 feature is end-of-day concentration.  Parametric SE families get a
normal 95% CI (beta +/- 1.96*SE).  The WB family uses the Stage-2 validated
entity-cluster wild bootstrap (Rademacher weights, B=999, V2_WB_SEEDS) and a
percentile 95% CI of the pseudo-beta distribution; its p-value is the
CGM-2008 ReBWB p with the (1+#)/(B+1) convention and the observed t from the
SAME entity-clustered covariance.

The optional anomaly-estimator factor (3 scorers) is NOT applied: the plan
declares a second H2/H3-style curve optional and not required for H7.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from nepsemsc.evaluation._panel_boot import build_bundle, pseudo_draws
from nepsemsc.evaluation.wild_bootstrap import (cluster_weights,
                                                wild_cluster_p)
from nepsemsc.ml.panel_regression import (fit_cluster_entity,
                                          fit_double_clustered_v2,
                                          fit_driscoll_kraay,
                                          fit_fama_macbeth)
from nepsemsc.utils.seeds_v2 import V2_WB_SEEDS

BASE_CONTROLS = ("log_volume_z", "market_ret_loo_z")
LIQUIDITY_CONTROLS = ("amihud_z", "roll_spread_z", "corwin_schultz_z")
SE_FAMILIES = ("DK", "DC", "FM", "WB")
OUTCOMES = (("abs_ret_fwd1", "abs_ret"), ("ret_fwd1", "ret"))
CONTROL_SETS = (("base", ()), ("gamma_all", LIQUIDITY_CONTROLS))
SUBSAMPLES = ("full", "bubble", "normal")
CUTOFFS = (("5pct", "end_of_day_concentration_z"),
           ("1pct", "eod_01_z"),
           ("10pct", "eod_10_z"))
FEATURE = "end_of_day_concentration"
ALPHA = 0.05


def spec_grid() -> pd.DataFrame:
    """Return the declared 72-row factor grid (one row per specification)."""
    rows = []
    for se in SE_FAMILIES:
        for outcome, outcome_label in OUTCOMES:
            for control_label, control_cols in CONTROL_SETS:
                for subsample in SUBSAMPLES:
                    for cutoff_label, cutoff_col in CUTOFFS:
                        rows.append({
                            "spec_id": "|".join([se, outcome_label,
                                                 control_label, subsample,
                                                 cutoff_label]),
                            "se_family": se,
                            "outcome": outcome,
                            "outcome_label": outcome_label,
                            "controls": control_label,
                            "control_cols": control_cols,
                            "subsample": subsample,
                            "cutoff": cutoff_label,
                            "cutoff_col": cutoff_col,
                        })
    out = pd.DataFrame(rows)
    # 4 SE x 2 outcomes x 2 control sets x 3 subsamples x 3 cutoffs = 144.
    # The plan's "= 72" is an arithmetic slip (deviation #20); all declared
    # factor levels are retained.
    assert len(out) == 144, len(out)
    return out


def subsample_panel(panel: pd.DataFrame, subsample: str) -> pd.DataFrame:
    """Calendar subsample; the v1 regime definition is year <= 2022 = bubble."""
    if subsample == "full":
        return panel
    year = pd.to_datetime(panel["date"]).dt.year
    if subsample == "bubble":
        return panel.loc[year <= 2022].reset_index(drop=True)
    if subsample == "normal":
        return panel.loc[year >= 2023].reset_index(drop=True)
    raise ValueError(f"unknown subsample {subsample!r}")


def _fit_parametric(panel: pd.DataFrame, outcome: str, cols: list[str],
                    feature: str, se_family: str) -> dict:
    if se_family == "DK":
        res = fit_driscoll_kraay(panel, outcome, cols, bandwidth=5)
        return {"beta": float(res.params[feature]),
                "se": float(res.std_errors[feature]),
                "t": float(res.tstats[feature]),
                "p": float(res.pvalues[feature]),
                "n_obs": int(res.nobs), "n_cross_sections": np.nan,
                "ci_lo": float(res.params[feature] - 1.959963984540054
                               * res.std_errors[feature]),
                "ci_hi": float(res.params[feature] + 1.959963984540054
                               * res.std_errors[feature])}
    if se_family == "DC":
        res = fit_double_clustered_v2(panel, outcome, cols)
        return {"beta": float(res.params[feature]),
                "se": float(res.std_errors[feature]),
                "t": float(res.tstats[feature]),
                "p": float(res.pvalues[feature]),
                "n_obs": int(res.nobs), "n_cross_sections": np.nan,
                "ci_lo": float(res.params[feature] - 1.959963984540054
                               * res.std_errors[feature]),
                "ci_hi": float(res.params[feature] + 1.959963984540054
                               * res.std_errors[feature])}
    if se_family == "FM":
        d = panel.dropna(subset=[outcome, *cols])
        res = fit_fama_macbeth(d, outcome, cols)
        st = res["coef_stats"][feature]
        return {"beta": float(st["beta"]), "se": float(st["se"]),
                "t": float(st["tstat"]), "p": float(st["pvalue"]),
                "n_obs": int(len(d)),
                "n_cross_sections": int(len(res["betas"])),
                "ci_lo": float(st["beta"] - 1.959963984540054 * st["se"]),
                "ci_hi": float(st["beta"] + 1.959963984540054 * st["se"])}
    raise ValueError(f"unknown parametric SE family {se_family!r}")


def fit_wb(panel: pd.DataFrame, outcome: str, cols: list[str], feature: str,
           seeds: list[int] | None = None) -> dict:
    """Wild-cluster (entity) bootstrap point, percentile CI and ReBWB p."""
    seeds = list(V2_WB_SEEDS if seeds is None else seeds)
    d = panel.dropna(subset=[outcome, *cols]).reset_index(drop=True)
    bundle, _ = build_bundle(d, outcome, cols, test_id="H7_spec",
                             feature=feature)
    obs = fit_cluster_entity(d, outcome, cols)
    t_obs = float(obs.tstats[feature])
    eta = cluster_weights(seeds, int(bundle.ent_idx.max()) + 1)
    draws = pseudo_draws(bundle, eta, cluster=True, cluster_cov=True)
    beta_star = bundle.beta[None, :] + draws["delta"]
    beta_star = beta_star[:, 0]
    t_star = draws["t_recentered"][:, 0]
    lo, hi = np.percentile(beta_star, [2.5, 97.5])
    return {"beta": float(bundle.beta[0]), "se": float(np.std(beta_star, ddof=1)),
            "t": t_obs,
            "p": wild_cluster_p(t_star, t_obs),
            "n_obs": int(len(d)), "n_cross_sections": np.nan,
            "ci_lo": float(lo), "ci_hi": float(hi)}


def fit_spec(panel: pd.DataFrame, spec: pd.Series,
             seeds: list[int] | None = None) -> dict:
    """Fit one declared specification and return bp-scale results."""
    sub = subsample_panel(panel, spec["subsample"])
    feature_col = spec["cutoff_col"]
    cols = [feature_col, *BASE_CONTROLS, *spec["control_cols"]]
    family = spec["se_family"]
    if family == "WB":
        raw = fit_wb(sub, spec["outcome"], cols, feature_col, seeds=seeds)
        ci_method = "wb_percentile"
    else:
        raw = _fit_parametric(sub, spec["outcome"], cols, feature_col, family)
        ci_method = "normal"
    out = {**spec.to_dict(), **raw}
    out.update({
        "beta_bp": 1e4 * raw["beta"],
        "se_bp": 1e4 * raw["se"],
        "ci_lo_bp": 1e4 * raw["ci_lo"],
        "ci_hi_bp": 1e4 * raw["ci_hi"],
        "ci_method": ci_method,
        "ci_excludes_0": bool(raw["ci_lo"] > 0 or raw["ci_hi"] < 0),
        "p_lt_05": bool(raw["p"] < ALPHA),
        "sign_positive": bool(raw["beta"] > 0),
    })
    return out


def run_spec_curve(panel: pd.DataFrame, seeds: list[int] | None = None,
                   verbose: bool = True) -> pd.DataFrame:
    """Run all 144 declared factorial specifications."""
    rows = []
    grid = spec_grid()
    for i, (_, spec) in enumerate(grid.iterrows(), start=1):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rows.append(fit_spec(panel, spec, seeds=seeds))
        if verbose and (i % 12 == 0 or i == len(grid)):
            print(f"  specification curve: {i}/{len(grid)}", flush=True)
    out = pd.DataFrame(rows)
    out = out.sort_values(["beta_bp", "spec_id"]).reset_index(drop=True)
    out["beta_rank"] = np.arange(1, len(out) + 1)
    return out


def curve_summary(curve: pd.DataFrame) -> pd.DataFrame:
    """Declared summary metrics, overall and split by outcome label.

    Median beta, share of CIs excluding zero, and the robustness ratio
    (max beta - min beta) / median beta.  The overall row mixes signed-return
    and absolute-return coefficients, so the outcome-split rows are the
    interpretable ones; both are reported rather than hiding the mix.
    """
    rows = []
    groups = [("overall", curve)]
    groups += [(f"outcome={o}", curve.loc[curve.outcome_label == o])
               for o in ("abs_ret", "ret")]
    for label, d in groups:
        med = float(d["beta_bp"].median())
        rows.append({
            "group": label,
            "n_specs": int(len(d)),
            "median_bp": med,
            "mean_bp": float(d["beta_bp"].mean()),
            "min_bp": float(d["beta_bp"].min()),
            "max_bp": float(d["beta_bp"].max()),
            "range_bp": float(d["beta_bp"].max() - d["beta_bp"].min()),
            "share_ci_excludes_0": float(d["ci_excludes_0"].mean()),
            "share_p_lt_05": float(d["p_lt_05"].mean()),
            "share_positive": float((d["beta_bp"] > 0).mean()),
            "robustness_ratio": (float(d["beta_bp"].max() - d["beta_bp"].min())
                                 / med if med != 0 else np.nan),
            "robustness_ratio_abs": (
                float(d["beta_bp"].max() - d["beta_bp"].min()) / abs(med)
                if med != 0 else np.nan),
        })
    return pd.DataFrame(rows)
