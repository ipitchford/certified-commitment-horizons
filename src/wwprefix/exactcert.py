"""Exact rational certification layer.

Every value labelled ``certified`` in this module is computed, or a
posteriori verified, in exact rational arithmetic (``fractions.Fraction``)
with **zero tolerances**.  Binary floating-point inputs parsed from JSON are
converted to rationals exactly, so the layer decides the mathematical
problem defined by the numbers actually supplied.

Design: floating point may *search* (scipy LPs propose witnesses and dual
mixtures) but may never *decide*.  Decisions -- zero tests, saturation,
breakpoints, tie topology, infinity -- are exact.  Anything the exact layer
cannot re-verify is reported as unresolved rather than silently promoted.

Certificates emitted here are self-contained: a witness demand vector, an
outside path, and (for upper bounds against the moving inside continuation)
an inside-path mixture.  ``scripts/check_certificate.py`` is a separately
implemented producer-side checker that re-verifies them without importing
this package.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

import numpy as np

from .graph import PrefixDeviationGraph, build_prefix_deviation_graph
from .model import (
    Path,
    WWInstance,
    follows_prefix,
    validate_complete_path,
)

Rat = Fraction
# ``None`` encodes +infinity for exact radii throughout this module.
OptRat = Fraction | None


class CertificationError(RuntimeError):
    """An exact internal invariant failed.  Never downgraded to a warning."""


def _fr(x: object) -> Rat:
    """Exact rational from a binary float, int, Fraction or numeric string."""
    if isinstance(x, Fraction):
        return x
    if isinstance(x, (int, np.integer)):
        return Fraction(int(x))
    if isinstance(x, (float, np.floating)):
        return Fraction(float(x))
    if isinstance(x, str):
        return Fraction(x)
    raise TypeError(f"cannot convert {type(x)!r} to Fraction")


def rat_str(x: OptRat) -> str | None:
    return None if x is None else f"{x.numerator}/{x.denominator}"


def rat_float(x: OptRat) -> float:
    return float("inf") if x is None else float(x)


def _lt(a: OptRat, b: OptRat) -> bool:
    """a < b on Fraction-with-infinity (None = +infinity)."""
    if a is None:
        return False
    if b is None:
        return True
    return a < b


@dataclass(frozen=True)
class ExactInstance:
    """Rational mirror of :class:`WWInstance` with strict exact validation."""

    K: tuple[Rat, ...]
    q: tuple[Rat, ...]
    demand: tuple[Rat, ...]
    floor: tuple[Rat, ...]
    weights: tuple[Rat, ...]

    @classmethod
    def from_rationals(
        cls,
        K: Sequence[object],
        q: Sequence[object],
        demand: Sequence[object],
        floor: Sequence[object] | None = None,
        weights: Sequence[object] | None = None,
    ) -> "ExactInstance":
        Kr = tuple(_fr(v) for v in K)
        qr = tuple(_fr(v) for v in q)
        d = tuple(_fr(v) for v in demand)
        if not (len(Kr) == len(qr) == len(d)) or not d:
            raise ValueError("K, q and demand must have equal positive lengths")
        ell = tuple([Fraction(0)] * len(d)) if floor is None else tuple(_fr(v) for v in floor)
        w = tuple([Fraction(1)] * len(d)) if weights is None else tuple(_fr(v) for v in weights)
        if len(ell) != len(d) or len(w) != len(d):
            raise ValueError("floor and weights must match demand")
        if any(v < 0 for v in Kr):
            raise ValueError("exact layer: setup costs must be non-negative")
        if any(v < 0 for v in ell):
            raise ValueError("exact layer: demand floors must be non-negative")
        if any(a < b for a, b in zip(d, ell)):
            raise ValueError("exact layer: nominal demand must lie weakly above the floor")
        if any(v <= 0 for v in w):
            raise ValueError("exact layer: weights must be strictly positive")
        if any(qr[t] < qr[t + 1] for t in range(len(qr) - 1)):
            raise ValueError(
                "exact layer: reduced slopes q must be exactly non-increasing; "
                "the supplied instance violates the ordering at machine precision"
            )
        return cls(Kr, qr, d, ell, w)

    @classmethod
    def from_ww(cls, instance: WWInstance) -> "ExactInstance":
        return cls.from_rationals(
            list(instance.K),
            list(instance.q),
            list(instance.demand),
            list(instance.floor),
            list(instance.weights),
        )

    @property
    def T(self) -> int:
        return len(self.demand)


def exact_path_coefficients(inst: ExactInstance, path: Sequence[int]) -> tuple[Rat, list[Rat]]:
    p = tuple(int(v) for v in path)
    if len(p) < 2 or any(i >= j for i, j in zip(p, p[1:])):
        raise ValueError("path or prefix must contain increasing nodes")
    if p[0] < 0 or p[-1] > inst.T:
        raise ValueError("path nodes lie outside the horizon")
    beta = [Fraction(0)] * inst.T
    kappa = Fraction(0)
    for i, j in zip(p, p[1:]):
        kappa += inst.K[i]
        for t in range(i, j):
            beta[t] = inst.q[i]
    return kappa, beta


def exact_path_cost(inst: ExactInstance, demand: Sequence[Rat], path: Sequence[int]) -> Rat:
    kappa, beta = exact_path_coefficients(inst, path)
    return kappa + sum((b * d for b, d in zip(beta, demand)), Fraction(0))


def exact_weighted_distance(inst: ExactInstance, demand: Sequence[Rat]) -> Rat:
    return max(
        (w * abs(d - dn) for w, d, dn in zip(inst.weights, demand, inst.demand)),
        default=Fraction(0),
    )


def exact_shortest_path(
    inst: ExactInstance,
    demand: Sequence[Rat] | None = None,
    *,
    start: int = 0,
) -> tuple[Rat, Path]:
    """Exact suffix shortest path with the deterministic tie-break of
    :func:`wwprefix.model.shortest_path` (fewer arcs, then lexicographic)."""
    d = tuple(inst.demand if demand is None else demand)
    T = inst.T
    if start == T:
        return Fraction(0), (T,)
    if not (0 <= start < T):
        raise ValueError("start must lie in 0,...,T")
    D = [Fraction(0)]
    for v in d:
        D.append(D[-1] + v)
    value: list[OptRat] = [None] * (T + 1)
    paths: list[Path | None] = [None] * (T + 1)
    value[start] = Fraction(0)
    paths[start] = (start,)
    for j in range(start + 1, T + 1):
        best: OptRat = None
        best_path: Path | None = None
        for i in range(start, j):
            if paths[i] is None:
                continue
            cand = value[i] + inst.K[i] + inst.q[i] * (D[j] - D[i])
            cand_path = (*paths[i], j)
            if (
                best_path is None
                or cand < best
                or (cand == best and (len(cand_path), cand_path) < (len(best_path), best_path))
            ):
                best = cand
                best_path = cand_path
        value[j] = best
        paths[j] = best_path
    if paths[T] is None or value[T] is None:
        raise CertificationError("complete lot-sizing DAG unexpectedly has no path")
    return value[T], paths[T]


def exact_constrained_inside_value(
    inst: ExactInstance,
    demand: Sequence[Rat],
    prefix: Sequence[int],
) -> tuple[Rat, Path]:
    pref = tuple(int(v) for v in prefix)
    prefix_value = exact_path_cost(inst, demand, pref)
    suffix_value, suffix = exact_shortest_path(inst, demand, start=pref[-1])
    return prefix_value + suffix_value, (*pref, *suffix[1:])


def exact_optimal_arc_dag(inst: ExactInstance) -> dict[int, tuple[int, ...]]:
    """Arcs lying on *exactly* optimal complete paths (zero-tolerance)."""
    T = inst.T
    D = [Fraction(0)]
    for v in inst.demand:
        D.append(D[-1] + v)
    forward: list[OptRat] = [None] * (T + 1)
    forward[0] = Fraction(0)
    for j in range(1, T + 1):
        forward[j] = min(
            forward[i] + inst.K[i] + inst.q[i] * (D[j] - D[i]) for i in range(j)
        )
    backward: list[OptRat] = [None] * (T + 1)
    backward[T] = Fraction(0)
    for i in range(T - 1, -1, -1):
        backward[i] = min(
            inst.K[i] + inst.q[i] * (D[j] - D[i]) + backward[j] for j in range(i + 1, T + 1)
        )
    optimum = forward[T]
    out: dict[int, list[int]] = {i: [] for i in range(T)}
    for i in range(T):
        for j in range(i + 1, T + 1):
            if forward[i] + inst.K[i] + inst.q[i] * (D[j] - D[i]) + backward[j] == optimum:
                out[i].append(j)
    return {i: tuple(v) for i, v in out.items()}


def exact_common_optimal_prefix(inst: ExactInstance) -> Path:
    dag = exact_optimal_arc_dag(inst)
    node = 0
    prefix = [0]
    while node < inst.T:
        successors = dag.get(node, ())
        if len(successors) != 1:
            break
        node = successors[0]
        prefix.append(node)
        if node == inst.T:
            break
    return tuple(prefix)


def exact_count_optimal_paths(inst: ExactInstance, *, cap: int | None = None) -> int:
    dag = exact_optimal_arc_dag(inst)
    counts = [0] * (inst.T + 1)
    counts[inst.T] = 1
    for i in range(inst.T - 1, -1, -1):
        total = sum(counts[j] for j in dag.get(i, ()))
        if cap is not None:
            total = min(total, cap)
        counts[i] = total
    return int(counts[0])


def exact_verify_nominal_optimal(inst: ExactInstance, path: Sequence[int]) -> bool:
    optimum, _ = exact_shortest_path(inst)
    return exact_path_cost(inst, inst.demand, path) == optimum


# ---------------------------------------------------------------------------
# Exact floor-aware halfspace radius (shared primitive)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExactHalfspaceResult:
    """inf{r >= 0 : min over the floor-truncated box of gap + c.(d-dhat) <= 0}.

    ``radius is None`` encodes a *proven* infinite radius.  A finite radius
    carries an exactly verified witness demand achieving the tie.
    """

    radius: OptRat
    gap: Rat
    witness: tuple[Rat, ...] | None
    status: str  # nominal_tie | finite | proven_infinite


def exact_halfspace_radius(
    inst: ExactInstance,
    gap: Rat,
    coefficients: Sequence[Rat],
) -> ExactHalfspaceResult:
    """Exact breakpoint walk for the fixed affine half-space distance.

    ``coefficients`` is the direction ``c`` such that moving demand from the
    nominal changes the affine gap by ``c.(d - dhat)``; positive entries can
    reduce the gap only down to the floor, negative entries reduce it
    without bound at rate ``|c_t|/w_t``.
    """
    c = [_fr(v) for v in coefficients]
    if len(c) != inst.T:
        raise ValueError("coefficient vector has the wrong length")
    if gap <= 0:
        return ExactHalfspaceResult(Fraction(0), gap, tuple(inst.demand), "nominal_tie")
    slack = [d - e for d, e in zip(inst.demand, inst.floor)]
    if all(v == 0 for v in c):
        return ExactHalfspaceResult(None, gap, None, "proven_infinite")

    breakpoints = sorted({inst.weights[t] * slack[t] for t in range(inst.T) if c[t] > 0 and slack[t] > 0})
    left = Fraction(0)
    reduction_left = Fraction(0)
    intervals: list[OptRat] = [*breakpoints, None]
    for right in intervals:
        slope = Fraction(0)
        for t in range(inst.T):
            if c[t] > 0 and inst.weights[t] * slack[t] > left:
                slope += c[t] / inst.weights[t]
            elif c[t] < 0:
                slope += (-c[t]) / inst.weights[t]
        if reduction_left >= gap:
            # Exactness invariant: the walk always terminates in the interval
            # where the reduction first reaches the gap, so equality holds.
            if reduction_left != gap:
                raise CertificationError("halfspace walk overshot the gap")
            radius = left
            witness = _halfspace_witness(inst, c, radius)
            _check_halfspace_witness(inst, gap, c, radius, witness)
            return ExactHalfspaceResult(radius, gap, witness, "finite")
        if slope > 0:
            candidate = left + (gap - reduction_left) / slope
            if right is None or candidate <= right:
                radius = candidate
                witness = _halfspace_witness(inst, c, radius)
                _check_halfspace_witness(inst, gap, c, radius, witness)
                return ExactHalfspaceResult(radius, gap, witness, "finite")
        if right is None:
            break
        reduction_left += slope * (right - left)
        left = right
    return ExactHalfspaceResult(None, gap, None, "proven_infinite")


def _halfspace_witness(inst: ExactInstance, c: Sequence[Rat], radius: Rat) -> tuple[Rat, ...]:
    revised = list(inst.demand)
    for t in range(inst.T):
        if c[t] > 0:
            step = min(radius / inst.weights[t], inst.demand[t] - inst.floor[t])
            revised[t] = inst.demand[t] - step
        elif c[t] < 0:
            revised[t] = inst.demand[t] + radius / inst.weights[t]
    return tuple(revised)


def _check_halfspace_witness(
    inst: ExactInstance,
    gap: Rat,
    c: Sequence[Rat],
    radius: Rat,
    witness: Sequence[Rat],
) -> None:
    if any(d < e for d, e in zip(witness, inst.floor)):
        raise CertificationError("halfspace witness violates the demand floor")
    if exact_weighted_distance(inst, witness) > radius:
        raise CertificationError("halfspace witness exceeds the claimed radius")
    achieved = gap + sum(
        (cv * (dv - dn) for cv, dv, dn in zip(c, witness, inst.demand)), Fraction(0)
    )
    if achieved > 0:
        raise CertificationError("halfspace witness fails to close the gap exactly")


def exact_pairwise_radius(
    inst: ExactInstance,
    competitor: Sequence[int],
    comparator: Sequence[int],
) -> ExactHalfspaceResult:
    """Exact distance until ``competitor`` ties the *fixed* ``comparator``."""
    k_q, beta_q = exact_path_coefficients(inst, competitor)
    k_p, beta_p = exact_path_coefficients(inst, comparator)
    # The gap falls when the difference C_Q - C_P falls, i.e. along -b.
    b = [bq - bp for bq, bp in zip(beta_q, beta_p)]
    gap = (k_q - k_p) + sum((bv * d for bv, d in zip(b, inst.demand)), Fraction(0))
    return exact_halfspace_radius(inst, gap, b)


# ---------------------------------------------------------------------------
# Exact frozen-comparator certificate via parametric shortest paths
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExactFrozenResult:
    radius: OptRat
    outside_path: Path | None
    witness: tuple[Rat, ...] | None
    witness_distance: OptRat
    status: str
    # finite | zero_radius | proven_infinite_no_outside_path |
    # proven_infinite_saturation
    residual_gap: OptRat  # for proven_infinite_saturation: certified min gap
    intervals_inspected: int
    newton_iterations: int
    graph_nodes: int
    graph_arcs: int


def _deviation_arc_data(
    inst: ExactInstance,
    graph: PrefixDeviationGraph,
    beta_star: Sequence[Rat],
    sat_le: Rat,
) -> tuple[list[Rat], list[Rat]]:
    """Exact per-arc (a, b) for the interval whose saturated set is
    {t : w_t (dhat_t - floor_t) <= sat_le}.  ``a - r b`` is the minimal gap of
    the arc's contribution over the box at radius ``r`` in the interval."""
    T = inst.T
    slack = [d - e for d, e in zip(inst.demand, inst.floor)]
    saturated = [inst.weights[t] * slack[t] <= sat_le for t in range(T)]
    # Per-tail prefix sums so each arc costs O(1).
    zero = Fraction(0)
    a_pre: dict[int, list[Rat]] = {}
    b_pre: dict[int, list[Rat]] = {}
    tails = sorted({arc.physical_i for arc in graph.arcs})
    for i in tails:
        arow = [zero] * (T + 1)
        brow = [zero] * (T + 1)
        acc_a, acc_b = zero, zero
        for t in range(T):
            if t >= i:
                c = inst.q[i] - beta_star[t]
                if c > 0:
                    if saturated[t]:
                        acc_a += c * inst.floor[t]
                    else:
                        acc_a += c * inst.demand[t]
                        acc_b += c / inst.weights[t]
                elif c < 0:
                    acc_a += c * inst.demand[t]
                    acc_b += (-c) / inst.weights[t]
            arow[t + 1] = acc_a
            brow[t + 1] = acc_b
        a_pre[i] = arow
        b_pre[i] = brow
    a = [zero] * len(graph.arcs)
    b = [zero] * len(graph.arcs)
    for arc in graph.arcs:
        i, j = arc.physical_i, arc.physical_j
        a[arc.idx] = inst.K[i] + a_pre[i][j] - a_pre[i][i]
        b[arc.idx] = b_pre[i][j] - b_pre[i][i]
        if b[arc.idx] < 0:
            raise CertificationError("negative parametric slope on a deviation arc")
    return a, b


