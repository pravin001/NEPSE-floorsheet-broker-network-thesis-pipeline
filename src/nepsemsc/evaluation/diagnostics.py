"""Design diagnostics for Stage 2 (VIF + correlation audit, plan V2-2)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from nepsemsc.evaluation._panel_boot import demean_twoway


def within_design(panel: pd.DataFrame, cols: list[str],
                  entity_col: str = "symbol", time_col: str = "date"
                  ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Two-way within-transformed design (entity + time FE absorbed)."""
    p = panel.sort_values([entity_col, time_col]).reset_index(drop=True)
    ent = pd.factorize(p[entity_col].astype(str), sort=True)[0]
    tim = pd.factorize(pd.to_datetime(p[time_col]), sort=True)[0]
    X = demean_twoway(p[cols].to_numpy(dtype=float), ent, tim)
    return X, ent, tim


def vif_table(panel: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """VIF_j = 1/(1-R2_j) on the within-transformed design.

    R2_j comes from regressing within-transformed column j on all other
    within-transformed columns (least squares, no intercept needed because
    the within columns are already centred).
    """
    X, _, _ = within_design(panel, cols)
    rows = []
    for j, c in enumerate(cols):
        y = X[:, j]
        Z = np.delete(X, j, axis=1)
        beta, *_ = np.linalg.lstsq(Z, y, rcond=None)
        resid = y - Z @ beta
        ss_res = float(resid @ resid)
        ss_tot = float(y @ y)
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
        r2 = min(max(r2, 0.0), 1.0 - 1e-15)
        rows.append({"feature": c, "r2_on_others": r2, "vif": 1.0 / (1.0 - r2)})
    return pd.DataFrame(rows).sort_values("vif", ascending=False).reset_index(drop=True)


def correlation_table(panel: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Pearson correlation matrix on the common row set."""
    return panel[cols].dropna().corr().round(6)


def max_abs_corr(corr: pd.DataFrame) -> pd.Series:
    """Largest |r| with any OTHER variable, per variable."""
    c = corr.abs().to_numpy(copy=True)
    np.fill_diagonal(c, 0.0)
    return pd.Series(c.max(axis=1), index=corr.index)
