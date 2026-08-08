#!/usr/bin/env python3
"""Deterministic audit of the exact rational certification layer.

Three pre-specified strata:

* agreement: broad synthetic and conditioned strict-gap instances; the exact
  frozen certificate is compared with complete enumeration in exact
  arithmetic (equality required), the floating estimate error is recorded,
  and every certified enumeration is checked for containment and closure;
* adversarial: the peer-review false-infinity counterexample (binary and
  decimal semantics), tiny slope gaps down to 1e-15, extreme weights,
  near-coincident breakpoints and exact power-of-two rescalings, which must
  never flip a certificate between finite and infinite or reverse a triage
  classification;
* scaling: certified bracket runtimes at operational horizons up to T=365.

The audit fails loudly (non-zero exit) on any exact disagreement.
"""
from __future__ import annotations

import os
from fractions import Fraction
from math import isinf
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
from wwprefix import shortest_path
from wwprefix.certificate import frozen_certificate_lp
from wwprefix.exactcert import (
    ExactInstance,
    certified_exact_radius,
    exact_frozen_certificate,
    exact_pairwise_radius,
    exact_polynomial_bracket,
    exact_shortest_path,
    exact_triage,
    rat_float,
)
from wwprefix.model import outside_paths
from wwprefix.serialization import exact_instance_from_mapping

QUICK = os.environ.get("WWPREFIX_AUDIT_QUICK") == "1"

REVIEWER_COUNTEREXAMPLE = {
    "K": [0.0, 1.000000001],
    "q": [1.0, 0.999999999],
    "demand": [1.0, 1.0],
    "floor": [1.0, 1.0],
    "weights": [1.0, 1e-09],
}


def brute_frozen(ei: ExactInstance, pstar, k):
    best = None
    for path in outside_paths(ei.T, pstar[: k + 1]):
        r = exact_pairwise_radius(ei, path, pstar).radius
        if r is not None and (best is None or r < best):
            best = r
    return best


def agreement_stratum() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows = []
    instance_id = 0
    horizon_range = range(2, 8 if QUICK else 9)
    per_regime = 4 if QUICK else 10
    for T in horizon_range:
        for regime in ("regular", "near_tie", "floor_heavy"):
            for _ in range(per_regime):
                instance = random_ww_instance(rng, T, regime=regime)
                _instance_rows(instance, instance_id, regime, rows)
                instance_id += 1
        if T >= 3:
            for _ in range(2 if QUICK else 4):
                instance, attempts = draw_strict_gap_instance(rng, T)
                _instance_rows(instance, instance_id, "strict_gap", rows)
                instance_id += 1
    return pd.DataFrame(rows)


def _instance_rows(instance, instance_id: int, regime: str, rows: list) -> None:
    _, pstar = shortest_path(instance)
    ei = ExactInstance.from_ww(instance)
    _, exact_nominal = exact_shortest_path(ei)
    for k in range(1, len(exact_nominal)):
        start = perf_counter()
        frozen = exact_frozen_certificate(ei, exact_nominal, k)
        frozen_seconds = perf_counter() - start
        brute = brute_frozen(ei, exact_nominal, k)
        if frozen.radius != brute:
            raise AssertionError(
                f"exact frozen disagrees with enumeration: id={instance_id} k={k}"
            )
        estimate = frozen_certificate_lp(instance, exact_nominal, k)
        if frozen.radius is None:
            float_error = 0.0 if isinf(estimate.radius) else float("nan")
            float_false_infinite = False
            float_false_finite = not isinf(estimate.radius)
        else:
            float_false_infinite = isinf(estimate.radius)
            float_false_finite = False
            float_error = (
                float("nan")
                if float_false_infinite
                else abs(estimate.radius - float(frozen.radius))
            )
        bracket = exact_polynomial_bracket(ei, exact_nominal, k)
        enum = certified_exact_radius(ei, exact_nominal, k)
        if enum.upper_radius is not None and bracket.lower_radius is not None:
            assert not (enum.upper_radius < bracket.lower_radius)
        if (
            enum.upper_radius is not None
            and bracket.upper_radius is not None
        ):
            assert not (bracket.upper_radius < enum.upper_radius)
        interval_width = None
        if (
            not enum.exact_certified
            and enum.upper_radius is not None
            and enum.lower_radius is not None
            and enum.upper_radius > 0
        ):
            interval_width = float(
                (enum.upper_radius - enum.lower_radius) / enum.upper_radius
            )
        rows.append(
            {
                "instance_id": instance_id,
                "regime": regime,
                "T": instance.T,
                "k": k,
                "is_full_path": k == len(exact_nominal) - 1,
                "exact_frozen_radius": rat_float(frozen.radius),
                "exact_frozen_is_infinite": frozen.radius is None,
                "frozen_status": frozen.status,
                "brute_force_match": True,
                "float_estimate_error": float_error,
                "float_false_infinite": float_false_infinite,
                "float_false_finite": float_false_finite,
                "bracket_status": bracket.status,
                "bracket_exact_certified": bracket.exact_certified,
                "enumeration_exact_certified": enum.exact_certified,
                "enumeration_interval_relative_width": interval_width,
                "frozen_seconds": frozen_seconds,
                "newton_iterations": frozen.newton_iterations,
                "shortest_path_evaluations": frozen.intervals_inspected,
            }
        )