def _graph_shortest_exact(
    graph: PrefixDeviationGraph,
    costs: Sequence[Rat],
) -> tuple[Rat, tuple[int, ...]]:
    """Exact DAG shortest path over the deviation graph (zero tolerance)."""
    out = graph.outgoing
    dist: dict[object, OptRat] = {node: None for node in graph.nodes}
    chosen: dict[object, tuple[int, ...] | None] = {node: None for node in graph.nodes}
    dist[graph.source] = Fraction(0)
    chosen[graph.source] = ()
    for node in graph.topological_nodes():
        current = chosen[node]
        if current is None:
            continue
        for arc in out[node]:
            cand = dist[node] + costs[arc.idx]
            cand_ids = (*current, arc.idx)
            incumbent = chosen[arc.head]
            if incumbent is None or cand < dist[arc.head] or (
                cand == dist[arc.head] and cand_ids < incumbent
            ):
                dist[arc.head] = cand
                chosen[arc.head] = cand_ids
    ids = chosen[graph.sink]
    if ids is None:
        raise CertificationError("deviation graph shortest-path pass failed to reach the sink")
    return dist[graph.sink], ids


def _frozen_witness(
    inst: ExactInstance,
    beta_star: Sequence[Rat],
    outside: Path,
    radius: Rat,
) -> tuple[Rat, ...]:
    """Full adversarial move for the exposed outside path at ``radius``."""
    _, beta_q = exact_path_coefficients(inst, outside)
    c = [bq - bs for bq, bs in zip(beta_q, beta_star)]
    return _halfspace_witness(inst, c, radius)


