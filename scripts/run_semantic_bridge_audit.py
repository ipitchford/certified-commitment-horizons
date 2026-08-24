#!/usr/bin/env python3
"""Exact finite audit of the classical active-horizon semantic bridge."""
from __future__ import annotations

import csv
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from wwprefix.bridge import (
    empty_setup_nodes,
    exact_graph_optimal_paths,
    exact_physical_setup_optima,
    setup_pattern_to_path,
)
from wwprefix.exactcert import ExactInstance
from wwprefix.model import CLASSICAL_ACTIVE_HORIZON, FORCED_SOURCE_GRAPH

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw" / "semantic_bridge_audit.csv"
SUMMARY = ROOT / "results" / "processed" / "semantic_bridge_audit_summary.json"


def main() -> None:
    rng = np.random.default_rng(2026081801)
    rows: list[dict[str, object]] = []
    for T in range(1, 11):
        for replicate in range(32):
            K = [int(rng.integers(0, 8))] + [
                int(v) for v in rng.integers(1, 9, max(T - 1, 0))
            ]
            q = list(np.cumsum(rng.integers(0, 6, T)[::-1])[::-1])
            demand = [int(rng.integers(1, 10))] + [
                int(v) for v in rng.integers(0, 10, max(T - 1, 0))
            ]
            floor = [Fraction(1, 3)] + [Fraction(0)] * max(T - 1, 0)
            weights = [Fraction(int(v), 2) for v in rng.integers(1, 5, T)]
            inst = ExactInstance.from_rationals(
                K, q, demand, floor, weights,
                semantic_mode=CLASSICAL_ACTIVE_HORIZON,
            )
            graph_value, graph_paths = exact_graph_optimal_paths(inst)
            physical_value, physical_patterns = exact_physical_setup_optima(inst)
            mapped = tuple(sorted(
                path for path in (
                    setup_pattern_to_path(pattern, T) for pattern in physical_patterns
                ) if path is not None
            ))
            empty = sum(bool(empty_setup_nodes(inst.demand, p)) for p in graph_paths)
            match = graph_value == physical_value and tuple(sorted(graph_paths)) == mapped and empty == 0
            if not match:
                raise AssertionError(f"semantic bridge mismatch at T={T}, replicate={replicate}")
            rows.append({
                "T": T,
                "replicate": replicate,
                "graph_optimum": str(graph_value),
                "physical_optimum": str(physical_value),
                "graph_optimal_paths": len(graph_paths),
                "physical_optimal_patterns": len(physical_patterns),
                "empty_optimal_graph_paths": empty,
                "exact_match": match,
            })

    # The excluded reviewer counterexample is recorded as a negative control.
    excluded = ExactInstance.from_rationals(
        [100, 1], [1, 0], [0, 1], [0, 0], [1, 1],
        semantic_mode=FORCED_SOURCE_GRAPH,
    )
    graph_value, _ = exact_graph_optimal_paths(excluded)
    physical_value, _ = exact_physical_setup_optima(excluded)

    RAW.parent.mkdir(parents=True, exist_ok=True)
    with RAW.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "seed": 2026081801,
        "horizons": [1, 10],
        "classical_active_horizon_instances": len(rows),
        "exact_cost_and_optimal_setup_set_matches": len(rows),
        "optimal_paths_with_empty_later_setup": 0,
        "failures": 0,
        "negative_control": {
            "instance": "K=(100,1), q=(1,0), d=(0,1), floor=(0,0)",
            "forced_source_graph_optimum": str(graph_value),
            "ordinary_physical_optimum": str(physical_value),
            "classical_mode_admissible": False,
        },
        "scope": (
            "Finite exact-rational enumeration of small instances; supports the "
            "implementation and source-to-encoding bridge but does not replace its proof."
        ),
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
