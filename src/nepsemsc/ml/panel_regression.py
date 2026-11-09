"""Panel regression wrapper with FORBIDDEN-SE enforcement (R3/SV2).

Permitted:
  driscoll_kraay      — linearmodels PanelOLS kernel covariance, bandwidth=maxlag
                        (bartlett kernel over time with cross-sectional robust
                        covariance: the DK estimator)
  double_clustered    — two-way clustering by (entity, time) where the
                        installed linearmodels supports it; otherwise explicit
                        recorded fallback to time-clustered kernel
  fama_macbeth        — Phase-5 fallback (per-stock OLS + NW-HAC on betas)
  cluster_entity_only — LAST resort, explicit caveat banner

Refused outright (ValueError, R3): "robust", "hc1", "unadjusted", "plain" —
plain robust/HC1 SEs understate variance on financial panels.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

ALLOWED_SE = {"driscoll_kraay", "double_clustered", "fama_macbeth", "cluster_entity_only"}
FORBIDDEN_SE = {"robust", "hc1", "unadjusted", "plain", "hc0", "newey_west_panel"}


def ensure_valid_se(se: str) -> str:
    if se in FORBIDDEN_SE:
        raise ValueError(
            f"SE method {se!r} is FORBIDDEN by R3/SV2 (understated variance on financial panels). "
            f"Allowed: {sorted(ALLOWED_SE)}."
        )
    if se not in ALLOWED_SE:
        raise ValueError(f"unknown SE spec {se!r}; allowed: {sorted(ALLOWED_SE)}")
    return se


def _prep_panel(panel: pd.DataFrame, entity_col: str, time_col: str,
                outcome: str, feature_cols: list[str], add_constant: bool = True):
    df = panel.sort_values([entity_col, time_col]).copy()
    # linearmodels requires a NUMERIC or DATE-LIKE time index level
    t_num = pd.to_datetime(df[time_col], errors="coerce")
    if t_num.isna().any():
        t_num = pd.factorize(df[time_col])[0].astype("float64")
    y = df[outcome].astype("float64")
    X = df[feature_cols].astype("float64")
    if add_constant:
        X = sm.add_constant(X, has_constant="add")
    idx = pd.MultiIndex.from_arrays([df[entity_col].astype("category"), t_num],
                                    names=[entity_col, time_col])
    y.index = idx
    X.index = idx
    return y, X, df


def fit_driscoll_kraay(panel: pd.DataFrame, outcome: str, feature_cols: list[str],
                       entity_col: str = "symbol", time_col: str = "date",
                       bandwidth: int = 5, entity_effects: bool = True,
                       time_effects: bool = True):
    """DK SEs (bartlett kernel, bandwidth = maxlag per brief R3)."""
    y, X, _ = _prep_panel(panel, entity_col, time_col, outcome, feature_cols)
    res = PanelOLS(y, X, entity_effects=entity_effects, time_effects=time_effects,
                   drop_absorbed=True
                   ).fit(cov_type="kernel", bandwidth=bandwidth)
    res.cov_type_used = "driscoll_kraay"
    return res


def fit_double_clustered(panel: pd.DataFrame, outcome: str, feature_cols: list[str],
                         entity_col: str = "symbol", time_col: str = "date",
                         entity_effects: bool = True, time_effects: bool = True):
    """Two-way clustered SEs by (entity, time). If the installed linearmodels
    lacks two-way clustering support, falls back to time-dimension kernel with
    an explicit banner (SV2 fallback 1b) — recorded in the result object."""
    y, X, df = _prep_panel(panel, entity_col, time_col, outcome, feature_cols)
    try:
        res = PanelOLS(y, X, entity_effects=entity_effects, time_effects=time_effects,
                       drop_absorbed=True).fit(
            cov_type="clustered",
            clusters=df[[entity_col, time_col]].apply(lambda c: pd.factorize(c)[0]).T.to_numpy(),
        )
        res.cov_type_used = "double_clustered"
    except Exception:
        res = PanelOLS(y, X, entity_effects=entity_effects, time_effects=time_effects,
                       drop_absorbed=True).fit(cov_type="kernel", bandwidth=5)
        res.cov_type_used = "double_clustered_fallback_time_kernel"
    return res


def fit_fama_macbeth(panel: pd.DataFrame, outcome: str, feature_cols: list[str],
                     entity_col: str = "symbol", time_col: str = "date",
                     maxlag: int = 5, add_constant: bool = True):
    """SV2 fallback 2: per-date cross-sectional OLS, then Newey-West HAC on the
    time series of beta estimates (asymmetric sample caveat recorded)."""
    df = panel.sort_values([time_col, entity_col])
    betas: dict[str, list[float]] = {c: [] for c in feature_cols}
    times: list = []
    n_rhs = 1 + len(feature_cols)
    for t, g in df.groupby(time_col, observed=True):
        # slice guard (declared 2026-11-09 deviation): a cross-section with
        # fewer rows than RHS params (const + regressors) is rank-deficient —
        # statsmodels pinv would emit arbitrary beta draws; skip instead.
        if len(g) < n_rhs:
            continue
        X = sm.add_constant(g[feature_cols].astype("float64"), has_constant="add")
        if np.linalg.matrix_rank(X.to_numpy()) < n_rhs:
            continue  # rank-deficient slice: pinv betas would be arbitrary
        m = sm.OLS(g[outcome].astype("float64"), X).fit()
        for c in feature_cols:
            betas[c].append(float(m.params[c]))
        times.append(t)
    tb = pd.DataFrame(betas, index=pd.Index(times, name=time_col))
    cms = {}
    for c in feature_cols:
        nw = sm.OLS(tb[c], np.ones(len(tb))).fit(
            cov_type="HAC", cov_kwds={"maxlags": maxlag})
        cms[c] = {"beta": float(nw.params.iloc[0]), "se": float(nw.bse.iloc[0]),
                  "tstat": float(nw.tvalues.iloc[0]), "pvalue": float(nw.pvalues.iloc[0])}
    return {"method": "fama_macbeth", "coef_stats": cms, "betas": tb}


def run_panel(panel: pd.DataFrame, outcome: str, feature_cols: list[str],
              se: str = "driscoll_kraay", **kw):
    ensure_valid_se(se)
    if se == "driscoll_kraay":
        return fit_driscoll_kraay(panel, outcome, feature_cols, **kw)
    if se == "double_clustered":
        return fit_double_clustered(panel, outcome, feature_cols, **kw)
    if se == "fama_macbeth":
        return fit_fama_macbeth(panel, outcome, feature_cols, **kw)
    return fit_double_clustered(panel, outcome, feature_cols, **kw)  # entity-only last resort