def exact_frozen_certificate(
    inst: ExactInstance,
    nominal_path: Sequence[int],
    k: int,
) -> ExactFrozenResult:
    """Exact frozen-comparator radius: min over outside paths of the exact
    pairwise radius against the fixed nominal path.

    The released implementation uses a finite exact parametric shortest-path
    procedure.  The manuscript's separate Charnes--Cooper construction proves
    polynomial-time computability; no polynomial iteration bound is claimed
    for this implementation.
    """
    pstar = validate_complete_path(nominal_path, inst.T)
    graph = build_prefix_deviation_graph(_as_ww_stub(inst), pstar, k)
    if not graph.has_source_sink_path():
        return ExactFrozenResult(
            None, None, None, None, "proven_infinite_no_outside_path",
            None, 0, 0, len(graph.nodes), len(graph.arcs),
        )
    kappa_star, beta_star = exact_path_coefficients(inst, pstar)
    slack = [d - e for d, e in zip(inst.demand, inst.floor)]
    breakpoints = sorted({inst.weights[t] * slack[t] for t in range(inst.T) if slack[t] > 0})

    def F_at(r: Rat, sat_le: Rat) -> tuple[Rat, tuple[int, ...]]:
        a, b = _deviation_arc_data(inst, graph, beta_star, sat_le)
        costs = [a[e] - r * b[e] for e in range(len(graph.arcs))]
        value, ids = _graph_shortest_exact(graph, costs)
        return value - kappa_star, ids

    inspected = 0

    # r = 0: the minimal nominal gap over outside paths.
    zero = Fraction(0)
    gap0, ids0 = F_at(zero, zero)
    inspected += 1
    if gap0 < 0:
        raise CertificationError(
            "an outside path is exactly cheaper than the supplied nominal path "
            "at the nominal demand; the nominal path is not exactly optimal"
        )
    if gap0 == 0:
        outside = graph.physical_path(ids0)
        return ExactFrozenResult(
            zero, outside, tuple(inst.demand), zero, "zero_radius",
            None, inspected, 0, len(graph.nodes), len(graph.arcs),
        )

    # Binary search over breakpoints for the first with F <= 0 (F is globally
    # non-increasing in r).  Evaluating at a breakpoint may use either
    # adjacent interval's data; contributions agree there exactly.
    lo, hi = 0, len(breakpoints) - 1
    crossing_index: int | None = None
    while lo <= hi:
        mid = (lo + hi) // 2
        r_mid = breakpoints[mid]
        sat_le = breakpoints[mid - 1] if mid > 0 else zero
        value, _ = F_at(r_mid, sat_le)
        inspected += 1
        if value <= 0:
            crossing_index = mid
            hi = mid - 1
        else:
            lo = mid + 1

    if crossing_index is not None:
        interval_left = breakpoints[crossing_index - 1] if crossing_index > 0 else zero
        sat_le = interval_left
        a, b = _deviation_arc_data(inst, graph, beta_star, sat_le)
        costs = [a[e] - breakpoints[crossing_index] * b[e] for e in range(len(graph.arcs))]
        value_n, ids_n = _graph_shortest_exact(graph, costs)
        value_n -= kappa_star
        r_n = breakpoints[crossing_index]
        inspected += 1
        if value_n > 0:
            raise CertificationError("crossing interval lost the root during refinement")
    else:
        # No breakpoint reaches zero; the crossing, if any, lies in the final
        # unbounded interval where every saturable coordinate is saturated.
        interval_left = breakpoints[-1] if breakpoints else zero
        sat_le = interval_left
        a, b = _deviation_arc_data(inst, graph, beta_star, sat_le)
        neg_max_b, ids_maxb = _graph_shortest_exact(graph, [-v for v in b])
        if neg_max_b == 0:
            residual, _ = F_at(interval_left, sat_le)
            inspected += 1
            if residual <= 0:
                raise CertificationError("final-interval residual contradicts the breakpoint scan")
            return ExactFrozenResult(
                None, None, None, None, "proven_infinite_saturation",
                residual, inspected, 0, len(graph.nodes), len(graph.arcs),
            )
        # Seed from the maximum-slope path: its own root bounds the crossing.
        av = sum((a[e] for e in ids_maxb), Fraction(0)) - kappa_star
        bv = sum((b[e] for e in ids_maxb), Fraction(0))
        if bv <= 0:
            raise CertificationError("final interval has a root but no positive slope")
        r_n = av / bv
        if r_n < interval_left:
            raise CertificationError("final-interval seed fell below the interval")
        value_n, ids_n = F_at(r_n, sat_le)
        inspected += 1
        if value_n > 0:
            raise CertificationError("final-interval seed does not bracket the root")

    # Newton (Dinkelbach) descent inside the crossing interval.  Starting
    # from a point with F <= 0, iterates decrease monotonically to the first
    # crossing and terminate exactly because there are finitely many pieces.
    def piece(ids: tuple[int, ...]) -> tuple[Rat, Rat]:
        av = sum((a[e] for e in ids), Fraction(0)) - kappa_star
        bv = sum((b[e] for e in ids), Fraction(0))
        return av, bv

    # Every strict Newton step selects a new active source--sink path.  The
    # graph is acyclic, so its exact source--sink path count is a finite (and
    # potentially exponential) correctness bound.  This replaces the former
    # arbitrary engineering cap; it is deliberately not described as a
    # polynomial complexity bound.
    path_counts = {node: 0 for node in graph.nodes}
    path_counts[graph.source] = 1
    outgoing = graph.outgoing
    for node in graph.topological_nodes():
        for arc in outgoing[node]:
            path_counts[arc.head] += path_counts[node]
    max_iterations = path_counts[graph.sink]
    if max_iterations <= 0:
        raise CertificationError("deviation graph unexpectedly has no source-sink path")

    iterations = 0
    while value_n != 0:
        iterations += 1
        if iterations > max_iterations:
            raise CertificationError(
                "parametric Newton exceeded the finite source-sink path bound"
            )
        av, bv = piece(ids_n)
        if bv <= 0:
            raise CertificationError(
                "active piece with non-positive slope encountered strictly below zero"
            )
        r_next = av / bv
        if r_next >= r_n:
            raise CertificationError("parametric Newton failed to decrease")
        r_n = r_next
        value_n, ids_n = F_at(r_n, sat_le)
        inspected += 1
    if r_n <= interval_left:
        raise CertificationError("parametric root escaped its interval")

    outside = graph.physical_path(ids_n)
    witness = _frozen_witness(inst, beta_star, outside, r_n)
    # Independent exact checks of the certificate.
    diff = exact_path_cost(inst, witness, outside) - exact_path_cost(inst, witness, pstar)
    if diff != 0:
        raise CertificationError("frozen witness does not tie the nominal path exactly")
    if any(d < e for d, e in zip(witness, inst.floor)):
        raise CertificationError("frozen witness violates the demand floor")
    distance = exact_weighted_distance(inst, witness)
    if distance > r_n:
        raise CertificationError("frozen witness exceeds the certified radius")
    cross = exact_pairwise_radius(inst, outside, pstar)
    if cross.radius != r_n:
        raise CertificationError("pairwise cross-check disagrees with the parametric root")
    return ExactFrozenResult(
        r_n, outside, witness, distance, "finite",
        None, inspected, iterations, len(graph.nodes), len(graph.arcs),
    )


