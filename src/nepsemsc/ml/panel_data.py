"""Phase-4 regression-panel construction — ONE implementation, two consumers
(EXP-0004b grid, EXP-0004d regime split) so DC7 fold-constants can never drift
between scripts.

Construction rules (same as EXP-0004b, deviation note 2026-11-09):
  * OOS TEST rows only (train scores are EDA-only, never pooled);
  * merge daily outcomes on (date, symbol); control `log_volume` from the
    carried-through `total_volume`;
  * per fold: winsor 1/99 + z-standardization of ALL regressors with
    TRAIN-fold constants of that fold's universe (DC7) — including the
    market-return control (2026-11-09 deviation: raw-scale market_return
    inflated κ(design) to a scale artifact);
  * outcomes stay RAW (their coefficients are bp per 1-SD regressor move).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TESTED_FEATURES = ["anomaly_score", "buyer_hhi", "self_loop_ratio",
                   "reciprocity", "end_of_day_concentration"]
Z_SOURCE_COLS = TESTED_FEATURES + ["log_volume", "market_ret_loo"]


def build_oos_panel(scores: pd.DataFrame, outcomes: pd.DataFrame,
                    extra_outcome_cols: tuple[str, ...] = ()
                    ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(panel, train): OOS test rows with outcomes + log_volume; and the
    train rows merged with market_ret_loo (fold-statistics input).
    `extra_outcome_cols` (e.g. fwd_k horizons, Phase-5 battery) ride along
    on the TEST merge ONLY — the base dropna row set is unchanged
    (`ret_fwd1` + Z_SOURCE_COLS); truncated tails stay NaN and are handled
    per-fit by each regression's own dropna. Default keeps EXP-0004b/d
    behaviour bit-identical."""
    sc = scores.copy()
    out = outcomes.copy()
    sc["date"] = pd.to_datetime(sc["date"]).dt.date
    out["date"] = pd.to_datetime(out["date"]).dt.date

    test_cols = ["date", "symbol", "ret_fwd1", "abs_ret_fwd1",
                 "market_ret_loo", *extra_outcome_cols]
    test = (sc.loc[~sc["is_train"]]
              .merge(out[test_cols], on=["date", "symbol"], how="left"))
    test["log_volume"] = np.log(test["total_volume"].clip(lower=1.0))
    test = test.dropna(subset=["ret_fwd1"] + Z_SOURCE_COLS).reset_index(drop=True)

    train = (sc.loc[sc["is_train"]]
               .merge(out[["date", "symbol", "market_ret_loo"]],
                      on=["date", "symbol"], how="left"))
    train["log_volume"] = np.log(train["total_volume"].clip(lower=1.0))
    return test, train


def train_fold_stats(train: pd.DataFrame,
                     cols: list[str] | None = None) -> dict[int, dict[str, dict[str, float]]]:
    """Per fold: (q1, q99, mu, sd) from TRAIN rows — winsor 1/99 then
    mean/sd of the clipped values (DC7)."""
    cols = Z_SOURCE_COLS if cols is None else cols
    stats: dict[int, dict[str, dict[str, float]]] = {}
    for fold_id, g in train.groupby("fold_id", observed=True):
        st: dict[str, dict[str, float]] = {}
        for col in cols:
            q1, q99 = float(g[col].quantile(0.01)), float(g[col].quantile(0.99))
            clipped = g[col].clip(q1, q99)
            st[col] = {"q1": q1, "q99": q99,
                       "mu": float(clipped.mean()),
                       "sd": float(clipped.std(ddof=0))}
        stats[fold_id] = st
    return stats


def standardize_test(panel: pd.DataFrame,
                     stats_by_fold: dict[int, dict[str, dict[str, float]]]
                     ) -> pd.DataFrame:
    """Adds `<col>_z` for every Z_SOURCE_COLS column, using the TRAIN-fold
    constants of the row's own fold (DC7). Nothing crosses folds."""
    panel = panel.copy()
    for fold_id, st in stats_by_fold.items():
        m = panel["fold_id"] == fold_id
        for col, s in st.items():
            panel.loc[m, col + "_z"] = (
                (panel.loc[m, col].clip(s["q1"], s["q99"]) - s["mu"]) / s["sd"])
    return panel
