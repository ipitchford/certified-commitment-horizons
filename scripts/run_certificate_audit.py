#!/usr/bin/env python3
"""Deterministic audit of the polynomial certificate and polynomial bracket.

The audit has two pre-specified strata:

* broad synthetic instances, used to test algebra and implementation over varied
  costs, floors and near ties;
* deliberately conditioned strict-gap instances, used as adversarial tests of
  conservatism.  Their frequency is not an estimate of real-world prevalence.
"""
from __future__ import annotations

from math import isfinite, isinf
from time import perf_counter

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from _common import (
    ROOT,
    SEED,
    draw_strict_gap_instance,
    environment_record,
    random_ww_instance,
    write_csv,
    write_json,
)
from wwprefix import (
    exact_radius_enumeration,
    fixed_competitor_inverse_lp,
    frozen_certificate_exhaustive,
    frozen_certificate_lp,
    polynomial_radius_bracket,
    shortest_path,
    verify_acyclic_nonnegative_circulation_property,
    verify_graph_bijection,
)
from wwprefix.graph import build_prefix_deviation_graph
from wwprefix.model import enumerate_paths, follows_prefix, path_coefficients


def explicit_fixed_q_radius(instance, pstar, k, qpath):
    """Independent small-horizon LP with one row per inside path."""
    T = instance.T
    prefix = pstar[: k + 1]
    kq, bq = path_coefficients(instance, qpath)
    objective = np.r_[np.zeros(T), 1.0]
    rows, rhs = [], []
    for t in range(T):
        row = np.zeros(T + 1)
        row[t], row[T] = 1.0, -1.0 / instance.weights[t]
        rows.append(row)
        rhs.append(instance.demand[t])
        row = np.zeros(T + 1)
        row[t], row[T] = -1.0, -1.0 / instance.weights[t]
        rows.append(row)
        rhs.append(-instance.demand[t])
    for inside in (p for p in enumerate_paths(T) if follows_prefix(p, prefix)):
        kp, bp = path_coefficients(instance, inside)
        row = np.zeros(T + 1)
        row[:T] = bq - bp
        rows.append(row)
        rhs.append(kp - kq)
    return linprog(
        objective,
        A_ub=np.asarray(rows),
        b_ub=np.asarray(rhs),
        bounds=[(instance.floor[t], None) for t in range(T)] + [(0.0, None)],
        method="highs",
    )


