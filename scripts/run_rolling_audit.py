#!/usr/bin/env python3
"""Deterministic audit of the Bellman-residual dead-zone theorem.

The audit samples positive-demand Wagner--Whitin instances, commits a nominal
setup prefix, draws floor-admissible realised demand, and checks the structural
regret bound using the conservative floating-point safe radius.  Literal order
quantities remain adjustable to realised demand; only setup epochs and cycle
boundaries are fixed.
"""
from __future__ import annotations

from math import isfinite

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
    WWInstance,
    bellman_residual,
    coefficient_diameter,
    dead_zone_bound,
    exact_radius_enumeration,
    frozen_certificate_lp,
    generic_lipschitz_bound,
    revision_norm,
    shortest_path,
)


def _realised_at_target_norm(
    instance: WWInstance,
    rng: np.random.Generator,
    target: float,
) -> np.ndarray:
    """Draw a direction and form a floor-admissible realised demand vector."""
    if target <= 0:
        return instance.demand.copy()
    direction = rng.normal(size=instance.T)
    direction /= max(np.max(np.abs(direction)), 1e-12)
    proposal = instance.demand + target * direction / instance.weights
    return np.maximum(instance.floor, proposal)


def _record_case(
    rows: list[dict[str, object]],
    *,
    case_id: int,
    stratum: str,
    regime: str,
    instance: WWInstance,
    nominal: tuple[int, ...],
    k: int,
    realised: np.ndarray,
    target_multiplier: float | None,
) -> None:
    prefix = nominal[: k + 1]
    certificate = frozen_certificate_lp(instance, nominal, k)
    radius = certificate.safe_radius
    norm = revision_norm(instance, instance.demand, realised, start=prefix[0])
    diameter = coefficient_diameter(instance, start=prefix[0])
    residual = bellman_residual(instance, realised, prefix)
    generic = generic_lipschitz_bound(
        instance, instance.demand, realised, start=prefix[0]
    )
    dead = dead_zone_bound(
        instance, instance.demand, realised, start=prefix[0], radius=radius
    )
    tolerance = 2e-7 * (1.0 + abs(dead) + abs(residual))
    rows.append(
        {
            "case_id": case_id,
            "stratum": stratum,
            "regime": regime,
            "T": instance.T,
            "nominal_arcs": len(nominal) - 1,
            "protected_arcs": k,
            "radius": radius,
            "radius_status": certificate.status,
            "target_multiplier": target_multiplier,
            "revision_norm": norm,
            "coefficient_diameter": diameter,
            "bellman_residual": residual,
            "generic_bound": generic,
            "dead_zone_bound": dead,
            "dead_zone_slack": dead - residual,
            "generic_slack": generic - residual,
            "dead_le_generic": bool(dead <= generic + tolerance),
            "theorem_holds": bool(residual <= dead + tolerance),
            "inside_dead_zone": bool((not isfinite(radius)) or norm <= radius + tolerance),
            "zero_residual_inside_dead_zone": bool(
                (not isfinite(radius) or norm <= radius + tolerance)
                and residual <= tolerance
            ),
        }
    )


