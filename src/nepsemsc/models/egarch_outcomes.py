"""EGARCH-standardized outcomes (v2 Stage 3, plan V2-3.2).

Model per (fold, symbol): EGARCH(1,1), mean='Constant', vol='EGARCH',
p=q=1, dist='normal', fit on the TRAIN-fold daily returns of that symbol ONLY
(>=60 non-null returns required; excluded symbols are counted). In arch 8.0
this declared call corresponds to `o=0` (symmetric EGARCH: parameters
mu/omega/alpha[1]/beta[1]); asymmetry would require `o=1`, which was not
pre-declared and is therefore NOT added.

OOS rows get z_{t+1} = (r_{t+1} - mu) / sigma_{t+1}, where the conditional
variance recursion is driven forward from the last TRAIN observation using the
TRAIN-estimated parameters and the symbol's observed returns. No test-fold
return enters the parameter fit; every sigma uses only information available
before the return it standardizes. Returns are scaled by 100 for optimizer
stability; the standardization z is scale-invariant.

Outcomes produced on the OOS panel:
  * z_fwd1     = z_{t+1}          (signed standardized forward return)
  * abs_z_fwd1 = |z_{t+1}|        (standardized forward absolute return)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

try:  # dependency installed in Stage 3 (SE-spec test run first)
    from arch import arch_model
except ImportError as exc:  # pragma: no cover
    raise ImportError("Stage 3 requires `arch` (installed in nepse-msc)") from exc

MIN_TRAIN_OBS = 60
_RETURN_SCALE = 100.0
_E_ABS_Z = float(np.sqrt(2.0 / np.pi))
# Numerical validity bound (deviation #17): under a standard-normal innovation
# |z| > 20 has probability ~1e-89; such a draw is a variance-recursion
# numerical artifact, not an economic observation. Only the two degenerate
# fold-0 fits hit it (5 rows); the rest of the panel has p99 |z| = 3.30.
Z_NUMERIC_MAX = 20.0


def fit_egarch(train_ret: np.ndarray):
    """Fit EGARCH(1,1) on one symbol's TRAIN returns (scaled x100)."""
    y = np.asarray(train_ret, dtype=float) * _RETURN_SCALE
    am = arch_model(y, mean="Constant", vol="EGARCH", p=1, q=1,
                    dist="normal", rescale=False)
    res = am.fit(disp="off", show_warning=False)
    params = res.params
    return res, {
        "mu": float(params["mu"]),
        "omega": float(params["omega"]),
        "alpha": float(params["alpha[1]"]),
        # arch's EGARCH(o=0) — the declared p=1,q=1 call — has no asymmetry
        # term; o=1 would add gamma[1] but was NOT pre-declared.
        "gamma": float(params["gamma[1]"]) if "gamma[1]" in params.index else 0.0,
        "beta": float(params["beta[1]"]),
    }


def filter_forward(res, params: dict, forward_ret: np.ndarray,
                   return_info: bool = False):
    """One-step-ahead sigma for `forward_ret`, starting at the last train obs.

    Returns sigma in RETURN units (the x100 scaling is removed). The recursion
    is validated against `res.conditional_volatility` inside
    `validate_recursion` on the train sample.

    Numerical guard (deviation #17): a fitted EGARCH with negative alpha and
    beta near 1 can drive log-variance to -inf after a large shock, so sigma
    underflows to exactly 0. The model then implies a degenerate (zero-variance)
    forward distribution and z is undefined; every later draw is contaminated
    through z in the recursion. We therefore return NaN for the failure point
    and ALL subsequent points rather than emitting inf / silently propagating
    NaN. `build_egarch_outcomes` counts these rows and flags the fit.
    """
    sigma_last = float(res.conditional_volatility[-1])
    if not np.isfinite(sigma_last) or sigma_last <= 0:
        raise ValueError("non-finite terminal conditional volatility")
    z_last = float(res.resid[-1]) / sigma_last
    log_s2 = float(np.log(sigma_last ** 2))
    n = len(forward_ret)
    sig = np.full(n, np.nan, dtype=float)
    stop_reason = None
    stop_index = None
    for i, r in enumerate(np.asarray(forward_ret, dtype=float)):
        log_s2 = (params["omega"]
                  + params["alpha"] * (abs(z_last) - _E_ABS_Z)
                  + params["gamma"] * z_last
                  + params["beta"] * log_s2)
        if not np.isfinite(log_s2):
            stop_reason, stop_index = "log_variance_nonfinite", i
            break
        sigma = float(np.exp(0.5 * log_s2))
        if not np.isfinite(sigma) or sigma <= 0.0:
            stop_reason, stop_index = "sigma_underflow", i
            break
        sig[i] = sigma / _RETURN_SCALE
        z = (r * _RETURN_SCALE - params["mu"]) / sigma
        if not np.isfinite(z):
            sig[i] = np.nan
            stop_reason, stop_index = "z_nonfinite", i
            break
        if abs(z) > Z_NUMERIC_MAX:
            sig[i] = np.nan
            stop_reason, stop_index = "extreme_z", i
            break
        z_last = z
    if return_info:
        return sig, {"stop_reason": stop_reason, "stop_index": stop_index}
    return sig