def _record_instance(
    *,
    instance,
    instance_id: int,
    regime: str,
    conditioned: bool,
    generator_attempts: int,
    rng: np.random.Generator,
    rows: list[dict],
    graph_rows: list[dict],
    fixed_q_rows: list[dict],
    graph_audit: bool,
    fixed_q_audit: bool,
) -> None:
    _, pstar = shortest_path(instance)

    if graph_audit:
        for k in range(1, len(pstar)):
            started = perf_counter()
            n_expanded, n_outside = verify_graph_bijection(instance, pstar, k)
            graph = build_prefix_deviation_graph(instance, pstar, k)
            graph_rows.append({
                "instance_id": instance_id,
                "T": instance.T,
                "regime": regime,
                "conditioned_strict_gap": conditioned,
                "k": k,
                "expanded_paths": n_expanded,
                "outside_paths": n_outside,
                "acyclic": verify_acyclic_nonnegative_circulation_property(graph),
                "nodes": len(graph.nodes),
                "arcs": len(graph.arcs),
                "runtime_seconds": perf_counter() - started,
            })

    previous_lp = float("inf")
    for k in range(1, len(pstar)):
        lp_started = perf_counter()
        lp = frozen_certificate_lp(instance, pstar, k)
        lp_time = perf_counter() - lp_started
        ex_started = perf_counter()
        ex = frozen_certificate_exhaustive(instance, pstar, k)
        ex_time = perf_counter() - ex_started
        if isinf(lp.radius) and isinf(ex.radius):
            abs_error = 0.0
        elif isfinite(lp.radius) and isfinite(ex.radius):
            abs_error = abs(lp.radius - ex.radius)
        else:
            abs_error = float("inf")

        bracket_started = perf_counter()
        bracket = polynomial_radius_bracket(instance, pstar, k)
        bracket_time = perf_counter() - bracket_started

        exact_started = perf_counter()
        exact = exact_radius_enumeration(instance, pstar, k, time_limit=30.0)
        exact_wall = perf_counter() - exact_started
        exact_contained = (
            bracket.lower_radius <= exact.radius + 1e-5
            and exact.radius <= bracket.upper_radius + 1e-5
        )

        rows.append({
            "instance_id": instance_id,
            "T": instance.T,
            "regime": regime,
            "conditioned_strict_gap": conditioned,
            "generator_attempts": generator_attempts,
            "nominal_path": "-".join(map(str, pstar)),
            "nominal_arcs": len(pstar) - 1,
            "k": k,
            "is_partial_prefix": k < len(pstar) - 1,
            "is_full_path": k == len(pstar) - 1,
            "lp_radius": lp.radius,
            "lp_safe_radius": lp.safe_radius,
            "exhaustive_frozen_radius": ex.radius,
            "absolute_error": abs_error,
            "lp_runtime_seconds": lp_time,
            "exhaustive_runtime_seconds": ex_time,
            "intervals_checked": lp.intervals_checked,
            "graph_nodes": lp.graph_nodes,
            "graph_arcs": lp.graph_arcs,
            "witness_difference": lp.witness_difference,
            "monotone_from_previous": lp.radius <= previous_lp + 1e-7,
            "bracket_lower": bracket.lower_radius,
            "bracket_upper": bracket.upper_radius,
            "bracket_width": (
                bracket.upper_radius - bracket.lower_radius
                if isfinite(bracket.upper_radius) and isfinite(bracket.lower_radius)
                else np.nan
            ),
            "bracket_exact_certified": bracket.exact_certified,
            "bracket_exact_reason": bracket.exact_reason,
            "lower_witness_closes": bracket.lower_witness_closes,
            "lower_witness_difference_to_inside": bracket.lower_witness_difference_to_inside,
            "bracket_runtime_seconds": bracket_time,
            "exact_radius": exact.radius,
            "exact_lower_bound": exact.lower_bound,
            "exact_status": exact.status,
            "exact_runtime_reported_seconds": exact.runtime_seconds,
            "exact_runtime_wall_seconds": exact_wall,
            "exact_paths_total": exact.paths_total,
            "exact_paths_processed": exact.paths_processed,
            "exact_paths_pruned": exact.paths_pruned,
            "exact_solver_failures": exact.solver_failures,
            "exact_contained": exact_contained,
        })
        previous_lp = lp.radius

    if fixed_q_audit and len(pstar) > 1:
        k = 1
        prefix = pstar[:2]
        outside = [p for p in enumerate_paths(instance.T) if not follows_prefix(p, prefix)]
        rng.shuffle(outside)
        for qpath in outside[: min(4, len(outside))]:
            compact = fixed_competitor_inverse_lp(instance, pstar, k, qpath)
            explicit = explicit_fixed_q_radius(instance, pstar, k, qpath)
            fixed_q_rows.append({
                "instance_id": instance_id,
                "T": instance.T,
                "regime": regime,
                "conditioned_strict_gap": conditioned,
                "outside_path": "-".join(map(str, qpath)),
                "compact_status": compact.status,
                "compact_radius": compact.radius,
                "explicit_success": bool(explicit.success),
                "explicit_status": int(explicit.status),
                "explicit_radius": float(explicit.fun) if explicit.success else np.nan,
                "absolute_error": (
                    abs(compact.radius - float(explicit.fun))
                    if compact.status == "optimal" and explicit.success
                    else np.nan
                ),
                "verified_difference": compact.verified_difference,
            })


def _quantiles(series: pd.Series) -> dict[str, float | None]:
    clean = series.replace([np.inf, -np.inf], np.nan).dropna()
    if clean.empty:
        return {"p10": None, "median": None, "p90": None}
    return {
        "p10": float(clean.quantile(0.10)),
        "median": float(clean.median()),
        "p90": float(clean.quantile(0.90)),
    }


