"""PHASE 5 — ROBUSTNESS BATTERY (plan §7 pre-declarations, EXP-0005a–g).

Sections (each in its own function; sequential execution; one prov row):
  a) leave-one-stock-out stability — drop each symbol from the OOS panel and
     re-fit the DK(bw=5) single-feature design for ALL 10 grid tests;
  b) alternative horizons t+2/t+3/t+5 — fwd-k outcome = close[t+k]/close[t]-1
     on the symbol's own available-session adjacency (the same object that
     defined fwd1); within-window closes only (no post-window borrowing for
     k >= 2 — conservative, coverage reported); full 10-grid refit + BH
     (family of 10 per horizon);
  c) alternative EoD thresholds (top 1%, top 10%) — same declared SQL as
     EXP-0003a with cutoff fraction f in {0.01, 0.10} on the SAME post-SV7
     row set (2023-02-16 excluded from ordering features); z-scaled with the
     SAME train-fold constants machinery; H7/H8 refit (raw DK p reported —
     threshold sensitivity, not a fresh inference family);
  d) alternative scorers rank-correlation vs IF (SV5): per fold,
     LeakSafeStandardizer duplicated (fit TRAIN rows of the fold universe,
     transform test), then Mahalanobis (cov + eps·I), diagonal z²-sum
     (z-score-sum-of-squares fallback), LocalOutlierFactor(novelty=True,
     n_neighbors=20) and OneClassSVM(rbf, nu=0.05, gamma='scale'); score
     = higher-must-mean-more-anomalous (sign convention stated); Spearman ρ
     vs the IF anomaly_score on OOS test rows per fold + pooled;
  e) drop-bubble-period re-run — grid refit on normal-era OOS rows only
     (2023+; fold-structure & constants unchanged); BH (family of 10 in
     subset) + headline survival;
  f) 5-stock EXTERNAL cross-section replication — fresh DC1 scoring with
     n_top=5 and EXCLUSION of the same fold's base top-10 before the
     ranking head (ranks 11–15 of the same train-only ranking), fresh
     IF(200) fits, fresh constants; full 10-grid + BH + survival;
  g) sequential fold-mode variant (D7) — same params, mode='sequential'
     (middle-segment coverage only, declared); descriptive: event shares,
     date spans, Spearman vs anchored scores on overlapping (date, symbol)
     test rows;
  z) master headline-survival table across variants →
     outputs/tables/robustness_headline_survival.csv  [STATUS REPORT input].

All numbers computed live [REAL]; no thresholds re-declared here beyond the
references above (plan §7 text is the pre-declaration).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np
import pandas as pd

from run_panel_regressions import GRID, BH_Q, _benjamini_hochberg
from nepsemsc.ml.panel_regression import run_panel
from nepsemsc.ml.panel_data import (build_oos_panel, standardize_test,
                                    train_fold_stats, Z_SOURCE_COLS)
from nepsemsc.ml.anomaly_scoring import (walk_forward_anomaly_scores_dc1,
                                         select_fold_universe,
                                         FEATURES_DEFAULT)
from nepsemsc.ml.standardize import LeakSafeStandardizer
from nepsemsc.ml.walk_forward import purged_folds
from nepsemsc.utils.io import atomic_write_df
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.tz import utc_iso

T0 = time.time()
HEADS = ["H4", "H6", "H7", "H8", "H10"]
DEFECT = "2023-02-16"
EPS = 1e-12

EOD_SQL = """
WITH fs AS (
    SELECT date, symbol, contract_no, volume
    FROM floorsheet_dedup
    WHERE volume IS NOT NULL AND volume > 0
      AND price > 0
      AND COALESCE(buyer_broker_id, '') <> ''
      AND COALESCE(seller_broker_id, '') <> ''
      AND COALESCE(symbol, '') <> ''
),
ranked AS (
    SELECT date, symbol, volume,
           ROW_NUMBER() OVER (PARTITION BY date, symbol
                              ORDER BY contract_no DESC) AS rn_desc,
           COUNT(*) OVER (PARTITION BY date, symbol) AS n_t
    FROM fs
    WHERE CAST(date AS VARCHAR) <> '{DEFECT}'
)
SELECT date, symbol,
       SUM(CASE WHEN rn_desc <= CAST(ceil(0.01 * n_t) AS BIGINT)
                THEN volume ELSE 0 END) / SUM(volume) AS eod_01,
       SUM(CASE WHEN rn_desc <= CAST(ceil(0.10 * n_t) AS BIGINT)
                THEN volume ELSE 0 END) / SUM(volume) AS eod_10