def _as_ww_stub(inst: ExactInstance) -> WWInstance:
    """Float stub used only for combinatorial graph construction."""
    return WWInstance(
        np.asarray([float(v) for v in inst.K], dtype=float),
        np.asarray([float(v) for v in inst.q], dtype=float),
        np.asarray([float(v) for v in inst.demand], dtype=float),
        np.asarray([float(v) for v in inst.floor], dtype=float),
        np.asarray([float(v) for v in inst.weights], dtype=float),
    )


# ---------------------------------------------------------------------------
# Certified upper bounds and the exact bracket
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CertifiedWitness:
    radius: Rat
    demand: tuple[Rat, ...]
    outside_path: Path
    inside_path: Path
    margin: Rat  # inside value minus outside value at the witness (>= 0)


def certify_strong_witness(
    inst: ExactInstance,
    prefix: Sequence[int],
    outside: Sequence[int],
    demand: Sequence[Rat],
) -> CertifiedWitness | None:
    """Exactly verify that ``demand`` makes ``outside`` at least tie the best
    prefix-retaining continuation.  Returns None when verification fails."""
    d = tuple(_fr(v) for v in demand)
    if any(v < e for v, e in zip(d, inst.floor)):
        return None
    inside_value, inside_path = exact_constrained_inside_value(inst, d, prefix)
    outside_value = exact_path_cost(inst, d, tuple(int(v) for v in outside))
    if outside_value > inside_value:
        return None
    return CertifiedWitness(
        exact_weighted_distance(inst, d),
        d,
        tuple(int(v) for v in outside),
        inside_path,
        inside_value - outside_value,
    )


