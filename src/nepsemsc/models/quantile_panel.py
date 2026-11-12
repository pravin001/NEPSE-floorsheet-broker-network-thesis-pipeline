"""Quantile panel regressions (v2 Stage 3, plan V2-3.1).

Declared implementation (pre-registration §V2-3):
  * primary: statsmodels ``QuantReg`` on the two-way design with
    ``C(symbol) + C(date)`` dummies (drop-first) absorbed into the design
    matrix; the full 7,116 x ~737 design is feasible in memory, so the
    declared fallback (per-timestamp pooled quantile with within-transform)
    is NOT used.
  * tau in {0.10, 0.25, 0.50, 0.75, 0.90}; 10 grid tests x 5 quantiles.
  * covariance: ``vcov='robust'`` — Koenker's heteroskedasticity-robust
    asymptotic covariance (statsmodels default for QuantReg). This is NOT a
    rank-based or bootstrap CI; the panel-dependence caveat is stated in the
    report and deviation row #18. 95% CI = beta +/- 1.96 * robust SE.
  * convergence: statsmodels' default ``p_tol=1e-6`` is a max|delta beta| test
    across all ~737 parameters and does not converge at tau=.90 within 2,000
    iterations (dummy-coefficient jitter). We use ``p_tol=1e-5`` and
    ``max_iter=1500``; all 50 fits converge, and the tested coefficient moves
    only ~0.2% at tau=.90 vs the stricter unconverged path (robust SE
    unchanged). Declared in deviation #18.
  * checkpointing: one row appended per (test_id, tau) so a 50-fit run
    (~20 min) can resume without refitting.

The design deliberately mirrors the v1 grid: tested feature + the two v1
controls, with entity and time effects absorbed by dummies.
"""
from __future__ import annotations

import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from nepsemsc.utils.io import atomic_write_df

TAUS = (0.10, 0.25, 0.50, 0.75, 0.90)
CONTROLS = ("log_volume_z", "market_ret_loo_z")
_Z95 = 1.959963984540054


def build_quantile_design(panel: pd.DataFrame, feature_col: str,
                          controls: tuple[str, ...] = CONTROLS) -> pd.DataFrame:
    """Feature + controls + drop-first symbol and date dummies + const."""
    parts = [panel[[feature_col, *controls]].astype(float)]
    parts.append(pd.get_dummies(panel["symbol"], prefix="sym",
                                drop_first=True, dtype=float))
    parts.append(pd.get_dummies(panel["date"].astype(str), prefix="d",
                                drop_first=True, dtype=float))
    X = pd.concat(parts, axis=1)
    X.insert(0, "const", 1.0)
    return X


def fit_quantile(panel: pd.DataFrame, outcome: str, feature_col: str,
                 tau: float, controls: tuple[str, ...] = CONTROLS,
                 max_iter: int = 1500, p_tol: float = 1e-5) -> dict:
    """One QuantReg fit; returns the tested coefficient in bp + robust CI."""
    X = build_quantile_design(panel, feature_col, controls)
    y = panel[outcome].to_numpy(dtype=float)
    t0 = time.time()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        # pass the DataFrame so params/bse/pvalues keep column labels
        res = sm.QuantReg(y, X).fit(
            q=tau, vcov="robust", max_iter=max_iter, p_tol=p_tol)
    elapsed = time.time() - t0
    hit_iter_cap = any("Maximum number of iterations" in str(w.message)
                       for w in caught)
    b = float(res.params[feature_col])
    se = float(res.bse[feature_col])
    p = float(res.pvalues[feature_col])
    ci = res.conf_int(alpha=0.05).loc[feature_col]
    return {
        "tau": float(tau),
        "beta": b,
        "beta_bp": 1e4 * b,
        "se_bp": 1e4 * se,
        "p_robust": p,
        "ci_lo_bp": 1e4 * float(ci.iloc[0]),
        "ci_hi_bp": 1e4 * float(ci.iloc[1]),
        "n_obs": int(res.nobs),
        "pseudo_r2": float(res.prsquared),
        "iterations": int(getattr(res, "iterations", -1)),
        "converged": bool(not hit_iter_cap
                          and getattr(res, "iterations", max_iter) < max_iter),
        "fit_seconds": round(elapsed, 2),
    }


