"""Romano-Wolf step-down FWER control (v2 plan V2-1.2; deviation #12).

Family = the 10 pre-declared grid tests (single feature + log_volume_z +
market_ret_loo_z; two-way absorbed FE; DK bartlett bw=5 — v1 primary).

Bootstrap: B=999 draws, ONE Rademacher sign per (symbol, session) row applied
to the frozen within-residuals (unrestricted wild bootstrap of the outcome:
y* = fitted_raw + eps*e), all 10 tests re-estimated per draw via the validated
exact engine (`_panel_boot.pseudo_draws`), recentered t*_h = dbeta_h / se*_h.

Adjusted p (classic free step-down, hypotheses ordered by observed |t|
descending == observed p ascending):
    rw_p_k = share( max_{h in remaining(k)} |t*_h| >= |t_k| )
with monotonicity enforcement. The prompt's LITERAL full-family min-p variant
is reported as a secondary column `rw_p_literal_minp_fullset`.
p-values use the (1 + #)/(B + 1) convention (declared in deviation #12).

Contract C2 (pseudo draws vs full PanelOLS refits) is validated by
scripts/validate_v2_engine.py before this module is trusted; the runner
re-asserts that validation CSV before computing.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from nepsemsc.evaluation._panel_boot import (DKBundle, p_functional,
                                             pseudo_draws)


def bootstrap_family(bundles: list[DKBundle], seeds: list[int],
                     chunk_size: int = 200,
                     checkpoint_path: str | Path | None = None) -> dict:
    """Common-draw bootstrap of the whole family.

    Returns {'t_obs': (H,), 'p_obs': (H,), 't_boot': (B,H), 'p_boot': (B,H)}.
    One Rademacher matrix per draw is shared across all tests (the SAME
    (symbol, session) sign flip applied to every outcome definition of that
    draw — the prompt's per-iteration draw semantics). Draws are processed in
    chunks; a partial checkpoint CSV is rewritten after each chunk and is
    deleted by the caller on success (plan V2-0).
    """
    n_rows = {b.n_rows for b in bundles}
    if len(n_rows) != 1:
        raise ValueError(f"family designs have different row counts: {n_rows}")
    n = n_rows.pop()
    B = len(seeds)
    H = len(bundles)
    t_obs = np.array([b.t_obs[0] for b in bundles])
    p_obs = np.array([b.p_obs[0] for b in bundles])
    t_boot = np.empty((B, H))
    p_boot = np.empty((B, H))

    for s in range(0, B, chunk_size):
        c = min(chunk_size, B - s)
        eta = np.empty((c, n), dtype=np.int8)
        for i in range(c):
            rng = np.random.default_rng(seeds[s + i])
            eta[i] = (rng.integers(0, 2, size=n) * 2 - 1).astype(np.int8)
        for j, b in enumerate(bundles):
            draws = pseudo_draws(b, eta, cluster=False)
            tj = draws["t_recentered"][:, 0]
            t_boot[s:s + c, j] = tj
            p_boot[s:s + c, j] = p_functional(np.abs(tj), b.df_resid)
        if checkpoint_path is not None:
            pd.DataFrame(t_boot[:s + c],
                         columns=[b.test_id for b in bundles]).to_csv(
                checkpoint_path, index=False)
    return {"t_obs": t_obs, "p_obs": p_obs, "t_boot": t_boot,
            "p_boot": p_boot, "B": B}


def stepdown(p_obs: np.ndarray, p_boot: np.ndarray) -> pd.DataFrame:
    """Classic Romano-Wolf free step-down + literal full-family variant.

    Returns one row per hypothesis in ORIGINAL input order with rw_p,
    rw_p_literal_minp_fullset and ordering metadata.
    """
    H = len(p_obs)
    B = p_boot.shape[0]
    order = np.argsort(p_obs, kind="mergesort")     # ascending observed p
    rw = np.empty(H)
    lit = np.empty(H)
    minp_full = p_boot.min(axis=1)
    for k in range(H):
        remaining = order[k:]
        minp_rem = p_boot[:, remaining].min(axis=1)
        p_k = p_obs[order[k]]
        # (1+#)/(B+1) — declared convention (deviation #12)
        rw[order[k]] = (1.0 + float(np.sum(minp_rem <= p_k))) / (B + 1.0)
        lit[order[k]] = (1.0 + float(np.sum(minp_full <= p_k))) / (B + 1.0)
    # monotone enforcement along the observed-p order
    prev = 0.0
    for k in range(H):
        i = order[k]
        rw[i] = max(rw[i], prev)
        prev = rw[i]
    out = pd.DataFrame({
        "order_ascending_p": np.empty(H, dtype=int),
        "rw_p": rw,
        "rw_p_literal_minp_fullset": lit,
    })
    out.loc[order, "order_ascending_p"] = np.arange(1, H + 1)
    return out


def wild_pvalue(t_boot: np.ndarray, t_obs: float) -> float:
    """CGM-style bootstrap p (recentered t*): share |t*| >= |t_obs|,
    (1+#)/(B+1) convention (Stage-2 wild bootstrap uses the same rule)."""
    return (1.0 + float(np.sum(np.abs(t_boot) >= abs(t_obs)))) / (len(t_boot) + 1.0)
