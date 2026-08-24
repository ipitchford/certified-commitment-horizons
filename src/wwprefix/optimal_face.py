"""Optimal-face witnesses for loss of a protected path prefix.

The strong-radius event is an optimal-face event, not merely a pairwise tie.
Whenever an optimal face contains both a prefix-retaining and a prefix-leaving
path, its connected one-skeleton contains an edge crossing that partition.
For a directed acyclic path polytope, the two endpoints of such an edge differ
on one contiguous divergence--remergence segment.  The helpers here construct
and audit that compressed witness on small exact instances; they are not used
to decide production certificates.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from .exactcert import ExactInstance, Rat, _fr, exact_path_cost
from .model import Path, enumerate_paths, follows_prefix, validate_prefix


@dataclass(frozen=True)
class OptimalFaceEdgeWitness:
    inside_path: Path
    outside_path: Path
    divergence_node: int
    remergence_node: int
    optimum: Rat
    optimal_path_count: int


def single_detour(path_a: Sequence[int], path_b: Sequence[int]) -> tuple[int, int] | None:
    """Return the divergence and remergence nodes for one contiguous detour.

    Paths must have the same source and sink.  ``None`` means that they are
    identical or their symmetric difference contains two or more disjoint
    divergence--remergence segments.
    """
    a = tuple(int(v) for v in path_a)
    b = tuple(int(v) for v in path_b)
    if len(a) < 2 or len(b) < 2 or a[0] != b[0] or a[-1] != b[-1]:
        raise ValueError("paths must share a source and sink")
    if a == b:
        return None

    prefix_edges = 0
    while (
        prefix_edges + 1 < len(a)
        and prefix_edges + 1 < len(b)
        and a[prefix_edges + 1] == b[prefix_edges + 1]
    ):
        prefix_edges += 1
    divergence = a[prefix_edges]
    if divergence != b[prefix_edges]:
        raise RuntimeError("common-prefix invariant failed")

    pos_a = {node: idx for idx, node in enumerate(a)}
    pos_b = {node: idx for idx, node in enumerate(b)}
    common_after = sorted(
        node for node in (set(a) & set(b)) if node > divergence
    )
    if not common_after:
        raise RuntimeError("paths unexpectedly have no common sink")
    remergence = common_after[0]
    ia, ib = pos_a[remergence], pos_b[remergence]
    if a[ia:] != b[ib:]:
        return None
    return divergence, remergence


def exact_optimal_paths_at(
    inst: ExactInstance,
    demand: Sequence[object],
    *,
    max_horizon: int = 20,
) -> tuple[Rat, tuple[Path, ...]]:
    """Enumerate all exactly optimal paths at ``demand`` for audit instances."""
    if inst.T > max_horizon:
        raise ValueError(f"audit enumeration is capped at T={max_horizon}")
    d = tuple(_fr(v) for v in demand)
    if len(d) != inst.T:
        raise ValueError("demand has the wrong length")
    costs = [(exact_path_cost(inst, d, path), path) for path in enumerate_paths(inst.T)]
    optimum = min(cost for cost, _ in costs)
    return optimum, tuple(path for cost, path in costs if cost == optimum)


def find_optimal_face_edge_witness(
    inst: ExactInstance,
    demand: Sequence[object],
    prefix: Sequence[int],
    *,
    max_horizon: int = 20,
) -> OptimalFaceEdgeWitness | None:
    """Find a single-detour co-optimal pair crossing the prefix partition.

    The routine exhausts the optimal path face and is therefore an audit tool,
    not a scalable solver.  The edge-witness theorem guarantees a result when
    the face contains at least one path on each side of the protected prefix.
    """
    pref = validate_prefix(prefix, inst.T)
    optimum, optimal = exact_optimal_paths_at(inst, demand, max_horizon=max_horizon)
    inside = tuple(path for path in optimal if follows_prefix(path, pref))
    outside = tuple(path for path in optimal if not follows_prefix(path, pref))
    if not inside or not outside:
        return None
    for p in inside:
        for q in outside:
            detour = single_detour(p, q)
            if detour is not None:
                return OptimalFaceEdgeWitness(
                    p, q, detour[0], detour[1], optimum, len(optimal)
                )
    raise RuntimeError(
        "optimal face crosses the prefix partition but no single-detour edge "
        "witness was found"
    )
