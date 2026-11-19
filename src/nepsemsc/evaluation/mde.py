"""MDE-based null classification (v2 plan V2-1.3 / v1 DC6/DC10 convention).

MDE_80 = (z_.975 + z_.80) x SE = (1.96 + 0.84) x SE — the SAME formula already
used in the frozen v1 grid (`mde_bp_80pct`); this module never re-estimates.

Classification rule (pre-declared):
    NULL_POWERED      iff |beta| <  MDE_80 / 2
    NULL_UNDERPOWERED iff |beta| >= MDE_80 / 2
Ties (floating equality) resolve to NULL_UNDERPOWERED (the honest side).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MDE_Z = 1.96 + 0.84


def mde_80(se: float) -> float:
    """80%-power MDE at alpha=.05 (same units as `se`)."""
    return MDE_Z * float(se)


def classify_null(beta: float, se: float) -> tuple[float, float, float, str]:
    """(mde80, ratio |beta|/(MDE80/2), |beta|, classification)."""
    m = mde_80(se)
    ratio = float(abs(beta) / (m / 2.0)) if m > 0 else np.nan
    cls = "NULL_POWERED" if abs(beta) < m / 2.0 else "NULL_UNDERPOWERED"
    return m, ratio, abs(beta), cls


def null_table(grid: pd.DataFrame,
               event_summary: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build the null-classification table from the current artifacts ONLY.

    Rows: every BH-failing Stage-1 null test (H1,H2,H3,H5,H9), the Stage-1
    demoted H8, and (if provided) the event-study overall CAR from the current
    v1-method summary. "Current" means the v2.1.0 live rebuild; the values are
    not copied from a frozen v2.0.2 artifact.
    """
    rows = []
    for _, r in grid.iterrows():
        hid = r["test_id"]
        if hid in {"H1", "H2", "H3", "H5", "H8", "H9"}:
            beta_bp = float(r["bp"])
            se_bp = float(r["se"]) * 1e4
            m, ratio, ab, cls = classify_null(beta_bp, se_bp)
            rows.append({
                "test_id": hid, "outcome": r["outcome"],
                "beta_bp": beta_bp, "se_bp": se_bp,
                "mde80_bp": m, "abs_beta_over_half_mde": ratio,
                "classification": cls,
                "basis": "current grid DK(bw=5) SE (rebuilt from raw archives)",
            })
    if event_summary is not None and len(event_summary):
        ev = event_summary.iloc[0]
        # overall CAR row of the frozen summary: car + t (same units)
        car = float(ev.get("mean_car", ev.get("car", np.nan)))
        t = float(ev.get("t_stat", ev.get("t", np.nan)))
        se = abs(car / t) if t not in (0.0, np.nan) and np.isfinite(t) else np.nan
        m, ratio, ab, cls = classify_null(car, se)
        rows.append({
            "test_id": "EVENT_CAR_OVERALL", "outcome": "car[-5,+5]",
            "beta_bp": car * 1e4, "se_bp": se * 1e4,
            "mde80_bp": m * 1e4, "abs_beta_over_half_mde": ratio,
            "classification": cls,
            "basis": "current v1-method event-study summary (rebuild; SE=car/t)",
        })
    return pd.DataFrame(rows)