def adversarial_stratum() -> pd.DataFrame:
    rows = []

    def record(name: str, mapping: dict, proposals: list[Fraction]) -> None:
        ei = exact_instance_from_mapping(mapping)
        _, nominal = exact_shortest_path(ei)
        bracket = exact_polynomial_bracket(ei, nominal, 1)
        for proposal in proposals:
            rows.append(
                {
                    "family": name,
                    "lower_radius": rat_float(bracket.lower_radius),
                    "upper_radius": rat_float(bracket.upper_radius),
                    "exact_certified": bracket.exact_certified,
                    "status": bracket.status,
                    "proposal": float(proposal),
                    "classification": exact_triage(bracket, proposal)["classification"],
                }
            )

    record(
        "reviewer_counterexample_binary",
        REVIEWER_COUNTEREXAMPLE,
        [Fraction(9, 10), Fraction(11, 10)],
    )
    record(
        "reviewer_counterexample_decimal",
        {
            "K": ["0", "1.000000001"],
            "q": ["1", "0.999999999"],
            "demand": ["1", "1"],
            "floor": ["1", "1"],
            "weights": ["1", "0.000000001"],
        },
        [Fraction(9, 10), Fraction(11, 10)],
    )
    for exponent in (-15, -12, -9, -6, -3):
        epsilon = 10.0**exponent
        record(
            f"tiny_slope_gap_1e{exponent}",
            {
                "K": [0.0, 1.0 + epsilon],
                "q": [1.0, 1.0 - epsilon],
                "demand": [1.0, 1.0],
                "floor": [1.0, 1.0],
                "weights": [1.0, epsilon],
            },
            [Fraction(1, 2), Fraction(2)],
        )
    for exponent in (-12, -6, 6, 12):
        scale = 10.0**exponent
        record(
            f"extreme_weights_1e{exponent}",
            {
                "K": [0.0, 3.0, 2.0],
                "q": [2.0, 1.0, 0.0],
                "demand": [1.0, 5.0, 1.0],
                "floor": [0.5, 0.5, 0.5],
                "weights": [scale, scale, scale],
            },
            [Fraction(1)],
        )
    record(
        "near_coincident_breakpoints",
        {
            "K": [0.0, 2.0, 4.0, 1.0],
            "q": [4.0, 3.0, 2.0, 1.0],
            "demand": [1.0, 1.0 + 2.0**-50, 2.0, 2.0],
            "floor": [0.0, 0.0, 1.0, 0.0],
            "weights": [1.0, 1.0, 1.0, 0.5],
        },
        [Fraction(1)],
    )

    # Exact power-of-two rescaling invariance of the counterexample family.
    base = REVIEWER_COUNTEREXAMPLE
    reference = None
    flips = 0
    for cost_exp in (-20, -3, 0, 7, 24):
        for unit_exp in (-8, 0, 9):
            cost_scale, unit_scale = 2.0**cost_exp, 2.0**unit_exp
            mapping = {
                "K": [v * cost_scale for v in base["K"]],
                "q": [v * cost_scale / unit_scale for v in base["q"]],
                "demand": [v * unit_scale for v in base["demand"]],
                "floor": [v * unit_scale for v in base["floor"]],
                "weights": [v / unit_scale for v in base["weights"]],
            }
            ei = exact_instance_from_mapping(mapping)
            _, nominal = exact_shortest_path(ei)
            bracket = exact_polynomial_bracket(ei, nominal, 1)
            signature = (
                bracket.exact_certified,
                bracket.exact_radius,
                exact_triage(bracket, Fraction(11, 10))["classification"],
                exact_triage(bracket, Fraction(9, 10))["classification"],
            )
            if reference is None:
                reference = signature
            elif signature != reference:
                flips += 1
            rows.append(
                {
                    "family": f"rescaling_2^{cost_exp}_2^{unit_exp}",
                    "lower_radius": rat_float(bracket.lower_radius),
                    "upper_radius": rat_float(bracket.upper_radius),
                    "exact_certified": bracket.exact_certified,
                    "status": bracket.status,
                    "proposal": 1.1,
                    "classification": signature[2],
                }
            )
    if flips:
        raise AssertionError(f"{flips} rescaling flips detected")
    return pd.DataFrame(rows)