def main() -> None:
    rng = np.random.default_rng(SEED)
    rows: list[dict] = []
    graph_rows: list[dict] = []
    fixed_q_rows: list[dict] = []
    instance_id = 0

    # Broad synthetic stratum: 162 generated instances.
    for T in range(2, 11):
        for rep in range(18):
            regime = ("regular", "floor_heavy", "near_tie")[rep % 3]
            instance = random_ww_instance(rng, T, regime=regime)
            instance_id += 1
            _record_instance(
                instance=instance,
                instance_id=instance_id,
                regime=regime,
                conditioned=False,
                generator_attempts=1,
                rng=rng,
                rows=rows,
                graph_rows=graph_rows,
                fixed_q_rows=fixed_q_rows,
                graph_audit=T <= 8 and rep < 3,
                fixed_q_audit=T <= 7 and rep < 3,
            )

    # Adversarial stratum: 96 conditioned instances, pre-declared as such.
    for T in range(3, 11):
        for rep in range(12):
            instance, attempts = draw_strict_gap_instance(rng, T)
            instance_id += 1
            _record_instance(
                instance=instance,
                instance_id=instance_id,
                regime="strict_gap",
                conditioned=True,
                generator_attempts=attempts,
                rng=rng,
                rows=rows,
                graph_rows=graph_rows,
                fixed_q_rows=fixed_q_rows,
                graph_audit=T <= 8 and rep < 2,
                fixed_q_audit=T <= 7 and rep < 2,
            )

    results = pd.DataFrame(rows)
    graphs = pd.DataFrame(graph_rows)
    fixed_q = pd.DataFrame(fixed_q_rows)
    out = ROOT / "results" / "raw"
    write_csv(results, out / "certificate_audit.csv")
    write_csv(graphs, out / "graph_bijection_audit.csv")
    write_csv(fixed_q, out / "fixed_competitor_audit.csv")

    finite_errors = results.loc[np.isfinite(results["absolute_error"]), "absolute_error"]
    finite_exact = results[np.isfinite(results["exact_radius"])].copy()
    positive_exact = finite_exact[finite_exact["exact_radius"] > 1e-10].copy()
    positive_exact["lower_to_exact"] = positive_exact["bracket_lower"] / positive_exact["exact_radius"]
    positive_exact["upper_to_exact"] = positive_exact["bracket_upper"] / positive_exact["exact_radius"]
    positive_exact["relative_bracket_width"] = (
        positive_exact["bracket_upper"] - positive_exact["bracket_lower"]
    ) / positive_exact["exact_radius"]
    partial = positive_exact[positive_exact["is_partial_prefix"]].copy()
    broad_partial = partial[~partial["conditioned_strict_gap"]]
    adversarial_partial = partial[partial["conditioned_strict_gap"]]

    by_regime = {}
    for regime, group in partial.groupby("regime"):
        by_regime[str(regime)] = {
            "rows": int(len(group)),
            "strict_lower_count": int((group["bracket_lower"] < group["exact_radius"] - 1e-6).sum()),
            "polynomial_exact_count": int(group["bracket_exact_certified"].sum()),
            "lower_to_exact": _quantiles(group["lower_to_exact"]),
            "upper_to_exact": _quantiles(group["upper_to_exact"]),
            "relative_bracket_width": _quantiles(group["relative_bracket_width"]),
        }

    full_mask = results["is_full_path"] & np.isfinite(results["exact_radius"])
    summary = {
        "environment": environment_record(),
        "design": {
            "broad_generated_instances": 162,
            "adversarial_conditioned_instances": 96,
            "adversarial_frequency_is_not_a_prevalence_estimate": True,
        },
        "generated_instances": int(results["instance_id"].nunique()),
        "certificate_comparisons": int(len(results)),
        "finite_certificate_comparisons": int(len(finite_errors)),
        "max_absolute_certificate_error": float(finite_errors.max()) if len(finite_errors) else None,
        "all_monotonicity_checks_pass": bool(results["monotone_from_previous"].all()),
        "all_graph_bijections_pass": bool((graphs["expanded_paths"] == graphs["outside_paths"]).all()),
        "all_graphs_acyclic": bool(graphs["acyclic"].all()),
        "graph_checks": int(len(graphs)),
        "fixed_competitor_comparisons": int(len(fixed_q)),
        "max_fixed_competitor_error": (
            float(fixed_q["absolute_error"].dropna().max())
            if fixed_q["absolute_error"].notna().any()
            else None
        ),
        "exact_cases": int(len(results)),
        "all_exact_brackets_contain": bool(results["exact_contained"].all()),
        "exact_solver_failures": int(results["exact_solver_failures"].sum()),
        "partial_positive_exact_cases": int(len(partial)),
        "broad_partial_positive_cases": int(len(broad_partial)),
        "broad_partial_strict_lower_count": int(
            (broad_partial["bracket_lower"] < broad_partial["exact_radius"] - 1e-6).sum()
        ),
        "adversarial_partial_positive_cases": int(len(adversarial_partial)),
        "adversarial_partial_strict_lower_count": int(
            (adversarial_partial["bracket_lower"] < adversarial_partial["exact_radius"] - 1e-6).sum()
        ),
        "partial_polynomial_exact_count": int(partial["bracket_exact_certified"].sum()),
        "partial_polynomial_exact_share": float(partial["bracket_exact_certified"].mean()),
        "partial_lower_to_exact": _quantiles(partial["lower_to_exact"]),
        "partial_upper_to_exact": _quantiles(partial["upper_to_exact"]),
        "partial_relative_bracket_width": _quantiles(partial["relative_bracket_width"]),
        "by_regime": by_regime,
        "full_path_exact_checks": int(full_mask.sum()),
        "full_path_max_lower_exact_error": (
            float(np.max(np.abs(results.loc[full_mask, "bracket_lower"] - results.loc[full_mask, "exact_radius"])))
            if full_mask.any()
            else None
        ),
    }
    write_json(summary, ROOT / "results" / "processed" / "certificate_audit_summary.json")
    print(summary)


if __name__ == "__main__":
    main()
