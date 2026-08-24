#!/usr/bin/env python3
"""Finite exact audit of the optimal-face edge-witness theorem."""
from __future__ import annotations

import csv
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from wwprefix.exactcert import ExactInstance, certified_exact_radius, exact_shortest_path, rat_str
from wwprefix.optimal_face import find_optimal_face_edge_witness

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw" / "optimal_face_edge_audit.csv"
SUMMARY = ROOT / "results" / "processed" / "optimal_face_edge_audit_summary.json"


def main() -> None:
    rng = np.random.default_rng(20260818)
    rows: list[dict[str, object]] = []
    case = 0
    for T in range(2, 9):
        for replicate in range(12):
            K = [int(v) for v in rng.integers(0, 8, T)]
            q = list(np.cumsum(rng.integers(0, 5, T)[::-1])[::-1])
            demand = [int(v) for v in rng.integers(1, 9, T)]
            floor = [min(int(a), b) for a, b in zip(rng.integers(0, 3, T), demand)]
            weights = [Fraction(int(v), 2) for v in rng.integers(1, 5, T)]
            inst = ExactInstance.from_rationals(K, q, demand, floor, weights)
            _, nominal = exact_shortest_path(inst)
            for k in range(1, len(nominal)):
                case += 1
                result = certified_exact_radius(inst, nominal, k)
                row: dict[str, object] = {
                    "case": case,
                    "T": T,
                    "replicate": replicate,
                    "k": k,
                    "nominal_path": "-".join(map(str, nominal)),
                    "status": result.status,
                    "exact_certified": result.exact_certified,
                    "exact_radius": rat_str(result.exact_radius),
                    "has_finite_witness": result.witness is not None,
                    "edge_witness_found": "not_applicable",
                    "optimal_path_count": "",
                    "inside_path": "",
                    "outside_path": "",
                    "divergence_node": "",
                    "remergence_node": "",
                }
                if result.exact_certified and result.witness is not None:
                    edge = find_optimal_face_edge_witness(
                        inst, result.witness.demand, nominal[: k + 1]
                    )
                    if edge is None:
                        raise AssertionError("finite exact destabilising witness lacks crossing edge")
                    row.update({
                        "edge_witness_found": True,
                        "optimal_path_count": edge.optimal_path_count,
                        "inside_path": "-".join(map(str, edge.inside_path)),
                        "outside_path": "-".join(map(str, edge.outside_path)),
                        "divergence_node": edge.divergence_node,
                        "remergence_node": edge.remergence_node,
                    })
                rows.append(row)

    RAW.parent.mkdir(parents=True, exist_ok=True)
    with RAW.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    # Restrict the denominator to finite, exactly certified destabilising witnesses.
    applicable = [r for r in rows if r["edge_witness_found"] is True]
    summary = {
        "seed": 20260818,
        "horizons": [2, 8],
        "instances": 7 * 12,
        "prefix_cases": len(rows),
        "finite_exact_witness_cases": len(applicable),
        "single_detour_edge_witnesses_found": sum(
            1 for r in applicable if r["edge_witness_found"] is True
        ),
        "failures": 0,
        "scope": (
            "Finite exact-rational audit of theorem implementation on random integer "
            "instances; not a proof of the universal theorem."
        ),
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
