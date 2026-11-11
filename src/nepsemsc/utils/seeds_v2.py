"""v2 seed additions (V2-0 of docs/analysis_plan_v2_extension.md).

ADDITIVE ONLY — the v1 pre-declared lists above are untouched. The first 200
V2_SCORE_PERM_SEEDS are IDENTICAL to v1 PLACEBO_SEEDS (asserted by
tests/test_v2_seeds.py) so the expanded 1000-permutation placebo shares the
v1 head of the sequence.
"""
from __future__ import annotations

# Appended under plan V2-0 (declared 2026-11-10, before any v2 run):
V2_SCORE_PERM_SEEDS = [826_001 + i for i in range(1000)]   # i=0..999; head == v1
V2_BLOCK_PERM_SEEDS = [828_001 + i for i in range(1000)]   # 1000 block permutations
V2_NEGCTRL_SEEDS = [829_001 + i for i in range(2000)]      # within-block shuffles
V2_RW_SEEDS = [830_001 + b for b in range(999)]            # Romano-Wolf B=999
V2_WB_SEEDS = [833_001 + b for b in range(999)]            # wild cluster B=999