def validate_recursion(res, params: dict, train_ret: np.ndarray,
                       tol: float = 1e-8) -> float:
    """Max relative error of the manual recursion vs arch's train sigma path."""
    y = np.asarray(train_ret, dtype=float) * _RETURN_SCALE
    sig = np.asarray(res.conditional_volatility, dtype=float)
    z = np.asarray(res.resid, dtype=float) / sig
    log_s2 = float(np.log(sig[0] ** 2))
    worst = 0.0
    for t in range(1, len(y)):
        log_s2 = (params["omega"]
                  + params["alpha"] * (abs(z[t - 1]) - _E_ABS_Z)
                  + params["gamma"] * z[t - 1]
                  + params["beta"] * log_s2)
        sig_hat = float(np.exp(0.5 * log_s2))
        worst = max(worst, abs(sig_hat - sig[t]) / max(abs(sig[t]), 1e-30))
    if worst > tol:
        raise ValueError(f"EGARCH recursion mismatch: rel {worst:.2e}")
    return worst


def build_egarch_outcomes(scores: pd.DataFrame,
                          outcomes: pd.DataFrame,
                          min_train: int = MIN_TRAIN_OBS
                          ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (oos_z, fit_log).

    oos_z: date, symbol, fold_id, z_fwd1, abs_z_fwd1 for OOS rows only.
    fit_log: one row per (fold_id, symbol) with n_train, converged, recursion
             max rel error, and exclusion reason (if any).
    """
    sc = scores.copy()
    out = outcomes.copy()
    sc["date"] = pd.to_datetime(sc["date"]).dt.date
    out["date"] = pd.to_datetime(out["date"]).dt.date
    out = out[["date", "symbol", "ret"]].sort_values(["symbol", "date"])

    # full symbol series (all sessions with a close/outcome row), plus the
    # next-session date so z_{t+1} can be mapped to the OOS row at t
    series = out.copy()
    series["next_date"] = series.groupby("symbol", observed=True)["date"].shift(-1)
    ret_by_sym = {s: g for s, g in series.groupby("symbol", observed=True)}

    z_rows = []
    log_rows = []
    for fold_id, fold in sc.groupby("fold_id", observed=True):
        for sym, sg in fold.groupby("symbol", observed=True):
            s = ret_by_sym.get(sym)
            if s is None:
                log_rows.append({"fold_id": fold_id, "symbol": sym,
                                 "n_train": 0, "converged": False,
                                 "recursion_max_rel": np.nan,
                                 "status": "no_series", "n_oos": 0,
                                 "n_usable_oos": 0, "n_forward_sigma_invalid": 0, "n_oos_excluded": 0, "stop_reason": None,
                                 "first_bad_sigma_date": pd.NaT,
                                 "flag_degenerate": True})
                continue
            train_dates = set(sg.loc[sg["is_train"], "date"])
            train = s[s["date"].isin(train_dates)]
            train_ret = train["ret"].dropna().to_numpy(dtype=float)
            if len(train_ret) < min_train:
                log_rows.append({"fold_id": fold_id, "symbol": sym,
                                 "n_train": len(train_ret), "converged": False,
                                 "recursion_max_rel": np.nan,
                                 "status": "fewer_than_min_train", "n_oos": 0,
                                 "n_usable_oos": 0, "n_forward_sigma_invalid": 0, "n_oos_excluded": 0, "stop_reason": None,
                                 "first_bad_sigma_date": pd.NaT,
                                 "flag_degenerate": True})
                continue
            try:
                res, params = fit_egarch(train_ret)
                conv = int(getattr(res, "convergence_flag", 0)) == 0
                if not np.isfinite(list(params.values())).all():
                    raise ValueError("non-finite EGARCH parameters")
                rec = validate_recursion(res, params, train_ret)
            except Exception as exc:  # noqa: BLE001 — counted, never silent
                log_rows.append({"fold_id": fold_id, "symbol": sym,
                                 "n_train": len(train_ret), "converged": False,
                                 "recursion_max_rel": np.nan,
                                 "status": f"fit_failed:{type(exc).__name__}",
                                 "n_oos": 0, "n_usable_oos": 0,
                                 "n_sigma_underflow": 0,
                                 "first_bad_sigma_date": pd.NaT,
                                 "flag_degenerate": True})
                continue
            last_train_date = train.loc[train["ret"].notna(), "date"].max()
            # forward path only needs the OOS window plus ONE session after it
            # (the last OOS row's z uses next_date); never the whole sample.
            oos_dates = sg.loc[~sg["is_train"], "date"]
            max_oos_date = oos_dates.max()
            nxt = s.loc[s["date"] > max_oos_date, "date"].min()
            cutoff = nxt if pd.notna(nxt) else max_oos_date
            fwd = s[(s["date"] > last_train_date) & (s["date"] <= cutoff)
                    & s["ret"].notna()]
            if len(fwd) == 0:
                log_rows.append({"fold_id": fold_id, "symbol": sym,
                                 "n_train": len(train_ret), "converged": conv,
                                 "recursion_max_rel": rec,
                                 "status": "no_forward_returns", "n_oos": 0,
                                 "n_usable_oos": 0, "n_forward_sigma_invalid": 0, "n_oos_excluded": 0, "stop_reason": None,
                                 "first_bad_sigma_date": pd.NaT,
                                 "flag_degenerate": True})
                continue
            sig, finfo = filter_forward(res, params,
                                        fwd["ret"].to_numpy(dtype=float),
                                        return_info=True)
            finite_sig = np.isfinite(sig) & (sig > 0)
            n_bad_sigma = int((~finite_sig).sum())
            first_bad_date = (fwd.loc[~finite_sig, "date"].min()
                              if n_bad_sigma else pd.NaT)
            with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
                z = (fwd["ret"].to_numpy(dtype=float) * _RETURN_SCALE
                     - params["mu"]) / (sig * _RETURN_SCALE)
            z[~finite_sig] = np.nan
            z[~np.isfinite(z)] = np.nan
            zmap = pd.DataFrame({"date": fwd["date"].to_numpy(),
                                 "z": z, "sigma": sig})
            oos = sg.loc[~sg["is_train"], ["date", "symbol"]].copy()
            oos = oos.merge(s, on=["date", "symbol"], how="left") \
                     .merge(zmap, left_on="next_date", right_on="date",
                            how="left", suffixes=("", "_z"))
            # a row is usable only if it has its own (non-null) current return
            # and a FINITE next-session z; otherwise the recursion has no
            # finite z_t anchor (underflow, non-convergence or missing return)
            z_num = pd.to_numeric(oos["z"], errors="coerce").to_numpy(dtype=float)
            usable = oos["ret"].notna().to_numpy() & np.isfinite(z_num)
            z_rows.append(pd.DataFrame({
                "date": oos.loc[usable, "date"].to_numpy(),
                "symbol": sym,
                "fold_id": fold_id,
                "z_fwd1": z_num[usable],
                "sigma_fwd1": pd.to_numeric(oos["sigma"], errors="coerce")
                                .to_numpy(dtype=float)[usable],
            }))
            status = "ok" if n_bad_sigma == 0 else "ok_with_sigma_underflow"
            if not usable.any():
                status = "no_usable_oos"
            log_rows.append({"fold_id": fold_id, "symbol": sym,
                             "n_train": len(train_ret), "converged": conv,
                             "recursion_max_rel": rec,
                             "status": status,
                             "n_oos": int(len(oos)),
                             "n_usable_oos": int(usable.sum()),
                             "n_forward_sigma_invalid": n_bad_sigma,
                             "n_oos_excluded": int(len(oos) - usable.sum()),
                             "first_bad_sigma_date": first_bad_date,
                             "stop_reason": finfo["stop_reason"],
                             "flag_degenerate": bool(n_bad_sigma > 0 or not conv)})

    oos_z = pd.concat(z_rows, ignore_index=True) if z_rows else pd.DataFrame(
        columns=["date", "symbol", "fold_id", "z_fwd1"])
    oos_z["abs_z_fwd1"] = oos_z["z_fwd1"].abs()
    fit_log = pd.DataFrame(log_rows)
    return oos_z, fit_log