def _repair_ladder(
    inst: ExactInstance,
    prefix: Sequence[int],
    outside: Sequence[int],
    demand: Sequence[float | Rat],
) -> CertifiedWitness | None:
    """Try the proposed float witness, then slightly inflated moves."""
    base = [_fr(v) for v in demand]
    for scale_exp in (None, -40, -24, -12, -6):
        if scale_exp is None:
            candidate = list(base)
        else:
            factor = 1 + Fraction(1, 2 ** (-scale_exp))
            candidate = [
                dn + factor * (v - dn) for v, dn in zip(base, inst.demand)
            ]
        candidate = [max(v, e) for v, e in zip(candidate, inst.floor)]
        witness = certify_strong_witness(inst, prefix, outside, candidate)
        if witness is not None:
            return witness
    return None


@dataclass(frozen=True)
class ExactBracketResult:
    lower_radius: OptRat            # certified lower bound on the strong radius
    upper_radius: OptRat            # certified upper bound (witness-backed)
    exact_radius: OptRat            # set only when certified exactly
    exact_certified: bool
    exact_reason: str | None
    frozen: ExactFrozenResult
    closure_holds: bool | None
    upper_witness: CertifiedWitness | None
    upper_float_estimate: float | None  # uncertified diagnostic only
    status: str
    # exact_infinite_no_outside_path | exact_infinite_saturation |
    # exact_finite | finite_bracket_certified_ends | lower_only_certified


