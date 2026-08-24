#!/usr/bin/env python3
"""Preregistered scaling benchmark (addendum item 6).

Implements `docs/benchmark_preregistration_addendum.md` exactly; the frozen
design's SHA-256 is recorded in the summary. The equivalence gate
(`results/processed/addendum_equivalence_summary.json`,
`zero_disagreements: true`) is a hard precondition.

Usage: run_addendum_benchmark.py [--smoke]
`--smoke` restricts to T=18 for a pipeline check; a smoke run never
overwrites full results (separate file suffix).
"""
from __future__ import annotations

import hashlib
import resource
import sys
from math import ceil, inf, isfinite
from pathlib import Path
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
    compact_fixed_radius_milp,
    compact_radius_milp,
    exact_polynomial_bracket,
    exact_radius_enumeration,
    fixed_radius_milp,
    shortest_path,
)
from wwprefix.exactcert import rat_float
from wwprefix.model import outside_path_count

HORIZONS = (18, 25, 35, 50, 75, 100)
FAMILIES = ("regular", "near_tie", "adversarial")
REPLICATES = 2
M1_CANDIDATE_CAP = 2**21
M1_TIME_LIMIT = 180.0
MILP_TIME_LIMIT = 60.0
PREREG = ROOT / "docs" / "benchmark_preregistration_addendum.md"


def _rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 * 1024.0)


def _instance_for(cell_index: int, T: int, family: str, rep: int):
    rng = np.random.default_rng(SEED + 7000 + cell_index)
    if family == "adversarial":
        if rep == 0:
            return random_ww_instance(rng, T, regime="floor_heavy"), "floor_heavy"
        instance, _attempts = draw_strict_gap_instance(rng, T)
        return instance, "strict_gap"
    return random_ww_instance(rng, T, regime=family), family


def _record(rows, base, method, **kwargs):
    row = dict(base)
    row["method"] = method
    row.update(kwargs)
    rows.append(row)


