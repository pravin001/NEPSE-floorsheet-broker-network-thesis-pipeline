"""Phase-7 FREEZE audit (DC19/DC20) — the thesis-freeze gate as tests."""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import pytest

FROZEN_FINGERPRINT = (
    "9a60208f16040c8246108f79060fa81b69f0fa5609a4a365c4c898898d6b012f")
SUPERSEDED = ROOT / "outputs" / "tables" / "superseded_v2_0_2"
ROBUSTNESS_TABLES = [
    "robustness_alt_eod_thresholds.csv", "robustness_alt_horizons.csv",
    "robustness_alt_scorers_rankcorr.csv", "robustness_drop_bubble_grid.csv",
    "robustness_headline_survival.csv", "robustness_loo_detail.csv",
    "robustness_loo_stability.csv", "robustness_sequential_variant.csv",
    "robustness_top5_external_grid.csv",
]


def test_config_fingerprint_is_frozen():
    """DC20: configs/project.yaml bytes == the registered frozen fingerprint."""
    live = hashlib.sha256((ROOT / "configs/project.yaml").read_bytes()).hexdigest()
    assert live == FROZEN_FINGERPRINT, (
        "project.yaml CHANGED after freeze — violates DC20 "
        f"(live sha256 {live}; frozen {FROZEN_FINGERPRINT})")


def test_robustness_battery_tables_frozen():
    for f in ROBUSTNESS_TABLES:
        assert (ROOT / "outputs/tables" / f).is_file(), f
    surv = pd.read_csv(ROOT / "outputs/tables/robustness_headline_survival.csv")
    assert len(surv) == 46                 # 46 variant x headline rows of record
    grid = pd.read_csv(ROOT / "outputs/tables/hypothesis_grid_results.csv")
    assert len(grid) == 10                 # 10 tested hypotheses
    summ = pd.read_csv(ROOT / "outputs/tables/anomaly_scoring_summary.csv")
    assert list(summ["fold_id"]) == [0, 1, 2, 3]


def test_register_is_complete():
    reg = (ROOT / "docs/experiment_register.md").read_text()
    for i in range(0, 8):
        assert f"| EXP-000{i}" in reg, f"EXP-000{i} missing"
    for exp in ("EXP-0005a", "EXP-0005b", "EXP-0005c", "EXP-0005d",
                "EXP-0005e", "EXP-0005f", "EXP-0005g", "EXP-0006", "EXP-0007"):
        assert f"| {exp} |" in reg, f"{exp} missing"


def test_provenance_manifest_pins_battery_and_cache():
    rows = pd.read_csv(ROOT / "data/metadata/provenance_manifest.csv")
    kinds = set(rows["kind"])
    assert "robustness_battery_exp0005a_g" in kinds
    assert "dashboard_cache_exp0006" in kinds
    assert len(rows) >= 46
    # every prov row carries a non-negative row count / licence column
    assert rows["licence"].notna().all()


def test_freeze_documents_exist():
    assert (ROOT / "docs/limitations.md").is_file()
    assert (ROOT / "docs/analysis_deviations.md").is_file()
    assert (ROOT / "docs/reproducibility.md").is_file()
    assert (ROOT / "requirements-lock.txt").is_file()
    lock = (ROOT / "requirements-lock.txt").read_text()
    assert "kagglehub==" in lock, "kagglehub must be pinned at freeze"


def test_bh_gate_is_self_consistent():
    """BH q and the q<=.10 flag must equal a fresh BH computation on p_dk.

    v2.1.0: the old test pinned the v2.0.2 BH set {H4,H6,H7,H8,H10}.  The
    reciprocity correction can legitimately move H6/H10, so the invariant is
    the multiplicity arithmetic, not the old membership.
    """
    grid = pd.read_csv(ROOT / "outputs/tables/hypothesis_grid_results.csv")
    p = grid["p_dk"].to_numpy(dtype=float)
    m = len(p)
    order = np.argsort(p)
    ranked = p[order] * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    q = np.empty_like(adj)
    q[order] = np.clip(adj, 0.0, 1.0)
    assert np.allclose(q, grid["bh_adj_p"].to_numpy(dtype=float), atol=1e-12)
    assert (q <= 0.10).tolist() == grid["bh_sig_q10"].astype(bool).tolist()
    # The flag must match the recorded q directly.
    assert (grid["bh_adj_p"] <= 0.10).tolist() == \
        grid["bh_sig_q10"].astype(bool).tolist()


def test_sign_flags_are_self_consistent():
    grid = pd.read_csv(ROOT / "outputs/tables/hypothesis_grid_results.csv")
    for _, r in grid.iterrows():
        declared = str(r["predicted_sign"])
        agrees = r["sign_agrees"]
        if declared == "pos":
            assert bool(agrees) == bool(r["bp"] > 0), r["test_id"]
        elif declared == "neg":
            assert bool(agrees) == bool(r["bp"] < 0), r["test_id"]
        else:
            assert pd.isna(agrees), r["test_id"]


def test_correction_invariance_for_untouched_features():
    """The reciprocity fix must not move hypotheses that do not use it.

    H1/H5/H9 use self-loop ratio, H4 uses buyer HHI, H7/H8 use end-of-day
    concentration.  H2/H3 use the anomaly score (which is scored from network
    features) and H6/H10 use reciprocity, so those five may change.  Exact
    reproduction of the six untouched regressions is a strong audit that the
    correction was not accompanied by an unintended pipeline change.
    """
    grid = pd.read_csv(ROOT / "outputs/tables/hypothesis_grid_results.csv")
    old = pd.read_csv(SUPERSEDED / "hypothesis_grid_results.csv")
    new = grid.set_index("test_id")
    old = old.set_index("test_id")
    for hid in ("H1", "H4", "H5", "H7", "H8", "H9"):
        assert new.loc[hid, "feature"] == old.loc[hid, "feature"]
        assert new.loc[hid, "outcome"] == old.loc[hid, "outcome"]
        assert int(new.loc[hid, "n_obs"]) == int(old.loc[hid, "n_obs"])
        assert float(new.loc[hid, "bp"]) == pytest.approx(
            float(old.loc[hid, "bp"]), abs=1e-12), hid
        assert float(new.loc[hid, "p_dk"]) == pytest.approx(
            float(old.loc[hid, "p_dk"]), abs=1e-12), hid
        assert float(new.loc[hid, "beta_dc"]) == pytest.approx(
            float(old.loc[hid, "beta_dc"]), abs=1e-12), hid
