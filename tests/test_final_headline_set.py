"""v2 Stage-5 canonical headline-set tests (plan V2-5).

v2.1.0: the old tests pinned the v2.0.2 outcome (H10 headline; fixed
fragile/powered sets).  The reciprocity correction may legitimately change any
of those rows, so these tests now verify the pre-declared composition rule
against the source tables.  They fail on an unearned label, not on a changed
result.
"""
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
HYPOTHESES = [f"H{i}" for i in range(1, 11)]


@pytest.fixture(scope="module")
def final() -> pd.DataFrame:
    return pd.read_csv(TABLES / "v2_final_headline_set.csv").set_index(
        "hypothesis")


@pytest.fixture(scope="module")
def sources() -> dict[str, pd.DataFrame]:
    liq = pd.read_csv(
        TABLES / "headline_with_liquidity_controls.csv"
    ).query("spec == 'single_feature_liquidity'").set_index("test_id")
    eg = pd.read_csv(
        TABLES / "headline_with_egarch_outcome.csv"
    ).query("spec == 'egarch_primary'").set_index("test_id")
    return {
        "grid": pd.read_csv(
            TABLES / "hypothesis_grid_results_v2.csv").set_index("test_id"),
        "rw": pd.read_csv(
            TABLES / "hypothesis_grid_results_rw.csv").set_index("test_id"),
        "conc": pd.read_csv(TABLES / "se_concordance.csv").set_index("test_id"),
        "liq": liq,
        "eg": eg,
        "mde": pd.read_csv(
            TABLES / "null_classification.csv").set_index("test_id"),
    }


def test_exact_columns_and_ten_unique_hypotheses(final):
    assert final.reset_index().columns.tolist() == EXACT
    assert final.index.tolist() == HYPOTHESES
    assert final.index.is_unique


def test_classification_taxonomy_and_no_unclassified_rows(final):
    assert set(final["final_classification"]) <= ALLOWED
    assert final["final_classification"].notna().all()


def test_headline_labels_earn_every_cap(final, sources):
    for hid, row in final.iterrows():
        label = row["final_classification"]
        if not str(label).startswith("HEADLINE"):
            continue
        assert label in {"HEADLINE_ROBUST", "HEADLINE_MODERATE"}
        assert sources["grid"].loc[hid, "result_classification"] == \
            "CONFIRMED_HEADLINE"
        assert bool(sources["conc"].loc[hid, "stage2_headline"])
        assert bool(sources["liq"].loc[hid, "survives_liquidity"])
        assert bool(sources["eg"].loc[hid, "survives_egarch"])
        want = "STRONG" if label == "HEADLINE_ROBUST" else "MODERATE"
        assert str(sources["conc"].loc[hid, "se_concordance"]) == want
        assert row["rw_p"] <= 0.10


def test_exploratory_row_is_earned(final, sources):
    exploratory = final.index[
        final["final_classification"] == "EXPLORATORY_POST_HOC"].tolist()
    assert exploratory == ["H4"]
    for hid in exploratory:
        assert sources["grid"].loc[hid, "result_classification"] == \
            "EXPLORATORY_POST_HOC"
        declared = {"positive": 1, "negative": -1}[
            final.loc[hid, "pre_declared_direction"]]
        assert np.sign(final.loc[hid, "estimated_beta"]) != np.sign(declared)


def test_fragile_labels_are_earned(final, sources):
    for hid, row in final.iterrows():
        if row["final_classification"] != "NULL_FRAGILE":
            continue
        base = str(sources["grid"].loc[hid, "result_classification"])
        if base == "NULL_FRAGILE":
            # Stage-1 fragility is an RW failure or a corrected BH failure
            # (a BH-failing fit is not confirmable and is not promoted).
            assert row["rw_p"] > 0.10 or not bool(
                sources["grid"].loc[hid, "bh_sig_q10"])
        elif base == "CONFIRMED_HEADLINE":
            # A confirmed result capped by Stage-2 or Stage-3 must have failed
            # at least one of those caps; it keeps its Stage-1 RW pass.
            assert row["rw_p"] <= 0.10
            caps = [
                not bool(sources["conc"].loc[hid, "stage2_headline"]),
                not bool(sources["liq"].loc[hid, "survives_liquidity"]),
                not bool(sources["eg"].loc[hid, "survives_egarch"]),
            ]
            assert any(caps), f"{hid}: capped without a failed cap"
        else:
            pytest.fail(f"{hid}: NULL_FRAGILE without fragility or a cap")


def test_null_labels_follow_stage1_and_mde(final, sources):
    for hid, row in final.iterrows():
        label = row["final_classification"]
        if label not in {"NULL_POWERED", "NULL_UNDERPOWERED"}:
            continue
        assert sources["grid"].loc[hid, "result_classification"] == \
            "NULL_ROBUST"
        mde = str(sources["mde"].loc[hid, "classification"])
        if label == "NULL_POWERED":
            assert mde == "NULL_POWERED"
        else:
            assert mde != "NULL_POWERED"


def test_beta_and_p_values_trace_to_frozen_grid(final, sources):
    for hid, row in final.iterrows():
        assert row["estimated_beta"] == pytest.approx(
            sources["grid"].loc[hid, "bp"], abs=0.0)
        assert row["dk_p"] == pytest.approx(
            sources["grid"].loc[hid, "p_dk"], abs=0.0)
        assert row["rw_p"] == pytest.approx(
            sources["rw"].loc[hid, "rw_p"], abs=0.0)


def test_dependence_and_stage3_flags_trace_to_sources(final, sources):
    for hid, row in final.iterrows():
        assert row["wild_bootstrap_p"] == pytest.approx(
            sources["conc"].loc[hid, "p_wb"], abs=0.0)
        expected_conc = ("NULL (0/4)"
                         if pd.isna(sources["conc"].loc[hid, "se_concordance"])
                         else str(sources["conc"].loc[hid, "se_concordance"]))
        assert row["se_concordance"] == expected_conc
        assert bool(row["survives_liquidity"]) == bool(
            sources["liq"].loc[hid, "survives_liquidity"])
        assert bool(row["survives_egarch"]) == bool(
            sources["eg"].loc[hid, "survives_egarch"])


def test_h4_keeps_its_opposite_sign_rationale(final):
    h4 = final.loc["H4"]
    assert h4["pre_declared_direction"] == "negative"
    assert h4["estimated_beta"] > 0


def test_tail_labels_are_explicit(final):
    tails = dict(zip(final.index, final["tail_concentration"]))
    for hid, label in tails.items():
        assert isinstance(label, str) and label
        assert "(" in label and label.endswith(")")
    # H7's outcome and feature are untouched by the reciprocity correction, so
    # its recorded tail shape remains part of the canonical record.
    assert tails["H7"] == "NONE (HUMP)"
    for hid in ("H1", "H2", "H3", "H5", "H9"):
        assert "descriptive" in tails[hid]
