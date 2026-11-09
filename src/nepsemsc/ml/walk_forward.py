"""Purged chronological walk-forward fold construction (R5/R7).

Two pre-declared modes. BOTH use the strict gap definition:
test_start_pos = train_end_pos + purge_gap_sessions + 1, i.e. EXACTLY
`purge_gap` sessions sit strictly between the last train session and the
first test session (gap = horizon(1) + embargo(5) = 6 sessions by brief).
No fold ever shares a session between its own train and test blocks (R5),
and fold ids are deterministic given the input dates (DC7).

* "anchored" (DEFAULT — expanding-window purged walk-forward):
  sorted unique sessions are cut at the n_folds + 2 boundary points
  linspace(0, n, n_folds + 2) forming chunks c_0..c_{n_folds}.
  Fold f (f = 0..n_folds-1):
      train = [0, start(c_{f+1}))        — EVERYTHING strictly before it
      test  = [start(c_{f+1}) + gap, end(c_{f+1}))
  so chunk 0 is pure warm-up training data and the training window grows
  fold over fold. Test blocks tile the timeline after the warm-up chunk:
  the 2021-22 bubble tail and 2024 both receive OOS scores.

* "sequential" (rolling pairs; KEPT as the Phase-5 robustness variant):
  split into 2*n_folds equal segments; fold k trains on segment k and
  tests on segment k+1 purged at its start. By construction only the
  middle segments receive scores.

Deviation record (2026-11-09, docs/analysis_deviations.md): default
changed from "sequential" to "anchored" BEFORE any test-fold data was
observed. Reason: sequential pairs never score the bubble tail or 2024 —
see deviations row for the full justification.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Sequence

import numpy as np
import pandas as pd

from nepsemsc.utils.seeds import if_seed  # re-exported; callers read fold seeds


MODES = ("anchored", "sequential")


@dataclass
class FoldSpec:
    fold_id: int
    train_dates: list
    test_dates: list
    train_pos: tuple[int, int]      # [start, end) into the sorted session index
    test_pos: tuple[int, int]
    purge_gap_sessions: int
    mode: str = "anchored"


def _sorted_unique_dates(dates: Sequence[Hashable] | pd.Series | pd.Index) -> list:
    u = np.array(pd.unique(pd.Series(list(dates))), dtype="object")
    try:
        u = np.array(sorted(u.tolist()), dtype="object")
    except TypeError:  # unorderable mix — fall back to lexicographic strings
        u = np.array(sorted(map(str, u.tolist())), dtype="object")
    return [x for x in u]


def _anchored_folds(u: list, n_folds: int, gap: int) -> list[FoldSpec]:
    n = len(u)
    bounds = np.linspace(0, n, n_folds + 2).astype(int)
    folds: list[FoldSpec] = []
    for f in range(n_folds):
        t_end = int(bounds[f + 1])            # train = [0, t_end)
        e0 = t_end + gap                      # strict gap ⇒ e0 = (t_end-1) + gap + 1
        e1 = int(bounds[f + 2])               # bounds has n_folds+2 points; last = n
        if t_end < 1:
            raise ValueError(f"fold {f}: empty warm-up training chunk")
        if e0 >= e1:
            raise ValueError(
                f"fold {f}: purge gap ({gap}) consumes the test chunk "
                f"({e0} >= {e1}); increase sessions or reduce n_folds/gap")
        folds.append(FoldSpec(
            fold_id=f,
            train_dates=u[0:t_end],
            test_dates=u[e0:e1],
            train_pos=(0, t_end),
            test_pos=(e0, e1),
            purge_gap_sessions=gap,
            mode="anchored",
        ))
    return folds


def _sequential_folds(u: list, n_folds: int, gap: int) -> list[FoldSpec]:
    n = len(u)
    seg_bounds = np.linspace(0, n, 2 * n_folds + 1).astype(int)
    folds: list[FoldSpec] = []
    for k in range(n_folds):
        t0, t1 = int(seg_bounds[k]), int(seg_bounds[k + 1])
        t1_incl = t1 - 1                       # last train session position
        e0 = t1 + gap                          # = t1_incl + gap + 1  ⇒ EXACTLY
        e1 = int(seg_bounds[k + 2])            #   `gap` sessions strictly between
        if e0 >= e1:
            raise ValueError(f"fold {k}: purge gap consumes the test segment "
                             f"({e0} >= {e1}); increase sessions per fold")
        folds.append(FoldSpec(
            fold_id=k,
            train_dates=u[t0:t1],
            test_dates=u[e0:e1],
            train_pos=(t0, t1),
            test_pos=(e0, e1),
            purge_gap_sessions=gap,
            mode="sequential",
        ))
    return folds


def purged_folds(
    dates: Sequence[Hashable] | pd.Series | pd.Index,
    n_folds: int = 4,
    purge_gap_sessions: int = 6,
    mode: str = "anchored",
) -> list[FoldSpec]:
    if mode not in MODES:
        raise ValueError(f"unknown fold mode {mode!r}; pre-declared modes: {MODES}")
    if purge_gap_sessions < 0:
        raise ValueError("purge_gap_sessions must be >= 0")
    u = _sorted_unique_dates(dates)
    n = len(u)
    if n < 2 * n_folds:
        raise ValueError(f"not enough sessions for {n_folds} folds: {n}")
    if mode == "anchored":
        return _anchored_folds(u, n_folds, purge_gap_sessions)
    return _sequential_folds(u, n_folds, purge_gap_sessions)


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
