"""EXP-0004d — REGIME SPLIT (R8) on the OOS anomaly/feature panel.

Plan §5 primary line for the 2021-2024 scope: regime = CALENDAR —
2021-2022 = "bubble era", 2023-2024 = "normal". Declared operations:

  * panel = the shared EXP-0004b construction (src/nepsemsc/ml/panel_data.py):
    OOS test rows only, per-fold winsor 1/99 + z-constants from TRAIN rows of
    the row's fold (DC7); 2023-02-16 excluded upstream at scoring;
  * `bubble` dummy: event-date year <= 2022. With time effects the bubble
    MAIN effect is absorbed by design; the feature x bubble INTERACTION is
    the identified/ tested object;
  * interaction regression per grid hypothesis (10): DK bw=5 on
    outcome ~ feat_z + feat_z_x_bubble + log_volume_z + market_ret_loo_z
    (+ entity & time FE); interaction coefficient, SE, t, p reported;
  * per-regime subsample betas: single-feature DK(bw=5) on bubble rows only
    and on normal rows only (descriptive contrast — small-sample caveat in
    fold 0 where the train window is short);
  * inference note: interaction p-values are DK-t; no BH family declared for
    this descriptive split (register labels it as such).

Output: outputs/tables/regime_split_results.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd

from nepsemsc.ml.panel_regression import run_panel
from nepsemsc.ml.panel_data import (build_oos_panel, standardize_test,
                                    train_fold_stats, TESTED_FEATURES)
from nepsemsc.utils.io import atomic_write_df
from nepsemsc.utils import provenance as prov
from nepsemsc.utils.tz import utc_iso

GRID = [  # mirrored from run_panel_regressions (single source of the grid)
    ("H1", "self_loop_ratio", "abs_ret_fwd1", "pos"),
    ("H2", "anomaly_score", "abs_ret_fwd1", "pos"),
    ("H3", "anomaly_score", "ret_fwd1", "neg"),
    ("H4", "buyer_hhi", "ret_fwd1", "neg"),
    ("H5", "buyer_hhi", "abs_ret_fwd1", "pos"),
    ("H6", "reciprocity", "ret_fwd1", "amb"),
    ("H7", "end_of_day_concentration", "abs_ret_fwd1", "pos"),
    ("H8", "end_of_day_concentration", "ret_fwd1", "neg"),
    ("H9", "self_loop_ratio", "ret_fwd1", "neg"),
    ("H10", "reciprocity", "abs_ret_fwd1", "pos"),
]


def main() -> None:
    scores = pd.read_parquet(ROOT / "data/processed/anomaly_scores.parquet")
    outcomes = pd.read_parquet(ROOT / "data/processed/daily_outcomes.parquet")

    panel, train = build_oos_panel(scores, outcomes)
    panel = standardize_test(panel, train_fold_stats(train))
    zcols = [c + "_z" for c in ["anomaly_score", "buyer_hhi", "self_loop_ratio",
                                "reciprocity", "end_of_day_concentration",
                                "log_volume", "market_ret_loo"]]
    panel = panel.dropna(subset=zcols).reset_index(drop=True)

    panel["bubble"] = (pd.to_datetime(panel["date"]).dt.year <= 2022).astype(float)
    print(f"regime panel rows: {len(panel):,} | bubble rows: "
          f"{int(panel.bubble.sum()):,} ({panel.bubble.mean():.1%}) [REAL]")

    rows = []
    for hid, feat, outcome, pred_sign in GRID:
        feat_z = feat + "_z"
        panel["feat_x_bubble"] = panel[feat_z] * panel["bubble"]
        base_cols = [feat_z, "feat_x_bubble", "log_volume_z", "market_ret_loo_z"]

        res = run_panel(panel, outcome, base_cols, se="driscoll_kraay", bandwidth=5)
        ib, isx = float(res.params["feat_x_bubble"]), float(res.std_errors["feat_x_bubble"])
        ip, it = float(res.pvalues["feat_x_bubble"]), float(res.tstats["feat_x_bubble"])
        bl, pl = float(res.params[feat_z]), float(res.pvalues[feat_z])

        sub = {}
        for label, sel in (("bubble", panel.bubble == 1), ("normal", panel.bubble == 0)):
            g = panel.loc[sel]
            r = run_panel(g, outcome, [feat_z, "log_volume_z", "market_ret_loo_z"],
                          se="driscoll_kraay", bandwidth=5)
            sub[label] = {"beta": float(r.params[feat_z]), "p": float(r.pvalues[feat_z]),
                          "n": int(len(g))}
        rows.append({
            "test_id": hid, "feature": feat, "outcome": outcome,
            "predicted_sign": pred_sign,
            "feat_z_beta": bl, "feat_z_p": pl,
            "interaction_beta": ib, "interaction_se": isx,
            "interaction_t": it, "interaction_p": ip,
            "beta_bubble": sub["bubble"]["beta"], "p_bubble": sub["bubble"]["p"],
            "n_bubble": sub["bubble"]["n"],
            "beta_normal": sub["normal"]["beta"], "p_normal": sub["normal"]["p"],
            "n_normal": sub["normal"]["n"],
        })
        print(f"{hid} {feat}→{outcome}: interaction β={ib:+.6f} t={it:+.2f} "
              f"p={ip:.4f} | bubble β={sub['bubble']['beta']:+.6f} "
              f"(n={sub['bubble']['n']}) | normal β={sub['normal']['beta']:+.6f} "
              f"(n={sub['normal']['n']}) [REAL]")

    out = pd.DataFrame(rows)
    atomic_write_df(out, ROOT / "outputs/tables/regime_split_results.csv", index=False)

    prov.record({
        "ts_utc": utc_iso(),
        "artifact": "outputs/tables/regime_split_results.csv",
        "kind": "regime_split_exp0004d",
        "source_path": "anomaly_scores.parquet (EXP-0004a) + daily_outcomes.parquet",
        "source_url": "derived", "sha256": "", "bytes": 0,
        "rows_sampled": len(panel), "rows_total": len(panel),
        "licence": "derived",
        "evidence": f"n={len(panel)}; calendar regimes per plan §5 primary; "
                    f"interaction DK bw=5; DESCRIPTIVE-REGIME split (no BH family)",
    })
    print("REGIME_DONE")


if __name__ == "__main__":
    main()
