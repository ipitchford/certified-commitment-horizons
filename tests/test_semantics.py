from __future__ import annotations

import pytest

from wwprefix.model import (
    CLASSICAL_ACTIVE_HORIZON,
    FORCED_SOURCE_GRAPH,
    WWInstance,
    enumerate_paths,
    path_cost,
    shortest_path,
)


def test_leading_zero_counterexample_is_graph_only() -> None:
    """The reviewer counterexample must never be labelled classical."""
    graph = WWInstance.create(
        K=[100, 1],
        q=[1, 0],
        demand=[0, 1],
        floor=[0, 0],
        semantic_mode=FORCED_SOURCE_GRAPH,
    )
    value, _ = shortest_path(graph)
    assert value == pytest.approx(101)

    with pytest.raises(ValueError, match=r"floor\[0\] > 0"):
        WWInstance.create(
            K=[100, 1],
            q=[1, 0],
            demand=[0, 1],
            floor=[0, 0],
            semantic_mode=CLASSICAL_ACTIVE_HORIZON,
        )


def test_classical_mode_excludes_costless_empty_later_setups() -> None:
    with pytest.raises(ValueError, match=r"K\[i\] > 0"):
        WWInstance.create(
            K=[0, 0, 2],
            q=[2, 2, 0],
            demand=[1, 0, 2],
            floor=[0.5, 0, 0],
            semantic_mode=CLASSICAL_ACTIVE_HORIZON,
        )

    graph = WWInstance.create(
        K=[0, 0, 2],
        q=[2, 2, 0],
        demand=[1, 0, 2],
        floor=[0.5, 0, 0],
        semantic_mode=FORCED_SOURCE_GRAPH,
    )
    # Inserting the zero-quantity, zero-cost setup at node 1 changes the graph
    # path but not its operational projection or cost.
    assert path_cost(graph, graph.demand, (0, 1, 2, 3)) == path_cost(
        graph, graph.demand, (0, 2, 3)
    )


def test_classical_mode_allows_interior_zero_demand_without_empty_optimal_cycles() -> None:
    inst = WWInstance.create(
        K=[0, 4, 2],
        q=[2, 1, 0],
        demand=[1, 0, 3],
        floor=[0.5, 0, 0],
        semantic_mode=CLASSICAL_ACTIVE_HORIZON,
    )
    optimum = min(path_cost(inst, inst.demand, path) for path in enumerate_paths(inst.T))
    optimal_paths = [
        path
        for path in enumerate_paths(inst.T)
        if path_cost(inst, inst.demand, path) == pytest.approx(optimum)
    ]
    for path in optimal_paths:
        for i, j in zip(path[1:-1], path[2:]):
            assert sum(inst.demand[i:j]) > 0


def test_classical_mode_preserves_the_semantic_contract_under_revisions() -> None:
    inst = WWInstance.create(
        K=[0, 2],
        q=[1, 0],
        demand=[1, 1],
        floor=[0.25, 0],
        semantic_mode=CLASSICAL_ACTIVE_HORIZON,
    )
    revised = inst.with_demand([0.25, 3])
    assert revised.semantic_mode == CLASSICAL_ACTIVE_HORIZON
    with pytest.raises(ValueError, match="above the floor"):
        inst.with_demand([0, 3])
