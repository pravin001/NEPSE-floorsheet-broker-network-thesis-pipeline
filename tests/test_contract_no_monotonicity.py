"""contract_no monotonicity audit tests (SV6 ordering discipline)."""
import pytest

pandas = pytest.importorskip("pandas")


def test_strictly_increasing_passes():
    from nepsemsc.data.quality import contract_monotonicity_report
    df = pandas.DataFrame({
        "symbol": ["A"] * 4, "date": ["2024-01-02"] * 4,
        "contract_no": [1, 2, 3, 4],
    })
    rep = contract_monotonicity_report(df)
    assert bool(rep["strictly_increasing"].iloc[0])
    assert int(rep["n_gaps"].iloc[0]) == 0


def test_gap_counted_but_still_increasing():
    from nepsemsc.data.quality import contract_monotonicity_report
    df = pandas.DataFrame({
        "symbol": ["A"] * 4, "date": ["2024-01-02"] * 4,
        "contract_no": [1, 2, 5, 9],
    })
    rep = contract_monotonicity_report(df)
    assert bool(rep["strictly_increasing"].iloc[0])
    assert int(rep["n_gaps"].iloc[0]) == 2
    assert int(rep["max_gap"].iloc[0]) == 4


def test_duplicate_contract_flags_not_increasing():
    from nepsemsc.data.quality import contract_monotonicity_report
    df = pandas.DataFrame({
        "symbol": ["A"] * 3, "date": ["2024-01-02"] * 3,
        "contract_no": [1, 2, 2],
    })
    rep = contract_monotonicity_report(df)
    assert not bool(rep["strictly_increasing"].iloc[0])
    assert int(rep["n_decreases"].iloc[0]) == 1


def test_shuffled_order_counts_after_sorting(toy_floorsheet):
    from nepsemsc.data.quality import contract_monotonicity_report
    rep = contract_monotonicity_report(toy_floorsheet)
    # toy generator ensures strict increase per (symbol, date) before shuffle
    assert (rep["strictly_increasing"] == True).all()
    assert (rep.groupby("date")["n_gaps"].sum() > 0).all()
