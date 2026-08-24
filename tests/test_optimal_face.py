from __future__ import annotations

from fractions import Fraction

import numpy as np

from wwprefix.exactcert import ExactInstance, certified_exact_radius, exact_shortest_path
from wwprefix.optimal_face import find_optimal_face_edge_witness, single_detour


def test_single_detour_recognises_one_and_rejects_two() -> None:
    assert single_detour((0, 1, 3, 5), (0, 2, 3, 5)) == (0, 3)
    assert single_detour((0, 1, 3, 4, 6), (0, 2, 3, 5, 6)) is None


def test_strict_gap_radius_has_a_single_detour_optimal_face_witness() -> None:
    inst = ExactInstance.from_rationals(
        K=[0, 3, 2],
        q=[2, 1, 0],
        demand=[1, 5, 1],
        floor=[Fraction(1, 2)] * 3,
        weights=[1, 1, 1],
    )
    _, nominal = exact_shortest_path(inst)
    result = certified_exact_radius(inst, nominal, 1)
    assert result.exact_certified and result.witness is not None
    witness = find_optimal_face_edge_witness(
        inst, result.witness.demand, nominal[:2]
    )
    assert witness is not None
    assert witness.inside_path[:2] == nominal[:2]
    assert witness.outside_path[:2] != nominal[:2]
    assert witness.divergence_node == 0
    assert witness.remergence_node in witness.inside_path
    assert witness.remergence_node in witness.outside_path


def test_edge_witness_theorem_on_exact_random_corpus() -> None:
    rng = np.random.default_rng(20260818)
    checked = 0
    for T in range(2, 8):
        for _ in range(8):
            K = [int(v) for v in rng.integers(0, 7, T)]
            q = list(np.cumsum(rng.integers(0, 4, T)[::-1])[::-1])
            demand = [int(v) for v in rng.integers(1, 8, T)]
            floor = [int(v) for v in rng.integers(0, 2, T)]
            floor = [min(a, b) for a, b in zip(floor, demand)]
            inst = ExactInstance.from_rationals(K, q, demand, floor, [1] * T)
            _, nominal = exact_shortest_path(inst)
            for k in range(1, len(nominal)):
                result = certified_exact_radius(inst, nominal, k)
                if not result.exact_certified or result.witness is None:
                    continue
                witness = find_optimal_face_edge_witness(
                    inst, result.witness.demand, nominal[: k + 1]
                )
                assert witness is not None
                checked += 1
    assert checked >= 25


def test_platform_noisy_lp_proposal_closes_to_exact_optimal_face_boundary() -> None:
    """A few ulps of HiGHS noise must not change an exactly verified result."""
    inst = ExactInstance.from_rationals(
        K=[5, 7, 1, 2, 3, 4, 0, 7],
        q=[19, 15, 14, 12, 9, 9, 6, 4],
        demand=[6, 5, 6, 4, 5, 7, 3, 5],
        floor=[2, 2, 2, 1, 0, 0, 1, 1],
        weights=[1, 1, 1, Fraction(3, 2), Fraction(3, 2), Fraction(3, 2), 1, 1],
    )
    _, nominal = exact_shortest_path(inst)
    result = certified_exact_radius(inst, nominal, 4)
    assert result.status == "exact_certified"
    assert result.exact_radius == Fraction(9, 2)
    assert result.witness is not None
    edge = find_optimal_face_edge_witness(inst, result.witness.demand, nominal[:5])
    assert edge is not None
    assert (edge.divergence_node, edge.remergence_node) == (2, 4)
