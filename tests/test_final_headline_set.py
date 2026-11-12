"""v2 Stage-5 canonical headline-set tests (plan V2-5)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import pytest

TABLES = ROOT / "outputs" / "tables"

EXACT = ["hypothesis", "pre_declared_direction", "estimated_beta", "dk_p",
         "rw_p", "wild_bootstrap_p", "se_concordance", "survives_liquidity",
         "survives_egarch", "tail_concentration", "final_classification"]
ALLOWED = {"HEADLINE_ROBUST", "HEADLINE_MODERATE", "EXPLORATORY_POST_HOC",
           "NULL_POWERED", "NULL_FRAGILE", "NULL_UNDERPOWERED"}


@pytest.fixture(scope="module")
def final() -> pd.DataFrame:
    return pd.read_csv(TABLES / "v2_final_headline_set.csv")


def test_exact_columns_and_ten_unique_hypotheses(final):
    assert final.columns.tolist() == EXACT
    assert final["hypothesis"].tolist() == [f"H{i}" for i in range(1, 11)]
    assert final["hypothesis"].is_unique


def test_classification_taxonomy_and_singletons(final):
    assert set(final["final_classification"]) <= ALLOWED
    headlines = final.loc[final["final_classification"].str.startswith("HEADLINE"),
                          "hypothesis"].tolist()
    assert headlines == ["H10"]
    assert final.loc[final["final_classification"] == "EXPLORATORY_POST_HOC",
                     "hypothesis"].tolist() == ["H4"]
    fragile = set(final.loc[final["final_classification"] == "NULL_FRAGILE",
                            "hypothesis"])
    powered = set(final.loc[final["final_classification"] == "NULL_POWERED",
                            "hypothesis"])
    assert fragile == {"H6", "H7", "H8"}
    assert powered == {"H1", "H2", "H3", "H5", "H9"}


def test_beta_and_p_values_trace_to_frozen_grid(final):
    grid = pd.read_csv(TABLES / "hypothesis_grid_results.csv").set_index("test_id")
    rw = pd.read_csv(TABLES / "hypothesis_grid_results_rw.csv").set_index("test_id")
    for _, row in final.iterrows():
        hid = row["hypothesis"]
        assert row["estimated_beta"] == pytest.approx(grid.loc[hid, "bp"])
        assert row["dk_p"] == pytest.approx(grid.loc[hid, "p_dk"])
        assert row["rw_p"] == pytest.approx(rw.loc[hid, "rw_p"])


def test_dependence_and_stage3_flags_trace_to_sources(final):
    conc = pd.read_csv(TABLES / "se_concordance.csv").set_index("test_id")
    liq = pd.read_csv(
        TABLES / "headline_with_liquidity_controls.csv"
    ).query("spec == 'single_feature_liquidity'").set_index("test_id")
    eg = pd.read_csv(
        TABLES / "headline_with_egarch_outcome.csv"
    ).query("spec == 'egarch_primary'").set_index("test_id")
    for _, row in final.iterrows():
        hid = row["hypothesis"]
        assert row["wild_bootstrap_p"] == pytest.approx(conc.loc[hid, "p_wb"])
        expected_conc = ("NULL (0/4)" if pd.isna(conc.loc[hid, "se_concordance"])
                         else str(conc.loc[hid, "se_concordance"]))
        assert row["se_concordance"] == expected_conc
        assert bool(row["survives_liquidity"]) == bool(
            liq.loc[hid, "survives_liquidity"])
        assert bool(row["survives_egarch"]) == bool(
            eg.loc[hid, "survives_egarch"])


def test_rw_partition_and_sign_of_headline(final):
    assert final.loc[final["final_classification"] == "HEADLINE_MODERATE",
                     "rw_p"].iloc[0] <= 0.10
    fragile = final[final["final_classification"] == "NULL_FRAGILE"]
    assert (fragile["rw_p"] > 0.10).all()
    # H4 is kept exploratory because its sign contradicts the declaration.
    h4 = final.set_index("hypothesis").loc["H4"]
    assert h4["pre_declared_direction"] == "negative"
    assert h4["estimated_beta"] > 0


def test_tail_labels_are_explicit(final):
    tails = dict(zip(final["hypothesis"], final["tail_concentration"]))
    assert tails["H10"] == "BOTH_TAILS (INCREASING)"
    assert tails["H7"] == "NONE (HUMP)"
    for hid in ("H1", "H2", "H3", "H5", "H9"):
        assert "descriptive" in tails[hid]
