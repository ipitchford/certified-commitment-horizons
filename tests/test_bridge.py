from __future__ import annotations

from fractions import Fraction

import numpy as np

from wwprefix.bridge import (
    empty_setup_nodes,
    exact_graph_optimal_paths,
    exact_physical_setup_optima,
    setup_pattern_to_path,
)
from wwprefix.exactcert import ExactInstance
from wwprefix.model import CLASSICAL_ACTIVE_HORIZON, FORCED_SOURCE_GRAPH


def test_leading_zero_is_not_equivalent_to_forced_source_graph() -> None:
    inst = ExactInstance.from_rationals(
        K=[100, 1], q=[1, 0], demand=[0, 1], floor=[0, 0], weights=[1, 1],
        semantic_mode=FORCED_SOURCE_GRAPH,
    )
    graph_value, _ = exact_graph_optimal_paths(inst)
    physical_value, physical = exact_physical_setup_optima(inst)
    assert graph_value == 101
    assert physical_value == 1
    assert physical == ((1,),)


def test_classical_bridge_exact_random_corpus() -> None:
    rng = np.random.default_rng(2026081801)
    checked = 0
    for T in range(1, 9):
        for _ in range(20):
            K = [int(rng.integers(0, 6))] + [int(v) for v in rng.integers(1, 7, max(T - 1, 0))]
            q = list(np.cumsum(rng.integers(0, 5, T)[::-1])[::-1])
            demand = [int(rng.integers(1, 8))] + [int(v) for v in rng.integers(0, 8, max(T - 1, 0))]
            floor = [Fraction(1, 2)] + [Fraction(0)] * max(T - 1, 0)
            inst = ExactInstance.from_rationals(
                K, q, demand, floor, [1] * T,
                semantic_mode=CLASSICAL_ACTIVE_HORIZON,
            )
            graph_value, graph_paths = exact_graph_optimal_paths(inst)
            physical_value, physical_patterns = exact_physical_setup_optima(inst)
            assert graph_value == physical_value
            mapped = tuple(
                sorted(
                    path for path in (
                        setup_pattern_to_path(pattern, T) for pattern in physical_patterns
                    )
                    if path is not None
                )
            )
            assert tuple(sorted(graph_paths)) == mapped
            assert all(not empty_setup_nodes(inst.demand, path) for path in graph_paths)
            checked += 1
    assert checked == 160