def exact_polynomial_bracket(
    inst: ExactInstance,
    nominal_path: Sequence[int],
    k: int,
    *,
    attempt_float_upper: bool = True,
) -> ExactBracketResult:
    pstar = validate_complete_path(nominal_path, inst.T)
    prefix = pstar[: k + 1]
    frozen = exact_frozen_certificate(inst, pstar, k)

    if frozen.status == "proven_infinite_no_outside_path":
        return ExactBracketResult(
            None, None, None, True,
            "no path can leave the protected prefix",
            frozen, None, None, None, "exact_infinite_no_outside_path",
        )
    if frozen.status == "proven_infinite_saturation":
        return ExactBracketResult(
            None, None, None, True,
            "even at maximal admissible reduction every outside path retains "
            "a certified positive gap to the nominal comparator",
            frozen, None, None, None, "exact_infinite_saturation",
        )

    assert frozen.radius is not None and frozen.outside_path is not None
    assert frozen.witness is not None

    closure = certify_strong_witness(inst, prefix, frozen.outside_path, frozen.witness)
    if closure is not None:
        if closure.radius > frozen.radius:
            raise CertificationError("closure witness exceeds the frozen radius")
        if closure.radius < frozen.radius:
            raise CertificationError(
                "closure witness destabilises strictly below the certified lower bound"
            )
        return ExactBracketResult(
            frozen.radius, frozen.radius, frozen.radius, True,
            "the exact frozen witness also ties or beats the best "
            "prefix-retaining continuation",
            frozen, True, closure, None, "exact_finite",
        )

    upper_witness: CertifiedWitness | None = None
    upper_float: float | None = None
    if attempt_float_upper:
        from .exact import fixed_competitor_inverse_lp

        proposal = fixed_competitor_inverse_lp(
            _as_ww_stub(inst), pstar, k, frozen.outside_path
        )
        lp_demand = None if proposal.revised_demand is None else list(proposal.revised_demand)
        if lp_demand is not None:
            upper_float = float(proposal.radius)
        certificate = certify_disjunct(
            inst, pstar, prefix, frozen.outside_path, lp_demand, proposal.dual_marginals
        )
        upper_witness = certificate.witness

    if upper_witness is not None and upper_witness.radius == frozen.radius:
        return ExactBracketResult(
            frozen.radius, frozen.radius, frozen.radius, True,
            "a certified strong witness exists exactly at the certified lower bound",
            frozen, False, upper_witness, upper_float, "exact_finite",
        )
    if upper_witness is not None:
        if upper_witness.radius < frozen.radius:
            raise CertificationError("certified upper bound fell below the certified lower bound")
        return ExactBracketResult(
            frozen.radius, upper_witness.radius, None, False, None,
            frozen, False, upper_witness, upper_float,
            "finite_bracket_certified_ends",
        )
    return ExactBracketResult(
        frozen.radius, None, None, False, None,
        frozen, False, None, upper_float, "lower_only_certified",
    )


def exact_triage(bracket: ExactBracketResult, proposed: Rat) -> dict[str, object]:
    """One-sided certified classification of a proposed revision radius."""
    if proposed < 0:
        raise ValueError("proposed radius must be non-negative")
    lower = bracket.lower_radius
    upper = bracket.upper_radius
    if lower is None:
        classification = "certified_no_destabilisation"
        basis = bracket.status
    elif proposed < lower:
        classification = "certified_no_destabilisation"
        basis = "proposed radius lies strictly below the certified exact lower bound"
    elif upper is not None and proposed >= upper:
        classification = "certified_destabilising_witness_exists"
        basis = "an exactly verified witness destabilises within the proposed radius"
    else:
        classification = "unresolved_requires_exact_escalation"
        basis = "the proposed radius lies inside the certified bracket"
    return {
        "radius": float(proposed),
        "radius_exact": rat_str(proposed),
        "classification": classification,
        "basis": basis,
        "strict_boundary_rule": "commit only when proposed_radius < certified lower bound",
    }


# ---------------------------------------------------------------------------
# Dual-mixture lower certificates and certified enumeration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MixtureCertificate:
    inside_paths: tuple[Path, ...]
    weights: tuple[Rat, ...]
    certified_lower: OptRat  # rho(Q) >= this value, exactly


def certify_disjunct_lower_from_mixture(
    inst: ExactInstance,
    competitor: Sequence[int],
    inside_paths: Sequence[Path],
    weights: Sequence[Rat],
) -> MixtureCertificate | None:
    """Exact lower bound on the fixed-competitor radius from an inside-path
    mixture: below the returned value the competitor is strictly beaten by the
    mixture, hence by the best inside continuation."""
    lam = [_fr(v) for v in weights]
    if any(v < 0 for v in lam):
        return None
    total = sum(lam, Fraction(0))
    if total <= 0:
        return None
    lam = [v / total for v in lam]
    k_q, beta_q = exact_path_coefficients(inst, competitor)
    const = k_q
    coeff = list(beta_q)
    for path, weight in zip(inside_paths, lam):
        k_p, beta_p = exact_path_coefficients(inst, path)
        const -= weight * k_p
        for t in range(inst.T):
            coeff[t] -= weight * beta_p[t]
    gap = const + sum((c * d for c, d in zip(coeff, inst.demand)), Fraction(0))
    if gap <= 0:
        return None
    result = exact_halfspace_radius(inst, gap, coeff)
    return MixtureCertificate(tuple(inside_paths), tuple(lam), result.radius)


