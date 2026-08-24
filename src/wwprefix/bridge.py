"""Exact audit helpers for the graph-to-lot-sizing semantic bridge.

These routines enumerate setup patterns and are intentionally restricted to
small horizons.  They provide an independent check of the source-to-encoding
claim; the production algorithms use the shortest-path formulations instead.
"""
from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from typing import Sequence

from .exactcert import ExactInstance, Rat, _fr, exact_path_cost
from .model import Path, enumerate_paths


def exact_physical_setup_cost(
    inst: ExactInstance,
    demand: Sequence[object],
    setups: Sequence[int],
) -> Rat | None:
    """Minimum reduced physical cost for a fixed set of open setup periods.

    Demand is assigned to the latest open setup no later than its due period.
    Ordered reduced slopes make that assignment optimal for the fixed setup
    pattern.  ``None`` denotes infeasibility because positive demand precedes
    the first open setup.  Open but unused setups still incur their setup cost.
    """
    d = tuple(_fr(v) for v in demand)
    if len(d) != inst.T:
        raise ValueError("demand has the wrong length")
    y = tuple(sorted(set(int(i) for i in setups)))
    if any(i < 0 or i >= inst.T for i in y):
        raise ValueError("setup periods lie outside the horizon")
    cost = sum((inst.K[i] for i in y), Fraction(0))
    for t, amount in enumerate(d):
        if amount == 0:
            continue
        eligible = [i for i in y if i <= t]
        if not eligible:
            return None
        cost += inst.q[max(eligible)] * amount
    return cost


def exact_physical_setup_optima(
    inst: ExactInstance,
    demand: Sequence[object] | None = None,
    *,
    max_horizon: int = 20,
) -> tuple[Rat, tuple[tuple[int, ...], ...]]:
    """Enumerate all minimum-cost physical setup patterns for audit use."""
    if inst.T > max_horizon:
        raise ValueError(f"audit enumeration is capped at T={max_horizon}")
    d = inst.demand if demand is None else tuple(_fr(v) for v in demand)
    feasible: list[tuple[Rat, tuple[int, ...]]] = []
    nodes = tuple(range(inst.T))
    for r in range(inst.T + 1):
        for setups in combinations(nodes, r):
            cost = exact_physical_setup_cost(inst, d, setups)
            if cost is not None:
                feasible.append((cost, setups))
    if not feasible:
        # This can happen only with positive demand and no permissible setup,
        # which the full enumeration rules out.
        raise RuntimeError("physical setup enumeration found no feasible plan")
    optimum = min(cost for cost, _ in feasible)
    return optimum, tuple(setups for cost, setups in feasible if cost == optimum)


def setup_pattern_to_path(setups: Sequence[int], T: int) -> Path | None:
    """Map a source-active setup pattern to a path; return None if it starts late."""
    y = tuple(sorted(set(int(i) for i in setups)))
    if not y or y[0] != 0:
        return None
    return (*y, T)


def empty_setup_nodes(
    demand: Sequence[object], path: Sequence[int]
) -> tuple[int, ...]:
    """Return setup nodes whose outgoing replenishment cycle serves no demand."""
    d = tuple(_fr(v) for v in demand)
    p = tuple(int(v) for v in path)
    return tuple(
        i for i, j in zip(p, p[1:])
        if sum(d[i:j], Fraction(0)) == 0
    )


def exact_graph_optimal_paths(
    inst: ExactInstance,
    demand: Sequence[object] | None = None,
    *,
    max_horizon: int = 20,
) -> tuple[Rat, tuple[Path, ...]]:
    """Enumerate all graph-optimal complete paths for a small exact instance."""
    if inst.T > max_horizon:
        raise ValueError(f"audit enumeration is capped at T={max_horizon}")
    d = inst.demand if demand is None else tuple(_fr(v) for v in demand)
    values = [(exact_path_cost(inst, d, p), p) for p in enumerate_paths(inst.T)]
    optimum = min(cost for cost, _ in values)
    return optimum, tuple(p for cost, p in values if cost == optimum)
