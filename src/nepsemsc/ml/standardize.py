"""Leakage-safe standardisation (R1/R5/DC7/DC8).

`LeakSafeStandardizer` computes winsorisation bounds AND mean/da sigma from the
TRAINING portion ONLY; transform() applies those stored constants to any fold
(TEST included) without recomputation. fit_transform is provided ONLY for the
training rows. This is the single standardisation engine for Module 2 — no
scikit-learn Pipeline(StandardScaler) on the full series, ever.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class LeakSafeStandardizer:
    """Fit-once, apply-with-frozen-constants scaler + winsoriser."""

    def __init__(self, feature_cols: list[str], winsor: tuple[float, float] = (0.01, 0.99)):
        self.feature_cols = list(feature_cols)
        self.winsor = winsor
        self._mu: pd.Series | None = None
        self._sd: pd.Series | None = None
        self._lower: pd.Series | None = None
        self._upper: pd.Series | None = None
        self.fitted_on: str | None = None  # fold label the stats came from
        self.applied_to: list[str] = []    # fold labels transformed since fit
        self.zero_variance_features: list[str] = []

    # ---------------------------------------------------------------- fit
    def fit(self, X_train: pd.DataFrame, fold_label: str = "train") -> "LeakSafeStandardizer":
        cols = [c for c in self.feature_cols if c in X_train.columns]
        if len(cols) != len(self.feature_cols):
            raise ValueError(f"missing feature columns: {sorted(set(self.feature_cols) - set(X_train.columns))}")
        sub = X_train[self.feature_cols].astype("float64")
        self._lower = sub.quantile(self.winsor[0])
        self._upper = sub.quantile(self.winsor[1])
        cl = sub.clip(lower=self._lower, upper=self._upper, axis=1)
        self._mu = cl.mean()
        self._sd = cl.std(ddof=0)
        self.zero_variance_features = [c for c in self.feature_cols if float(self._sd[c]) < 1e-12]
        # zero-variance features get identity scaling (sd := 1) so transform
        # cannot produce division-by-zero; the column is dropped from the
        # feature matrix upstream if it carries no information.
        self._sd[self.zero_variance_features] = 1.0
        self.fitted_on = fold_label
        self.applied_to = []
        return self

    def fit_transform(self, X_train: pd.DataFrame, fold_label: str = "train") -> pd.DataFrame:
        self.fit(X_train, fold_label=fold_label)
        return self.transform(X_train, fold_label=fold_label)

    # ----------------------------------------------------------- transform
    def transform(self, X: pd.DataFrame, fold_label: str = "test") -> pd.DataFrame:
        if self._mu is None:
            raise RuntimeError("LeakSafeStandardizer used before fit() — R1 violation guard")
        cols = [c for c in self.feature_cols if c in X.columns]
        if len(cols) != len(self.feature_cols):
            raise ValueError("missing feature columns at transform time")
        sub = X[self.feature_cols].astype("float64")
        cl = sub.clip(lower=self._lower, upper=self._upper, axis=1)
        out = (cl - self._mu) / self._sd
        self.applied_to.append(fold_label)
        return out

    # ---------------------------------------------------------------- meta
    @property
    def stats_(self) -> dict:
        return {"mu": self._mu, "sd": self._sd,
                "winsor_lower": self._lower, "winsor_upper": self._upper,
                "fitted_on": self.fitted_on,
                "zero_variance_features": self.zero_variance_features}
