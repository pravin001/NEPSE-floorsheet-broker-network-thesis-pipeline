"""EXP-0004e — EVENT STUDY around OOS anomaly events (plan §6, SV3 chain).

Pre-declared operationalization (before this run):
  * events   = OOS test rows flagged is_event (EXP-0004a; 2023-02-16 already
    excluded upstream). Each event (symbol t0) uses NO outcome information
    beyond what a real-time observer at t0− would have;
  * estimation sample = the 60 most recent available sessions of the SAME
    symbol with complete (ret, market_ret_loo), strictly BEFORE t0 − 6
    (never overlapping the event window [t-5, t+5]), excluding sessions the
    symbol itself had flagged is_event in the OOS scores (any fold);
    minimum 40 observations;
  * market return = DC9 leave-one-out equal-weight (tier1 segment) — the
    same market object as the regressions;
  * model choice per plan §6: fit OLS ret ~ market_ret_loo on the
    estimation sample; trigger R² < 0.1 OR |β| > 3 → method
    "market_adjusted" (AR = ret − market_ret_loo); else "market_model"
    (AR = ret − α̂ − β̂·market_ret_loo); if <40 obs → "raw" (AR = ret;
    joint-test caveat, reported separately);
  * event window = the 5 available sessions immediately before and after
    t0 plus t0 itself (symbol's own available-session calendar; truncated
    at data bounds with truncation reported);
  * CAR = Σ AR over the window. Statistics: mean/median CAR overall and by
    method; one-sample t-test with an explicit caveat that overlapping
    event windows and cross-sectional dependence make it an upper bound on
    significance (no cluster adjustment here; register labels accordingly).

Outputs: outputs/tables/event_study_cars.csv · event_study_daily_ars.csv ·
         event_study_summary.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import statsmodels.api as sm

from nepsemsc.utils.io import atomic_write_df
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.tz import utc_iso

EST_LOOKBACK = 60
EST_MIN = 40
HALF_WINDOW = 5
R2_TRIGGER = 0.10
BETA_TRIGGER = 3.0


def fit_market_model(est: pd.DataFrame) -> dict:
    if len(est) < EST_MIN:
        return {"method": "raw", "alpha": float("nan"), "beta": float("nan"),
                "r2": float("nan"), "n_est": len(est)}
    X = sm.add_constant(est["market_ret_loo"].astype(float), has_constant="add")
    m = sm.OLS(est["ret"].astype(float), X).fit()
    return {"method": "market_model", "alpha": float(m.params["const"]),
            "beta": float(m.params["market_ret_loo"]), "r2": float(m.rsquared),
            "n_est": len(est)}


def trigger(st: dict) -> str:
    if st["method"] != "market_model":
        return st["method"]
    if (st["r2"] < R2_TRIGGER) or abs(st["beta"]) > BETA_TRIGGER:
        return "market_adjusted"
    return "market_model"


def main() -> None:
    scores = pd.read_parquet(ROOT / "data/processed/anomaly_scores.parquet")
    scores["date"] = pd.to_datetime(scores["date"]).dt.date
    events = scores.loc[(~scores["is_train"]) & (scores["is_event"]),
                        ["date", "symbol", "fold_id", "anomaly_score"]].copy()
    px = pd.read_parquet(ROOT / "data/processed/daily_outcomes.parquet")
    px["date"] = pd.to_datetime(px["date"]).dt.date

    # flag-map: sessions a symbol had flagged events anywhere OOS
    ev_map = set(zip(events["symbol"], events["date"]))

    by_sym = {sym: g.sort_values("date").reset_index(drop=True)
              for sym, g in px.groupby("symbol", observed=True)}

    rows, ar_rows = [], []
    n_trunc = 0
    for (dt0, sym) in zip(events["date"], events["symbol"]):
        g = by_sym.get(sym)
        if g is None:
            continue
        dates = g["date"].to_numpy()
        pos0 = int(np.searchsorted(dates, dt0))
        if pos0 >= len(dates) or dates[pos0] != dt0:
            continue  # event session absent from outcome calendar (tier1 scope)

        # ---- estimation sample: 60 non-event sessions strictly before window start
        est_mask = []
        i = pos0 - 1 - HALF_WINDOW
        while i >= 0 and len(est_mask) < EST_LOOKBACK:
            d = dates[i]
            if (sym, d) in ev_map:
                i -= 1
                continue
            est_mask.append(i)
            i -= 1
        est_idx = sorted(est_mask)
        est = g.iloc[est_idx][["ret", "market_ret_loo"]].dropna()
        st = fit_market_model(est)
        method = trigger(st)

        # ---- event window: positions pos0-HW .. pos0+HW (clipped)
        lo, hi = pos0 - HALF_WINDOW, pos0 + HALF_WINDOW
        if lo < 0 or hi >= len(dates):
            n_trunc += 1
        lo, hi = max(lo, 0), min(hi, len(dates) - 1)
        win = g.iloc[lo:hi + 1]
        ret = win["ret"].to_numpy(float)
        mkt = win["market_ret_loo"].to_numpy(float)
        if method == "market_model":
            ar = ret - (st["alpha"] + st["beta"] * mkt)
        elif method == "market_adjusted":
            ar = ret - mkt
        else:
            ar = ret
        car = float(np.nansum(ar))
        fold_lkup = events.loc[(events["date"] == dt0) & (events["symbol"] == sym), "fold_id"]
        rows.append({
            "date": dt0, "symbol": sym,
            "fold_id": int(fold_lkup.iloc[0]),
            "method": method, "alpha_est": st["alpha"], "beta_est": st["beta"],
            "r2_est": st["r2"], "n_est": st["n_est"], "n_window": int(hi - lo + 1),
            "car": car,
        })
        for lag, a in zip(range(lo - pos0, hi - pos0 + 1), ar):
            ar_rows.append({"lag": lag, "method": method, "ar": float(a)})

    cars = pd.DataFrame(rows)
    daily = pd.DataFrame(ar_rows)
    ev01 = cars["car"].reset_index(drop=True)

    from scipy import stats as sps
    t_all = sps.ttest_1samp(ev01.to_numpy(), 0.0)
    summary = cars.groupby("method", observed=True)["car"].agg(
        n="size", mean="mean", median="median", sd="std").reset_index()
    summary["t_p"] = [
        float(sps.ttest_1samp(cars.loc[cars["method"] == m, "car"], 0.0).pvalue)
        for m in summary["method"]]
    ar_path = daily.groupby(["lag", "method"], observed=True)["ar"].agg(
        ["mean", "median", "size"]).reset_index()

    atomic_write_df(cars, ROOT / "outputs/tables/event_study_cars.csv", index=False)
    atomic_write_df(ar_path, ROOT / "outputs/tables/event_study_daily_ars.csv", index=False)
    atomic_write_df(summary, ROOT / "outputs/tables/event_study_summary.csv", index=False)
    print(f"events processed: {len(cars):,} | truncated windows: {n_trunc}")
    print(summary.to_string(index=False))
    print(f"ALL-events CAR: mean {ev01.mean():+.5f} | t {t_all.statistic:+.2f} "
          f"| p {t_all.pvalue:.4f} | n={len(ev01)} [REAL] "
          f"(overlapping-window caveat: upper bound on significance)")

    prov.record({
        "ts_utc": utc_iso(),
        "artifact": "outputs/tables/event_study_cars.csv",
        "kind": "event_study_exp0004e",
        "source_path": "anomaly_scores.parquet (EXP-0004a) + daily_outcomes.parquet",
        "source_url": "derived", "sha256": "", "bytes": 0,
        "rows_sampled": len(cars), "rows_total": len(cars),
        "licence": "derived",
        "evidence": f"events={len(cars)}; mean_car={ev01.mean():+.5f}; "
                    f"t={t_all.statistic:+.2f} p={t_all.pvalue:.4f}; "
                    f"methods={summary.set_index('method')['n'].to_dict()}",
    })
    print("EVENT_STUDY_DONE")


if __name__ == "__main__":
    main()