def main() -> None:
    rng = np.random.default_rng(SEED + 41)
    rows: list[dict[str, object]] = []
    case_id = 0

    # Broad, unconditioned synthetic stratum.
    regimes = ("regular", "near_tie", "floor_heavy")
    horizons = tuple(range(3, 13))
    multipliers = (0.0, 0.35, 0.8, 1.0, 1.25, 2.0)
    for regime in regimes:
        for T in horizons:
            for rep in range(8):
                instance = random_ww_instance(rng, T, regime=regime)
                _, nominal = shortest_path(instance)
                k = int(rng.integers(1, len(nominal)))
                certificate = frozen_certificate_lp(instance, nominal, k)
                multiplier = multipliers[(rep + T) % len(multipliers)]
                if isfinite(certificate.safe_radius):
                    target = multiplier * max(certificate.safe_radius, 1e-7)
                else:
                    target = float(rng.uniform(0.1, 3.0))
                realised = _realised_at_target_norm(instance, rng, target)
                case_id += 1
                _record_case(
                    rows,
                    case_id=case_id,
                    stratum="broad_unconditioned",
                    regime=regime,
                    instance=instance,
                    nominal=nominal,
                    k=k,
                    realised=realised,
                    target_multiplier=multiplier,
                )

    # Deliberately conditioned adversarial stratum.  It tests strict lower
    # certificates; it is not used to estimate prevalence in any population.
    for T in (3, 5, 7, 9, 11):
        for rep in range(24):
            instance, _ = draw_strict_gap_instance(rng, T)
            _, nominal = shortest_path(instance)
            k = 1
            certificate = frozen_certificate_lp(instance, nominal, k)
            multiplier = multipliers[(rep + T) % len(multipliers)]
            target = multiplier * max(certificate.safe_radius, 1e-7)
            realised = _realised_at_target_norm(instance, rng, target)
            case_id += 1
            _record_case(
                rows,
                case_id=case_id,
                stratum="conditioned_adversarial",
                regime="strict_gap",
                instance=instance,
                nominal=nominal,
                k=k,
                realised=realised,
                target_multiplier=multiplier,
            )

    # Condition on a realised revision that makes an outside path strictly
    # better.  This deliberately stresses positive-regret cases and is not a
    # prevalence sample.  Exact enumeration is restricted to T <= 10.
    positive_target = 100
    positive_found = 0
    positive_attempts = 0
    while positive_found < positive_target and positive_attempts < 500:
        positive_attempts += 1
        T = int(rng.integers(3, 11))
        regime = regimes[int(rng.integers(0, len(regimes)))]
        instance = random_ww_instance(rng, T, regime=regime)
        _, nominal = shortest_path(instance)
        k = int(rng.integers(1, len(nominal)))
        exact = exact_radius_enumeration(instance, nominal, k, time_limit=3.0)
        if exact.status != "optimal" or exact.revised_demand is None:
            continue
        direction = exact.revised_demand - instance.demand
        if np.max(np.abs(direction)) <= 1e-10:
            continue
        realised = None
        # First extend radially beyond the exact boundary.
        for factor in (1.02, 1.05, 1.15, 1.35, 1.75, 2.5):
            candidate = np.maximum(instance.floor, instance.demand + factor * direction)
            if bellman_residual(instance, candidate, nominal[: k + 1]) > 1e-8:
                realised = candidate
                break
        if realised is None:
            continue
        positive_found += 1
        case_id += 1
        _record_case(
            rows,
            case_id=case_id,
            stratum="conditioned_destabilising",
            regime=regime,
            instance=instance,
            nominal=nominal,
            k=k,
            realised=realised,
            target_multiplier=None,
        )

    # Explicit edge cases required by the theorem statement.
    degenerate = WWInstance.create(
        K=[0.0, 1.0], q=[1.0, 0.0], demand=[1.0, 1.0], floor=[0.0, 0.0]
    )
    _, nominal = shortest_path(degenerate)
    case_id += 1
    _record_case(
        rows,
        case_id=case_id,
        stratum="edge_case",
        regime="nominal_tie_zero_radius",
        instance=degenerate,
        nominal=nominal,
        k=1,
        realised=np.asarray([1.4, 0.9]),
        target_multiplier=None,
    )

    singleton = WWInstance.create(K=[5.0], q=[0.0], demand=[2.0], floor=[0.0])
    _, nominal = shortest_path(singleton)
    case_id += 1
    _record_case(
        rows,
        case_id=case_id,
        stratum="edge_case",
        regime="no_outside_infinite_radius",
        instance=singleton,
        nominal=nominal,
        k=1,
        realised=np.asarray([5.0]),
        target_multiplier=None,
    )

    df = pd.DataFrame(rows)
    write_csv(df, ROOT / "results/raw/rolling_audit.csv")

    finite_ratio = df.loc[
        (df["bellman_residual"] > 1e-10) & np.isfinite(df["dead_zone_bound"]),
        "dead_zone_bound",
    ].to_numpy() / df.loc[
        (df["bellman_residual"] > 1e-10) & np.isfinite(df["dead_zone_bound"]),
        "bellman_residual",
    ].to_numpy()
    generic_ratio = df.loc[
        df["bellman_residual"] > 1e-10, "generic_bound"
    ].to_numpy() / df.loc[df["bellman_residual"] > 1e-10, "bellman_residual"].to_numpy()

    inside = df["inside_dead_zone"].astype(bool)
    summary = {
        "environment": environment_record(),
        "scope": (
            "structural setup decisions with uncapacitated quantity recourse; "
            "all realised demand vectors satisfy the coordinate floors"
        ),
        "design": {
            "broad_instances": int((df["stratum"] == "broad_unconditioned").sum()),
            "conditioned_adversarial_instances": int(
                (df["stratum"] == "conditioned_adversarial").sum()
            ),
            "conditioned_destabilising_instances": int(
                (df["stratum"] == "conditioned_destabilising").sum()
            ),
            "conditioned_destabilising_attempts": positive_attempts,
            "edge_cases": int((df["stratum"] == "edge_case").sum()),
            "horizons": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "target_norm_multipliers": list(multipliers),
        },
        "cases": int(len(df)),
        "theorem_violations": int((~df["theorem_holds"].astype(bool)).sum()),
        "dead_exceeds_generic_violations": int((~df["dead_le_generic"].astype(bool)).sum()),
        "max_residual_minus_dead_bound": float(
            (df["bellman_residual"] - df["dead_zone_bound"]).max()
        ),
        "max_dead_minus_generic": float(
            (df["dead_zone_bound"] - df["generic_bound"]).max()
        ),
        "inside_dead_zone_cases": int(inside.sum()),
        "inside_dead_zone_nonzero_residual_cases": int(
            (~df.loc[inside, "zero_residual_inside_dead_zone"].astype(bool)).sum()
        ),
        "residual_quantiles": {
            key: float(value)
            for key, value in zip(
                ["p50", "p75", "p90", "p95", "max"],
                np.quantile(df["bellman_residual"], [0.5, 0.75, 0.9, 0.95, 1.0]),
            )
        },
        "dead_bound_quantiles": {
            key: float(value)
            for key, value in zip(
                ["p50", "p75", "p90", "p95", "max"],
                np.quantile(df["dead_zone_bound"], [0.5, 0.75, 0.9, 0.95, 1.0]),
            )
        },
        "generic_bound_quantiles": {
            key: float(value)
            for key, value in zip(
                ["p50", "p75", "p90", "p95", "max"],
                np.quantile(df["generic_bound"], [0.5, 0.75, 0.9, 0.95, 1.0]),
            )
        },
        "bound_to_positive_residual_ratios": {
            "positive_residual_cases": int((df["bellman_residual"] > 1e-10).sum()),
            "dead_zone": {
                "median": None if finite_ratio.size == 0 else float(np.median(finite_ratio)),
                "p90": None if finite_ratio.size == 0 else float(np.quantile(finite_ratio, 0.9)),
                "max": None if finite_ratio.size == 0 else float(np.max(finite_ratio)),
            },
            "generic": {
                "median": None if generic_ratio.size == 0 else float(np.median(generic_ratio)),
                "p90": None if generic_ratio.size == 0 else float(np.quantile(generic_ratio, 0.9)),
                "max": None if generic_ratio.size == 0 else float(np.max(generic_ratio)),
            },
        },
        "edge_case_records": df.loc[df["stratum"] == "edge_case"].to_dict("records"),
    }
    write_json(summary, ROOT / "results/processed/rolling_audit_summary.json")
    print(summary)


if __name__ == "__main__":
    main()
