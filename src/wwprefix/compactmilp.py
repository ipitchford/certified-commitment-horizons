"""Compact production-balance exact formulations (addendum, item 4).

The released fixed-radius model binarises every expanded arc and couples it
to demand through Theta(T^3) McCormick products.  The models here use the
original reduced lot-sizing variables instead: setup indicators ``y``,
production quantities ``x``, inventories ``I`` and the demand vector ``d``.
Unit costs multiply quantities, not path indicators, so no bilinear terms
arise: ``T`` binaries, ``O(T)`` continuous variables and ``O(T^2)`` rows.

Conversion lemma (proved in the addendum section of the manuscript): for
any feasible plan ``(y, x, I)`` with the mandatory nominal-source setup
``y_0 = 1``, reassigning every unit of period-``t`` demand to the latest
open setup at or before ``t`` produces the zero-inventory plan of the path
whose nodes are exactly ``{i : y_i = 1} + {T}``; ordered slopes make the
reassignment cost-non-increasing, unused setups become zero-quantity
cycles at identical cost, and ``y`` is untouched, so a linear deviation
row in ``y`` certifies that the induced path leaves the protected prefix.
Conversely every outside path is a feasible deviating plan of equal cost.
Hence, at every fixed admissible demand, the minimum deviating-plan cost
equals the outside envelope ``B_k(d)`` exactly, and the fixed-radius and
minimum-radius models below are exact reformulations, not relaxations.

Solver outputs remain floating point.  Every finite result is therefore
pushed through the exact layer (:func:`wwprefix.exactcert.certify_strong_witness`
with the release's repair ladder); only the exactly re-verified witness is
labelled certified.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import inf
from time import perf_counter
from typing import Sequence

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from .exactcert import CertifiedWitness, ExactInstance, certify_disjunct
from .model import (
    Path,
    WWInstance,
    constrained_inside_path,
    follows_prefix,
    outside_path_count,
    path_coefficients,
    path_cost,
    validate_complete_path,
)


@dataclass(frozen=True)
class CompactMILPResult:
    """Result of a compact production-balance solve.

    ``radius`` is populated in minimum-radius mode, ``decision`` in
    fixed-radius mode.  ``certified_witness`` is non-``None`` exactly when
    the exact layer re-verified a destabilising witness; everything else is
    solver-level evidence.
    """

    radius: float | None
    decision: bool | None
    minimum_gap_upper_bound: float | None
    minimum_gap_lower_bound: float | None
    revised_demand: np.ndarray | None
    outside_path: Path | None
    inside_path: Path | None
    verified_difference: float | None
    certified_witness: CertifiedWitness | None
    status: str
    solver_status: int
    solver_message: str
    mip_gap: float | None
    mip_node_count: int | None
    runtime_seconds: float
    n_variables: int
    n_constraints: int


def _build_and_solve(
    instance: WWInstance,
    nominal_path: Sequence[int],
    k: int,
    *,
    mode: str,
    radius: float | None,
    radius_cap: float | None,
    time_limit: float,
    mip_rel_gap: float,
) -> tuple[object, dict[str, object]]:
    """Shared constructor for the decision and minimum-radius models."""
    pstar = validate_complete_path(nominal_path, instance.T)
    if not (1 <= k <= len(pstar) - 1):
        raise ValueError("invalid protected-prefix length k")
    prefix = pstar[: k + 1]
    s = prefix[-1]
    T = instance.T
    k_pref, beta_pref = path_coefficients(instance, prefix)

    if mode == "decision":
        assert radius is not None and radius >= 0
        lower_d = np.maximum(instance.floor, instance.demand - radius / instance.weights)
        upper_d = instance.demand + radius / instance.weights
    else:
        assert radius_cap is not None and radius_cap >= 0
        lower_d = np.asarray(instance.floor, dtype=float)
        upper_d = instance.demand + radius_cap / instance.weights

    d_index = list(range(T))
    y_index = [T + i for i in range(T)]
    x_index = [2 * T + i for i in range(T)]
    inv_index = [3 * T + t for t in range(T)]
    pi_nodes = list(range(s, T + 1))
    pi_offset = 4 * T
    pi_index = {node: pi_offset + r for r, node in enumerate(pi_nodes)}
    nvar = pi_offset + len(pi_nodes) + (1 if mode == "radius" else 0)
    r_index = nvar - 1 if mode == "radius" else None

    big_m = float(np.sum(upper_d))
    max_arc_abs = max(
        abs(instance.K[i]) + abs(instance.q[i]) * float(np.sum(upper_d[i:j]))
        for i in range(T)
        for j in range(i + 1, T + 1)
    )
    potential_bound = (T + 1) * max(1.0, max_arc_abs)

    lower = np.full(nvar, -np.inf)
    upper = np.full(nvar, np.inf)
    lower[:T], upper[:T] = lower_d, upper_d
    for i in range(T):
        lower[y_index[i]], upper[y_index[i]] = 0.0, 1.0
        lower[x_index[i]], upper[x_index[i]] = 0.0, big_m
        lower[inv_index[i]], upper[inv_index[i]] = 0.0, big_m
    lower[y_index[0]] = 1.0  # every path pays the source setup
    lower[inv_index[T - 1]] = upper[inv_index[T - 1]] = 0.0
    for node in pi_nodes:
        lower[pi_index[node]] = -potential_bound
        upper[pi_index[node]] = potential_bound
    lower[pi_index[s]] = upper[pi_index[s]] = 0.0
    if r_index is not None:
        lower[r_index], upper[r_index] = 0.0, float(radius_cap)

    integrality = np.zeros(nvar, dtype=int)
    for i in range(T):
        integrality[y_index[i]] = 1

    row_entries: list[dict[int, float]] = []
    row_lb: list[float] = []
    row_ub: list[float] = []

    def add_row(entries: dict[int, float], lb: float, ub: float) -> None:
        row_entries.append(entries)
        row_lb.append(lb)
        row_ub.append(ub)

    # Inventory balance I_t - I_{t-1} - x_t + d_t = 0 with I_{-1} = 0.
    for t in range(T):
        entries = {inv_index[t]: 1.0, x_index[t]: -1.0, d_index[t]: 1.0}
        if t > 0:
            entries[inv_index[t - 1]] = -1.0
        add_row(entries, 0.0, 0.0)

    # Production only at open setups.
    for i in range(T):
        add_row({x_index[i]: 1.0, y_index[i]: -big_m}, -np.inf, 0.0)

    # Deviation row: sum_gap y_i + sum_prot (1 - y_v) >= 1.
    gap_nodes = [i for i in range(1, min(s, T)) if i not in prefix]
    protected_setup_nodes = [v for v in prefix[1:] if v < T]
    entries = {y_index[i]: 1.0 for i in gap_nodes}
    for v in protected_setup_nodes:
        entries[y_index[v]] = entries.get(y_index[v], 0.0) - 1.0
    add_row(entries, 1.0 - len(protected_setup_nodes), np.inf)

    # Suffix shortest-path potentials for the moving inside continuation.
    for i in range(s, T):
        for j in range(i + 1, T + 1):
            entries = {pi_index[j]: 1.0, pi_index[i]: -1.0}
            for t in range(i, j):
                entries[d_index[t]] = entries.get(d_index[t], 0.0) - float(instance.q[i])
            add_row(entries, -np.inf, float(instance.K[i]))

    plan_cost = {y_index[i]: float(instance.K[i]) for i in range(T)}
    for i in range(T):
        plan_cost[x_index[i]] = float(instance.q[i])

    objective = np.zeros(nvar, dtype=float)
    if mode == "decision":
        # Minimise plan cost minus the best inside value; the sign decides.
        for col, value in plan_cost.items():
            objective[col] += value
        objective[:T] -= beta_pref
        objective[pi_index[T]] = -1.0
    else:
        # Couple plan cost <= inside value; minimise the radius.
        entries = dict(plan_cost)
        for t in range(T):
            entries[d_index[t]] = entries.get(d_index[t], 0.0) - float(beta_pref[t])
        entries[pi_index[T]] = entries.get(pi_index[T], 0.0) - 1.0
        add_row(entries, -np.inf, float(k_pref))
        for t in range(T):
            w = float(instance.weights[t])
            add_row({d_index[t]: w, r_index: -1.0}, -np.inf, w * float(instance.demand[t]))
            add_row({d_index[t]: -w, r_index: -1.0}, -np.inf, -w * float(instance.demand[t]))
        objective[r_index] = 1.0

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
    meta = {
        "prefix": prefix,
        "k_pref": k_pref,
        "beta_pref": beta_pref,
        "y_index": y_index,
        "r_index": r_index,
        "elapsed": elapsed,
        "nvar": nvar,
        "nrows": len(row_entries),
    }
    return result, meta


def _induced_path(instance: WWInstance, y_values: Sequence[float]) -> Path | None:
    nodes = [i for i in range(instance.T) if y_values[i] > 0.5]
    if not nodes or nodes[0] != 0:
        return None
    return (*nodes, instance.T)


def _certify(
    instance: WWInstance,
    pstar: Path,
    prefix: Path,
    outside: Path,
    demand: Sequence[float],
) -> CertifiedWitness | None:
    """Exact witness for the exposed competitor at the proposed demand.

    Delegates to the release's disjunct certifier, whose preferred witness
    is the exact tie demand against the binding inside comparator; a raw
    float snap plus inflation ladder is only its fallback.  This keeps the
    certified upper bound at the exact boundary instead of a
    tolerance-inflated copy of it.
    """
    inst = ExactInstance.from_ww(instance)
    certificate = certify_disjunct(inst, pstar, prefix, outside, list(demand), None)
    return certificate.witness


def compact_fixed_radius_milp(
    instance: WWInstance,
    nominal_path: Sequence[int],
    k: int,
    radius: float,
    *,
    time_limit: float = 60.0,
    mip_rel_gap: float = 1e-9,
    tol: float = 1e-7,
) -> CompactMILPResult:
    """Decide destabilisability within a fixed radius, compactly."""
    if radius < 0:
        raise ValueError("radius must be non-negative")
    pstar = validate_complete_path(nominal_path, instance.T)
    prefix = pstar[: k + 1]
    if outside_path_count(instance.T, prefix) == 0:
        return CompactMILPResult(
            None, False, None, None, None, None, None, None, None,
            "no_outside_path", 2, "No outside path exists.", None, None, 0.0, 0, 0,
        )
    result, meta = _build_and_solve(
        instance, nominal_path, k,
        mode="decision", radius=radius, radius_cap=None,
        time_limit=time_limit, mip_rel_gap=mip_rel_gap,
    )
    k_pref = meta["k_pref"]
    dual_raw = getattr(result, "mip_dual_bound", None)
    gap_lower = None if dual_raw is None else float(dual_raw - k_pref)
    mip_gap = None if getattr(result, "mip_gap", None) is None else float(result.mip_gap)
    nodes = None if getattr(result, "mip_node_count", None) is None else int(result.mip_node_count)

    if result.x is None:
        if result.status == 2:
            status, decision = "infeasible", False
        elif result.status == 1:
            status = "time_limit_no_incumbent"
            decision = False if gap_lower is not None and gap_lower > tol else None
        else:
            status, decision = "solver_failure", None
        return CompactMILPResult(
            None, decision, None, gap_lower, None, None, None, None, None,
            status, int(result.status), str(result.message), mip_gap, nodes,
            meta["elapsed"], meta["nvar"], meta["nrows"],
        )

    x = np.asarray(result.x, dtype=float)
    revised = x[: instance.T]
    outside = _induced_path(instance, [x[i] for i in meta["y_index"]])
    gap_upper = None if result.fun is None else float(result.fun - k_pref)
    inside_path: Path | None = None
    verified: float | None = None
    witness: CertifiedWitness | None = None
    if outside is not None and not follows_prefix(outside, prefix):
        inside_value, inside_path = constrained_inside_path(instance, revised, prefix)
        verified = float(path_cost(instance, revised, outside) - inside_value)
        if verified <= 5 * tol:
            witness = _certify(instance, pstar, prefix, outside, revised)

    if witness is not None:
        decision = True
    elif verified is not None and verified <= 5 * tol:
        decision = True  # float-level witness, certification failed
    elif result.status == 0 and gap_upper is not None and gap_upper > tol:
        decision = False
    elif gap_lower is not None and gap_lower > tol:
        decision = False
    else:
        decision = None

    if result.status == 0:
        status = "optimal" if outside is not None else "numerical_validation_failure"
    elif result.status == 1:
        status = "time_limit_feasible"
    else:
        status = "solver_failure_feasible"
    return CompactMILPResult(
        None, decision, gap_upper, gap_lower, revised, outside, inside_path,
        verified, witness, status, int(result.status), str(result.message),
        mip_gap, nodes, meta["elapsed"], meta["nvar"], meta["nrows"],
    )


def compact_radius_milp(
    instance: WWInstance,
    nominal_path: Sequence[int],
    k: int,
    *,
    radius_cap: float,
    time_limit: float = 60.0,
    mip_rel_gap: float = 1e-9,
    tol: float = 1e-7,
) -> CompactMILPResult:
    """Minimise the destabilisation radius directly over the capped box.

    Infeasibility certifies (at solver level) that no destabilisation exists
    within ``radius_cap``; it is not a proof of an infinite radius.
    """
    if radius_cap < 0:
        raise ValueError("radius_cap must be non-negative")
    pstar = validate_complete_path(nominal_path, instance.T)
    prefix = pstar[: k + 1]
    if outside_path_count(instance.T, prefix) == 0:
        return CompactMILPResult(
            inf, None, None, None, None, None, None, None, None,
            "no_outside_path", 2, "No outside path exists.", None, None, 0.0, 0, 0,
        )
    result, meta = _build_and_solve(
        instance, nominal_path, k,
        mode="radius", radius=None, radius_cap=radius_cap,
        time_limit=time_limit, mip_rel_gap=mip_rel_gap,
    )
    mip_gap = None if getattr(result, "mip_gap", None) is None else float(result.mip_gap)
    nodes = None if getattr(result, "mip_node_count", None) is None else int(result.mip_node_count)

    if result.x is None:
        if result.status == 2:
            status = "no_destabilisation_within_cap"
        elif result.status == 1:
            status = "time_limit_no_incumbent"
        else:
            status = "solver_failure"
        return CompactMILPResult(
            None, None, None, None, None, None, None, None, None,
            status, int(result.status), str(result.message), mip_gap, nodes,
            meta["elapsed"], meta["nvar"], meta["nrows"],
        )

    x = np.asarray(result.x, dtype=float)
    revised = x[: instance.T]
    radius_value = float(x[meta["r_index"]])
    outside = _induced_path(instance, [x[i] for i in meta["y_index"]])
    inside_path: Path | None = None
    verified: float | None = None
    witness: CertifiedWitness | None = None
    if outside is not None and not follows_prefix(outside, prefix):
        inside_value, inside_path = constrained_inside_path(instance, revised, prefix)
        verified = float(path_cost(instance, revised, outside) - inside_value)
        witness = _certify(instance, pstar, prefix, outside, revised)

    if result.status == 0:
        status = "optimal" if outside is not None else "numerical_validation_failure"
    elif result.status == 1:
        status = "time_limit_feasible"
    else:
        status = "solver_failure_feasible"
    return CompactMILPResult(
        radius_value, None, None, None, revised, outside, inside_path, verified,
        witness, status, int(result.status), str(result.message), mip_gap,
        nodes, meta["elapsed"], meta["nvar"], meta["nrows"],
    )


def compact_arc_radius_milp(
    instance: WWInstance,
    nominal_path: Sequence[int],
    r: int,
    *,
    radius_cap: float,
    time_limit: float = 60.0,
    mip_rel_gap: float = 1e-9,
    tol: float = 1e-7,
) -> CompactMILPResult:
    """One-protected-arc radius via the suffix sub-instance (decomposition).

    The reported radius is the full-instance weighted distance: coordinates
    before the arc's tail are irrelevant to the event and stay nominal.
    """
    from .decomposition import arc_subproblem_path, sub_ww_instance

    pstar = validate_complete_path(nominal_path, instance.T)
    if not (0 <= r <= len(pstar) - 2):
        raise ValueError("r must index a nominal arc")
    sub = sub_ww_instance(instance, pstar[r])
    sub_path = arc_subproblem_path(pstar, r)
    return compact_radius_milp(
        sub, sub_path, 1,
        radius_cap=radius_cap, time_limit=time_limit,
        mip_rel_gap=mip_rel_gap, tol=tol,
    )
