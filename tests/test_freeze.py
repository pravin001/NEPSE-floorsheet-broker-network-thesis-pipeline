"""Phase-7 FREEZE audit (DC19/DC20) — the thesis-freeze gate as tests."""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import pytest

FROZEN_FINGERPRINT = (
    "9a60208f16040c8246108f79060fa81b69f0fa5609a4a365c4c898898d6b012f")
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


def test_headlines_of_record_stable():
    """The 5 BH-passing headlines + sign directions as registered (EXP-0004b):
    any change to these numbers invalidates the thesis text — fail loudly."""
    grid = pd.read_csv(ROOT / "outputs/tables/hypothesis_grid_results.csv")
    passing = set(grid.loc[grid["bh_sig_q10"], "test_id"])
    assert passing == {"H4", "H6", "H7", "H8", "H10"}
    signs = dict(zip(grid["test_id"], grid["bp"] > 0))
    assert signs["H7"] and signs["H10"]           # positive
    assert not signs["H8"]                        # negative
    assert signs["H4"]                            # opposite vs declared −
    assert not signs["H6"]                        # negative
