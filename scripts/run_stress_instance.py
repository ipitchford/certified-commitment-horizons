#!/usr/bin/env python3
"""Reproduce the disclosed candidate-generation bottleneck stress case."""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from _common import ROOT, environment_record, write_json
from wwprefix import WWInstance, exact_radius_enumeration, fixed_radius_milp, polynomial_radius_bracket
from wwprefix.model import from_one_based

PATH = ROOT / "examples/benchmark_hard_instance_id26_T18.json"


def main() -> None:
    payload = json.loads(PATH.read_text())
    inst = WWInstance.create(**payload["instance"])
    nominal = from_one_based(payload["nominal_path"])
    k = 1

    t0 = perf_counter()
    bracket = polynomial_radius_bracket(inst, nominal, k)
    bracket_wall = perf_counter() - t0

    exact = exact_radius_enumeration(inst, nominal, k, time_limit=5.0)
    probe = bracket.safe_lower_radius * 1.01
    milp = fixed_radius_milp(inst, nominal, k, probe, time_limit=2.0)

    out = {
        "environment": environment_record(),
        "instance_file": str(PATH.relative_to(ROOT)),
        "T": inst.T,
        "nominal_path_zero_based": nominal,
        "protected_arcs": k,
        "polynomial_bracket": {
            "lower": bracket.safe_lower_radius,
            "upper": bracket.upper_radius,
            "status": bracket.status,
            "wall_seconds": bracket_wall,
        },
        "exact_enumeration_5_second_limit": {
            "status": exact.status,
            "lower_bound": exact.lower_bound,
            "upper_bound": exact.radius,
            "paths_total": exact.paths_total,
            "paths_processed": exact.paths_processed,
            "candidate_generation_seconds": exact.candidate_generation_seconds,
            "disjunct_solve_seconds": exact.disjunct_solve_seconds,
            "wall_seconds": exact.runtime_seconds,
            "note": "candidate generation is atomic in this implementation",
        },
        "fixed_radius_milp_2_second_limit": {
            "proposed_radius": probe,
            "status": milp.status,
            "decision": milp.decision,
            "minimum_gap_upper_bound": milp.minimum_gap_upper_bound,
            "minimum_gap_lower_bound": milp.minimum_gap_lower_bound,
            "mip_gap": milp.mip_gap,
            "nodes": milp.mip_node_count,
            "wall_seconds": milp.runtime_seconds,
        },
    }
    write_json(out, ROOT / "results/processed/exact_stress_case.json")
    print(out)


if __name__ == "__main__":
    main()
