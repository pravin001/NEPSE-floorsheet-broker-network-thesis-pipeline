"""v2 Stage-1 seed-range tests (plan V2-0)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nepsemsc.utils.seeds import PLACEBO_SEEDS
from nepsemsc.utils.seeds_v2 import (V2_BLOCK_PERM_SEEDS, V2_NEGCTRL_SEEDS,
                                     V2_RW_SEEDS, V2_SCORE_PERM_SEEDS,
                                     V2_WB_SEEDS)


def test_declared_lengths():
    assert len(V2_SCORE_PERM_SEEDS) == 1000
    assert len(V2_BLOCK_PERM_SEEDS) == 1000
    assert len(V2_NEGCTRL_SEEDS) == 2000
    assert len(V2_RW_SEEDS) == 999
    assert len(V2_WB_SEEDS) == 999


def test_ranges_are_exact_and_unique():
    assert V2_SCORE_PERM_SEEDS == [826_001 + i for i in range(1000)]
    assert V2_BLOCK_PERM_SEEDS == [828_001 + i for i in range(1000)]
    assert V2_NEGCTRL_SEEDS == [829_001 + i for i in range(2000)]
    assert V2_RW_SEEDS == [830_001 + i for i in range(999)]
    assert V2_WB_SEEDS == [833_001 + i for i in range(999)]
    for seq in (V2_SCORE_PERM_SEEDS, V2_BLOCK_PERM_SEEDS, V2_NEGCTRL_SEEDS,
                V2_RW_SEEDS, V2_WB_SEEDS):
        assert len(seq) == len(set(seq))


def test_first_200_score_seeds_equal_v1_placebo_seeds():
    """The expanded battery must extend, never replace, the v1 sequence."""
    assert V2_SCORE_PERM_SEEDS[:200] == PLACEBO_SEEDS


def test_used_ranges_do_not_overlap():
    """Executed draws are disjoint. NOTE (pre-declaration inconsistency,
    deviation-logged): the declared 2000-seed negctrl list extends to
    831000 and overlaps the RW range; only its first 1000 seeds are used,
    and those are disjoint from every other executed range."""
    used = [set(V2_SCORE_PERM_SEEDS), set(V2_BLOCK_PERM_SEEDS),
            set(V2_NEGCTRL_SEEDS[:1000]), set(V2_RW_SEEDS), set(V2_WB_SEEDS)]
    for i in range(len(used)):
        for j in range(i + 1, len(used)):
            assert not (used[i] & used[j])


def test_declared_negctrl_full_list_overlap_is_pinned():
    """Pin the declared-range overlap so it cannot grow unnoticed."""
    assert (set(V2_NEGCTRL_SEEDS) & set(V2_RW_SEEDS)
            == set(range(830_001, 831_000)))
    assert not (set(V2_NEGCTRL_SEEDS[:1000]) & set(V2_RW_SEEDS))
