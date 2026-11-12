"""Pre-declared subgroup heterogeneity (v2 Stage 4, plan V2-4).

Splits (ALL built from TRAIN-fold information only, DC7):

  size        train-fold mean daily OHLCV turnover (PROXY for value traded),
              split at the cross-symbol median within each fold;
  liquidity   train-fold median Amihud illiquidity, split at the cross-symbol
              median within each fold (above = illiquid);
  turnover    train-fold mean daily turnover rank within the fold's OOS-usable
              universe: top-3 vs bottom-7;
  circuit     NOT IMPLEMENTABLE — the corpus has no circuit-breaker/limit-hit
              flag; registered NOT_EXECUTED, never fabricated.

For each split and the four headline-style tests (H4/H7/H8/H10) the module
reports group-by-group DK(bw=5) betas with 95% CIs, true two-way clustered
p-values as a secondary column, and the declared heterogeneity test: the
group x feature interaction coefficient from the pooled two-way FE design.
Bonferroni disclosure: 6 subgroup cells per test (3 splits x 2 groups) for
group betas, and 3 split interactions per test for interaction terms.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nepsemsc.ml.panel_regression import (fit_double_clustered_v2,
                                          fit_driscoll_kraay)

BASE_CONTROLS = ("log_volume_z", "market_ret_loo_z")
SUBGROUP_TESTS = ("H4", "H7", "H8", "H10")
SPLITS = ("size", "liquidity", "turnover_tier")
HIGH_LABEL = {"size": "large", "liquidity": "illiquid",
              "turnover_tier": "top3"}
GROUP_LABELS = {
    "size": ("small", "large"),
    "liquidity": ("liquid", "illiquid"),
    "turnover_tier": ("bottom7", "top3"),
}
GROUP_COL = {"size": "size_group", "liquidity": "liquidity_group",
             "turnover_tier": "turnover_tier"}
N_CELLS = 6          # 3 splits x 2 groups, per test
N_INTERACTIONS = 3   # 3 splits, per test


def assign_subgroups(panel: pd.DataFrame, train: pd.DataFrame,
                     ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Return fold x symbol split assignments (train-only statistics)."""
    tr = train[["fold_id", "date", "symbol", "amihud",
                "log_volume"]].copy()
    tr["date"] = pd.to_datetime(tr["date"])
    ox = ohlcv[["date", "symbol", "turnover"]].copy()
    ox["date"] = pd.to_datetime(ox["date"])
    tr = tr.merge(ox, on=["date", "symbol"], how="left")

    universe = panel[["fold_id", "symbol"]].drop_duplicates()
    stats = (tr.groupby(["fold_id", "symbol"], observed=True)
             .agg(mean_turnover=("turnover", "mean"),
                  median_amihud=("amihud", "median"),
                  n_train=("date", "size"))
             .reset_index())
    stats = universe.merge(stats, on=["fold_id", "symbol"], how="left")
    if stats[["mean_turnover", "median_amihud"]].isna().any().any():
        miss = stats.loc[stats[["mean_turnover", "median_amihud"]]
                         .isna().any(axis=1),
                         ["fold_id", "symbol"]]
        raise ValueError(f"subgroup stats missing for {len(miss)} "
                         f"fold-symbol pairs: {miss.to_dict('records')}")

    out = []
    for fold_id, g in stats.groupby("fold_id", observed=True):
        g = g.copy()
        med_turn = float(g["mean_turnover"].median())
        med_amihud = float(g["median_amihud"].median())
        g["size_group"] = np.where(g["mean_turnover"] > med_turn,
                                   "large", "small")
        g["liquidity_group"] = np.where(g["median_amihud"] > med_amihud,
                                        "illiquid", "liquid")
        g = g.sort_values(["mean_turnover", "symbol"],
                          ascending=[False, True]).reset_index(drop=True)
        g["turnover_rank"] = np.arange(1, len(g) + 1)
        g["turnover_tier"] = np.where(g["turnover_rank"] <= 3,
                                      "top3", "bottom7")
        g["fold_size_median_turnover"] = med_turn
        g["fold_liquidity_median_amihud"] = med_amihud
        out.append(g)
    return pd.concat(out, ignore_index=True)


