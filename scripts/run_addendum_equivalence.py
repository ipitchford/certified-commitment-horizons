#!/usr/bin/env python3
"""Corpus equivalence gate for the compact production-balance solver.

Regenerates the release's existing small-instance corpora deterministically
and requires the compact minimum-radius model to reproduce every exact
T<=18 radius, witness and infinite-radius result before any scalability
claim is made (addendum item 5; the brief's sanity check).

Strata:

* ``agreement``: the exact-certification audit corpus (T = 2..8, regimes
  regular / near_tie / floor_heavy / strict_gap, every protected k).  The
  reference is ``certified_exact_radius`` in exact rational arithmetic.
  Finite references require the compact radius to match to 1e-6 relative,
  an exactly re-verified witness, and — adversarially — that the certified
  witness radius is never strictly below the reference rational (which
  would refute the reference).  Infinite references require
  ``no_destabilisation_within_cap`` at a generous probe cap, recorded as
  solver-level consistency, with the exact infinity certificate remaining
  the exact layer's.
* ``benchmark``: the exact-benchmark corpus (T = 6..18, k = 1).  The
  reference is the released float enumeration (15 s limit, historically all
  resolved).  The compact radius and its certified witness must agree to
  1e-6 relative.
* ``decomposition``: for agreement instances with T <= 7, the exact
  min-over-arcs radius must equal the direct certified radius as rationals.

Exit code is non-zero on any disagreement.  Results:
``results/raw/addendum_equivalence.csv`` and
``results/processed/addendum_equivalence_summary.json``.
"""
from __future__ import annotations

import os
import sys
from fractions import Fraction
from math import inf, isfinite
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
    ExactInstance,
    certified_exact_radius,
    compact_radius_milp,
    decomposed_certified_radius,
    exact_radius_enumeration,
    shortest_path,
)
from wwprefix.exactcert import exact_shortest_path, rat_float

QUICK = os.environ.get("WWPREFIX_ADDENDUM_QUICK") == "1"
REL_TOL = 1e-6


def _spread(instance) -> float:
    return float(np.max(instance.weights * (instance.demand - instance.floor)))


def _cap(instance, anchor: float) -> float:
    return 4.0 * (1.0 + _spread(instance) + anchor)


def _agreement_instances():
    rng = np.random.default_rng(SEED)
    instance_id = 0
    horizon_range = range(2, 8 if QUICK else 9)
    per_regime = 4 if QUICK else 10
    for T in horizon_range:
        for regime in ("regular", "near_tie", "floor_heavy"):
            for _ in range(per_regime):
                yield instance_id, regime, random_ww_instance(rng, T, regime=regime)
                instance_id += 1
        if T >= 3:
            for _ in range(2 if QUICK else 4):
                instance, _attempts = draw_strict_gap_instance(rng, T)
                yield instance_id, "strict_gap", instance
                instance_id += 1


def _benchmark_instances():
    rng = np.random.default_rng(SEED + 101)
    instance_id = 0
    horizons = (6, 10) if QUICK else (6, 10, 14, 16, 18)
    for T in horizons:
        for regime in ("regular", "near_tie", "strict_gap"):
            for _rep in range(2):
                if regime == "strict_gap":
                    instance, _attempts = draw_strict_gap_instance(rng, T)
                else:
                    instance = random_ww_instance(rng, T, regime=regime)
                instance_id += 1
                yield instance_id, regime, instance


def _agreement_rows(rows: list[dict], failures: list[str]) -> None:
    for instance_id, regime, instance in _agreement_instances():
        ei = ExactInstance.from_ww(instance)
        _, nominal = exact_shortest_path(ei)
        for k in range(1, len(nominal)):
            reference = certified_exact_radius(ei, nominal, k)
            row = {
                "stratum": "agreement",
                "instance_id": instance_id,
                "regime": regime,
                "T": instance.T,
                "k": k,
                "reference_status": reference.status,
                "reference_certified": reference.exact_certified,
                "reference_radius": rat_float(reference.exact_radius)
                if reference.exact_certified
                else None,
            }
            if not reference.exact_certified:
                row["match_class"] = "reference_unresolved"
                rows.append(row)
                continue
            if reference.exact_radius is not None:
                exact_value = float(reference.exact_radius)
                start = perf_counter()
                result = compact_radius_milp(
                    instance, nominal, k, radius_cap=_cap(instance, exact_value)
                )
                row["compact_seconds"] = perf_counter() - start
                row["compact_status"] = result.status
                row["compact_radius"] = result.radius
                ok = (
                    result.status == "optimal"
                    and result.radius is not None
                    and abs(result.radius - exact_value) <= REL_TOL * (1.0 + exact_value)
                    and result.certified_witness is not None
                )
                if ok:
                    certified = result.certified_witness.radius
                    row["certified_witness_radius"] = float(certified)
                    if certified < reference.exact_radius:
                        failures.append(
                            f"agreement id={instance_id} k={k}: certified witness "
                            f"{certified} strictly below exact reference "
                            f"{reference.exact_radius} — reference refuted?"
                        )
                        row["match_class"] = "witness_below_reference"
                    elif abs(float(certified) - exact_value) <= REL_TOL * (1.0 + exact_value):
                        row["match_class"] = "exact_match_certified"
                    else:
                        failures.append(
                            f"agreement id={instance_id} k={k}: certified witness "
                            f"radius {float(certified)} far from exact {exact_value}"
                        )
                        row["match_class"] = "certified_witness_gap"
                else:
                    failures.append(
                        f"agreement id={instance_id} k={k}: compact radius "
                        f"{result.radius} ({result.status}) vs exact {exact_value}"
                    )
                    row["match_class"] = "radius_mismatch"
            else:
                start = perf_counter()
                result = compact_radius_milp(
                    instance, nominal, k, radius_cap=_cap(instance, 0.0)
                )
                row["compact_seconds"] = perf_counter() - start
                row["compact_status"] = result.status
                if result.status == "no_destabilisation_within_cap":
                    row["match_class"] = "infinite_consistent_within_cap"
                else:
                    failures.append(
                        f"agreement id={instance_id} k={k}: reference infinite but "
                        f"compact returned {result.status} radius {result.radius}"
                    )
                    row["match_class"] = "infinite_mismatch"
            rows.append(row)