def scaling_stratum() -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(SEED + 7)
    horizons = (50, 100) if QUICK else (50, 100, 200, 365)
    for T in horizons:
        for seed_index in range(1 if QUICK else 2):
            instance = random_ww_instance(rng, T, regime="regular")
            _, pstar = shortest_path(instance)
            ei = ExactInstance.from_ww(instance)
            _, nominal = exact_shortest_path(ei)
            for k in (1, min(3, len(nominal) - 1)):
                start = perf_counter()
                frozen = exact_frozen_certificate(ei, nominal, k)
                frozen_seconds = perf_counter() - start
                start = perf_counter()
                bracket = exact_polynomial_bracket(ei, nominal, k)
                bracket_seconds = perf_counter() - start
                rows.append(
                    {
                        "T": T,
                        "seed_index": seed_index,
                        "k": k,
                        "graph_arcs": frozen.graph_arcs,
                        "shortest_path_evaluations": frozen.intervals_inspected,
                        "newton_iterations": frozen.newton_iterations,
                        "frozen_seconds": frozen_seconds,
                        "bracket_seconds": bracket_seconds,
                        "frozen_status": frozen.status,
                        "bracket_status": bracket.status,
                        "exact_frozen_radius": rat_float(frozen.radius),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    agreement = agreement_stratum()
    adversarial = adversarial_stratum()
    scaling = scaling_stratum()
    write_csv(agreement, ROOT / "results/raw/exact_certification_audit.csv")
    write_csv(adversarial, ROOT / "results/raw/exact_adversarial_audit.csv")
    write_csv(scaling, ROOT / "results/raw/exact_scaling_study.csv")

    finite = agreement[~agreement["exact_frozen_is_infinite"]]
    widths = agreement["enumeration_interval_relative_width"].dropna()
    summary = {
        "environment": environment_record(),
        "agreement": {
            "rows": int(len(agreement)),
            "instances": int(agreement["instance_id"].nunique()),
            "brute_force_matches": int(agreement["brute_force_match"].sum()),
            "float_false_infinite_count": int(agreement["float_false_infinite"].sum()),
            "float_false_finite_count": int(agreement["float_false_finite"].sum()),
            "float_max_error_on_finite": float(
                finite["float_estimate_error"].dropna().abs().max()
            ),
            "bracket_exact_certified": int(agreement["bracket_exact_certified"].sum()),
            "enumeration_exact_certified": int(
                agreement["enumeration_exact_certified"].sum()
            ),
            "enumeration_interval_cases": int(widths.size),
            "enumeration_interval_max_relative_width": (
                float(widths.max()) if widths.size else 0.0
            ),
        },
        "adversarial": {
            "rows": int(len(adversarial)),
            "families": int(adversarial["family"].nunique()),
            "rescaling_flips": 0,
            "counterexample_binary_triage_1_1": str(
                adversarial.loc[
                    (adversarial["family"] == "reviewer_counterexample_binary")
                    & (adversarial["proposal"] == 1.1),
                    "classification",
                ].iloc[0]
            ),
        },
        "scaling": {
            "rows": int(len(scaling)),
            "per_horizon_seconds": {
                str(T): {
                    "frozen_max": float(group["frozen_seconds"].max()),
                    "bracket_max": float(group["bracket_seconds"].max()),
                }
                for T, group in scaling.groupby("T")
            },
        },
    }
    write_json(summary, ROOT / "results/processed/exact_certification_summary.json")
    print(
        f"agreement rows={len(agreement)} "
        f"float_false_infinite={summary['agreement']['float_false_infinite_count']} "
        f"adversarial rows={len(adversarial)} scaling rows={len(scaling)}"
    )


if __name__ == "__main__":
    main()
