"""Polynomial frozen-comparator lower certificate."""
from __future__ import annotations

from dataclasses import dataclass
from math import inf, isfinite
from typing import Any, Sequence

import numpy as np
from scipy.optimize import linprog

from .graph import PrefixDeviationGraph, build_prefix_deviation_graph
from .model import Path, WWInstance, outside_paths, path_coefficients, path_cost, validate_complete_path
from .pairwise import path_pairwise_radius


@dataclass(frozen=True)
class FrozenCertificateResult:
    radius: float
    safe_radius: float
    outside_path: Path | None
    revised_demand: np.ndarray | None
    interval_left: float | None
    interval_right: float | None
    status: str
    lp_status: int | None
    lp_message: str | None
    witness_difference: float | None
    intervals_checked: int
    graph_nodes: int
    graph_arcs: int
    numerical_safety_margin: float


def _safe_value(value: float, tol: float) -> tuple[float, float]:
    if not isfinite(value):
        return value, 0.0
    margin = max(10.0 * tol, 10.0 * tol * (1.0 + abs(value)))
    return max(0.0, value - margin), margin


def _interval_arc_data(
    instance: WWInstance,
    graph: PrefixDeviationGraph,
    beta_star: np.ndarray,
    left: float,
    *,
    tol: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return path-additive ``a,b`` with worst gap ``a(P)-kappa*-r b(P)``."""
    a = np.zeros(len(graph.arcs), dtype=float)
    b = np.zeros(len(graph.arcs), dtype=float)
    floor_breakpoint = instance.weights * (instance.demand - instance.floor)
    for arc in graph.arcs:
        i, j = arc.physical_i, arc.physical_j
        intercept = float(instance.K[i])
        slope = 0.0
        for t in range(i, j):
            coefficient = float(instance.q[i] - beta_star[t])
            if coefficient < -tol:
                intercept += coefficient * instance.demand[t]
                slope += (-coefficient) / instance.weights[t]
            elif coefficient > tol:
                if floor_breakpoint[t] <= left + tol:
                    intercept += coefficient * instance.floor[t]
                else:
                    intercept += coefficient * instance.demand[t]
                    slope += coefficient / instance.weights[t]
        a[arc.idx] = intercept
        b[arc.idx] = slope
    return a, b


def _charnes_cooper_ratio(
    graph: PrefixDeviationGraph,
    a: np.ndarray,
    b: np.ndarray,
    kappa_star: float,
) -> tuple[float | None, Any]:
    """Minimise ``(a x-kappa*)/(b x)`` over outside path flows with ``b x>0``."""
    E = len(graph.arcs)
    N, h, _ = graph.incidence_without_sink()
    # y = tau x.  Acyclicity implies tau>0: if tau=0 then N y=0,
    # y>=0, and source-removal in the DAG forces y=0, contradicting b y=1.
    A_eq = np.zeros((N.shape[0] + 1, E + 1), dtype=float)
    A_eq[:-1, :E] = N
    A_eq[:-1, E] = -h
    A_eq[-1, :E] = b
    rhs = np.zeros(N.shape[0] + 1, dtype=float)
    rhs[-1] = 1.0
    objective = np.concatenate([a, [-kappa_star]])
    result = linprog(
        objective,
        A_eq=A_eq,
        b_eq=rhs,
        bounds=[(0.0, None)] * (E + 1),
        method="highs",
    )
    if not result.success:
        return None, result
    return float(result.fun), result


def frozen_certificate_lp(
    instance: WWInstance,
    nominal_path: Sequence[int],
    k: int,
    *,
    tol: float = 1e-8,
) -> FrozenCertificateResult:
    """Compute the frozen-comparator lower certificate in polynomial time.

    The returned ``radius`` is the floating-point optimum. ``safe_radius``
    subtracts a disclosed numerical margin and is the value intended for a
    one-sided operational comparison. The theorem in the manuscript concerns
    exact rational arithmetic.
    """
    pstar = validate_complete_path(nominal_path, instance.T)
    graph = build_prefix_deviation_graph(instance, pstar, k)
    if not graph.has_source_sink_path():
        return FrozenCertificateResult(
            inf,
            inf,
            None,
            None,
            None,
            None,
            "no_outside_path",
            None,
            None,
            None,
            0,
            len(graph.nodes),
            len(graph.arcs),
            0.0,
        )

    kappa_star, beta_star = path_coefficients(instance, pstar)
    breakpoints = sorted(
        {
            float(instance.weights[t] * (instance.demand[t] - instance.floor[t]))
            for t in range(instance.T)
            if instance.demand[t] > instance.floor[t] + tol
        }
    )
    endpoints = [0.0, *breakpoints, inf]
    collapsed: list[float] = []
    for value in endpoints:
        if not collapsed:
            collapsed.append(value)
        elif not isfinite(value):
            collapsed.append(value)
        elif abs(value - collapsed[-1]) > tol:
            collapsed.append(value)

    last_lp: Any | None = None
    for idx, (left, right) in enumerate(zip(collapsed, collapsed[1:]), start=1):
        a, b = _interval_arc_data(instance, graph, beta_star, left, tol=tol)
        endpoint_value, endpoint_arcs = graph.shortest_path(a - left * b, tol=tol)
        endpoint_gap = float(endpoint_value - kappa_star)
        if endpoint_gap <= tol:
            outside = graph.physical_path(endpoint_arcs)
            pair = path_pairwise_radius(instance, outside, pstar, tol=tol / 10)
            estimate = float(pair.radius if pair.radius <= left + 100 * tol else left)
            revised = pair.revised_demand if pair.revised_demand is not None else instance.demand.copy()
            witness = float(path_cost(instance, revised, outside) - path_cost(instance, revised, pstar))
            safe, margin = _safe_value(estimate, tol)
            return FrozenCertificateResult(
                estimate,
                safe,
                outside,
                revised,
                left,
                right,
                "finite_at_endpoint",
                None,
                None,
                witness,
                idx,
                len(graph.nodes),
                len(graph.arcs),
                margin,
            )

        ratio, result = _charnes_cooper_ratio(graph, a, b, kappa_star)
        last_lp = result
        if ratio is None:
            # No path has a positive denominator on this interval.
            continue
        if ratio < left - 100 * tol:
            raise RuntimeError(
                f"linear-fractional optimum {ratio} lies below interval left endpoint {left}"
            )
        if ratio <= right + 100 * tol:
            candidate = max(left, float(ratio))
            boundary_value, boundary_arcs = graph.shortest_path(a - candidate * b, tol=1e-7)
            outside = graph.physical_path(boundary_arcs)
            pair = path_pairwise_radius(instance, outside, pstar, tol=tol / 10)
            estimate = float(pair.radius)
            revised = pair.revised_demand
            if (
                not isfinite(estimate)
                or estimate < left - 1e-5
                or estimate > right + 1e-5
                or revised is None
            ):
                estimate = candidate
                revised = None
                witness = float(boundary_value - kappa_star)
                status = "finite_numerical_no_recovered_witness"
            else:
                witness = float(path_cost(instance, revised, outside) - path_cost(instance, revised, pstar))
                status = "finite"
            safe, margin = _safe_value(estimate, tol)
            return FrozenCertificateResult(
                estimate,
                safe,
                outside,
                revised,
                left,
                right,
                status,
                int(result.status),
                str(result.message),
                witness,
                idx,
                len(graph.nodes),
                len(graph.arcs),
                margin,
            )

    return FrozenCertificateResult(
        inf,
        inf,
        None,
        None,
        collapsed[-2] if len(collapsed) >= 2 else 0.0,
        inf,
        "infinite",
        None if last_lp is None else int(last_lp.status),
        None if last_lp is None else str(last_lp.message),
        None,
        len(collapsed) - 1,
        len(graph.nodes),
        len(graph.arcs),
        0.0,
    )


def frozen_certificate_exhaustive(
    instance: WWInstance,
    nominal_path: Sequence[int],
    k: int,
    *,
    tol: float = 1e-10,
) -> FrozenCertificateResult:
    """Exhaustive small-horizon oracle for the frozen comparator."""
    pstar = validate_complete_path(nominal_path, instance.T)
    prefix = pstar[: k + 1]
    best = inf
    best_path: Path | None = None
    best_revision: np.ndarray | None = None
    seen = 0
    for path in outside_paths(instance.T, prefix):
        seen += 1
        result = path_pairwise_radius(instance, path, pstar, tol=tol)
        if result.radius < best:
            best = result.radius
            best_path = path
            best_revision = result.revised_demand
    if seen == 0:
        status = "no_outside_path"
    elif isfinite(best):
        status = "finite"
    else:
        status = "infinite"
    witness = None
    if best_path is not None and best_revision is not None:
        witness = float(
            path_cost(instance, best_revision, best_path)
            - path_cost(instance, best_revision, pstar)
        )
    safe, margin = _safe_value(best, tol)
    return FrozenCertificateResult(
        best,
        safe,
        best_path,
        best_revision,
        None,
        None,
        status,
        None,
        None,
        witness,
        0,
        0,
        0,
        margin,
    )
