"""Placebo machinery tests (R2)."""
import numpy as np
import pytest


def test_exact_seed_list_and_count():
    from nepsemsc.ml.placebo import permuted_scores
    scores = np.arange(10, dtype="float64")
    perms = permuted_scores(scores)  # no argument = pre-declared 200
    assert len(perms) == 200
    for i, p in enumerate(perms):
        assert sorted(p) == sorted(scores)  # permutations preserve multiset


def test_determinism_same_seeds():
    from nepsemsc.ml.placebo import permuted_scores
    scores = np.arange(10, dtype="float64")
    assert all((a == b).all() for a, b in zip(permuted_scores(scores), permuted_scores(scores)))


def test_placebo_p_value_bounds_and_rule():
    from nepsemsc.ml.placebo import placebo_p_value, placebo_significance
    rng = np.random.default_rng(0)
    pb = rng.normal(0.0, 1.0, 1000)
    v = placebo_p_value(10.0, pb)          # observed far right of placebo
    assert v == 0.0
    assert placebo_significance(10.0, pb)  # ≤ 0.05 share
    w = placebo_p_value(-3.0, pb)
    assert 0.95 < w <= 1.0
    assert not placebo_significance(-3.0, pb)


def test_below_200_permutations_rejected():
    from nepsemsc.ml.placebo import permuted_scores
    with pytest.raises(ValueError):
        permuted_scores(np.arange(5.0), n_permutations=150)