def run_quantile_grid(panel: pd.DataFrame, grid, checkpoint_path: str | Path,
                      taus: tuple[float, ...] = TAUS,
                      controls: tuple[str, ...] = CONTROLS) -> pd.DataFrame:
    """Run 10 tests x 5 taus with per-(test,tau) checkpoint/resume."""
    checkpoint_path = Path(checkpoint_path)
    existing = (pd.read_csv(checkpoint_path)
                if checkpoint_path.exists() else pd.DataFrame())
    done = set(zip(existing.get("test_id", []),
                   existing.get("tau", []))) if len(existing) else set()
    rows = existing.to_dict("records") if len(existing) else []
    total = len(grid) * len(taus)
    for hid, feature, outcome, _sign in grid:
        for tau in taus:
            if (hid, float(tau)) in done:
                continue
            rec = fit_quantile(panel, outcome, feature + "_z", tau, controls)
            rec.update({"test_id": hid, "feature": feature,
                        "outcome": outcome, "design": "twoway_dummies",
                        "ci_method": "koenker_robust_asymptotic"})
            rows.append(rec)
            atomic_write_df(pd.DataFrame(rows), checkpoint_path)
            print(f"    {hid} tau={tau:.2f}: bp={rec['beta_bp']:+.3f} "
                  f"p={rec['p_robust']:.4f} ({rec['fit_seconds']:.1f}s, "
                  f"{len(rows)}/{total})", flush=True)
    return pd.DataFrame(rows)


def tail_summary(q: pd.DataFrame, base_bp: dict[str, float] | None = None
                 ) -> pd.DataFrame:
    """Pre-declared tail classification from extreme-tau sign + 95% CI.

    Rule (deviation #18): at tau=.10 and .90 a tail is *significant* iff the
    robust 95% CI excludes 0.  The reference sign is the v1 DK mean effect
    (passed in `base_bp`; falls back to the quantile median if absent).  The
    label uses the reference: same-sign extreme(s) -> LOWER_TAIL / UPPER_TAIL
    / BOTH_TAILS; an extreme that is significant only with the OPPOSITE sign
    -> TAIL_MIXED; no significant extreme -> NONE.  Magnitudes are reported
    alongside, but the label is sign+CI only (no means-only claim).
    """
    base_bp = base_bp or {}
    out = []
    for hid, g in q.groupby("test_id", sort=False):
        g = g.set_index("tau")
        med = float(g.loc[0.50, "beta_bp"]) if 0.50 in g.index else np.nan
        ref_bp = float(base_bp.get(hid, med))
        ref = np.sign(ref_bp) if np.isfinite(ref_bp) and ref_bp != 0 else 0.0
        labels = {}
        for tau in (0.10, 0.90):
            if tau not in g.index:
                labels[tau] = "missing"
                continue
            row = g.loc[tau]
            sig = (row["ci_lo_bp"] > 0) or (row["ci_hi_bp"] < 0)
            same = np.sign(row["beta_bp"]) == ref if ref != 0 else False
            labels[tau] = ("sig_same" if sig and same else
                           "sig_opposite" if sig else "not_sig")
        if labels.get(0.10) == "sig_same" and labels.get(0.90) == "sig_same":
            cls = "BOTH_TAILS"
        elif labels.get(0.90) == "sig_same":
            cls = "UPPER_TAIL"
        elif labels.get(0.10) == "sig_same":
            cls = "LOWER_TAIL"
        elif "sig_opposite" in labels.values():
            cls = "TAIL_MIXED"
        else:
            cls = "NONE"
        row = {"test_id": hid, "median_bp": med,
               "base_bp_v1": float(ref_bp),
               "tail_classification": cls,
               "tau10_label": labels.get(0.10),
               "tau90_label": labels.get(0.90)}
        for tau in TAUS:
            if tau in g.index:
                row[f"bp_tau{int(tau*100)}"] = float(g.loc[tau, "beta_bp"])
                row[f"ci_lo_tau{int(tau*100)}"] = float(g.loc[tau, "ci_lo_bp"])
                row[f"ci_hi_tau{int(tau*100)}"] = float(g.loc[tau, "ci_hi_bp"])
                row[f"p_tau{int(tau*100)}"] = float(g.loc[tau, "p_robust"])
        b10, b50, b90 = (row.get("bp_tau10", np.nan), row.get("bp_tau50", np.nan),
                         row.get("bp_tau90", np.nan))
        if np.isfinite(b10) and np.isfinite(b50) and np.isfinite(b90):
            row["beta_ratio_90_10"] = b90 / b10 if b10 != 0 else np.nan
            if b10 < b50 < b90:
                row["tail_shape"] = "INCREASING"
            elif b10 > b50 > b90:
                row["tail_shape"] = "DECREASING"
            elif b50 > b10 and b50 > b90:
                row["tail_shape"] = "HUMP"
            elif b50 < b10 and b50 < b90:
                row["tail_shape"] = "U_SHAPE"
            else:
                row["tail_shape"] = "MIXED"
        else:
            row["beta_ratio_90_10"] = np.nan
            row["tail_shape"] = "MISSING"
        row["lower_ci_excludes_0"] = bool(row.get("ci_lo_tau10", 0) > 0
                                          or row.get("ci_hi_tau10", 0) < 0)
        row["upper_ci_excludes_0"] = bool(row.get("ci_lo_tau90", 0) > 0
                                          or row.get("ci_hi_tau90", 0) < 0)
        out.append(row)
    return pd.DataFrame(out)
