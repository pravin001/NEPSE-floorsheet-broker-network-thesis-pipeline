"""v2 engine validation (contracts C1+C2) — evidence artifact, Stage 1.

Builds the frozen v1 panel, constructs engine bundles for two designs
(H2 anomaly; H7 EoD concentration), then:
  C1: engine covariance vs linearmodels res.cov (base fit);
  C2: pseudo-draw t/SE vs FULL PanelOLS refits (4 draws x 2 designs).
Writes outputs/logs/v2_engine_validation.log (tee) and a small CSV.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd

from nepsemsc.evaluation._panel_boot import (build_bundle, pseudo_draws,
                                             make_pseudo_panel,
                                             p_functional)
from nepsemsc.ml.panel_data import build_oos_panel, train_fold_stats, standardize_test
from nepsemsc.ml.panel_regression import fit_driscoll_kraay
from nepsemsc.utils.seeds_v2 import V2_RW_SEEDS


def main() -> None:
    t_all = time.time()
    scores = pd.read_parquet(ROOT / "data/processed/anomaly_scores.parquet")
    outcomes = pd.read_parquet(ROOT / "data/processed/daily_outcomes.parquet")
    panel, train = build_oos_panel(scores, outcomes)
    panel = standardize_test(panel, train_fold_stats(train))
    panel = panel.dropna(subset=[c + "_z" for c in
                                 ["anomaly_score", "log_volume", "market_ret_loo"]]
                         ).reset_index(drop=True)
    print(f"panel rows: {len(panel)}")

    designs = [
        ("H2", "anomaly_score", "abs_ret_fwd1", ["anomaly_score_z", "log_volume_z"]),
        ("H7", "end_of_day_concentration", "abs_ret_fwd1",
         ["end_of_day_concentration_z", "log_volume_z"]),
    ]
    rows = []
    outcomes_ok = True
    for test_id, feature, outcome, cols in designs:
        bundle, res = build_bundle(panel, outcome, cols, test_id=test_id, feature=feature)
        print(f"[{test_id}] C1 base rel err = {bundle.base_rel_err:.2e} "
              f"| p functional rel = {bundle.p_rel_err:.2e}")
        # C2: 4 random draws
        rng = np.random.default_rng(V2_RW_SEEDS[0])
        B_val = 4
        eta = (rng.integers(0, 2, size=(B_val, len(panel))) * 2 - 1).astype(np.int8)
        out = pseudo_draws(bundle, eta, cluster=False)
        for d in range(B_val):
            u = eta[d].astype(float) * bundle.e_w
            pseudo = make_pseudo_panel(panel, bundle, u)
            r = fit_driscoll_kraay(pseudo, "_y_pseudo_", cols, bandwidth=5)
            max_rel = 0.0
            for j, c in enumerate(cols):
                t_ref = float(r.tstats[c]); se_ref = float(r.std_errors[c])
                b_ref = float(r.params[c])
                t_eng = out["t_raw"][d, j]; se_eng = out["se"][d, j]
                b_eng = out["beta_raw"][d, j]
                max_rel = max(max_rel,
                              abs(t_eng - t_ref) / max(abs(t_ref), 1e-30),
                              abs(se_eng - se_ref) / max(abs(se_ref), 1e-30),
                              abs(b_eng - b_ref) / max(abs(b_ref), 1e-30))
            print(f"  [{test_id}] draw {d}: max rel {max_rel:.2e}")
            rows.append({"test_id": test_id, "draw": d, "max_rel": max_rel,
                         "pass": max_rel < 1e-8})
            outcomes_ok &= bool(max_rel < 1e-8)

    df = pd.DataFrame(rows)
    outp = ROOT / "outputs/tables/v2_engine_validation.csv"
    df.to_csv(outp, index=False)
    print(f"C2 OVERALL: {'PASS' if outcomes_ok else 'FAIL'} "
          f"({len(rows)} draws, max {df.max_rel.max():.2e}); "
          f"wall {time.time() - t_all:.1f}s")
    print("ROW: v2_engine_validation.csv written")


if __name__ == "__main__":
    main()
