"""Prefix-to-arc decomposition of the strong radius and the NP verifier.

Local-tie lemma (addendum): for every admissible demand ``d``,

    B_k(d) <= A_k(d)   iff   there is r < k with O_r(d) <= E_r(d),

where, at protected arc ``(v_r, v_{r+1})`` with unconstrained optimal
suffix values ``V``,

    E_r(d) = c_{v_r v_{r+1}}(d) + V_{v_{r+1}}(d),
    O_r(d) = min_{j > v_r, j != v_{r+1}} c_{v_r j}(d) + V_j(d).

``O_r <= E_r`` says the protected Bellman arc at ``v_r`` has ceased to be
compulsory.  The radius corollary takes the weighted distance on both
sides: ``rho_prefix = min_{r<k} rho_r`` where ``rho_r`` depends only on
periods ``v_r, ..., T-1`` and equals the strong radius, with ``k = 1``, of
the suffix sub-instance whose nominal path starts with the protected arc.
Everything here is decided in exact rational arithmetic; the float helper
exists only for fuzzing and diagnostics.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

import numpy as np

from .exactcert import (
    CertifiedEnumerationResult,
    ExactInstance,
    OptRat,
    Rat,
    _fr,
    _lt,
    certified_exact_radius,
    exact_path_cost,
    exact_shortest_path,
    exact_weighted_distance,
)
from .model import (
    FORCED_SOURCE_GRAPH,
    Path,
    WWInstance,
    follows_prefix,
    shortest_path,
    validate_complete_path,
)


def local_tie_gaps(
    instance: WWInstance,
    demand: Sequence[float],
    nominal_path: Sequence[int],
    k: int,
) -> list[tuple[float, float]]:
    """Float ``(O_r, E_r)`` per protected arc; diagnostics only."""
    pstar = validate_complete_path(nominal_path, instance.T)
    if not (1 <= k <= len(pstar) - 1):
        raise ValueError("invalid protected-prefix length k")
    d = np.asarray(demand, dtype=float)
    suffix_value = [shortest_path(instance, d, start=j)[0] for j in range(instance.T + 1)]
    D = np.concatenate(([0.0], np.cumsum(d)))
    gaps: list[tuple[float, float]] = []
    for r in range(k):
        i, protected = pstar[r], pstar[r + 1]
        expected = float(
            instance.K[i] + instance.q[i] * (D[protected] - D[i]) + suffix_value[protected]
        )
        alternatives = [
            float(instance.K[i] + instance.q[i] * (D[j] - D[i]) + suffix_value[j])
            for j in range(i + 1, instance.T + 1)
            if j != protected
        ]
        gaps.append((min(alternatives) if alternatives else float("inf"), expected))
    return gaps


def exact_local_tie_holds(
    inst: ExactInstance,
    demand: Sequence[Rat],
    nominal_path: Sequence[int],
    k: int,
) -> bool:
    """Zero-tolerance test of ``exists r < k: O_r(d) <= E_r(d)``."""
    pstar = validate_complete_path(nominal_path, inst.T)
    if not (1 <= k <= len(pstar) - 1):
        raise ValueError("invalid protected-prefix length k")
    d = tuple(_fr(v) for v in demand)
    D = [Fraction(0)]
    for v in d:
        D.append(D[-1] + v)
    suffix_value = [exact_shortest_path(inst, d, start=j)[0] for j in range(inst.T + 1)]
    for r in range(k):
        i, protected = pstar[r], pstar[r + 1]
        expected = inst.K[i] + inst.q[i] * (D[protected] - D[i]) + suffix_value[protected]
        for j in range(i + 1, inst.T + 1):
            if j == protected:
                continue
            if inst.K[i] + inst.q[i] * (D[j] - D[i]) + suffix_value[j] <= expected:
                return True
    return False


def sub_ww_instance(instance: WWInstance, start: int) -> WWInstance:
    """Suffix sub-instance on periods ``start, ..., T-1`` (zero-based)."""
    if not (0 <= start < instance.T):
        raise ValueError("start must be an interior node with outgoing arcs")
    return WWInstance.create(
        instance.K[start:],
        instance.q[start:],
        instance.demand[start:],
        instance.floor[start:],
        instance.weights[start:],
        semantic_mode=FORCED_SOURCE_GRAPH,
        check_ordered=False,
    )


def sub_exact_instance(inst: ExactInstance, start: int) -> ExactInstance:
    if not (0 <= start < inst.T):
        raise ValueError("start must be an interior node with outgoing arcs")
    return ExactInstance(
        inst.K[start:],
        inst.q[start:],
        inst.demand[start:],
        inst.floor[start:],
        inst.weights[start:],
        FORCED_SOURCE_GRAPH,
    )


def arc_subproblem_path(nominal_path: Sequence[int], r: int) -> Path:
    """Shifted nominal path of the one-arc sub-problem at protected arc ``r``."""
    pstar = tuple(int(v) for v in nominal_path)
    if not (0 <= r <= len(pstar) - 2):
        raise ValueError("r must index a nominal arc")
    start = pstar[r]
    return tuple(v - start for v in pstar[r:])


@dataclass(frozen=True)
class DecomposedRadiusResult:
    """Exact minimum over one-protected-arc sub-problems."""

    lower_radius: OptRat
    upper_radius: OptRat
    exact_radius: OptRat
    exact_certified: bool
    argmin_arc: int | None  # index r of a minimising protected arc
    per_arc: tuple[CertifiedEnumerationResult, ...]
    status: str


def decomposed_certified_radius(
    inst: ExactInstance,
    nominal_path: Sequence[int],
    k: int,
    *,
    max_paths: int | None = None,
    max_candidates: int | None = None,
) -> DecomposedRadiusResult:
    """Certified strong radius via ``rho_prefix = min_{r<k} rho_r``.

    Each ``rho_r`` is computed by :func:`certified_exact_radius` on the
    suffix sub-instance with the single protected arc first.  The overall
    value is exactly certified when a minimising sub-problem is certified
    and every other sub-problem is either certified or carries a certified
    lower bound at or above the minimum.
    """
    pstar = validate_complete_path(nominal_path, inst.T)
    if not (1 <= k <= len(pstar) - 1):
        raise ValueError("invalid protected-prefix length k")
    per_arc: list[CertifiedEnumerationResult] = []
    for r in range(k):
        sub = sub_exact_instance(inst, pstar[r])
        sub_path = arc_subproblem_path(pstar, r)
        per_arc.append(
            certified_exact_radius(
                sub, sub_path, 1, max_paths=max_paths, max_candidates=max_candidates
            )
        )

    upper: OptRat = None
    argmin: int | None = None
    for r, result in enumerate(per_arc):
        if result.upper_radius is not None and _lt(result.upper_radius, upper):
            upper, argmin = result.upper_radius, r

    # Minimum of valid per-arc lower bounds.  A proven-infinite arc
    # contributes +infinity; an arc with nothing certified contributes the
    # trivial bound zero, never a silent skip.
    lower: OptRat = None
    for result in per_arc:
        if result.exact_certified and result.exact_radius is None:
            arc_lower: OptRat = None
        elif result.lower_radius is not None:
            arc_lower = result.lower_radius
        else:
            arc_lower = Fraction(0)
        if _lt(arc_lower, lower):
            lower = arc_lower

    if all(result.status == "refused_by_candidate_guard" for result in per_arc):
        return DecomposedRadiusResult(
            Fraction(0), None, None, False, None, tuple(per_arc), "refused_by_candidate_guard"
        )

    certified = True
    for result in per_arc:
        if result.exact_certified:
            continue
        if upper is not None and result.lower_radius is not None and result.lower_radius >= upper:
            continue
        certified = False
    if upper is None:
        # No sub-problem produced a witness; exact infinity needs every arc
        # certified infinite.
        certified = all(
            result.exact_certified and result.exact_radius is None for result in per_arc
        )
        return DecomposedRadiusResult(
            None if certified else lower,
            None,
            None,
            certified,
            None,
            tuple(per_arc),
            "proven_infinite" if certified else "unresolved",
        )
    return DecomposedRadiusResult(
        upper if certified else lower,
        upper,
        upper if certified else None,
        certified,
        argmin,
        tuple(per_arc),
        "exact_certified" if certified else "certified_interval",
    )


def np_verifier(
    inst: ExactInstance,
    nominal_path: Sequence[int],
    k: int,
    proposed_radius: Rat,
    outside_path: Sequence[int],
    demand: Sequence[Rat],
) -> bool:
    """Polynomial-time exact verifier realising the NP-membership proof.

    Accepts exactly when the certificate ``(outside_path, demand)`` shows
    ``rho_{k,w} <= proposed_radius``: the path must leave the protected
    prefix, the demand must respect floors and the weighted radius box, and
    the outside cost must tie or beat the best prefix-retaining value.  All
    arithmetic is rational; runtime is O(T^2) exact operations.
    """
    pstar = validate_complete_path(nominal_path, inst.T)
    if not (1 <= k <= len(pstar) - 1):
        raise ValueError("invalid protected-prefix length k")
    R = _fr(proposed_radius)
    if R < 0:
        return False
    prefix = pstar[: k + 1]
    qpath = tuple(int(v) for v in outside_path)
    try:
        validate_complete_path(qpath, inst.T)
    except ValueError:
        return False
    if follows_prefix(qpath, prefix):
        return False
    d = tuple(_fr(v) for v in demand)
    if len(d) != inst.T:
        return False
    if any(v < e for v, e in zip(d, inst.floor)):
        return False
    if exact_weighted_distance(inst, d) > R:
        return False
    prefix_value = exact_path_cost(inst, d, prefix)
    suffix_value, _ = exact_shortest_path(inst, d, start=prefix[-1])
    return exact_path_cost(inst, d, qpath) <= prefix_value + suffix_value