def _decompose_dual_flow(
    marginals: Sequence[float],
    s: int,
    T: int,
    coupling_dual: float,
) -> list[tuple[Path, float]] | None:
    """Greedy path decomposition of the (approximate) dual flow on the suffix
    DAG.  Returns suffix paths from s to T with positive weights, or None."""
    if coupling_dual <= 1e-12:
        return None
    flow: dict[tuple[int, int], float] = {}
    idx = 0
    for i in range(s, T):
        for j in range(i + 1, T + 1):
            value = -float(marginals[idx]) / coupling_dual
            idx += 1
            if value > 1e-12:
                flow[(i, j)] = value
    paths: list[tuple[Path, float]] = []
    guard = 0
    while True:
        guard += 1
        if guard > 10_000:
            return None
        outgoing = [(arc, f) for arc, f in flow.items() if arc[0] == s and f > 1e-9]
        if not outgoing:
            break
        node = s
        walk: list[int] = [s]
        amount = float("inf")
        while node != T:
            options = [(arc, f) for arc, f in flow.items() if arc[0] == node and f > 1e-9]
            if not options:
                return None
            arc, f = max(options, key=lambda item: item[1])
            amount = min(amount, f)
            node = arc[1]
            walk.append(node)
        for i, j in zip(walk, walk[1:]):
            flow[(i, j)] -= amount
        paths.append((tuple(walk), amount))
    if not paths:
        return None
    return paths


def mixture_from_lp_duals(
    inst: ExactInstance,
    prefix: Sequence[int],
    marginals: Sequence[float] | None,
) -> tuple[list[Path], list[Rat]] | None:
    """Reconstruct an inside-path mixture from the compact LP's dual values."""
    if marginals is None:
        return None
    T = inst.T
    s = tuple(prefix)[-1]
    n_box = 2 * T
    n_potential = (T - s) * (T - s + 1) // 2
    if len(marginals) != n_box + n_potential + 1:
        return None
    coupling_dual = -float(marginals[-1])
    suffix = _decompose_dual_flow(
        marginals[n_box : n_box + n_potential], s, T, coupling_dual
    )
    if suffix is None:
        return None
    inside_paths = [(*tuple(prefix), *walk[1:]) for walk, _ in suffix]
    weights = [
        Fraction(w).limit_denominator(10**12) for _, w in suffix
    ]
    if any(w <= 0 for w in weights):
        return None
    return inside_paths, weights


@dataclass(frozen=True)
class DisjunctCertificate:
    """Certified bounds on the fixed-competitor radius of one outside path."""

    lower: OptRat
    upper: OptRat
    witness: CertifiedWitness | None
    closed: bool


def certify_disjunct(
    inst: ExactInstance,
    pstar: Path,
    prefix: Path,
    qpath: Path,
    lp_demand: Sequence[float] | None,
    lp_marginals: Sequence[float] | None,
) -> DisjunctCertificate:
    """Exactly certified bounds on rho(qpath) against the moving inside
    continuation.

    Lower bounds: the exact pairwise radius against *any* inside comparator
    is valid, because a revision that keeps the competitor strictly above one
    inside path keeps it strictly above the inside minimum.  The comparators
    tried are the nominal path, the binding inside path at the LP witness,
    and (fallback) a dual mixture reconstructed from the LP marginals.

    Upper bounds: exactly verified strong witnesses only.  The preferred
    witness is the exact tie demand of the binding-comparator pairwise
    radius; when that demand also ties or beats the whole inside envelope
    the disjunct closes exactly.
    """
    lower: OptRat = exact_pairwise_radius(inst, qpath, pstar).radius
    upper: OptRat = None
    best_witness: CertifiedWitness | None = None

    def note_upper(witness: CertifiedWitness | None) -> None:
        nonlocal upper, best_witness
        if witness is not None and (upper is None or witness.radius < upper):
            upper = witness.radius
            best_witness = witness

    def note_lower(value: OptRat) -> None:
        nonlocal lower
        if value is None or (lower is not None and value > lower):
            lower = value

    if lp_demand is not None:
        d_rat = tuple(_fr(v) for v in lp_demand)
        d_rat = tuple(max(v, e) for v, e in zip(d_rat, inst.floor))
        _, binding_inside = exact_constrained_inside_value(inst, d_rat, prefix)
        pw = exact_pairwise_radius(inst, qpath, binding_inside)
        if pw.radius is not None and pw.witness is not None:
            note_lower(pw.radius)
            note_upper(certify_strong_witness(inst, prefix, qpath, pw.witness))
        elif pw.radius is None:
            note_lower(None)
        note_upper(_repair_ladder(inst, prefix, qpath, list(lp_demand)))
        if upper is not None and best_witness is not None:
            # The binding comparator at the certified witness can differ from
            # the one at the LP proposal; retry the closure there.
            refined = exact_pairwise_radius(inst, qpath, best_witness.inside_path)
            if refined.radius is not None:
                note_lower(refined.radius)
            elif refined.radius is None and refined.status == "proven_infinite":
                note_lower(None)
        if (lower is not None and upper is not None and lower != upper) or (
            lp_marginals is not None and upper is None
        ):
            mixture = mixture_from_lp_duals(inst, prefix, lp_marginals)
            if mixture is not None:
                cert = certify_disjunct_lower_from_mixture(inst, qpath, *mixture)
                if cert is not None:
                    note_lower(cert.certified_lower)

    if lower is not None and (upper is None or lower < upper):
        # The bounds do not close (typically an LP-infeasible disjunct whose
        # radius is genuinely infinite).  Probe for a separating inside-path
        # mixture at a generous fixed radius and certify whatever it proves.
        from .exact import separating_mixture_probe

        spread = max(
            (float(w * (d - e)) for w, d, e in zip(inst.weights, inst.demand, inst.floor)),
            default=0.0,
        )
        anchor = float(lower) if upper is None else float(upper)
        probe_radius = 4.0 * (1.0 + spread + anchor)
        probe = separating_mixture_probe(
            _as_ww_stub(inst), pstar, len(prefix) - 1, qpath, probe_radius
        )
        mixture = mixture_from_lp_duals(inst, prefix, probe)
        if mixture is not None:
            cert = certify_disjunct_lower_from_mixture(inst, qpath, *mixture)
            if cert is not None:
                note_lower(cert.certified_lower)

    if lower is not None and upper is not None and lower > upper:
        raise CertificationError(
            "certified disjunct lower bound exceeds a certified witness radius"
        )
    closed = (lower is None and upper is None) or (
        lower is not None and upper is not None and lower == upper
    )
    return DisjunctCertificate(lower, upper, best_witness, closed)


