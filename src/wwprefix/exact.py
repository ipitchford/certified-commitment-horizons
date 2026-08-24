"""Exact fixed-competitor, disjunctive and fixed-radius formulations."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import inf, isfinite
from time import perf_counter
from typing import Sequence

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import lil_matrix

from .graph import build_prefix_deviation_graph
from .model import (
    Path,
    WWInstance,
    constrained_inside_path,
    follows_prefix,
    outside_path_count,
    outside_paths,
    path_coefficients,
    path_cost,
    validate_complete_path,
)
from .pairwise import path_pairwise_radius


@dataclass(frozen=True)
class FixedCompetitorResult:
    radius: float
    outside_path: Path
    revised_demand: np.ndarray | None
    inside_path: Path | None
    verified_difference: float | None
    weighted_distance: float | None
    status: str
    solver_status: int
    solver_message: str
    runtime_seconds: float
    # Non-positive scipy marginals of the inequality rows, in construction
    # order (2T box rows, then suffix-potential rows, then the coupling row).
    # Consumed by the exact layer to reconstruct dual mixture certificates.
    dual_marginals: tuple[float, ...] | None = None


@dataclass(frozen=True)
class ExactRadiusResult:
    radius: float
    lower_bound: float
    outside_path: Path | None
    revised_demand: np.ndarray | None
    inside_path: Path | None
    verified_difference: float | None
    paths_total: int
    paths_processed: int
    paths_pruned: int
    infeasible_disjuncts: int
    solver_failures: int
    status: str
    runtime_seconds: float
    candidate_generation_seconds: float = 0.0
    disjunct_solve_seconds: float = 0.0


@dataclass(frozen=True)
class FixedRadiusMILPResult:
    radius: float
    minimum_gap_upper_bound: float | None
    minimum_gap_lower_bound: float | None
    decision: bool | None
    revised_demand: np.ndarray | None
    outside_path: Path | None
    inside_path: Path | None
    verified_difference: float | None
    status: str
    solver_status: int
    solver_message: str
    mip_gap: float | None
    mip_node_count: int | None
    runtime_seconds: float


def fixed_competitor_inverse_lp(
    instance: WWInstance,
    nominal_path: Sequence[int],
    k: int,
    outside_path: Sequence[int],
    *,
    tol: float = 1e-8,
) -> FixedCompetitorResult:
    """Exact LP for one outside path against the moving inside continuation."""
    pstar = validate_complete_path(nominal_path, instance.T)
    qpath = validate_complete_path(outside_path, instance.T)
    if not (1 <= k <= len(pstar) - 1):
        raise ValueError("invalid protected-prefix length k")
    prefix = pstar[: k + 1]
    if follows_prefix(qpath, prefix):
        raise ValueError("outside_path retains the protected prefix")
    s = prefix[-1]
    T = instance.T
    k_q, beta_q = path_coefficients(instance, qpath)
    k_pref, beta_pref = path_coefficients(instance, prefix)

    r_idx = T
    pi_nodes = tuple(range(s, T + 1))
    pi_index = {node: T + 1 + idx for idx, node in enumerate(pi_nodes)}
    nvar = T + 1 + len(pi_nodes)
    objective = np.zeros(nvar, dtype=float)
    objective[r_idx] = 1.0
    bounds: list[tuple[float | None, float | None]] = [
        (float(instance.floor[t]), None) for t in range(T)
    ]
    bounds.append((0.0, None))
    bounds.extend([(None, None)] * len(pi_nodes))

    rows: list[np.ndarray] = []
    rhs: list[float] = []
    for t in range(T):
        row = np.zeros(nvar)
        row[t] = 1.0
        row[r_idx] = -1.0 / instance.weights[t]
        rows.append(row)
        rhs.append(float(instance.demand[t]))

        row = np.zeros(nvar)
        row[t] = -1.0
        row[r_idx] = -1.0 / instance.weights[t]
        rows.append(row)
        rhs.append(float(-instance.demand[t]))

    # pi_j - pi_i <= c_ij(d). With pi_s=0, the greatest feasible pi_T is
    # exactly the shortest suffix-path value from s to T.
    for i in range(s, T):
        for j in range(i + 1, T + 1):
            row = np.zeros(nvar)
            row[i:j] = -instance.q[i]
            row[pi_index[j]] += 1.0
            row[pi_index[i]] -= 1.0
            rows.append(row)
            rhs.append(float(instance.K[i]))

    # C_Q(d) <= C_prefix(d) + pi_T.
    row = np.zeros(nvar)
    row[:T] = beta_q - beta_pref
    row[pi_index[T]] = -1.0
    rows.append(row)
    rhs.append(float(k_pref - k_q))

    A_eq = np.zeros((1, nvar), dtype=float)
    A_eq[0, pi_index[s]] = 1.0
    start = perf_counter()
    result = linprog(
        objective,
        A_ub=np.vstack(rows),
        b_ub=np.asarray(rhs),
        A_eq=A_eq,
        b_eq=np.array([0.0]),
        bounds=bounds,
        method="highs",
    )
    elapsed = perf_counter() - start
    if not result.success:
        status = "infeasible" if result.status == 2 else "solver_failure"
        return FixedCompetitorResult(
            inf,
            qpath,
            None,
            None,
            None,
            None,
            status,
            int(result.status),
            str(result.message),
            elapsed,
        )

    revised = np.asarray(result.x[:T], dtype=float)
    inside_value, inside_path = constrained_inside_path(instance, revised, prefix, tol=tol)
    outside_value = path_cost(instance, revised, qpath)
    verified = float(outside_value - inside_value)
    radius = float(result.fun)
    distance = float(np.max(instance.weights * np.abs(revised - instance.demand)))
    status = "optimal"
    if distance > radius + 5e-6 * (1 + abs(radius)) or verified > 5e-6 * (1 + abs(inside_value)):
        status = "numerical_validation_failure"
    marginals = getattr(getattr(result, "ineqlin", None), "marginals", None)
    return FixedCompetitorResult(
        radius,
        qpath,
        revised,
        inside_path,
        verified,
        distance,
        status,
        int(result.status),
        str(result.message),
        elapsed,
        None if marginals is None else tuple(float(v) for v in marginals),
    )


def separating_mixture_probe(
    instance: WWInstance,
    nominal_path: Sequence[int],
    k: int,
    outside_path: Sequence[int],
    radius: float,
) -> tuple[float, ...] | None:
    """Dual probe for a separating inside-path mixture at a fixed radius.

    Minimises the slack ``s`` in ``C_Q(d) <= inside_value(d) + s`` over the
    radius-``radius`` box.  When the optimal slack is positive, the dual
    values identify an inside-path mixture that dominates the competitor on
    the whole box; the exact layer re-verifies any mixture before use.  Row
    ordering matches :func:`fixed_competitor_inverse_lp` so the same dual
    reader applies (2T box rows, suffix-potential rows, coupling row).
    """
    pstar = validate_complete_path(nominal_path, instance.T)
    qpath = validate_complete_path(outside_path, instance.T)
    prefix = pstar[: k + 1]
    s = prefix[-1]
    T = instance.T
    k_q, beta_q = path_coefficients(instance, qpath)
    k_pref, beta_pref = path_coefficients(instance, prefix)

    slack_idx = T
    pi_nodes = tuple(range(s, T + 1))
    pi_index = {node: T + 1 + idx for idx, node in enumerate(pi_nodes)}
    nvar = T + 1 + len(pi_nodes)
    objective = np.zeros(nvar, dtype=float)
    objective[slack_idx] = 1.0
    bounds: list[tuple[float | None, float | None]] = [
        (float(instance.floor[t]), None) for t in range(T)
    ]
    bounds.append((None, None))
    bounds.extend([(None, None)] * len(pi_nodes))

    rows: list[np.ndarray] = []
    rhs: list[float] = []
    for t in range(T):
        row = np.zeros(nvar)
        row[t] = 1.0
        rows.append(row)
        rhs.append(float(instance.demand[t] + radius / instance.weights[t]))
        row = np.zeros(nvar)
        row[t] = -1.0
        rows.append(row)
        rhs.append(float(-(instance.demand[t] - radius / instance.weights[t])))
    for i in range(s, T):
        for j in range(i + 1, T + 1):
            row = np.zeros(nvar)
            row[i:j] = -instance.q[i]
            row[pi_index[j]] += 1.0
            row[pi_index[i]] -= 1.0
            rows.append(row)
            rhs.append(float(instance.K[i]))
    row = np.zeros(nvar)
    row[:T] = beta_q - beta_pref
    row[pi_index[T]] = -1.0
    row[slack_idx] = -1.0
    rows.append(row)
    rhs.append(float(k_pref - k_q))

    A_eq = np.zeros((1, nvar), dtype=float)
    A_eq[0, pi_index[s]] = 1.0
    result = linprog(
        objective,
        A_ub=np.vstack(rows),
        b_ub=np.asarray(rhs),
        A_eq=A_eq,
        b_eq=np.array([0.0]),
        bounds=bounds,
        method="highs",
    )
    if not result.success or result.fun is None or result.fun <= 0:
        return None
    marginals = getattr(getattr(result, "ineqlin", None), "marginals", None)
    if marginals is None:
        return None
    return tuple(float(v) for v in marginals)


def exact_radius_enumeration(
    instance: WWInstance,
    nominal_path: Sequence[int],
    k: int,
    *,
    max_paths: int | None = None,
    max_candidates: int | None = None,
    time_limit: float | None = None,
    tol: float = 1e-8,
) -> ExactRadiusResult:
    """Exact finite disjunction with fixed-path lower-bound ordering/pruning.

    On interruption, ``radius`` is the best feasible upper bound and
    ``lower_bound`` is the next unprocessed fixed-path lower bound.

    Candidate generation is atomic and materialises every outside path:
    exactly ``2^(T-1) - 2^max(T-1-s, 0)`` records for a prefix ending at
    node ``s`` (the addendum enumeration-complexity theorem), so it is
    worst-case exponential in ``T``. ``max_candidates`` refuses, from the
    closed form and before any generation, escalations whose disjunction
    would exceed the cap; the returned status is
    ``refused_by_candidate_guard`` with the trivial certified bracket
    ``[0, inf)``.
    """
    total_start = perf_counter()
    pstar = validate_complete_path(nominal_path, instance.T)
    if not (1 <= k <= len(pstar) - 1):
        raise ValueError("invalid protected-prefix length k")
    prefix = pstar[: k + 1]
    predicted_candidates = outside_path_count(instance.T, prefix)
    if max_candidates is not None and predicted_candidates > max_candidates:
        return ExactRadiusResult(
            inf,
            0.0,
            None,
            None,
            None,
            None,
            predicted_candidates,
            0,
            predicted_candidates,
            0,
            0,
            "refused_by_candidate_guard",
            perf_counter() - total_start,
            candidate_generation_seconds=0.0,
            disjunct_solve_seconds=0.0,
        )
    candidates = [
        (path_pairwise_radius(instance, path, pstar).radius, path)
        for path in outside_paths(instance.T, prefix)
    ]
    candidates.sort(key=lambda item: (item[0], item[1]))
    candidate_seconds = perf_counter() - total_start
    total = len(candidates)
    if total == 0:
        return ExactRadiusResult(
            inf, inf, None, None, None, None, 0, 0, 0, 0, 0,
            "no_outside_path", candidate_seconds,
            candidate_generation_seconds=candidate_seconds,
            disjunct_solve_seconds=0.0,
        )

    # The limit includes bound generation.  Candidate generation is currently
    # atomic, so an overrun can be reported only after all path lower bounds
    # have been formed and sorted.
    if time_limit is not None and candidate_seconds >= time_limit:
        return ExactRadiusResult(
            inf,
            float(candidates[0][0]),
            None,
            None,
            None,
            None,
            total,
            0,
            total,
            0,
            0,
            "time_limit_before_disjuncts",
            candidate_seconds,
            candidate_generation_seconds=candidate_seconds,
            disjunct_solve_seconds=0.0,
        )

    best = inf
    best_result: FixedCompetitorResult | None = None
    processed = 0
    infeasible = 0
    failures = 0
    next_lower = candidates[0][0]
    status = "optimal"
    solve_start = perf_counter()

    for position, (lower, qpath) in enumerate(candidates):
        next_lower = float(lower)
        if lower >= best - tol:
            # All remaining disjuncts have lower bound at least the incumbent.
            next_lower = best
            break
        if max_paths is not None and processed >= max_paths:
            status = "path_limit"
            break
        if time_limit is not None and perf_counter() - total_start >= time_limit:
            status = "time_limit"
            break
        result = fixed_competitor_inverse_lp(instance, pstar, k, qpath, tol=tol)
        processed += 1
        if result.status == "optimal":
            if result.radius < best:
                best = result.radius
                best_result = result
        elif result.status == "infeasible":
            infeasible += 1
        else:
            failures += 1
            status = "solver_failure"
            break
    else:
        next_lower = inf

    solve_seconds = perf_counter() - solve_start
    elapsed = perf_counter() - total_start
    if status == "optimal":
        if isfinite(best):
            next_lower = best
        else:
            status = "infinite"
            next_lower = inf
    pruned = total - processed
    if best_result is None:
        return ExactRadiusResult(
            best,
            float(next_lower),
            None,
            None,
            None,
            None,
            total,
            processed,
            pruned,
            infeasible,
            failures,
            status,
            elapsed,
            candidate_generation_seconds=candidate_seconds,
            disjunct_solve_seconds=solve_seconds,
        )
    return ExactRadiusResult(
        best_result.radius,
        float(next_lower),
        best_result.outside_path,
        best_result.revised_demand,
        best_result.inside_path,
        best_result.verified_difference,
        total,
        processed,
        pruned,
        infeasible,
        failures,
        status,
        elapsed,
        candidate_generation_seconds=candidate_seconds,
        disjunct_solve_seconds=solve_seconds,
    )


def fixed_radius_milp(
    instance: WWInstance,
    nominal_path: Sequence[int],
    k: int,
    radius: float,
    *,
    time_limit: float = 60.0,
    mip_rel_gap: float = 1e-9,
    tol: float = 1e-7,
) -> FixedRadiusMILPResult:
    """Decide whether an outside optimum can occur within a fixed radius."""
    if radius < 0:
        raise ValueError("radius must be non-negative")
    pstar = validate_complete_path(nominal_path, instance.T)
    if not (1 <= k <= len(pstar) - 1):
        raise ValueError("invalid protected-prefix length k")
    prefix = pstar[: k + 1]
    s = prefix[-1]
    graph = build_prefix_deviation_graph(instance, pstar, k)
    if not graph.has_source_sink_path():
        return FixedRadiusMILPResult(
            radius, None, None, False, None, None, None, None,
            "no_outside_path", 2, "No outside path exists.", 0.0, 0, 0.0,
        )

    T = instance.T
    E = len(graph.arcs)
    lower_d = np.maximum(instance.floor, instance.demand - radius / instance.weights)
    upper_d = instance.demand + radius / instance.weights
    k_pref, beta_pref = path_coefficients(instance, prefix)

    d_index = list(range(T))
    z_offset = T
    z_index = [z_offset + e for e in range(E)]
    product_pairs = [
        (arc.idx, t)
        for arc in graph.arcs
        for t in range(arc.physical_i, arc.physical_j)
    ]
    u_offset = z_offset + E
    u_index = {(e, t): u_offset + r for r, (e, t) in enumerate(product_pairs)}
    pi_nodes = list(range(s, T + 1))
    pi_offset = u_offset + len(product_pairs)
    pi_index = {node: pi_offset + r for r, node in enumerate(pi_nodes)}
    nvar = pi_offset + len(pi_nodes)

    objective = np.zeros(nvar, dtype=float)
    objective[:T] = -beta_pref
    for arc in graph.arcs:
        objective[z_index[arc.idx]] += instance.K[arc.physical_i]
        for t in range(arc.physical_i, arc.physical_j):
            objective[u_index[(arc.idx, t)]] += instance.q[arc.physical_i]
    objective[pi_index[T]] = -1.0

    lower = np.full(nvar, -np.inf)
    upper = np.full(nvar, np.inf)
    lower[:T], upper[:T] = lower_d, upper_d
    lower[z_offset : z_offset + E] = 0.0
    upper[z_offset : z_offset + E] = 1.0
    for e, t in product_pairs:
        lower[u_index[(e, t)]] = 0.0
        upper[u_index[(e, t)]] = upper_d[t]

    max_arc_abs = max(
        abs(instance.K[i])
        + abs(instance.q[i]) * float(np.sum(upper_d[i:j]))
        for i in range(T)
        for j in range(i + 1, T + 1)
    )
    potential_bound = (T + 1) * max(1.0, max_arc_abs)
    for node in pi_nodes:
        lower[pi_index[node]] = -potential_bound
        upper[pi_index[node]] = potential_bound

    integrality = np.zeros(nvar, dtype=int)
    integrality[z_offset : z_offset + E] = 1

    row_entries: list[dict[int, float]] = []
    row_lb: list[float] = []
    row_ub: list[float] = []

    def add_row(entries: dict[int, float], lb: float, ub: float) -> None:
        row_entries.append(entries)
        row_lb.append(lb)
        row_ub.append(ub)

    N, h, _ = graph.incidence_without_sink()
    for r in range(N.shape[0]):
        entries = {z_index[e]: float(N[r, e]) for e in range(E) if N[r, e] != 0}
        add_row(entries, float(h[r]), float(h[r]))

    # McCormick envelopes for u_e,t = z_e d_t on the fixed demand box.
    for e, t in product_pairs:
        z = z_index[e]
        u = u_index[(e, t)]
        d = d_index[t]
        L, U = float(lower_d[t]), float(upper_d[t])
        add_row({z: L, u: -1.0}, -np.inf, 0.0)             # L z <= u
        add_row({u: 1.0, z: -U}, -np.inf, 0.0)             # u <= U z
        add_row({d: 1.0, z: U, u: -1.0}, -np.inf, U)       # u >= d-U(1-z)
        add_row({u: 1.0, d: -1.0, z: -L}, -np.inf, -L)     # u <= d-L(1-z)

    # Suffix shortest-path potentials.
    for i in range(s, T):
        for j in range(i + 1, T + 1):
            entries: dict[int, float] = {pi_index[j]: 1.0, pi_index[i]: -1.0}
            for t in range(i, j):
                entries[d_index[t]] = entries.get(d_index[t], 0.0) - float(instance.q[i])
            add_row(entries, -np.inf, float(instance.K[i]))
    add_row({pi_index[s]: 1.0}, 0.0, 0.0)

    A = lil_matrix((len(row_entries), nvar), dtype=float)
    for r, entries in enumerate(row_entries):
        for col, value in entries.items():
            A[r, col] = value
    constraints = LinearConstraint(A.tocsr(), np.asarray(row_lb), np.asarray(row_ub))

    start = perf_counter()
    result = milp(
        objective,
        integrality=integrality,
        bounds=Bounds(lower, upper),
        constraints=constraints,
        options={"time_limit": float(time_limit), "mip_rel_gap": float(mip_rel_gap)},
    )
    elapsed = perf_counter() - start
    dual_raw = getattr(result, "mip_dual_bound", None)
    dual_gap = None if dual_raw is None else float(dual_raw - k_pref)
    mip_gap = None if getattr(result, "mip_gap", None) is None else float(result.mip_gap)
    nodes = None if getattr(result, "mip_node_count", None) is None else int(result.mip_node_count)

    if result.x is None:
        if result.status == 2:
            status, decision = "infeasible", False
        elif result.status == 1:
            status, decision = "time_limit_no_incumbent", False if dual_gap is not None and dual_gap > tol else None
        else:
            status, decision = "solver_failure", None
        return FixedRadiusMILPResult(
            radius,
            None,
            dual_gap,
            decision,
            None,
            None,
            None,
            None,
            status,
            int(result.status),
            str(result.message),
            mip_gap,
            nodes,
            elapsed,
        )

    x = np.asarray(result.x, dtype=float)
    revised = x[:T]
    selected_set = {arc.idx for arc in graph.arcs if x[z_index[arc.idx]] > 0.5}
    outside: Path | None = None
    try:
        node = graph.source
        ordered: list[int] = []
        while node != graph.sink:
            choices = [arc for arc in graph.outgoing[node] if arc.idx in selected_set]
            if len(choices) != 1:
                raise ValueError("selected edges do not form one expanded path")
            arc = choices[0]
            ordered.append(arc.idx)
            node = arc.head
        outside = graph.physical_path(ordered)
    except Exception:
        outside = None

    objective_gap = None if result.fun is None else float(result.fun - k_pref)
    inside_path: Path | None = None
    verified: float | None = None
    if outside is not None:
        inside_value, inside_path = constrained_inside_path(instance, revised, prefix, tol=tol)
        verified = float(path_cost(instance, revised, outside) - inside_value)

    witness_yes = verified is not None and verified <= 5 * tol
    if witness_yes:
        decision = True
    elif result.status == 0 and objective_gap is not None and objective_gap > tol:
        decision = False
    elif dual_gap is not None and dual_gap > tol:
        decision = False
    else:
        decision = None

    if result.status == 0:
        status = "optimal" if outside is not None and verified is not None else "numerical_validation_failure"
    elif result.status == 1:
        status = "time_limit_feasible"
    else:
        status = "solver_failure_feasible"
    return FixedRadiusMILPResult(
        radius,
        objective_gap,
        dual_gap,
        decision,
        revised,
        outside,
        inside_path,
        verified,
        status,
        int(result.status),
        str(result.message),
        mip_gap,
        nodes,
        elapsed,
    )
