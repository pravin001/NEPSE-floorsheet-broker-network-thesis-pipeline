"""Event-study upgrade: BMP + rank tests on the frozen v1 windows (V2-4).

NO WINDOW RE-ESTIMATION.  For every one of the 686 v1 events the module
reconstructs the event-window abnormal returns from the stored v1 parameters
(`alpha_est`, `beta_est`, `method`) and the same `daily_outcomes` series, and
verifies that the reconstructed CAR equals the stored `car` (hard gate).  The
estimation sample is selected with the identical v1 rule (60 most recent
non-event sessions strictly before t0-5, minimum 40) solely to recover the
residual scale needed for standardisation — the market-model coefficients are
NOT re-fitted.

Statistics:
  * BMP (Boehmer-Musumeci-Poulsen 1991): standardise each event CAR by its
    prediction-error variance (market-model estimation variance plus the
    out-of-sample forecast correction), then use the cross-sectional t of the
    standardized CARs.  Event-window overlap and cross-sectional dependence
    remain, so the p-value is an upper bound on significance (caveat kept).
  * Corrado-style rank test: rank each event-window AR among the estimation
    window + event window ARs (average ties), sum the event-window ranks, and
    use the cross-sectional z of the centred rank sums.
  * Market-adjusted variant: AR = ret - market_ret_loo on the SAME windows and
    the same estimation samples, with market-adjusted residual scale.

The 16 v1 market-adjusted (illiquid-trigger) events stay in the 686-event
headline sample but their separate result is reported in the appendix block.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sps
from scipy.stats import rankdata

HALF_WINDOW = 5
EST_LOOKBACK = 60
EST_MIN = 40


def _estimation_indices(dates: np.ndarray, pos0: int,
                        ev_map: set[tuple[str, object]],
                        sym: str) -> list[int]:
    out: list[int] = []
    i = pos0 - 1 - HALF_WINDOW
    while i >= 0 and len(out) < EST_LOOKBACK:
        d = dates[i]
        if (sym, d) in ev_map:
            i -= 1
            continue
        out.append(i)
        i -= 1
    return sorted(out)


def reconstruct(cars: pd.DataFrame, outcomes: pd.DataFrame,
                scores: pd.DataFrame) -> tuple[pd.DataFrame, dict, list[dict]]:
    """Rebuild AR paths from stored v1 parameters; verify CAR."""
    cars = cars.copy()
    cars["date"] = pd.to_datetime(cars["date"]).dt.date
    ev = scores.loc[(~scores["is_train"]) & (scores["is_event"]),
                    ["date", "symbol"]].copy()
    ev["date"] = pd.to_datetime(ev["date"]).dt.date
    ev_map = set(zip(ev["symbol"], ev["date"]))

    px = outcomes.copy()
    px["date"] = pd.to_datetime(px["date"]).dt.date
    by_sym = {s: g.sort_values("date").reset_index(drop=True)
              for s, g in px.groupby("symbol", observed=True)}

    rows, payload = [], {}
    for k, r in cars.reset_index(drop=True).iterrows():
        g = by_sym[r["symbol"]]
        dates = g["date"].to_numpy()
        pos0 = int(np.searchsorted(dates, r["date"]))
        if pos0 >= len(dates) or dates[pos0] != r["date"]:
            raise ValueError(f"event session missing for {r['symbol']} "
                             f"{r['date']}")
        est_idx = _estimation_indices(dates, pos0, ev_map, r["symbol"])
        est = g.iloc[est_idx][["ret", "market_ret_loo"]].dropna()
        if len(est) != int(r["n_est"]):
            raise ValueError(f"estimation sample mismatch {r['symbol']} "
                             f"{r['date']}: {len(est)} vs {r['n_est']}")

        lo, hi = pos0 - HALF_WINDOW, pos0 + HALF_WINDOW
        lo, hi = max(lo, 0), min(hi, len(dates) - 1)
        win = g.iloc[lo:hi + 1]
        ret = win["ret"].to_numpy(float)
        mkt = win["market_ret_loo"].to_numpy(float)
        est_ret = est["ret"].to_numpy(float)
        est_mkt = est["market_ret_loo"].to_numpy(float)

        if r["method"] == "market_model":
            ar_est = est_ret - (r["alpha_est"] + r["beta_est"] * est_mkt)
            ar = ret - (r["alpha_est"] + r["beta_est"] * mkt)
            df = max(len(est) - 2, 1)
            mean_mkt = float(est_mkt.mean())
            sxx = float(np.sum((est_mkt - mean_mkt) ** 2))
            corr = (len(ar) + len(ar) ** 2 / len(est)
                    + float(np.sum((mkt - mean_mkt) ** 2)) / max(sxx, 1e-30))
        elif r["method"] == "market_adjusted":
            ar_est = est_ret - est_mkt
            ar = ret - mkt
            df = max(len(est) - 1, 1)
            corr = len(ar) + len(ar) ** 2 / len(est)
        else:
            ar_est = est_ret
            ar = ret
            df = max(len(est) - 1, 1)
            corr = len(ar) + len(ar) ** 2 / len(est)

        sigma2 = float(np.nansum(ar_est ** 2) / df)
        car_recon = float(np.nansum(ar))
        complete = bool(np.isfinite(ar).all() and np.isfinite(ar_est).all())
        if complete:
            combined = np.concatenate([ar_est, ar])
            ranks = rankdata(combined, method="average")
            rank_sum = float(ranks[len(ar_est):].sum())
            m_total = len(combined)
        else:
            rank_sum = np.nan
            m_total = len(ar_est) + len(ar)
        var_car = sigma2 * corr
        scar = car_recon / np.sqrt(var_car) if var_car > 0 else np.nan

        rows.append({**r.to_dict(), "event_idx": k,
                     "lag_lo": int(lo - pos0), "lag_hi": int(hi - pos0),
                     "car_recon": car_recon,
                     "car_abs_diff": abs(car_recon - float(r["car"])),
                     "sigma2_est": sigma2, "var_car": var_car,
                     "scar": scar, "rank_sum": rank_sum,
                     "m_total": m_total, "ar_complete": complete,
                     "illiquid_appendix": r["method"] == "market_adjusted"})
        payload[k] = {"est_ret": est_ret, "est_mkt": est_mkt,
                      "win_ret": ret, "win_mkt": mkt,
                      "n_est": len(est), "complete": complete}
    return (pd.DataFrame(rows), payload,
            pd.DataFrame(_ar_long(rows, payload)))


def _ar_long(rows: list[dict], payload: dict) -> list[dict]:
    out = []
    for k, row in enumerate(rows):
        p = payload[k]
        if row["method"] == "market_model":
            ar = p["win_ret"] - (row["alpha_est"]
                                 + row["beta_est"] * p["win_mkt"])
        elif row["method"] == "market_adjusted":
            ar = p["win_ret"] - p["win_mkt"]
        else:
            ar = p["win_ret"]
        for lag, a in zip(range(row["lag_lo"], row["lag_hi"] + 1), ar):
            out.append({"event_idx": k, "lag": lag, "ar": float(a)})
    return out


def bmp_test(scar: np.ndarray) -> dict:
    s = np.asarray(scar, float)
    s = s[np.isfinite(s)]
    n = len(s)
    mean = float(s.mean())
    sd = float(s.std(ddof=1))
    t = mean / (sd / np.sqrt(n))
    return {"n": n, "mean": mean, "sd": sd, "t": float(t),
            "p": float(2 * sps.t.sf(abs(t), n - 1)),
            "z": float(mean * np.sqrt(n)),
            "p_z": float(2 * sps.norm.sf(abs(mean * np.sqrt(n))))}


def corrado_rank(rank_sum: np.ndarray, n_est: np.ndarray,
                 n_window: np.ndarray) -> dict:
    """Cross-sectional Corrado-style rank-sum test (average ties)."""
    rs = np.asarray(rank_sum, float)
    exp = np.asarray(n_window, float) * (np.asarray(n_est, float)
                                         + np.asarray(n_window, float) + 1) / 2
    ok = np.isfinite(rs)
    centered = rs[ok] - exp[ok]
    n = len(centered)
    z = float(centered.mean() / (centered.std(ddof=1) / np.sqrt(n)))
    return {"n": n, "mean_centered": float(centered.mean()),
            "sd_centered": float(centered.std(ddof=1)), "z": z,
            "p": float(2 * sps.norm.sf(abs(z)))}


def clustered_inference(per_event: pd.DataFrame) -> pd.DataFrame:
    """Date-clustered descriptive inference (events are not independent).

    The headline tests treat events as independent, but 686 events fall on
    393 dates and 68.2% of events share their date with another event.  This
    table aggregates each statistic to the date level (mean CAR, mean centred
    rank sum) and runs a one-sample t across dates.  Dates themselves remain
    dependent through overlapping symbols and event windows, so the p-values
    are still upper bounds, not exact tests.
    """
    df = per_event.copy()
    exp = df["n_window"] * (df["n_est"] + df["n_window"] + 1) / 2
    specs = (
        ("mean_car", df["car"]),
        ("corrado_rank_centered", df["rank_sum"] - exp),
        ("corrado_rank_centered_ma", df["rank_sum_ma"] - exp),
    )
    rows = []
    for label, values in specs:
        d = pd.DataFrame({"date": df["date"], "v": values}).dropna()
        g = d.groupby("date", sort=True)["v"].mean()
        n = len(g)
        mean = float(g.mean())
        se = float(g.std(ddof=1) / np.sqrt(n))
        t = mean / se if se > 0 else np.nan
        p = float(2 * sps.t.sf(abs(t), n - 1)) if np.isfinite(t) else np.nan
        rows.append({
            "statistic": label, "n_dates": n, "mean": mean, "se": se,
            "t": t, "p_value": p,
            "note": "date-clustered descriptive; still an upper bound",
        })
    return pd.DataFrame(rows)


def market_adjusted_variant(payload: dict) -> pd.DataFrame:
    """Uniform market-adjusted ARs on the same estimation/event windows."""
    rows = []
    for k, p in payload.items():
        ar_est = p["est_ret"] - p["est_mkt"]
        ar = p["win_ret"] - p["win_mkt"]
        df = max(p["n_est"] - 1, 1)
        sigma2 = float(np.nansum(ar_est ** 2) / df)
        car = float(np.nansum(ar))
        var = sigma2 * (len(ar) + len(ar) ** 2 / p["n_est"])
        scar = car / np.sqrt(var) if var > 0 else np.nan
        if p["complete"]:
            ranks = rankdata(np.concatenate([ar_est, ar]), method="average")
            rank_sum = float(ranks[len(ar_est):].sum())
        else:
            rank_sum = np.nan
        rows.append({"event_idx": k, "car_ma": car, "scar_ma": scar,
                     "rank_sum_ma": rank_sum, "n_est": p["n_est"],
                     "n_window": len(ar)})
    return pd.DataFrame(rows)


def upgrade(cars: pd.DataFrame, outcomes: pd.DataFrame,
            scores: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame,
                                           pd.DataFrame, dict]:
    """Return (summary, per_event, ar_long, gate)."""
    aug, payload, ar_long = reconstruct(cars, outcomes, scores)
    gate = {"n_events": len(aug),
            "max_car_abs_diff": float(aug["car_abs_diff"].max()),
            "n_incomplete_ar": int((~aug["ar_complete"]).sum())}

    variant = market_adjusted_variant(payload).drop(
        columns=["n_est", "n_window"])
    per_event = aug.merge(variant, on="event_idx", how="left")

    def _rows(sample: str, model: str, car: np.ndarray,
              scar: np.ndarray, rank_sum: np.ndarray,
              n_est: np.ndarray, n_win: np.ndarray,
              note: str = "") -> list[dict]:
        c = np.asarray(car, float)
        c = c[np.isfinite(c)]
        mt = sps.ttest_1samp(c, 0.0) if len(c) > 1 else None
        bmp = bmp_test(scar)
        cr = corrado_rank(rank_sum, n_est, n_win)
        base = {"sample": sample, "n_events": int(len(c)), "model": model,
                "mean_car": float(c.mean()), "sd_car": float(c.std(ddof=1)),
                "note": note}
        return [
            {**base, "test": "mean_car_t", "statistic": float(mt.statistic),
             "p_value": float(mt.pvalue)},
            {**base, "test": "bmp_car_t", "statistic": bmp["t"],
             "p_value": bmp["p"]},
            {**base, "test": "bmp_car_z", "statistic": bmp["z"],
             "p_value": bmp["p_z"]},
            {**base, "test": "corrado_rank_car_z", "statistic": cr["z"],
             "p_value": cr["p"]},
        ]

    summary = []
    summary += _rows("all_686", "v1_method", per_event["car"],
                     per_event["scar"], per_event["rank_sum"],
                     per_event["n_est"], per_event["n_window"],
                     "headline sample; overlapping windows caveat")
    summary += _rows("all_686", "market_adjusted", per_event["car_ma"],
                     per_event["scar_ma"], per_event["rank_sum_ma"],
                     per_event["n_est"], per_event["n_window"],
                     "uniform market-adjusted variant on same windows")
    app = per_event.loc[per_event["illiquid_appendix"]]
    summary += _rows("illiquid_16_appendix", "v1_method", app["car"],
                     app["scar"], app["rank_sum"], app["n_est"],
                     app["n_window"], "appendix only; not a headline quote")
    return pd.DataFrame(summary), per_event, ar_long, gate