@dataclass(frozen=True)
class CertifiedEnumerationResult:
    lower_radius: OptRat
    upper_radius: OptRat
    exact_radius: OptRat
    exact_certified: bool
    witness: CertifiedWitness | None
    paths_total: int
    paths_processed: int
    paths_pruned_exactly: int
    disjuncts_upper_certified: int
    disjuncts_lower_certified: int
    disjuncts_unresolved: int
    status: str


def certified_exact_radius(
    inst: ExactInstance,
    nominal_path: Sequence[int],
    k: int,
    *,
    max_paths: int | None = None,
) -> CertifiedEnumerationResult:
    """Finite disjunction over outside paths with exact pairwise lower bounds
    for ordering/pruning, float LP proposals per disjunct, and exact
    certification of every bound that enters the returned record.

    The returned ``lower_radius`` is the exact minimum, over all outside
    paths, of that path's best certified lower bound; ``upper_radius`` is the
    smallest exactly verified witness radius.  ``exact_certified`` holds only
    when the two coincide as rationals with every disjunct accounted for.
    """
    from .exact import fixed_competitor_inverse_lp
    from .model import outside_paths

    pstar = validate_complete_path(nominal_path, inst.T)
    prefix = pstar[: k + 1]
    stub = _as_ww_stub(inst)

    candidates: list[tuple[OptRat, Path]] = []
    for path in outside_paths(inst.T, prefix):
        pairwise = exact_pairwise_radius(inst, path, pstar)
        candidates.append((pairwise.radius, path))
    total = len(candidates)
    if total == 0:
        return CertifiedEnumerationResult(
            None, None, None, True, None, 0, 0, 0, 0, 0, 0, "no_outside_path",
        )
    finite = sorted(
        [(r, p) for r, p in candidates if r is not None], key=lambda item: (item[0], item[1])
    )
    infinite_count = total - len(finite)

    best_upper: OptRat = None
    best_witness: CertifiedWitness | None = None
    # Certified lower bound per finite candidate, updated as disjuncts run.
    disjunct_lowers: list[OptRat] = [r for r, _ in finite]
    processed = 0
    upper_certified = 0
    lower_improved = 0
    status = "complete"

    for position, (pairwise_lower, qpath) in enumerate(finite):
        if best_upper is not None and pairwise_lower >= best_upper:
            # Exact pairwise bound already proves this and, by sorting, every
            # later disjunct cannot undercut the incumbent witness.
            break
        if max_paths is not None and processed >= max_paths:
            status = "path_limit"
            break
        processed += 1
        proposal = fixed_competitor_inverse_lp(stub, pstar, k, qpath)
        lp_demand = None if proposal.revised_demand is None else list(proposal.revised_demand)
        certificate = certify_disjunct(
            inst, pstar, prefix, qpath, lp_demand, proposal.dual_marginals
        )
        if certificate.witness is not None:
            upper_certified += 1
            if best_upper is None or certificate.witness.radius < best_upper:
                best_upper = certificate.witness.radius
                best_witness = certificate.witness
        if _lt(disjunct_lowers[position], certificate.lower):
            disjunct_lowers[position] = certificate.lower
            lower_improved += 1

    # Assemble the certified global bounds.  Every candidate contributes its
    # best certified lower bound; None encodes a proven infinite disjunct.
    caps = [
        v for v in disjunct_lowers
        if v is not None and (best_upper is None or v < best_upper)
    ]
    if best_upper is None:
        certified_lower_global: OptRat = min(caps) if caps else None
        if not caps and status == "complete":
            return CertifiedEnumerationResult(
                None, None, None, True, None, total, processed,
                infinite_count, upper_certified, lower_improved, 0,
                "proven_infinite",
            )
        return CertifiedEnumerationResult(
            certified_lower_global, None, None, False, None, total, processed,
            infinite_count, upper_certified, lower_improved, len(caps), status,
        )
    certified_lower_global = min(caps) if caps else best_upper
    exact = not caps and status == "complete"
    pruned_exactly = infinite_count + sum(
        1 for v in disjunct_lowers if v is not None and v >= best_upper
    )
    return CertifiedEnumerationResult(
        certified_lower_global,
        best_upper,
        best_upper if exact else None,
        exact,
        best_witness,
        total,
        processed,
        pruned_exactly,
        upper_certified,
        lower_improved,
        len(caps),
        status,
    )