def _run_cell(rows: list[dict], base: dict, instance, nominal, k: int) -> None:
    prefix = nominal[: k + 1]
    n_out = outside_path_count(instance.T, prefix)
    base = dict(base, k=k, s_node=prefix[-1], n_out_closed_form=n_out)

    # M4: polynomial certificate bracket (exact rational ends).
    inst = ExactInstance.from_ww(instance)
    rss0, t0 = _rss_mb(), perf_counter()
    bracket = exact_polynomial_bracket(inst, nominal, k)
    m4_seconds = perf_counter() - t0
    lower = bracket.lower_radius
    upper = bracket.upper_radius
    _record(
        rows, base, "M4_polynomial_bracket",
        wall_seconds=m4_seconds, rss_peak_mb=_rss_mb(), rss_delta_mb=max(0.0, _rss_mb() - rss0),
        status=bracket.status, exact_certified=bracket.exact_certified,
        lower_radius=rat_float(lower), upper_radius=rat_float(upper),
        bracket_width_rel=(
            float((upper - lower) / (1 + upper)) if lower is not None and upper is not None else None
        ),
        # The bracket's task is certified bounds; it resolves whenever it
        # returns certified ends (exact closure or a certified interval).
        resolved=bracket.status
        in {
            "exact_finite",
            "exact_infinite_no_outside_path",
            "exact_infinite_saturation",
            "finite_bracket_certified_ends",
        },
    )

    lower_f = rat_float(lower)
    upper_f = rat_float(upper)
    anchor = 0.0
    if isfinite(upper_f):
        anchor = upper_f
    elif isfinite(lower_f):
        anchor = lower_f
    spread = float(np.max(instance.weights * (instance.demand - instance.floor)))
    radius_cap = 4.0 * (1.0 + spread + anchor)
    if isfinite(lower_f) and isfinite(upper_f):
        probe = 0.5 * (lower_f + upper_f)
    elif isfinite(lower_f):
        probe = lower_f
    else:
        probe = radius_cap / 4.0

    # M1: exhaustive enumeration under the closed-form candidate guard.
    rss0, t0 = _rss_mb(), perf_counter()
    m1 = exact_radius_enumeration(
        instance, nominal, k, max_candidates=M1_CANDIDATE_CAP, time_limit=M1_TIME_LIMIT
    )
    _record(
        rows, base, "M1_enumeration",
        wall_seconds=perf_counter() - t0, rss_peak_mb=_rss_mb(),
        rss_delta_mb=max(0.0, _rss_mb() - rss0),
        status=m1.status, radius=None if not isfinite(m1.radius) else m1.radius,
        lower_radius=None if not isfinite(m1.lower_bound) else m1.lower_bound,
        paths_total=m1.paths_total, paths_processed=m1.paths_processed,
        candidate_generation_seconds=m1.candidate_generation_seconds,
        resolved=m1.status in {"optimal", "infinite"},
    )

    # M2: released arc-product fixed-radius MILP at the probe.
    rss0, t0 = _rss_mb(), perf_counter()
    try:
        m2 = fixed_radius_milp(
            instance, nominal, k, probe, time_limit=MILP_TIME_LIMIT
        )
        _record(
            rows, base, "M2_arc_product_milp",
            wall_seconds=perf_counter() - t0, rss_peak_mb=_rss_mb(),
            rss_delta_mb=max(0.0, _rss_mb() - rss0),
            status=m2.status, probe_radius=probe, decision=m2.decision,
            mip_nodes=m2.mip_node_count, mip_gap=m2.mip_gap,
            resolved=m2.decision is not None,
        )
    except MemoryError:
        _record(
            rows, base, "M2_arc_product_milp",
            wall_seconds=perf_counter() - t0, rss_peak_mb=_rss_mb(),
            rss_delta_mb=max(0.0, _rss_mb() - rss0),
            status="memory_error", probe_radius=probe, decision=None, resolved=False,
        )

    # M3: compact minimum-radius model.
    rss0, t0 = _rss_mb(), perf_counter()
    m3 = compact_radius_milp(
        instance, nominal, k, radius_cap=radius_cap, time_limit=MILP_TIME_LIMIT
    )
    certified = None if m3.certified_witness is None else float(m3.certified_witness.radius)
    _record(
        rows, base, "M3_compact_min_radius",
        wall_seconds=perf_counter() - t0, rss_peak_mb=_rss_mb(),
        rss_delta_mb=max(0.0, _rss_mb() - rss0),
        status=m3.status, radius=m3.radius, radius_cap=radius_cap,
        certified_witness_radius=certified,
        mip_nodes=m3.mip_node_count, mip_gap=m3.mip_gap,
        n_variables=m3.n_variables, n_constraints=m3.n_constraints,
        resolved=m3.status in {"optimal", "no_destabilisation_within_cap"},
        lower_bound_consistent=(
            None if m3.radius is None or not isfinite(lower_f)
            else bool(m3.radius >= lower_f - 1e-6 * (1 + abs(lower_f)))
        ),
    )

    # M3b: compact decision model at the same probe.
    rss0, t0 = _rss_mb(), perf_counter()
    m3b = compact_fixed_radius_milp(
        instance, nominal, k, probe, time_limit=MILP_TIME_LIMIT
    )
    _record(
        rows, base, "M3b_compact_decision",
        wall_seconds=perf_counter() - t0, rss_peak_mb=_rss_mb(),
        rss_delta_mb=max(0.0, _rss_mb() - rss0),
        status=m3b.status, probe_radius=probe, decision=m3b.decision,
        mip_nodes=m3b.mip_node_count, mip_gap=m3b.mip_gap,
        n_variables=m3b.n_variables, n_constraints=m3b.n_constraints,
        resolved=m3b.decision is not None,
    )


