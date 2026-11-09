"""Purged chronological walk-forward fold construction (R5/R7).

Sequential mode (default, matches the brief fold spec):
  sorted unique sessions are split into 2 * n_folds contiguous segments;
  fold k trains on segment k  [t0:t1] and tests on segment k+1 starting
  AFTER `purge_gap` sessions (strict gap: test_start_pos = train_end_pos + gap + 1).
  gap = horizon(1) + embargo(5) = 6 sessions by the brief.

The fold object carries `train_pos`/`test_pos` (0-based positions in the sorted
session index) and the dates themselves; nothing else is inferred, and no
fold shares a session with its test block.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Hashable

import numpy as np
import pandas as pd

from nepsemsc.utils.seeds import if_seed


@dataclass
class FoldSpec:
    fold_id: int
    train_dates: list
    test_dates: list
    train_pos: tuple[int, int]      # [start, end) into the sorted session index
    test_pos: tuple[int, int]
    purge_gap_sessions: int


def purged_folds(
    dates: Sequence[Hashable] | pd.Series | pd.Index,
    n_folds: int = 4,
    purge_gap_sessions: int = 6,
    mode: str = "sequential",
) -> list[FoldSpec]:
    if mode != "sequential":
        raise NotImplementedError(f"fold mode {mode!r} not pre-declared (analysis_plan.md)")
    u = np.array(pd.unique(pd.Series(list(dates))), dtype="object")
    u = np.array(sorted(u.tolist()), dtype="object")
    n = len(u)
    if n < 2 * n_folds:
        raise ValueError(f"not enough sessions for {n_folds} folds: {n}")
    seg_bounds = np.linspace(0, n, 2 * n_folds + 1).astype(int)
    folds: list[FoldSpec] = []
    for k in range(n_folds):
        t0, t1 = int(seg_bounds[k]), int(seg_bounds[k + 1])
        t1_incl = t1 - 1                       # last train session position
        e0 = t1 + purge_gap_sessions           # = t1_incl + gap + 1  ⇒ EXACTLY
        e1 = int(seg_bounds[k + 2])            #   `gap` sessions strictly between
        if e0 >= e1:
            raise ValueError(f"fold {k}: purge gap consumes the test segment "
                             f"({e0} >= {e1}); increase sessions per fold")
        folds.append(FoldSpec(
            fold_id=k,
            train_dates=[u[i] for i in range(t0, t1)],
            test_dates=[u[i] for i in range(e0, e1)],
            train_pos=(t0, t1),
            test_pos=(e0, e1),
            purge_gap_sessions=purge_gap_sessions,
        ))
    return folds


def frame_fold_masks(feature_frame: pd.DataFrame, folds: list[FoldSpec],
                     date_col: str = "date") -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Boolean masks (train, test) per fold for a frame indexed by date rows."""
    out: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for f in folds:
        is_test = feature_frame[date_col].isin(f.test_dates).to_numpy()
        is_train = feature_frame[date_col].isin(f.train_dates).to_numpy()
        out[f.fold_id] = (is_train, is_test)
    return out


def assert_no_fold_overlap(folds: list[FoldSpec]) -> None:
    for f in folds:
        s = set(f.train_dates) & set(f.test_dates)
        if s:
            raise AssertionError(f"fold {f.fold_id} shares {len(s)} sessions between train and test — R5 violation")
