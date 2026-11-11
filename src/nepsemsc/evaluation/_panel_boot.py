"""Validated fast panel-bootstrap engine (v2 A++, plan V2-0/V2-1/V2-2).

Mirrors the v1 PRIMARY estimator EXACTLY — the linearmodels-7.1 class
`DriscollKraay` (selected by cov_type="kernel" in the v1 wrapper):
    xi_t  = sum_{i in period t} (eps_i * x_it)   cross-sectionally summed scores
    S     = xi_0'xi_0 + sum_{j=1..bw} w_j (xi'_{t}xi_{t+j} + transpose)
    V     = scale * inv(X'X) S inv(X'X),
    scale = nobs / nobs_eff, nobs_eff = nobs - extra_df - nvar*(debiased),
    w_j   = 1 - j/(bw+1)   (bartlett; bandwidth=5 as in v1),
    inference: Student-t with df_resid (verified = res.pvalues functional).

The subtract-const subtlety: within-transformed const column is exactly zero
(consistent with linearmodels docs), so all block algebra is restricted to the
non-constant columns — exactly block-equivalent (asserted numerically).

HARD CONTRACTS (BundleError => fall back to full PanelOLS refits):
  C1. base-fit covariance replication vs res.cov within rel 1e-8;
  C2. pseudo-draw t/SE vs full PanelOLS refits within rel 1e-8
      (>=2 designs x >=3 draws; enforced by the Stage-1 runner).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import sparse
from scipy.stats import t as student_t

from nepsemsc.ml.panel_regression import fit_driscoll_kraay

REL_TOL = 1e-8


class BundleError(RuntimeError):
    """Any engine/reference mismatch — caller switches to the slow path."""


# ---------------------------- two-way demeaning ---------------------------- #
def _contig_group_means(u: np.ndarray, starts: np.ndarray, ends: np.ndarray) -> np.ndarray:
    """Per-group means of contiguous blocks broadcast back to (n x m)."""
    sums = np.add.reduceat(u, starts, axis=0)
    lengths = (ends - starts).astype(float)[:, None]
    out = np.empty_like(u)
    pos = 0
    for i in range(len(starts)):
        m_ = ends[i] - starts[i]
        out[pos:pos + m_] = sums[i][None, :] / lengths[i][0]
        pos += m_
    return out


def demean_twoway(u: np.ndarray, ent_idx: np.ndarray, tim_idx: np.ndarray,
                  max_iter: int = 400, tol: float = 1e-14) -> np.ndarray:
    """Exact two-way demeaning via alternating projections (von Neumann).

    Projects onto the orthocomplement of span{entity dummies}+span{time
    dummies} — SAME operator linearmodels uses for PanelOLS 'both' demeaning
    (unique projection operator, so converged iteration == their transform).
    ent_idx: contiguous non-decreasing entity codes; tim_idx: any codes.
    """
    u = np.array(u, dtype="float64", copy=True)
    ents = np.unique(ent_idx)
    starts = np.searchsorted(ent_idx, ents, side="left")
    ends = np.searchsorted(ent_idx, ents, side="right")
    n_tim = int(tim_idx.max()) + 1
    tcnt = np.bincount(tim_idx, minlength=n_tim).astype(float)
    tcnt_safe = np.where(tcnt == 0, 1.0, tcnt)
    m_e = m_t = np.inf
    for _ in range(max_iter):
        u -= _contig_group_means(u, starts, ends)
        tsum = np.zeros((n_tim, u.shape[1]))
        np.add.at(tsum, tim_idx, u)
        u -= tsum[tim_idx] / tcnt_safe[tim_idx, None]
        m_e = float(np.abs(_contig_group_means(u, starts, ends)).max())
        tsum2 = np.zeros((n_tim, u.shape[1]))
        np.add.at(tsum2, tim_idx, u)
        m_t = float(np.abs(tsum2 / tcnt_safe[:, None]).max())
        if max(m_e, m_t) < tol:
            break
    else:
        raise BundleError(
            f"demean_twoway failed to converge (m_e={m_e:.2e}, m_t={m_t:.2e})")
    return u


# ------------------------------ kernel pieces ------------------------------ #
def bartlett_weights(bw: int) -> np.ndarray:
    """K(j) = 1 - j/(bw+1), j = 0..bw — linearmodels iv.covariance._bartlett."""
    return 1.0 - np.arange(bw + 1) / (bw + 1)


def dk_S_from_period_scores(xi: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """DK kernel sum S for per-period score tensors.

    xi: (n_t, k) single draw OR (c, n_t, k) batch. Returns (k,k) or (c,k,k).
    S = ξ'ξ + Σ_{j>=1} w_j (ξ_t'ξ_{t+j} + (ξ_t'ξ_{t+j})').
    """
    if xi.ndim == 2:
        S = xi.T @ xi
        T_ = xi.shape[0]
        for j in range(1, len(weights)):
            if j >= T_:
                break
            op = xi[j:].T @ xi[:-j]
            S += weights[j] * (op + op.T)
        return S
    c, n_t, k = xi.shape
    S = np.empty((c, k, k))
    S[:, :, :] = np.einsum("ctk,ctl->ckl", xi, xi)
    for j in range(1, len(weights)):
        if j >= n_t:
            break
        op = np.einsum("ctk,ctl->ckl", xi[:, j:, :], xi[:, :-j, :])
        S += weights[j] * (op + np.transpose(op, (0, 2, 1)))
    return S


# ------------------------------ design bundle ------------------------------- #
@dataclass
class DKBundle:
    """Engine-ready copy of ONE base DK fit (v1 estimator)."""
    test_id: str
    feature: str
    outcome: str
    cols: list                       # [const, feature_z, controls...] as in v1 res
    X_w: np.ndarray                  # (n, k) within design, NON-CONSTANT columns
    col_names: list
    e_w: np.ndarray                  # (n,) within residual
    beta: np.ndarray                 # (k,) v1 point estimates
    t_obs: np.ndarray
    se_obs: np.ndarray
    df_resid: int
    ent_idx: np.ndarray              # (n,) entity codes (contiguous)
    tim_idx: np.ndarray              # (n,) time codes (sorted uniques)
    weights: np.ndarray              # (bw+1,) bartlett
    calib_c: float                   # == linearmodels `scale` (validated)
    y_fitted_raw: np.ndarray         # (n,) raw-scale fitted, model order
    p_obs: np.ndarray
    tim_sums: sparse.csr_matrix      # (T, n) 0/1 scatter matrix
    base_rel_err: float = field(default=np.inf)
    p_rel_err: float = field(default=np.inf)

    @property
    def n_rows(self):
        return self.X_w.shape[0]

    @property
    def k(self):
        return self.X_w.shape[1]

    @property
    def bandwidth(self):
        return len(self.weights) - 1


def _prep_panel(panel: pd.DataFrame, outcome: str, feature_cols: Sequence[str]):
    """IDENTICAL conventions to v1 `_prep_panel` (sorted entity/time)."""
    df = panel.sort_values(["symbol", "date"]).copy()
    t_num = pd.to_datetime(df["date"], errors="coerce")
    if t_num.isna().any():
        t_num = pd.factorize(df["date"])[0].astype("float64")
    y = df[outcome].astype("float64")
    X = df[list(feature_cols)].astype("float64")
    X = sm.add_constant(X, has_constant="add")
    idx = pd.MultiIndex.from_arrays([df["symbol"].astype("category"), t_num],
                                    names=["symbol", "date"])
    y.index = idx
    X.index = idx
    return y, X, df


def p_functional(t: np.ndarray | float, df_resid: int) -> np.ndarray:
    """Two-sided Student-t p with df_resid (linearmodels panel functional)."""
    return 2.0 * student_t.sf(np.abs(t), df_resid)


def build_bundle(panel: pd.DataFrame, outcome: str, feature_cols: Sequence[str],
                 test_id: str, feature: str, bandwidth: int = 5
                 ) -> tuple[DKBundle, object]:
    """(bundle, res): base DK fit + validated engine bundle (contracts C1)."""
    res = fit_driscoll_kraay(panel, outcome, list(feature_cols), bandwidth=bandwidth)
    res.cov_type_used = "driscoll_kraay"

    oi = res.model._original_index                     # model row order
    y, X, df = _prep_panel(panel, outcome, feature_cols)
    lookup = {(str(a), pd.Timestamp(b)): i for i, (a, b) in enumerate(X.index)}
    try:
        order = np.array([lookup[(str(a), pd.Timestamp(b))] for (a, b) in oi], dtype=int)
    except (KeyError, ValueError, TypeError) as exc:
        raise BundleError(f"model order map failed: {exc}")

    md_x = np.asarray(res.model._x, dtype=float)
    Xraw_all = X.iloc[order].to_numpy(dtype=float)     # X already carries const
    if Xraw_all.shape != md_x.shape or not np.allclose(Xraw_all, md_x, atol=1e-12):
        raise BundleError("raw design mismatch vs res.model._x (ordering contract)")

    e_w = np.asarray(res.wresids, dtype=float)
    if not np.isfinite(e_w).all():
        raise BundleError("non-finite base residuals")

    col_names = list(res.params.index)
    keep = [c for c in col_names if c != "const"]
    Ki = [col_names.index(c) for c in keep]
    beta = np.array([float(res.params[c]) for c in keep])
    t_obs = np.array([float(res.tstats[c]) for c in keep])
    se_obs = np.array([float(res.std_errors[c]) for c in keep])
    p_obs = np.array([float(res.pvalues[c]) for c in keep])
    df_resid = int(res.df_resid) if hasattr(res, "df_resid") else (len(e_w) - len(col_names))
    full_cov = np.asarray(res.cov, dtype=float)
    if full_cov.shape != (len(col_names), len(col_names)):
        full_cov = res.cov.loc[col_names, col_names].to_numpy(dtype=float)

    syms = np.asarray([str(a) for (a, b) in oi], dtype=object)
    dates = np.asarray([pd.Timestamp(b) for (a, b) in oi])
    ent_idx = pd.factorize(syms, sort=True)[0]
    if not np.all(np.diff(ent_idx) >= 0):
        raise BundleError("entity codes not contiguous")
    tim_idx = pd.factorize(dates, sort=True)[0].astype(int)
    X_w = demean_twoway(md_x[:, Ki], ent_idx, tim_idx)

    weights = bartlett_weights(bandwidth)
    # C1: replicate res.cov feature block
    xi_base = (e_w[:, None] * X_w)                     # (n, k) row scores
    # per-period sums (T, k)
    n_tim = int(tim_idx.max()) + 1
    xi_t = np.zeros((n_tim, X_w.shape[1]))
    np.add.at(xi_t, tim_idx, xi_base)
    S = dk_S_from_period_scores(xi_t, weights)         # (k, k)
    Ainv = np.linalg.inv(X_w.T @ X_w)
    V_block = full_cov[np.ix_(Ki, Ki)]
    M = Ainv @ S @ Ainv
    denom = float((M * M).sum())
    calib_c = float((M * V_block).sum() / denom)
    rel = float(np.abs(calib_c * M - V_block).max() / np.abs(V_block).max())
    if not (0.0 < calib_c < np.inf) or rel > REL_TOL:
        raise BundleError(
            f"[{test_id}] base covariance replication rel={rel:.2e} (c={calib_c:.6g})")

    # p-functional verification (student-t df_resid == linearmodels pvalues)
    p_eng = p_functional(t_obs, df_resid)
    p_rel = float(np.abs(p_eng - p_obs).max())
    if p_rel > 1e-9:
        raise BundleError(f"[{test_id}] p-functional mismatch rel={p_rel:.2e}")

    if len(order) == len(panel) and (order == np.arange(len(order))).all():
        fitted_raw = np.asarray(res.fitted_values, dtype=float).ravel()
    else:
        f_in = np.asarray(res.fitted_values, dtype=float).ravel()
        fitted_raw = np.empty_like(f_in)
        fitted_raw[order] = f_in
    if not np.isfinite(fitted_raw).all():
        raise BundleError("non-finite fitted values")

    tim_sums = sparse.csr_matrix(
        (np.ones(len(tim_idx), dtype="float64"),
         (tim_idx, np.arange(len(tim_idx), dtype=int))),
        shape=(n_tim, len(tim_idx)))
    bundle = DKBundle(
        test_id=test_id, feature=feature, outcome=outcome, cols=col_names,
        X_w=X_w, col_names=keep, e_w=e_w, beta=beta, t_obs=t_obs, se_obs=se_obs,
        df_resid=df_resid, ent_idx=ent_idx, tim_idx=tim_idx, weights=weights,
        calib_c=calib_c, y_fitted_raw=fitted_raw, p_obs=p_obs,
        tim_sums=tim_sums, base_rel_err=rel, p_rel_err=p_rel)
    return bundle, res


# --------------------------- pseudo-fit bootstrap --------------------------- #
def pseudo_draws(bundle: DKBundle, eta: np.ndarray, cluster: bool = False,
                 chunk_size: int = 1700, demean_tol: float = 1e-13
                 ) -> dict:
    """Vectorized wild-bootstrap draws on the frozen design.

    eta: (B, n_row) row-level weights (RW scheme), OR (B, n_entities) when
    cluster=True (Stage-2 wild cluster bootstrap, one weight per symbol).
    Returns {'delta': (B,k), 'se': (B,k), 't_recentered': (B,k),
             't_raw': (B,k), 'beta_raw': (B,k)}.
    """
    X = bundle.X_w
    n, k = X.shape
    e = bundle.e_w
    ent, tim = np.asarray(bundle.ent_idx), np.asarray(bundle.tim_idx)
    Ainv = np.linalg.inv(X.T @ X)
    weights = bundle.weights
    eta_rows = eta[:, bundle.ent_idx] if cluster else eta
    B = eta.shape[0]

    delta = np.empty((B, k))
    se = np.empty((B, k))
    for s in range(0, B, chunk_size):
        c = min(chunk_size, B - s)
        u = eta_rows[s:s + c].astype("float64") * e[None, :]          # (c, n)
        w_u = demean_twoway(u.T, ent, tim, tol=demean_tol).T          # (c, n)
        d = w_u @ X @ Ainv.T                                          # (c, k)
        e_star = w_u - d @ X.T                                        # (c, n)
        scores_rows = e_star[:, :, None] * X[None, :, :]              # (c, n, k)
        mat = scores_rows.transpose(1, 0, 2).reshape(n, c * k)        # (n, c*k)
        xi_t = bundle.tim_sums @ mat                                  # (T, c*k)
        xi_t = xi_t.reshape(bundle.tim_sums.shape[0], c, k).transpose(1, 0, 2)
        S = dk_S_from_period_scores(xi_t, weights)                    # (c, k, k)
        V = bundle.calib_c * (Ainv @ S) @ Ainv
        se_c = np.sqrt(np.einsum("bii->bi", V))
        delta[s:s + c] = d
        se[s:s + c] = se_c
    out = bundle.beta[None, :] + delta
    return {"delta": delta, "se": se, "t_recentered": delta / se,
            "t_raw": out / se, "beta_raw": out}


def make_pseudo_panel(panel: pd.DataFrame, bundle: DKBundle, u: np.ndarray,
                      outcome_tmp: str = "_y_pseudo_") -> pd.DataFrame:
    """Panel copy with pseudo outcome fitted_raw + u for full-refit validation.

    Row order must equal the bundle's order (panel sorted by symbol/date).
    """
    out = panel.sort_values(["symbol", "date"]).copy().reset_index(drop=True)
    if len(out) != bundle.n_rows:
        raise BundleError("pseudo panel row count mismatch")
    out[outcome_tmp] = (np.asarray(bundle.y_fitted_raw, dtype=float)
                        + np.asarray(u, dtype=float))
    return out


def slow_pseudo_refit(panel: pd.DataFrame, bundle: DKBundle, u: np.ndarray,
                      bandwidth: int = 5):
    """Full linearmodels refit for validation / slow path (pre-declared
    fallback; also the reference for contract C2)."""
    pseudo = make_pseudo_panel(panel, bundle, u)
    return fit_driscoll_kraay(pseudo, "_y_pseudo_", list(bundle.col_names),
                              bandwidth=bandwidth)
