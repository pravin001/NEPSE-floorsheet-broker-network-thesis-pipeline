"""Effective sample size for the v2 panel tables (plan V2-4).

The v1/v2 grid reports `n_obs`, which overstates independent information in a
two-way fixed-effects panel: entity and time effects absorb degrees of freedom.
This module adds the declared columns:

    n_stocks    unique entities in the estimation sample
    n_dates     unique time periods in the estimation sample
    n_obs       complete-case rows used by the regression
    n_effective n_obs - (n_stocks - 1) - (n_dates - 1)   [PanelOLS two-way FE]
    n_cross_sections  number of valid Fama-MacBeth cross-sections
                      (rows >= 1 + #regressors AND full-rank design)

`n_effective` is the PanelOLS definition declared in the plan.  Fama-MacBeth
uses one beta per valid cross-section, so its effective count is
`n_cross_sections`; both columns are reported so the reader never has to guess
which estimator a count belongs to.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def _fm_cross_sections(panel: pd.DataFrame, outcome: str,
                       feature_cols: list[str]) -> int:
    """Count FM slices that clear the Phase-5 row-count AND full-rank guards."""
    d = panel.dropna(subset=[outcome, *feature_cols])
    n_rhs = 1 + len(feature_cols)
    n_cross = 0
    for _, g in d.groupby("date", observed=True):
        if len(g) < n_rhs:
            continue
        X = sm.add_constant(g[feature_cols].astype("float64"),
                            has_constant="add")
        if np.linalg.matrix_rank(X.to_numpy(dtype=float)) < n_rhs:
            continue
        n_cross += 1
    return n_cross


def effective_n(panel: pd.DataFrame, outcome: str,
                feature_cols: list[str]) -> dict:
    """Return the declared effective-N columns for one design."""
    d = panel.dropna(subset=[outcome, *feature_cols])
    n_obs = int(len(d))
    n_stocks = int(d["symbol"].nunique())
    n_dates = int(d["date"].nunique())
    n_effective = int(n_obs - max(n_stocks - 1, 0) - max(n_dates - 1, 0))
    return {
        "n_stocks": n_stocks,
        "n_dates": n_dates,
        "n_obs": n_obs,
        "n_effective": n_effective,
        "n_cross_sections": _fm_cross_sections(d, outcome, feature_cols),
    }


def add_effective_n(grid: pd.DataFrame, panel: pd.DataFrame,
                    grid_cols: tuple[str, str, str] = ("test_id", "feature",
                                                       "outcome"),
                    controls: tuple[str, ...] = ("log_volume_z",
                                                 "market_ret_loo_z")
                    ) -> pd.DataFrame:
    """Add the five effective-N columns to a grid table in place (copy).

    The grid must carry the v1 `feature` and `outcome` columns. Every test uses
    its own feature_z + the two base controls, exactly the v1 design.
    """
    out = grid.copy()
    cols = {c: [] for c in ("n_stocks", "n_dates", "n_obs", "n_effective",
                            "n_cross_sections")}
    for _, row in out.iterrows():
        feat = str(row[grid_cols[1]]) + "_z"
        eff = effective_n(panel, str(row[grid_cols[2]]), [feat, *controls])
        for c in cols:
            cols[c].append(eff[c])
    for c, vals in cols.items():
        out[c] = vals
    return out
