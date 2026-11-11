"""Wild cluster bootstrap (Cameron-Gelbach-Miller 2008 ReBWB, plan V2-2).

Protocol (pre-declared in docs/analysis_plan_v2_extension.md before any v2
Stage-2 result):
  * cluster = symbol (entity); B=999 draws from V2_WB_SEEDS;
  * ONE Rademacher weight eta_g in {-1,+1} per cluster per draw, shared by
    the whole 10-test family (same draw applied to every test);
  * pseudo-outcome y* = y_hat + eta_g * e (within-residuals), refit the SAME
    two-way FE model, recentered t* = (beta* - beta_hat)/SE*_CLUSTER where
    SE*_CLUSTER is the entity-clustered covariance of the pseudo-sample;
  * p_WB = (1 + #{|t*| >= |t_obs_cluster|}) / (B + 1), two-sided, with
    t_obs_cluster = beta_hat / SE_CLUSTER of the observed fit.

The observed t uses the SAME cluster-robust estimator as the bootstrap —
using the DK t with cluster-robust bootstrap draws is a mismatch and would
over-reject. The engine is the Stage-1-validated `pseudo_draws` with
`cluster=True, cluster_cov=True`; validation against full
`PanelOLS(cov_type="clustered")` refits is a hard gate (C2-style).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from nepsemsc.evaluation._panel_boot import (BundleError, DKBundle,
                                             make_pseudo_panel, pseudo_draws)
from nepsemsc.ml.panel_regression import fit_cluster_entity

REL_TOL = 1e-8


def cluster_weights(seeds: list[int], n_clusters: int) -> np.ndarray:
    """(B, n_clusters) int8 Rademacher matrix, one rng per declared seed."""
    eta = np.empty((len(seeds), n_clusters), dtype=np.int8)
    for i, seed in enumerate(seeds):
        rng = np.random.default_rng(seed)
        eta[i] = (rng.integers(0, 2, size=n_clusters) * 2 - 1).astype(np.int8)
    return eta


def wild_cluster_p(t_boot: np.ndarray, t_obs: float) -> float:
    """Two-sided ReBWB p with the (1+#)/(B+1) convention."""
    t = np.asarray(t_boot, dtype=float)
    return float((1.0 + np.sum(np.abs(t) >= abs(t_obs))) / (len(t) + 1.0))


def slow_cluster_refit(panel: pd.DataFrame, bundle: DKBundle, u: np.ndarray):
    """Full PanelOLS refit with entity-clustered covariance (validation only)."""
    pseudo = make_pseudo_panel(panel, bundle, u)
    return fit_cluster_entity(pseudo, "_y_pseudo_", list(bundle.col_names))


def bootstrap_wild_cluster(panel: pd.DataFrame, bundles: list[DKBundle],
                           seeds: list[int], chunk_size: int = 200,
                           checkpoint_path: str | Path | None = None) -> dict:
    """Common-draw wild cluster bootstrap of the whole family.

    Returns {'t_obs','t_dk','se_cluster_obs','p_obs','t_boot','p_wb','B',
             'n_clusters'}.
    """
    if not bundles:
        raise ValueError("empty bundle family")
    ent = bundles[0].ent_idx
    n_rows = {b.n_rows for b in bundles}
    if len(n_rows) != 1:
        raise ValueError(f"family designs have different row counts: {n_rows}")
    for b in bundles:
        if not np.array_equal(b.ent_idx, ent):
            raise BundleError(f"[{b.test_id}] entity coding differs across family")
    n_clusters = int(ent.max()) + 1
    B = len(seeds)
    H = len(bundles)
    eta = cluster_weights(seeds, n_clusters)
    t_dk = np.array([b.t_obs[0] for b in bundles])
    p_obs = np.array([b.p_obs[0] for b in bundles])

    # observed cluster-robust SE/t (the same estimator as the bootstrap draws)
    se_cluster = np.empty(H)
    t_cluster = np.empty(H)
    for j, b in enumerate(bundles):
        res = fit_cluster_entity(panel, b.outcome, list(b.col_names))
        # column 0 is the tested feature (bundle spec = [feature_z, *controls])
        se_cluster[j] = float(res.std_errors[b.col_names[0]])
        t_cluster[j] = float(res.tstats[b.col_names[0]])

    t_boot = np.empty((B, H))
    for s in range(0, B, chunk_size):
        c = min(chunk_size, B - s)
        for j, b in enumerate(bundles):
            draws = pseudo_draws(b, eta[s:s + c], cluster=True,
                                 cluster_cov=True)
            t_boot[s:s + c, j] = draws["t_recentered"][:, 0]
        if checkpoint_path is not None:
            pd.DataFrame(t_boot[:s + c],
                         columns=[b.test_id for b in bundles]).to_csv(
                checkpoint_path, index=False)
    p_wb = np.array([wild_cluster_p(t_boot[:, j], t_cluster[j])
                     for j in range(H)])
    return {"t_obs": t_cluster, "t_dk": t_dk,
            "se_cluster_obs": se_cluster, "p_obs": p_obs,
            "t_boot": t_boot, "p_wb": p_wb, "B": B,
            "n_clusters": n_clusters}


def validate_cluster_engine(panel: pd.DataFrame, bundles: list[DKBundle],
                            seeds: list[int]) -> float:
    """C2-style gate: cluster pseudo-draws vs FULL clustered refits.

    Uses the first len(seeds) draws and every bundle (>=2 designs expected).
    Returns the worst relative error (base SE + draw beta/se/t) and raises
    on failure.
    """
    if len(bundles) < 2:
        raise BundleError("validation needs >=2 designs")
    eta = cluster_weights(seeds, int(bundles[0].ent_idx.max()) + 1)
    worst = 0.0
    for b in bundles:
        # eta = +1 for every cluster reproduces the observed sample exactly
        ones = np.ones((1, eta.shape[1]), dtype=np.int8)
        base = pseudo_draws(b, ones, cluster=True, cluster_cov=True)
        ref_base = fit_cluster_entity(panel, b.outcome, list(b.col_names))
        worst = max(worst,
                    abs(float(base["se"][0, 0])
                        - float(ref_base.std_errors[b.col_names[0]]))
                    / max(abs(float(ref_base.std_errors[b.col_names[0]])),
                          1e-30))
        draws = pseudo_draws(b, eta, cluster=True, cluster_cov=True)
        for d in range(len(seeds)):
            u = eta[d].astype(float)[b.ent_idx] * b.e_w
            ref = slow_cluster_refit(panel, b, u)
            for j, col in enumerate(b.col_names):
                for got, want in ((float(b.beta[j] + draws["delta"][d, j]),
                                   float(ref.params[col])),
                                  (float(draws["se"][d, j]),
                                   float(ref.std_errors[col]))):
                    worst = max(worst, abs(got - want) / max(abs(want), 1e-30))
            for j, col in enumerate(b.col_names):
                se_ref = float(ref.std_errors[col])
                t_ref = (float(ref.params[col]) - float(b.beta[j])) / se_ref
                worst = max(worst,
                            abs(float(draws["t_recentered"][d, j]) - t_ref)
                            / max(abs(t_ref), 1e-30))
    if worst > REL_TOL:
        raise BundleError(f"wild-cluster engine vs full refits rel={worst:.2e}")
    return worst
