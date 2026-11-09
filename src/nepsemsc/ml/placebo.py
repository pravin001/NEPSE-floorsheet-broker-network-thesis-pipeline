"""Placebo machinery (R2) — permutations under the PRE-DECLARED seed list."""
from __future__ import annotations

import numpy as np

from nepsemsc.utils.seeds import PLACEBO_SEEDS, placebo_seed


def permuted_scores(scores: np.ndarray, n_permutations: int | None = None) -> list[np.ndarray]:
    """Exactly the pre-declared seed list (826001..826200) → deterministic
    permutations OPTIONAL count (R2 requires >= 200; default is the listed 200)."""
    if n_permutations is not None:
        if n_permutations < 200:
            raise ValueError("R2 requires at least 200 permutations")
        seeds = [placebo_seed(i) for i in range(n_permutations)]
    else:
        seeds = PLACEBO_SEEDS
    arr = np.asarray(scores, dtype="float64")
    return [np.random.default_rng(s).permutation(arr) for s in seeds]


def placebo_p_value(observed_beta: float, placebo_betas: np.ndarray) -> float:
    """One-sided upper share: fraction of placebo betas >= observed."""
    pb = np.asarray(placebo_betas, dtype="float64")
    return float((pb >= observed_beta).mean())


def placebo_significance(observed_beta: float, placebo_betas: np.ndarray,
                         alpha: float = 0.05) -> bool:
    """Headline-beta rule: significant iff observed beats the (1-alpha)
    percentile — equivalently placebo_p_value <= alpha (R2)."""
    return placebo_p_value(observed_beta, placebo_betas) <= alpha
