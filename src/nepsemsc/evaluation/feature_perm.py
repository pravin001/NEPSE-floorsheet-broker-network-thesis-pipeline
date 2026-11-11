"""Fast feature-permutation fits on the frozen FE design (Stage 1, 1.5).

The v1 placebo machinery refits `PanelOLS` per permutation (~200 draws x
1-2 tests). The expanded v2 battery needs 1000 draws x 4 constructions, so
this module reuses the SAME validated two-way-demeaning / DK-kernel algebra
as `_panel_boot` but keeps the OUTCOME fixed and permutes the FEATURE column
(the design changes per draw; the residuals are not pseudo-draws).

Contract C3 (validated before use by the Stage-1 runner and by
tests/test_romano_wolf.py): for >=3 random permutations on >=2 designs,
fast-fit beta/SE/t vs full `fit_driscoll_kraay` refits must agree to
rel <= 1e-8. On failure the caller falls back to full refits.

Only the feature coefficient (column 0) is returned; controls are fixed.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from nepsemsc.evaluation._panel_boot import (BundleError, DKBundle,
                                             dk_S_from_period_scores,
                                             demean_twoway, p_functional)


@dataclass
class PermEngine:
    """Frozen-controls engine for feature permutations on one base design."""
    test_id: str
    outcomes: list[str]
    y_w: dict[str, np.ndarray]          # within-transformed outcomes
    C_w: np.ndarray                     # (n, k-1) within-transformed controls
    ent_idx: np.ndarray
    tim_idx: np.ndarray
    weights: np.ndarray
    calib_c: float
    df_resid: int
    n_rows: int


def make_perm_engine(panel: pd.DataFrame, bundle: DKBundle,
                     outcomes: list[str]) -> PermEngine:
    """Build from a validated base bundle (row order must be identity)."""
    p = panel.sort_values(["symbol", "date"]).reset_index(drop=True)
    if len(p) != bundle.n_rows:
        raise BundleError("panel row count mismatch")
    syms = p["symbol"].astype(str).to_numpy()
    ent = pd.factorize(syms, sort=True)[0]
    if not np.array_equal(ent, bundle.ent_idx):
        raise BundleError("entity coding mismatch vs bundle")
    dates = pd.to_datetime(p["date"])
    tim = pd.factorize(dates, sort=True)[0]
    if not np.array_equal(tim, bundle.tim_idx):
        raise BundleError("time coding mismatch vs bundle")
    y_w = {}
    for oc in outcomes:
        y = p[oc].to_numpy(dtype=float)
        if not np.isfinite(y).all():
            raise BundleError(f"non-finite outcome {oc}")
        y_w[oc] = demean_twoway(y[:, None], ent, tim)[:, 0]
    return PermEngine(test_id=bundle.test_id, outcomes=list(outcomes),
                      y_w=y_w, C_w=bundle.X_w[:, 1:].copy(),
                      ent_idx=bundle.ent_idx.copy(), tim_idx=bundle.tim_idx.copy(),
                      weights=bundle.weights.copy(), calib_c=bundle.calib_c,
                      df_resid=bundle.df_resid, n_rows=bundle.n_rows)


def perm_fit(engine: PermEngine, feature_perm: np.ndarray) -> dict:
    """One permuted-feature DK fit; returns per-outcome beta/se/t/p arrays."""
    f = np.asarray(feature_perm, dtype=float)
    if f.shape != (engine.n_rows,):
        raise BundleError("feature permutation length mismatch")
    f_w = demean_twoway(f[:, None], engine.ent_idx, engine.tim_idx)[:, 0]
    X = np.column_stack([f_w, engine.C_w])
    Ainv = np.linalg.inv(X.T @ X)
    Xt = X.T
    out = {k: np.empty(len(engine.outcomes)) for k in ("beta", "se", "t", "p")}
    for j, oc in enumerate(engine.outcomes):
        yw = engine.y_w[oc]
        b = Ainv @ (Xt @ yw)
        e = yw - X @ b
        scores = e[:, None] * X
        xi = np.zeros((int(engine.tim_idx.max()) + 1, X.shape[1]))
        np.add.at(xi, engine.tim_idx, scores)
        S = dk_S_from_period_scores(xi, engine.weights)
        V = engine.calib_c * (Ainv @ S) @ Ainv
        se = float(np.sqrt(V[0, 0]))
        b0 = float(b[0])
        t = b0 / se
        out["beta"][j] = b0
        out["se"][j] = se
        out["t"][j] = t
        out["p"][j] = float(p_functional(t, engine.df_resid))
    return out


# ------------------------------ permutation schemes ------------------------ #
def permute_full(feature: np.ndarray, seed: int) -> np.ndarray:
    """v1-compatible full-panel unordered shuffle (one rng per draw)."""
    rng = np.random.default_rng(seed)
    return rng.permutation(np.asarray(feature, dtype=float))


def permute_full_v1(feature_v1: np.ndarray, sort_order: np.ndarray,
                    seed: int) -> np.ndarray:
    """EXACT v1 draw mapping: shuffle the v1-order array, then reorder to the
    engine's sorted panel order.

    v1 assigned `rng.permutation(base[feat].to_numpy())` on the unsorted
    panel; `run_panel` then sorted internally. The same seeded draw therefore
    maps to a different sorted vector than shuffling the sorted array, so the
    expanded battery must reproduce v1 via this route (first-200 ≡ v1).
    """
    rng = np.random.default_rng(seed)
    perm = rng.permutation(np.asarray(feature_v1, dtype=float))
    return perm[np.asarray(sort_order, dtype=int)]


def permute_blocks(feature: np.ndarray, symbols: np.ndarray, seed: int,
                   block: int = 5) -> np.ndarray:
    """Whole-block permutation WITHIN symbol (NEPSE week ~= 5 sessions).

    Blocks never cross symbols: each symbol's block list gets its own
    rng.permutation draw, consumed in symbol order.
    """
    f = np.asarray(feature, dtype=float)
    sym = np.asarray(symbols)
    rng = np.random.default_rng(seed)
    out = np.empty_like(f)
    start = 0
    for i in range(1, len(sym) + 1):
        if i == len(sym) or sym[i] != sym[start]:
            idx = np.arange(start, i)
            blocks = [idx[s:s + block] for s in range(0, len(idx), block)]
            order = rng.permutation(len(blocks))
            pos = start
            for k in order:
                blk = blocks[k]
                out[pos:pos + len(blk)] = f[blk]
                pos += len(blk)
            start = i
    return out


def shares(beta_perm: np.ndarray, beta_obs: float,
           predicted_sign: str) -> dict[str, float]:
    """Sided v1 share + the new two-sided absolute share (mean convention)."""
    pb = np.asarray(beta_perm, dtype=float)
    upper = float((pb >= beta_obs).mean())
    lower = float((pb <= beta_obs).mean())
    two = float((np.abs(pb) >= abs(beta_obs)).mean())
    sided = upper if predicted_sign == "pos" else lower
    return {"upper": upper, "lower": lower, "two_sided": two, "sided": sided}


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score interval for a binomial share (local 95% CI)."""
    if n <= 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (float(centre - half), float(centre + half))
