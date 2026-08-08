from __future__ import annotations

import math

import numpy as np
import pytest

from wwprefix import (
    WWInstance,
    admissibility_aware_score,
    bellman_residual,
    bonferroni_allocation,
    coefficient_diameter,
    dead_zone_bound,
    frozen_certificate_exhaustive,
    generic_lipschitz_bound,
    radial_projection,
    shortest_path,
    split_conformal_threshold,
)


def test_admissibility_score_and_conformal_rank() -> None:
    weights = [1, 2]
    assert admissibility_aware_score([1, -0.5], [2, 2], [0, 0], weights) == pytest.approx(1.0)
    assert math.isinf(admissibility_aware_score([0, -3], [2, 2], [0, 0], weights))
    result = split_conformal_threshold([1, 2, 3, 4, 5, 6, 7, 8, 9], 0.2)
    assert result.rank == 8
    assert result.threshold == 8
    assert result.guarantee.startswith("one_step")
    assert sum(bonferroni_allocation(0.1, 4)) == pytest.approx(0.1)


def test_conformal_empirical_rank_sanity() -> None:
    rng = np.random.default_rng(77)
    covered = 0
    trials = 5000
    for _ in range(trials):
        scores = rng.lognormal(size=50)
        threshold = split_conformal_threshold(scores[:-1], 0.1).threshold
        covered += scores[-1] <= threshold
    # Monte Carlo sanity band, not a theorem test.
    assert 0.88 <= covered / trials <= 0.92


def test_coefficient_diameter_by_enumeration() -> None:
    from wwprefix.model import enumerate_paths, path_coefficients

    rng = np.random.default_rng(9)
    for T in range(2, 7):
        inst = WWInstance.create(
            K=np.zeros(T),
            q=np.cumsum(rng.uniform(0.2, 2, T)[::-1])[::-1],
            demand=np.ones(T),
            weights=rng.uniform(0.5, 2, T),
        )
        betas = [path_coefficients(inst, p)[1] for p in enumerate_paths(T)]
        brute = max(np.sum(np.abs(a - b) / inst.weights) for a in betas for b in betas)
        assert coefficient_diameter(inst, 0) == pytest.approx(brute)


def test_dead_zone_bound_random() -> None:
    rng = np.random.default_rng(17)
    checked = 0
    for T in range(3, 8):
        for _ in range(30):
            inst = WWInstance.create(
                K=rng.uniform(0, 12, T),
                q=np.cumsum(rng.uniform(0.2, 1.5, T)[::-1])[::-1],
                demand=rng.uniform(1, 6, T),
                floor=np.full(T, 0.1),
                weights=rng.uniform(0.7, 1.5, T),
            )
            _, pstar = shortest_path(inst)
            k = 1
            block = pstar[: k + 1]
            radius = frozen_certificate_exhaustive(inst, pstar, k).radius
            realised = np.maximum(inst.floor, inst.demand + rng.normal(0, 2, T))
            residual = bellman_residual(inst, realised, block)
            bound = dead_zone_bound(inst, inst.demand, realised, 0, radius)
            generic = generic_lipschitz_bound(inst, inst.demand, realised, 0)
            assert residual <= bound + 3e-7
            assert bound <= generic + 1e-9
            projected = radial_projection(inst, inst.demand, realised, 0, radius)
            assert np.all(projected >= inst.floor - 1e-9)
            checked += 1
    assert checked >= 100


def test_zero_and_infinite_radius_cases() -> None:
    inst = WWInstance.create(K=[0], q=[1], demand=[2], floor=[0])
    assert dead_zone_bound(inst, [2], [100], 0, math.inf) == 0.0
    inst2 = WWInstance.create(K=[0, 1], q=[1, 0], demand=[2, 3], floor=[0, 0])
    bound = dead_zone_bound(inst2, [2, 3], [5, 1], 0, 0)
    assert bound == pytest.approx(generic_lipschitz_bound(inst2, [2, 3], [5, 1], 0))