def _benchmark_rows(rows: list[dict], failures: list[str]) -> None:
    for instance_id, regime, instance in _benchmark_instances():
        _, nominal = shortest_path(instance)
        k = 1
        reference = exact_radius_enumeration(instance, nominal, k, time_limit=15.0)
        row = {
            "stratum": "benchmark",
            "instance_id": instance_id,
            "regime": regime,
            "T": instance.T,
            "k": k,
            "reference_status": reference.status,
            "reference_radius": None if not isfinite(reference.radius) else reference.radius,
        }
        if reference.status == "optimal" and isfinite(reference.radius):
            start = perf_counter()
            result = compact_radius_milp(
                instance, nominal, k, radius_cap=_cap(instance, reference.radius)
            )
            row["compact_seconds"] = perf_counter() - start
            row["compact_status"] = result.status
            row["compact_radius"] = result.radius
            scale = 1.0 + reference.radius
            ok = (
                result.status == "optimal"
                and result.radius is not None
                and abs(result.radius - reference.radius) <= REL_TOL * scale
                and result.certified_witness is not None
                and abs(float(result.certified_witness.radius) - reference.radius)
                <= REL_TOL * scale
            )
            if ok:
                row["certified_witness_radius"] = float(result.certified_witness.radius)
                row["match_class"] = "float_match_certified"
            else:
                failures.append(
                    f"benchmark id={instance_id} T={instance.T}: compact "
                    f"{result.radius} ({result.status}) vs enumeration {reference.radius}"
                )
                row["match_class"] = "radius_mismatch"
        elif reference.status == "infinite":
            start = perf_counter()
            result = compact_radius_milp(
                instance, nominal, k, radius_cap=_cap(instance, 0.0)
            )
            row["compact_seconds"] = perf_counter() - start
            row["compact_status"] = result.status
            if result.status == "no_destabilisation_within_cap":
                row["match_class"] = "infinite_consistent_within_cap"
            else:
                failures.append(
                    f"benchmark id={instance_id}: reference infinite but compact "
                    f"returned {result.status}"
                )
                row["match_class"] = "infinite_mismatch"
        else:
            row["match_class"] = "reference_unresolved"
        rows.append(row)


def _decomposition_rows(rows: list[dict], failures: list[str]) -> None:
    for instance_id, regime, instance in _agreement_instances():
        if instance.T > 7:
            continue
        ei = ExactInstance.from_ww(instance)
        _, nominal = exact_shortest_path(ei)
        for k in range(1, len(nominal)):
            direct = certified_exact_radius(ei, nominal, k)
            decomposed = decomposed_certified_radius(ei, nominal, k)
            row = {
                "stratum": "decomposition",
                "instance_id": instance_id,
                "regime": regime,
                "T": instance.T,
                "k": k,
                "reference_certified": direct.exact_certified,
                "decomposed_certified": decomposed.exact_certified,
            }
            if direct.exact_certified and decomposed.exact_certified:
                if decomposed.exact_radius == direct.exact_radius:
                    row["match_class"] = "exact_rational_equality"
                    row["reference_radius"] = rat_float(direct.exact_radius)
                else:
                    failures.append(
                        f"decomposition id={instance_id} k={k}: min-over-arcs "
                        f"{decomposed.exact_radius} != direct {direct.exact_radius}"
                    )
                    row["match_class"] = "decomposition_mismatch"
            else:
                row["match_class"] = "unresolved_pair"
            rows.append(row)


def main() -> None:
    rows: list[dict] = []
    failures: list[str] = []
    start = perf_counter()
    _agreement_rows(rows, failures)
    _benchmark_rows(rows, failures)
    _decomposition_rows(rows, failures)
    frame = pd.DataFrame(rows)
    write_csv(frame, ROOT / "results" / "raw" / "addendum_equivalence.csv")

    counts = frame["match_class"].value_counts().to_dict()
    summary = {
        "rows": int(len(frame)),
        "match_class_counts": {k: int(v) for k, v in counts.items()},
        "failures": failures,
        "zero_disagreements": not failures,
        "quick_mode": QUICK,
        "relative_tolerance": REL_TOL,
        "wall_seconds": perf_counter() - start,
        "environment": environment_record(),
        "gate": (
            "PASSED: the compact model reproduces every resolved exact "
            "reference; scaling benchmark may run"
            if not failures
            else "FAILED: scaling benchmark must not run"
        ),
    }
    write_json(summary, ROOT / "results" / "processed" / "addendum_equivalence_summary.json")
    print(f"rows={len(frame)} classes={counts}")
    if failures:
        print("DISAGREEMENTS:")
        for line in failures:
            print(" -", line)
        sys.exit(1)
    print("equivalence gate PASSED")


if __name__ == "__main__":
    main()