def _fit_group(d: pd.DataFrame, outcome: str, feat: str) -> dict:
    cols = [feat, *BASE_CONTROLS]
    res = fit_driscoll_kraay(d, outcome, cols, bandwidth=5)
    try:
        dc = fit_double_clustered_v2(d, outcome, cols)
        p_dc = float(dc.pvalues[feat])
    except Exception:
        p_dc = np.nan
    beta = float(res.params[feat])
    se = float(res.std_errors[feat])
    return {"beta_bp": 1e4 * beta, "se_bp": 1e4 * se,
            "t": float(res.tstats[feat]), "p_dk": float(res.pvalues[feat]),
            "p_dc_v2": p_dc,
            "ci_lo_bp": 1e4 * (beta - 1.959963984540054 * se),
            "ci_hi_bp": 1e4 * (beta + 1.959963984540054 * se),
            "n_obs": int(res.nobs)}


def _fit_interaction(d: pd.DataFrame, outcome: str, feat: str,
                     high_label: str, group_col: str) -> dict:
    dd = d.copy()
    dummy = (dd[group_col] == high_label).astype(float)
    dd["_feat_x_high"] = dd[feat] * dummy
    cols = [feat, "_feat_x_high", *BASE_CONTROLS]
    res = fit_driscoll_kraay(dd, outcome, cols, bandwidth=5)
    beta = float(res.params["_feat_x_high"])
    se = float(res.std_errors["_feat_x_high"])
    return {"beta_bp": 1e4 * beta, "se_bp": 1e4 * se,
            "t": float(res.tstats["_feat_x_high"]),
            "p_dk": float(res.pvalues["_feat_x_high"]),
            "ci_lo_bp": 1e4 * (beta - 1.959963984540054 * se),
            "ci_hi_bp": 1e4 * (beta + 1.959963984540054 * se),
            "n_obs": int(res.nobs)}


def subgroup_table(panel: pd.DataFrame,
                   grid: pd.DataFrame) -> pd.DataFrame:
    """Build the declared subgroup + interaction rows for H4/H7/H8/H10."""
    grid = grid.set_index("test_id")
    rows = []
    for test_id in SUBGROUP_TESTS:
        feat = str(grid.loc[test_id, "feature"]) + "_z"
        outcome = str(grid.loc[test_id, "outcome"])
        d0 = panel.dropna(subset=[outcome, feat, *BASE_CONTROLS])
        for split in SPLITS:
            gcol = GROUP_COL[split]
            for group in GROUP_LABELS[split]:
                d = d0.loc[d0[gcol] == group]
                fit = _fit_group(d, outcome, feat)
                rows.append({
                    "test_id": test_id, "split": split, "group": group,
                    "row_type": "group", "feature": feat, "outcome": outcome,
                    **fit,
                    "n_stocks": int(d["symbol"].nunique()),
                    "n_dates": int(d["date"].nunique()),
                    "bonferroni_family": N_CELLS,
                    "p_bonf": min(1.0, fit["p_dk"] * N_CELLS),
                    "status": "ESTIMATED",
                    "note": "",
                })
            it = _fit_interaction(d0, outcome, feat, HIGH_LABEL[split], gcol)
            rows.append({
                "test_id": test_id, "split": split,
                "group": f"{HIGH_LABEL[split]}_vs_"
                         f"{GROUP_LABELS[split][0]}",
                "row_type": "interaction", "feature": feat,
                "outcome": outcome, **it,
                "n_stocks": int(d0["symbol"].nunique()),
                "n_dates": int(d0["date"].nunique()),
                "bonferroni_family": N_INTERACTIONS,
                "p_bonf": min(1.0, it["p_dk"] * N_INTERACTIONS),
                "status": "ESTIMATED",
                "note": "heterogeneity test = group x feature interaction",
            })
        rows.append({
            "test_id": test_id, "split": "circuit_breaker",
            "group": "not_applicable", "row_type": "not_executed",
            "feature": feat, "outcome": outcome,
            "beta_bp": np.nan, "se_bp": np.nan, "t": np.nan,
            "p_dk": np.nan, "p_dc_v2": np.nan, "ci_lo_bp": np.nan,
            "ci_hi_bp": np.nan, "n_obs": 0, "n_stocks": 0, "n_dates": 0,
            "bonferroni_family": np.nan, "p_bonf": np.nan,
            "status": "NOT_EXECUTED",
            "note": "no circuit-breaker/limit-hit flag exists in the corpus "
                    "or any verified archive; row registered, not fabricated",
        })
    return pd.DataFrame(rows)