FROM ranked
GROUP BY 1, 2
""".replace("{DEFECT}", DEFECT)


def dk_fit(panel: pd.DataFrame, outcome: str, feat_z: str,
           controls: tuple[str, ...] = ("log_volume_z", "market_ret_loo_z")
           ) -> dict:
    cols = [feat_z, *controls]
    d = panel.dropna(subset=[outcome, *cols])
    res = run_panel(d, outcome, cols, se="driscoll_kraay", bandwidth=5)
    return {"beta": float(res.params[feat_z]),
            "bp": float(1e4 * res.params[feat_z]),
            "se": float(res.std_errors[feat_z]),
            "t": float(res.tstats[feat_z]),
            "p_dk": float(res.pvalues[feat_z]),
            "n": int(len(d))}


def horizon_grid(panel: pd.DataFrame, out_key: dict[str, str]) -> pd.DataFrame:
    rows = []
    for hid, feat, outcome, sign in GRID:
        feat_z = feat + "_z"
        r = dk_fit(panel, out_key[hid], feat_z)
        r.update({"test_id": hid, "feature": feat, "outcome": out_key[hid],
                  "predicted_sign": sign, "n_obs": r.pop("n")})
        rows.append(r)
    gd = pd.DataFrame(rows)
    gd["bh_adj_p"] = _benjamini_hochberg(list(gd["p_dk"]), BH_Q)[1]
    gd["bh_sig_q10"] = gd["bh_adj_p"] <= BH_Q
    gd["sign_agrees"] = [
        np.nan if s == "amb" else ((b > 0) == (s == "pos"))
        for b, s in zip(gd["beta"], gd["predicted_sign"])]
    return gd


def sec_eod_thresholds() -> pd.DataFrame:
    """c) alternative EoD cutoffs 1%/10%; base 5% comes from EXP-0003a."""
    from nepsemsc.data.duckdb_loader import get_conn
    con = get_conn()
    eod = con.execute(EOD_SQL).df()
    con.close()
    eod["date"] = pd.to_datetime(eod["date"]).dt.date
    print(f"  alt-eod SQL rows: {len(eod):,} "
          f"(day count {eod['date'].nunique()}, expectation 937 = 938 - defect)")

    scores = pd.read_parquet(ROOT / "data/processed/anomaly_scores.parquet")
    outcomes = pd.read_parquet(ROOT / "data/processed/daily_outcomes.parquet")
    scores = scores.merge(eod, on=["date", "symbol"], how="left")
    panel, train = build_oos_panel(scores, outcomes)
    st = train_fold_stats(train, cols=Z_SOURCE_COLS + ["eod_01", "eod_10"])
    panel = standardize_test(panel, st)

    rows = []
    for thr, col in (("1%", "eod_01_z"), ("5% (base, EXP-0003a)",
                    "end_of_day_concentration_z"), ("10%", "eod_10_z")):
        for hid, outcome in (("H7", "abs_ret_fwd1"), ("H8", "ret_fwd1")):
            r = dk_fit(panel, outcome, col)
            r.update({"threshold": thr, "test_id": hid, "outcome": outcome,
                      "n_obs": r.pop("n")})
            rows.append(r)
    out = pd.DataFrame(rows)
    return out


def sec_alt_scorers(scores: pd.DataFrame) -> pd.DataFrame:
    """d) SV5 alternative scorers, rank-correlation vs IF on OOS test rows."""
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.svm import OneClassSVM
    from scipy import stats as sps

    feats = FEATURES_DEFAULT
    rows = []
    for fold_id, g in scores.groupby("fold_id", observed=True):
        tr = g.loc[g["is_train"]]
        te = g.loc[~g["is_train"]]
        if len(tr) < 50 or len(te) < 20:
            continue
        scaler = LeakSafeStandardizer(feature_cols=feats, winsor=(0.01, 0.99))
        X_tr = scaler.fit_transform(tr, fold_label=f"fold{fold_id}_alt_train").to_numpy()
        X_te = scaler.transform(te, fold_label=f"fold{fold_id}_alt_test").to_numpy()

        if_score = te["anomaly_score"].to_numpy(float)
        mu = X_tr.mean(axis=0)

        # Mahalanobis (full-rank, eps regularised)
        S = np.cov(X_tr, rowvar=False)
        S = S + np.eye(len(feats)) * EPS * max(1.0, float(np.trace(S)))
        try:
            S_inv = np.linalg.inv(S)
        except np.linalg.LinAlgError:
            S_inv = np.linalg.pinv(S)
        md = np.sqrt(np.maximum(
            ((X_te - mu) @ S_inv * (X_te - mu)).sum(axis=1), 0.0))

        # diagonal Mahalanobis == sum of squared standardized deviations
        # (linear spaces); HIGHER = MORE anomalous — same direction as IF
        varz = X_tr.std(axis=0)
        zsum = (((X_te - mu) ** 2) / (varz ** 2 + EPS)).sum(axis=1)

        lof = LocalOutlierFactor(n_neighbors=20, novelty=True).fit(X_tr)
        lof_s = -lof.score_samples(X_te)

        svm = OneClassSVM(kernel="rbf", nu=0.05, gamma="scale").fit(X_tr)
        svm_s = -svm.decision_function(X_te)

        for name, alt in (("mahalanobis", md), ("diag_z2_sum", zsum),
                          ("lof_novelty", lof_s), ("ocsvm", svm_s)):
            rho, p = sps.spearmanr(alt, if_score)
            rows.append({"fold_id": fold_id, "scorer": name, "n_test": len(te),
                         "spearman_r": float(rho), "p_spearman": float(p)})
    out = pd.DataFrame(rows)
    pooled = out.groupby("scorer", observed=True)["spearman_r"].agg(
        ["mean", "median", "min", "max"]).round(4)
    print("  per-fold alt-scorer rank-corr vs IF (spearman):")
    print(pooled.to_string())
    return out


def sec_loo(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """a) leave-one-stock-out stability across all 10 tests."""
    symbols = sorted(panel["symbol"].astype(str).unique())
    detail, summary = [], []
    for hid, feat, outcome, sign in GRID:
        feat_z = feat + "_z"
        base = dk_fit(panel, outcome, feat_z)
        bs = []
        for sym in symbols:
            r = dk_fit(panel.loc[panel["symbol"] != sym], outcome, feat_z)
            r.update({"test_id": hid, "dropped_symbol": sym})
            detail.append(r)
            bs.append(r["beta"])
        same_sign = sum((b > 0) == (base["beta"] > 0) for b in bs)
        n_p10 = sum(1 for r in detail if r["test_id"] == hid
                    and r["p_dk"] < 0.10)
        summary.append({
            "test_id": hid, "feature": feat, "outcome": outcome,
            "beta_full": base["beta"], "p_full": base["p_dk"],
            "n_symbols": len(symbols), "beta_min": min(bs), "beta_max": max(bs),
            "n_same_sign": same_sign, "n_p_dk_lt_10": n_p10,
            "sign_stable": same_sign == len(symbols),
        })
    return pd.DataFrame(summary), pd.DataFrame(detail)


def sec_drop_bubble(panel: pd.DataFrame) -> pd.DataFrame:
    """e) normal-era rows only (2023+); constants & folds unchanged."""
    year = pd.to_datetime(panel["date"]).dt.year
    sub = panel.loc[year >= 2023].copy()
    gd = horizon_grid(sub, {hid: out for hid, _, out, _ in GRID})
    print(f"  drop-bubble panel rows: {len(sub):,} (dropped "
          f"{len(panel) - len(sub):,} bubble-era rows)")
    return gd


def fwd_k_outcomes(outcomes: pd.DataFrame, ks: tuple[int, ...] = (2, 3, 5)
                   ) -> pd.DataFrame:
    """fwd_k[t] = close[t+k]/close[t] - 1 on the symbol's OWN available-'
    session adjacency (same leading-shift convention as ret_fwd1[t] =
    ret[t+1] in build_outcomes.py); NaN for the last k sessions per symbol
    (within-window closes only — coverage reported in section b)."""
    px = outcomes.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = px.groupby("symbol", observed=True)["close"]
    for k in ks:
        nxt = g.shift(-k)                       # close at t+k within group
        px[f"ret_fwd{k}"] = (nxt / px["close"] - 1.0).to_numpy()
        px[f"abs_ret_fwd{k}"] = px[f"ret_fwd{k}"].abs().to_numpy()
    return px


def load_feature_frame() -> pd.DataFrame:
    """FULL daily features frame — EXACT EXP-0004a input protocol
    (run_anomaly_scoring.py): renames → date-normalize → 2023-02-16 rows
    dropped. Sections f/g RE-SCORE fresh universes against it; the scores
    parquet is NOT valid input there (it persists only base-universe rows)."""
    feat = pd.read_parquet(ROOT / "data/processed/daily_features.parquet")
    feat = feat.rename(columns={"self_loop_volume_ratio": "self_loop_ratio",
                                "reciprocity_volume": "reciprocity"})
    feat["date"] = pd.to_datetime(feat["date"]).dt.date
    n0 = len(feat)
    feat = feat.loc[feat["date"].astype(str) != DEFECT].copy()
    print(f"  feature frame: {n0:,} → {len(feat):,} rows (defect excluded)")
    return feat


def sec_top5(feat: pd.DataFrame, outcomes: pd.DataFrame
             ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """f) external cross-section: ranks 11-15 of the SAME DC1 train-only
    ranking, per fold (excluded = that fold's base top-10)."""
    turnover = outcomes[["symbol", "date", "turnover"]].dropna()
    folds = purged_folds(feat["date"], n_folds=4,
                         purge_gap_sessions=6, mode="anchored")
    base_univ = {f.fold_id: set(select_fold_universe(turnover, f.train_dates,
                                                     n_top=10, min_coverage=0.90))
                 for f in folds}
    uni_labels = []
    for f in folds:
        ext = select_fold_universe(turnover, f.train_dates, n_top=5,
                                   min_coverage=0.90,
                                   excluded=base_univ[f.fold_id])
        uni_labels.append(f"k{f.fold_id}: " + ",".join(ext))
    print("  external top-5 universes:", " | ".join(uni_labels))
    sc, ssum = walk_forward_anomaly_scores_dc1(
        feat, turnover, n_folds=4, purge_gap_sessions=6, n_estimators=200,
        contamination="auto", mode="anchored", n_top=5, min_coverage=0.90,
        event_quantile=0.90,
        per_fold_exclude=lambda f: base_univ[f.fold_id])
    return sc, ssum


def sec_sequential(feat: pd.DataFrame, outcomes: pd.DataFrame):
    turnover = outcomes[["symbol", "date", "turnover"]].dropna()
    sc, ssum = walk_forward_anomaly_scores_dc1(
        feat, turnover, n_folds=4, purge_gap_sessions=6, n_estimators=200,
        contamination="auto", mode="sequential", n_top=10, min_coverage=0.90,
        event_quantile=0.90)
    return sc, ssum


def spearman_overlap(base_scores: pd.DataFrame, oos_other: pd.DataFrame,
                     label: str) -> float:
    from scipy import stats as sps
    b = base_scores.loc[~base_scores["is_train"],
                        ["date", "symbol", "anomaly_score"]]
    o = oos_other.loc[~oos_other["is_train"],
                      ["date", "symbol", "anomaly_score"]]
    m = b.merge(o, on=["date", "symbol"], suffixes=("_anch", f"_{label}"))
    rho, p = sps.spearmanr(m[f"anomaly_score_{label}"].to_numpy(float),
                           m["anomaly_score_anch"].to_numpy(float))
    print(f"  {label} vs anchored (overlapping OOS rows n={len(m):,}): "
          f"spearman r={float(rho):+.4f} p={float(p):.4f} [REAL]")
    return float(rho)


def main() -> None:
    scores = pd.read_parquet(ROOT / "data/processed/anomaly_scores.parquet")
    outcomes = pd.read_parquet(ROOT / "data/processed/daily_outcomes.parquet")

    master: list[dict] = []

    # ---------- z0) BASE variant rows (numbers of record, EXP-0004b/c) ------
    base_grid = pd.read_csv(ROOT / "outputs/tables/hypothesis_grid_results.csv")
    for h in HEADS:
        row = base_grid.loc[base_grid.test_id == h].iloc[0]
        master.append({
            "variant": "base t+1 (EXP-0004b)", "test_id": h,
            "bp": float(row["bp"]), "p_dk": float(row["p_dk"]),
            "bh_pass": bool(row["bh_sig_q10"]),
            "sign_agrees": (np.nan if pd.isna(row["sign_agrees"])
                            else bool(row["sign_agrees"]))})

    # ---------- b) alt horizons (needs fwd_k merged before panel build) ----
    print("[b] alternative horizons t+2/t+3/t+5")
    out_fk = fwd_k_outcomes(outcomes)
    out_keys = ("ret_fwd2", "abs_ret_fwd2", "ret_fwd3", "abs_ret_fwd3",
                "ret_fwd5", "abs_ret_fwd5")
    p, tr = build_oos_panel(scores, out_fk, extra_outcome_cols=out_keys)
    p = standardize_test(p, train_fold_stats(tr))
    for k in (2, 3, 5):
        cov = int(p[f"abs_ret_fwd{k}"].notna().sum())
        print(f"  t+{k} horizon coverage: {cov:,}/{len(p):,} panel rows "
              f"({cov / len(p):.1%}; within-window closes only)")
        out_key = {}
        for hid in {h for h, *_ in GRID}:
            out_key[hid] = ("abs_ret_fwd" if dict((h, o) for h, _, o, _ in GRID)[hid]
                            .startswith("abs") else "ret_fwd") + str(k)
        gd = horizon_grid(p, out_key)
        gd.insert(0, "horizon", k)
        atomic_write_df(gd, ROOT / "outputs" /
                        "tables" / "robustness_alt_horizons.csv", index=False)
        for h in HEADS:
            row = gd.loc[gd.test_id == h].iloc[0]
            master.append({"variant": f"t+{k}", "test_id": h,
                           "bp": row["bp"], "p_dk": row["p_dk"],
                           "bh_pass": row["bh_sig_q10"],
                           "sign_agrees": row["sign_agrees"]})
        print(f"  t+{k}: heads BH-pass "
              f"{int(sum(gd.loc[gd.test_id.isin(HEADS), 'bh_sig_q10']))}/5")

    # ---------- c) alt EoD thresholds --------------------------------------
    print("[c] alternative EoD thresholds (1%, 10%) vs base 5%")
    alt_eod = sec_eod_thresholds()
    atomic_write_df(alt_eod, ROOT / "outputs" / "tables" /
                    "robustness_alt_eod_thresholds.csv", index=False)
    base_eod = alt_eod.loc[alt_eod.threshold.str.startswith("5%")]
    for _, r in alt_eod.iterrows():
        if r["threshold"].startswith("5%"):
            master.append({"variant": f"eod {r['threshold']}", "test_id": r["test_id"],
                           "bp": r["bp"], "p_dk": r["p_dk"],
                           "bh_pass": np.nan, "sign_agrees": np.nan})
        else:
            b5 = base_eod.loc[base_eod.test_id == r["test_id"], "bp"].iloc[0]
            concord = (r["bp"] > 0) == (b5 > 0)
            master.append({"variant": f"eod {r['threshold']}",
                           "test_id": r["test_id"], "bp": r["bp"],
                           "p_dk": r["p_dk"],
                           "bh_pass": concord,  # concordance column
                           "sign_agrees": float(concord)})
            print(f"  {r['test_id']} {r['threshold']}: bp {r['bp']:+.2f} "
                  f"p {r['p_dk']:.4f} (base 5% bp {b5:+.2f}) [REAL]")

    # ---------- base panel for a / d / e -----------------------------------
    panel, train = build_oos_panel(scores, outcomes)
    panel = standardize_test(panel, train_fold_stats(train))
    panel = panel.dropna(subset=[c + "_z" for c in Z_SOURCE_COLS]).reset_index(drop=True)

    # ---------- a) LOO ------------------------------------------------------
    print("[a] leave-one-stock-out stability")
    loo_sum, loo_detail = sec_loo(panel)
    atomic_write_df(loo_sum, ROOT / "outputs" / "tables" /
                    "robustness_loo_stability.csv", index=False)
    atomic_write_df(loo_detail, ROOT / "outputs" / "tables" /
                    "robustness_loo_detail.csv", index=False)
    for h in HEADS:
        row = loo_sum.loc[loo_sum.test_id == h].iloc[0]
        master.append({"variant": "loo_full_sample", "test_id": h,
                       "bp": row["beta_full"] * 1e4, "p_dk": row["p_full"],
                       "bh_pass": row["p_full"] < BH_Q,
                       "sign_agrees": ((row["beta_full"] > 0)
                                       == (h in POS_H)) if h in POS_H else
                       (not (row["beta_full"] > 0)) if h in NEG_H else np.nan})
        master.append({"variant": "loo_beta_spread", "test_id": h,
                       "bp": row["beta_min"] * 1e4, "p_dk": np.nan,
                       "bh_pass": np.nan,
                       "sign_agrees": float(row["sign_stable"])})
    print(loo_sum[["test_id", "beta_full", "p_full", "n_same_sign",
                   "n_p_dk_lt_10", "sign_stable"]].to_string(index=False))

    # ---------- d) alt scorers ---------------------------------------------
    print("[d] SV5 alternative scorers vs IF (Spearman, per fold OOS)")
    alt_sc = sec_alt_scorers(scores)
    atomic_write_df(alt_sc, ROOT / "outputs" / "tables" /
                    "robustness_alt_scorers_rankcorr.csv", index=False)

    # ---------- e) drop-bubble ---------------------------------------------
    print("[e] drop-bubble re-run (2023+ rows)")
    gd_db = sec_drop_bubble(panel)
    atomic_write_df(gd_db, ROOT / "outputs" / "tables" /
                    "robustness_drop_bubble_grid.csv", index=False)
    for h in HEADS:
        row = gd_db.loc[gd_db.test_id == h].iloc[0]
        master.append({"variant": "drop_bubble", "test_id": h,
                       "bp": row["bp"], "p_dk": row["p_dk"],
                       "bh_pass": row["bh_sig_q10"],
                       "sign_agrees": row["sign_agrees"]})
    print(gd_db[["test_id", "bp", "p_dk", "bh_adj_p", "sign_agrees"]]
          .to_string(index=False))

    # ---------- f) external top-5 ------------------------------------------
    print("[f] 5-stock external cross-section (ranks 11-15 of the DC1 ranking)")
    feat_full = load_feature_frame()
    sc5, sum5 = sec_top5(feat_full, outcomes)
    print(sum5[["fold_id", "universe", "n_test_complete", "n_test_events",
                "event_share_test"]].to_string(index=False))
    p5, tr5 = build_oos_panel(sc5, out_fk)
    p5 = standardize_test(p5, train_fold_stats(tr5))
    gd5 = horizon_grid(p5, {hid: ("abs_ret_fwd1" if dict(
        (h, o) for h, _, o, _ in GRID)[hid].startswith("abs")
        else "ret_fwd1") for hid in {h for h, *_ in GRID}})
    atomic_write_df(gd5, ROOT / "outputs" / "tables" /
                    "robustness_top5_external_grid.csv", index=False)
    for h in HEADS:
        row = gd5.loc[gd5.test_id == h].iloc[0]
        master.append({"variant": "top5_external", "test_id": h,
                       "bp": row["bp"], "p_dk": row["p_dk"],
                       "bh_pass": row["bh_sig_q10"],
                       "sign_agrees": row["sign_agrees"]})
    print(gd5[["test_id", "bp", "p_dk", "bh_adj_p", "sign_agrees"]]
          .to_string(index=False))

    # ---------- g) sequential variant --------------------------------------
    print("[g] sequential fold-mode variant (D7)")
    feat_full = load_feature_frame()
    sseq, ssumq = sec_sequential(feat_full, outcomes)
    print(ssumq[["fold_id", "train_dates", "test_dates", "n_test_events",
                 "event_share_test"]].to_string(index=False))
    rho = spearman_overlap(scores, sseq, "seq")
    seq_desc = ssumq[["fold_id", "train_dates", "test_dates",
                      "n_test_complete", "n_test_events",
                      "event_share_test"]].copy()
    seq_desc["spearman_vs_anchored_overlap"] = np.nan
    seq_desc["spearman_vs_anchored_pooled"] = rho
    atomic_write_df(seq_desc, ROOT / "outputs" / "tables" /
                    "robustness_sequential_variant.csv", index=False)

    # ---------- z) master survival -----------------------------------------
    surv = pd.DataFrame(master)
    atomic_write_df(surv, ROOT / "outputs" / "tables" /
                    "robustness_headline_survival.csv", index=False)
    print("headline survival (rows variant x test):", len(surv))

    prov.record({
        "ts_utc": utc_iso(),
        "artifact": "outputs/tables/robustness_headline_survival.csv",
        "kind": "robustness_battery_exp0005a_g",
        "source_path": "anomaly_scores.parquet (EXP-0004a) + daily_outcomes.parquet"
                       " + floorsheet_dedup (alt-EoD SQL)",
        "source_url": "derived", "sha256": "", "bytes": 0,
        "rows_sampled": len(panel), "rows_total": len(panel),
        "licence": "derived",
        "evidence": "sections a-g per plan §7; master table "
                    f"{len(surv)} rows; spearman_seq={rho:+.4f}",
    })
    print("BATTERY_DONE", f"in {time.time() - T0:.0f}s")


POS_H = {"H1", "H2", "H5", "H7", "H10"}
NEG_H = {"H3", "H4", "H8", "H9"}

if __name__ == "__main__":
    main()