def main() -> None:
    smoke = "--smoke" in sys.argv
    summarise_only = "--summarise-only" in sys.argv
    gate_path = ROOT / "results" / "processed" / "addendum_equivalence_summary.json"
    if not gate_path.exists():
        sys.exit("equivalence gate summary missing; run run_addendum_equivalence.py first")
    import json

    gate = json.loads(gate_path.read_text())
    if not gate.get("zero_disagreements"):
        sys.exit("equivalence gate FAILED; the benchmark must not run")

    prereg_hash = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    suffix = "_smoke" if smoke else ""
    deviations: list[str] = []
    start = perf_counter()
    if summarise_only:
        # Rebuild the summary from the existing raw rows without re-running
        # any solve.  Used once on 2026-08-18 after the M4 rows' missing
        # `resolved` flag was fixed; the deviation is recorded below.
        frame = pd.read_csv(ROOT / "results" / "raw" / f"addendum_benchmark{suffix}.csv")
        if "resolved" in frame.columns:
            m4_mask = frame["method"] == "M4_polynomial_bracket"
            frame.loc[m4_mask, "resolved"] = frame.loc[m4_mask, "status"].isin(
                [
                    "exact_finite",
                    "exact_infinite_no_outside_path",
                    "exact_infinite_saturation",
                    "finite_bracket_certified_ends",
                ]
            )
        deviations.append(
            "2026-08-18: summary recomputed from unchanged raw rows after fixing "
            "the missing `resolved` flag on M4_polynomial_bracket records "
            "(bracket rows previously counted as unresolved in P1)."
        )
    else:
        horizons = (18,) if smoke else HORIZONS
        rows: list[dict] = []
        cell_index = 0
        for T in HORIZONS:
            for family in FAMILIES:
                for rep in range(REPLICATES):
                    current = cell_index
                    cell_index += 1
                    if T not in horizons:
                        continue
                    instance, variant = _instance_for(current, T, family, rep)
                    _, nominal = shortest_path(instance)
                    m = len(nominal) - 1
                    k = max(1, ceil(m / 2))
                    base = {
                        "cell_index": current,
                        "T": T,
                        "family": family,
                        "variant": variant,
                        "replicate": rep,
                        "nominal_arcs": m,
                    }
                    _run_cell(rows, base, instance, nominal, k)
                    if T == 18 and m >= 1:
                        _run_cell(rows, dict(base, contrast="full_path"), instance, nominal, m)
                    print(
                        f"cell {current} done: T={T} {family}/{variant} rep={rep} "
                        f"({perf_counter() - start:.0f}s elapsed)",
                        flush=True,
                    )
        frame = pd.DataFrame(rows)
        write_csv(frame, ROOT / "results" / "raw" / f"addendum_benchmark{suffix}.csv")

    def _p1(method: str) -> int | None:
        resolved = frame[(frame["method"] == method) & (frame["resolved"] == True)]  # noqa: E712
        return None if resolved.empty else int(resolved["T"].max())

    wall_seconds_total = perf_counter() - start
    if summarise_only:
        prior_path = ROOT / "results" / "processed" / f"addendum_benchmark_summary{suffix}.json"
        if prior_path.exists():
            prior = json.loads(prior_path.read_text())
            wall_seconds_total = prior.get("wall_seconds_total", wall_seconds_total)
            deviations[:0] = [d for d in prior.get("deviations", []) if d not in deviations]
    summary = {
        "preregistration_sha256": prereg_hash,
        "smoke": smoke,
        "rows": int(len(frame)),
        "wall_seconds_total": wall_seconds_total,
        "P1_largest_resolved_T": {
            method: _p1(method)
            for method in (
                "M1_enumeration", "M2_arc_product_milp",
                "M3_compact_min_radius", "M3b_compact_decision",
                "M4_polynomial_bracket",
            )
        },
        "M1_refusals": int((frame["status"] == "refused_by_candidate_guard").sum()),
        "deviations": deviations,
        "environment": environment_record(),
    }
    if not smoke:
        both = frame[frame["method"].isin(["M2_arc_product_milp", "M3b_compact_decision"])]
        pivot = both.pivot_table(
            index=["cell_index", "k"], columns="method", values="wall_seconds", aggfunc="first"
        ).dropna()
        if not pivot.empty:
            ratio = pivot["M2_arc_product_milp"] / pivot["M3b_compact_decision"]
            summary["P2_decision_walltime_ratio_M2_over_M3b"] = {
                "median": float(ratio.median()),
                "p25": float(ratio.quantile(0.25)),
                "p75": float(ratio.quantile(0.75)),
                "cells": int(len(ratio)),
            }
        m4 = frame[frame["method"] == "M4_polynomial_bracket"]
        widths = m4["bracket_width_rel"].dropna()
        summary["P3_bracket_width_rel"] = {
            "median": None if widths.empty else float(widths.median()),
            "max": None if widths.empty else float(widths.max()),
            "closed_fraction": float((m4["exact_certified"] == True).mean()),  # noqa: E712
        }
    write_json(summary, ROOT / "results" / "processed" / f"addendum_benchmark_summary{suffix}.json")
    print(f"rows={len(frame)} wall={summary['wall_seconds_total']:.0f}s")


if __name__ == "__main__":
    main()
