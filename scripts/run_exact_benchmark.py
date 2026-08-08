#!/usr/bin/env python3
"""Benchmark exact disjunction and fixed-radius MILP escalation.

The benchmark reports absolute path counts, all solver statuses, wall-clock
phases and timeouts.  It is a synthetic implementation benchmark, not an
industrial workload model.
"""
from __future__ import annotations

from math import isfinite
import os
from time import perf_counter

import numpy as np
import pandas as pd

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
    fixed_radius_milp,
    polynomial_radius_bracket,
    shortest_path,
)


def _q(values: pd.Series) -> dict[str, float | None]:
    x = values.replace([np.inf, -np.inf], np.nan).dropna()
    if x.empty:
        return {"p25": None, "median": None, "p75": None, "p90": None, "max": None}
    return {
        "p25": float(x.quantile(0.25)),
        "median": float(x.median()),
        "p75": float(x.quantile(0.75)),
        "p90": float(x.quantile(0.90)),
        "max": float(x.max()),
    }


def main() -> None:
    rng = np.random.default_rng(SEED + 101)
    exact_rows: list[dict] = []
    milp_rows: list[dict] = []
    instance_id = 0

    for T in (6, 10, 14, 16, 18):
        for regime in ("regular", "near_tie", "strict_gap"):
            for rep in range(2):
                if regime == "strict_gap":
                    instance, attempts = draw_strict_gap_instance(rng, T)
                else:
                    instance = random_ww_instance(rng, T, regime=regime)
                    attempts = 1
                _, nominal = shortest_path(instance)
                k = 1
                instance_id += 1

                bracket_start = perf_counter()
                bracket = polynomial_radius_bracket(instance, nominal, k)
                bracket_wall = perf_counter() - bracket_start

                exact_start = perf_counter()
                exact = exact_radius_enumeration(
                    instance,
                    nominal,
                    k,
                    time_limit=15.0,
                )
                exact_wall = perf_counter() - exact_start
                exact_rows.append({
                    "instance_id": instance_id,
                    "T": T,
                    "regime": regime,
                    "replicate": rep,
                    "generator_attempts": attempts,
                    "nominal_arcs": len(nominal) - 1,
                    "protected_arcs": k,
                    "is_full_path": k == len(nominal) - 1,
                    "bracket_lower": bracket.lower_radius,
                    "bracket_upper": bracket.upper_radius,
                    "bracket_status": bracket.status,
                    "bracket_runtime_seconds": bracket_wall,
                    "exact_status": exact.status,
                    "exact_radius_upper_bound": exact.radius,
                    "exact_radius_lower_bound": exact.lower_bound,
                    "terminal_bracket_width": (
                        exact.radius - exact.lower_bound
                        if isfinite(exact.radius) and isfinite(exact.lower_bound)
                        else np.nan
                    ),
                    "paths_total": exact.paths_total,
                    "paths_processed": exact.paths_processed,
                    "paths_pruned": exact.paths_pruned,
                    "processed_fraction": (
                        exact.paths_processed / exact.paths_total if exact.paths_total else 0.0
                    ),
                    "infeasible_disjuncts": exact.infeasible_disjuncts,
                    "solver_failures": exact.solver_failures,
                    "candidate_generation_seconds": exact.candidate_generation_seconds,
                    "disjunct_solve_seconds": exact.disjunct_solve_seconds,
                    "exact_runtime_reported_seconds": exact.runtime_seconds,
                    "exact_runtime_wall_seconds": exact_wall,
                    "witness_difference": exact.verified_difference,
                })
                print(
                    f"exact instance={instance_id} T={T} regime={regime} rep={rep} "
                    f"status={exact.status} paths={exact.paths_total} wall={exact_wall:.3f}s",
                    flush=True,
                )
                write_csv(pd.DataFrame(exact_rows), ROOT / "results" / "raw" / "exact_benchmark.partial.csv")

                # MILP probes are restricted a priori because model construction and
                # branch-and-bound can dominate the benchmark.
                if (
                    not os.environ.get("SKIP_MILP")
                    and rep == 0
                    and T <= 16
                    and exact.status == "optimal"
                    and isfinite(exact.radius)
                ):
                    epsilon = max(1e-5, 1e-4 * (1.0 + exact.radius))
                    probes = (
                        ("below", max(0.0, exact.radius - epsilon), False),
                        ("above", exact.radius + epsilon, True),
                    )
                    for side, proposed, expected in probes:
                        start = perf_counter()
                        result = fixed_radius_milp(
                            instance,
                            nominal,
                            k,
                            proposed,
                            time_limit=2.0,
                            mip_rel_gap=1e-8,
                        )
                        wall = perf_counter() - start
                        milp_rows.append({
                            "instance_id": instance_id,
                            "T": T,
                            "regime": regime,
                            "replicate": rep,
                            "nominal_arcs": len(nominal) - 1,
                            "is_full_path": k == len(nominal) - 1,
                            "side": side,
                            "proposed_radius": proposed,
                            "expected_decision": expected,
                            "decision": result.decision,
                            "decision_matches_when_resolved": (
                                result.decision == expected if result.decision is not None else None
                            ),
                            "status": result.status,
                            "solver_status": result.solver_status,
                            "runtime_reported_seconds": result.runtime_seconds,
                            "runtime_wall_seconds": wall,
                            "mip_gap": result.mip_gap,
                            "mip_node_count": result.mip_node_count,
                            "minimum_gap_upper_bound": result.minimum_gap_upper_bound,
                            "minimum_gap_lower_bound": result.minimum_gap_lower_bound,
                            "verified_difference": result.verified_difference,
                        })
                        print(
                            f"  milp side={side} status={result.status} decision={result.decision} "
                            f"wall={wall:.3f}s",
                            flush=True,
                        )
                        write_csv(pd.DataFrame(milp_rows), ROOT / "results" / "raw" / "milp_benchmark.partial.csv")

    exact_df = pd.DataFrame(exact_rows)
    milp_df = pd.DataFrame(milp_rows)
    write_csv(exact_df, ROOT / "results" / "raw" / "exact_benchmark.csv")
    write_csv(milp_df, ROOT / "results" / "raw" / "milp_benchmark.csv")

    exact_by_T: dict[str, dict] = {}
    for T, g in exact_df.groupby("T"):
        exact_by_T[str(int(T))] = {
            "instances": int(len(g)),
            "statuses": {str(k): int(v) for k, v in g["exact_status"].value_counts().items()},
            "paths_total": _q(g["paths_total"]),
            "paths_processed": _q(g["paths_processed"]),
            "processed_fraction": _q(g["processed_fraction"]),
            "candidate_generation_seconds": _q(g["candidate_generation_seconds"]),
            "disjunct_solve_seconds": _q(g["disjunct_solve_seconds"]),
            "wall_seconds": _q(g["exact_runtime_wall_seconds"]),
        }

    milp_by_T: dict[str, dict] = {}
    for T, g in milp_df.groupby("T"):
        resolved = g[g["decision"].notna()]
        milp_by_T[str(int(T))] = {
            "probes": int(len(g)),
            "statuses": {str(k): int(v) for k, v in g["status"].value_counts().items()},
            "resolved": int(len(resolved)),
            "correct_when_resolved": int(resolved["decision_matches_when_resolved"].sum()),
            "wall_seconds": _q(g["runtime_wall_seconds"]),
            "nodes": _q(g["mip_node_count"]),
        }

    summary = {
        "environment": environment_record(),
        "design": {
            "horizons": [6, 10, 14, 16, 18],
            "regimes": ["regular", "near_tie", "strict_gap"],
            "replicates_per_cell": 2,
            "exact_time_limit_seconds_including_candidate_generation": 15.0,
            "milp_time_limit_seconds_per_probe": 2.0,
            "boundary_separation": "max(1e-5, 1e-4*(1+rho))",
        },
        "exact_instances": int(len(exact_df)),
        "exact_statuses": {str(k): int(v) for k, v in exact_df["exact_status"].value_counts().items()},
        "exact_solver_failures": int(exact_df["solver_failures"].sum()),
        "exact_witness_max_positive_difference": (
            float(exact_df["witness_difference"].dropna().max())
            if exact_df["witness_difference"].notna().any()
            else None
        ),
        "exact_by_horizon": exact_by_T,
        "milp_probes": int(len(milp_df)),
        "milp_statuses": {str(k): int(v) for k, v in milp_df["status"].value_counts().items()},
        "milp_resolved": int(milp_df["decision"].notna().sum()),
        "milp_unresolved": int(milp_df["decision"].isna().sum()),
        "milp_correct_when_resolved": int(
            milp_df.loc[milp_df["decision"].notna(), "decision_matches_when_resolved"].sum()
        ),
        "milp_by_horizon": milp_by_T,
    }
    write_json(summary, ROOT / "results" / "processed" / "exact_benchmark_summary.json")
    print(summary)


if __name__ == "__main__":
    main()
