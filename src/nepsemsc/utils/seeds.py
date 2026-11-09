"""Global seed policy — PRE-DECLARED 2026-11-08 (DC14/DC20).

Every stochastic operation MUST read from this module. These values were
chosen TODAY, before any test-fold data was observed; they are part of the
frozen analysis design (docs/analysis_plan.md) and config (configs/project.yaml).

The 200 placebo permutation seeds are exactly 826001..826200, and they are
declared as a closed explicit list so that no experiment can silently change
the sample size or the seed sequence (R2: "same seed list pre-declared").
"""
from __future__ import annotations

GENERATION_DATE = "2026-11-08"

GLOBAL_SEED = 20261108  # numpy default seeding, replication docs

# Isolation Forest per purged fold (fold_0 .. fold_3), R7
IF_FOLD_SEEDS: list[int] = [917501, 917502, 917503, 917504]

# 200 pre-declared placebo permutation seeds (R2), explicit closed list
PLACEBO_SEEDS: list[int] = [826_001 + i for i in range(200)]

# deterministic network layout seed for interactive graph drawings (Phase 6)
NETWORK_LAYOUT_SEED = 11082026


def if_seed(fold_id: int) -> int:
    """Seed for the Isolation Forest of a given purged fold."""
    if not 0 <= fold_id < len(IF_FOLD_SEEDS):
        raise ValueError(f"fold_id out of range: {fold_id}")
    return IF_FOLD_SEEDS[fold_id]


def placebo_seed(i: int) -> int:
    """Seed for placebo permutation r_i (function of position ONLY)."""
    if not 0 <= i < len(PLACEBO_SEEDS):
        raise ValueError(f"permutation index out of range: {i}")
    return PLACEBO_SEEDS[i]
