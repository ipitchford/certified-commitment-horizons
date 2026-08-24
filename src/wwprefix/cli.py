"""Command-line interface.

Every value under a ``certified_*`` key is computed or re-verified in exact
rational arithmetic with zero tolerances (see ``wwprefix.exactcert``).
Floating-point results appear only under ``float_search`` and are labelled
diagnostic estimates; they never influence a certified classification.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Optional

import typer

from .bracket import polynomial_radius_bracket
from .certificate import frozen_certificate_lp
from .exact import fixed_radius_milp
from .exactcert import (
    CertifiedWitness,
    ExactBracketResult,
    ExactInstance,
    certified_exact_radius,
    certify_strong_witness,
    exact_common_optimal_prefix,
    exact_count_optimal_paths,
    exact_path_cost,
    exact_polynomial_bracket,
    exact_shortest_path,
    exact_triage,
    rat_float,
    rat_str,
)
from .serialization import (
    dump_json,
    exact_instance_from_mapping,
    instance_from_mapping,
    load_json,
    path_from_public,
    path_to_public,
)

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _parse_exact_radius(text: str, option: str) -> Fraction:
    try:
        value = Fraction(text)
    except (ValueError, ZeroDivisionError) as error:
        raise typer.BadParameter(
            f"{option} must be a decimal or p/q rational, e.g. '1.25' or '5/4'"
        ) from error
    if value < 0:
        raise typer.BadParameter(f"{option} must be non-negative")
    return value


def _load(path: Path):
    document = load_json(path)
    raw_instance = document.get("instance", document)
    if not isinstance(raw_instance, dict):
        raise typer.BadParameter("'instance' must be a JSON object")
    instance = instance_from_mapping(raw_instance)
    exact = exact_instance_from_mapping(raw_instance)
    optimum, nominal = exact_shortest_path(exact)
    if document.get("nominal_path") is not None:
        supplied = path_from_public(document["nominal_path"])
        if exact_path_cost(exact, exact.demand, supplied) != optimum:
            raise typer.BadParameter(
                "supplied nominal_path is not exactly optimal for the supplied "
                "instance; the exact optimum differs"
            )
        nominal = supplied
    return instance, exact, optimum, nominal


def _write(value: dict, output: Optional[Path]) -> None:
    text = dump_json(value, output)
    if output is None:
        typer.echo(text, nl=False)


def _exact_pair(value) -> dict:
    return {"float": rat_float(value), "exact": "inf" if value is None else rat_str(value)}


def _demand_public(demand) -> dict | None:
    if demand is None:
        return None
    return {
        "float": [float(v) for v in demand],
        "exact": [rat_str(v) for v in demand],
    }


def _witness_public(witness: CertifiedWitness | None) -> dict | None:
    if witness is None:
        return None
    return {
        "radius": _exact_pair(witness.radius),
        "demand": _demand_public(witness.demand),
        "outside_path": path_to_public(witness.outside_path),
        "inside_path": path_to_public(witness.inside_path),
        "inside_minus_outside_margin": _exact_pair(witness.margin),
    }


def _certified_bracket_public(bracket: ExactBracketResult) -> dict:
    frozen = bracket.frozen
    if bracket.status == "exact_infinite_no_outside_path":
        infinity = "proven_infinite_no_outside_path"
    elif bracket.status == "exact_infinite_saturation":
        infinity = "proven_infinite_saturation"
    else:
        infinity = "not_infinite"
    return {
        "arithmetic": "exact_rational_zero_tolerance",
        "status": bracket.status,
        "infinity_status": infinity,
        "exact_certified": bracket.exact_certified,
        "exact_reason": bracket.exact_reason,
        "lower_radius": _exact_pair(bracket.lower_radius),
        "upper_radius": _exact_pair(bracket.upper_radius),
        "exact_radius": None if bracket.exact_radius is None and not bracket.exact_certified
        else _exact_pair(bracket.exact_radius),
        "closure_holds": bracket.closure_holds,
        "frozen_certificate": {
            "radius": _exact_pair(frozen.radius),
            "status": frozen.status,
            "outside_path": path_to_public(frozen.outside_path),
            "witness_demand": _demand_public(frozen.witness),
            "witness_distance": None if frozen.witness_distance is None
            else _exact_pair(frozen.witness_distance),
            "residual_gap": None if frozen.residual_gap is None
            else _exact_pair(frozen.residual_gap),
            "intervals_inspected": frozen.intervals_inspected,
            "newton_iterations": frozen.newton_iterations,
            "graph_nodes": frozen.graph_nodes,
            "graph_arcs": frozen.graph_arcs,
        },
        "upper_witness": _witness_public(bracket.upper_witness),
    }


def _float_search_public(instance, nominal, k) -> dict:
    frozen = frozen_certificate_lp(instance, nominal, k)
    bracket = polynomial_radius_bracket(instance, nominal, k)
    return {
        "role": "diagnostic_floating_point_estimates_only_no_certification",
        "frozen_estimate": {
            "radius": frozen.radius,
            "status": frozen.status,
            "outside_path": path_to_public(frozen.outside_path),
            "intervals_checked": frozen.intervals_checked,
        },
        "bracket_estimate": {
            "lower_radius": bracket.lower_radius,
            "upper_radius": bracket.upper_radius,
            "status": bracket.status,
        },
    }




def _semantics_public(exact: ExactInstance) -> dict:
    classical = exact.semantic_mode == "classical_active_horizon"
    return {
        "mode": exact.semantic_mode,
        "classical_lot_sizing_bridge_active": classical,
        "interpretation": (
            "canonical productive setup schedules in the classical active-horizon "
            "Wagner-Whitin model"
            if classical
            else "forced-source path graph; period-1 setup is mandatory and empty "
            "zero-cost setup nodes remain distinct graph decisions"
        ),
        "bridge_conditions": (
            {
                "first_period_floor_strictly_positive": True,
                "later_setup_costs_strictly_positive": True,
            }
            if classical
            else None
        ),
    }

def _nominal_public(exact: ExactInstance, optimum, nominal, k) -> dict:
    common = exact_common_optimal_prefix(exact)
    prefix_common = k <= len(common) - 1 and nominal[: k + 1] == common[: k + 1]
    return {
        "path": path_to_public(nominal),
        "optimum": _exact_pair(optimum),
        "verified_exactly_optimal": True,
        "optima_count": exact_count_optimal_paths(exact, cap=10**9),
        "common_optimal_prefix": path_to_public(common),
        "protected_prefix_common_to_all_nominal_optima": prefix_common,
    }


def _escalation_public(result) -> dict:
    return {
        "arithmetic": "exact_rational_zero_tolerance",
        "status": result.status,
        "exact_certified": result.exact_certified,
        "lower_radius": _exact_pair(result.lower_radius),
        "upper_radius": _exact_pair(result.upper_radius),
        "exact_radius": None if result.exact_radius is None else _exact_pair(result.exact_radius),
        "witness": _witness_public(result.witness),
        "paths_total": result.paths_total,
        "paths_processed": result.paths_processed,
        "paths_pruned_exactly": result.paths_pruned_exactly,
        "disjuncts_upper_certified": result.disjuncts_upper_certified,
        "disjuncts_lower_certified": result.disjuncts_lower_certified,
        "disjuncts_unresolved": result.disjuncts_unresolved,
    }


@app.command()
def certify(
    input_file: Path = typer.Argument(..., exists=True, readable=True),
    k: int = typer.Option(..., min=1),
    exact: bool = typer.Option(False, "--exact", help="Certified finite-disjunction escalation."),
    proposed_radius: Optional[str] = typer.Option(
        None,
        "--proposed-radius",
        help="Decimal or p/q rational; parsed exactly (e.g. '1.25' or '5/4').",
    ),
    max_paths: Optional[int] = typer.Option(None, min=1),
    skip_float_search: bool = typer.Option(
        False, "--skip-float-search", help="Omit the diagnostic floating-point estimates."
    ),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    """Certified commitment record for the first k replenishment cycles."""
    instance, exact_inst, optimum, nominal = _load(input_file)
    if k > len(nominal) - 1:
        raise typer.BadParameter("k exceeds the number of nominal arcs")
    bracket = exact_polynomial_bracket(exact_inst, nominal, k)
    payload: dict = {
        "command": "certify",
        "schema_version": "3.0",
        "model_semantics": _semantics_public(exact_inst),
        "nominal": _nominal_public(exact_inst, optimum, nominal, k),
        "protected_arcs": k,
        "certified_bracket": _certified_bracket_public(bracket),
    }
    if not skip_float_search:
        payload["float_search"] = _float_search_public(instance, nominal, k)
    if proposed_radius is not None:
        proposed = _parse_exact_radius(proposed_radius, "--proposed-radius")
        payload["proposed_radius_triage"] = exact_triage(bracket, proposed)
    if exact:
        result = certified_exact_radius(exact_inst, nominal, k, max_paths=max_paths)
        payload["certified_exact_escalation"] = _escalation_public(result)
        if proposed_radius is not None:
            proposed = _parse_exact_radius(proposed_radius, "--proposed-radius")
            refined = dict(payload["proposed_radius_triage"])
            if result.lower_radius is None or (
                result.lower_radius is not None and proposed < result.lower_radius
            ):
                refined["classification"] = "certified_no_destabilisation"
                refined["basis"] = "proposed radius lies strictly below the certified escalated lower bound"
            elif result.upper_radius is not None and proposed >= result.upper_radius:
                refined["classification"] = "certified_destabilising_witness_exists"
                refined["basis"] = "an exactly verified witness destabilises within the proposed radius"
            payload["proposed_radius_triage"] = refined
    _write(payload, output)


@app.command()
def decide(
    input_file: Path = typer.Argument(..., exists=True, readable=True),
    k: int = typer.Option(..., min=1),
    radius: str = typer.Option(
        ..., help="Decimal or p/q rational; parsed exactly (e.g. '1.25' or '5/4')."
    ),
    time_limit: float = typer.Option(60.0, min=0.001),
    force_milp: bool = typer.Option(
        False, "--force-milp", help="Run the MILP even when the certificate already decides."
    ),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    """Decide WW-Prefix-Radius-infinity at a fixed radius.

    The certified layer decides whenever the exact bracket resolves the
    radius; the MILP is solver-level escalation whose affirmative witnesses
    are re-verified exactly and whose negative answers are reported as
    solver-level evidence, never as certificates.
    """
    instance, exact_inst, optimum, nominal = _load(input_file)
    if k > len(nominal) - 1:
        raise typer.BadParameter("k exceeds the number of nominal arcs")
    radius_exact = _parse_exact_radius(radius, "--radius")
    bracket = exact_polynomial_bracket(exact_inst, nominal, k)
    triage = exact_triage(bracket, radius_exact)
    payload: dict = {
        "command": "decide",
        "schema_version": "3.0",
        "model_semantics": _semantics_public(exact_inst),
        "nominal": _nominal_public(exact_inst, optimum, nominal, k),
        "protected_arcs": k,
        "certified_bracket": _certified_bracket_public(bracket),
        "certified_triage": triage,
    }
    needs_milp = force_milp or triage["classification"] == "unresolved_requires_exact_escalation"
    if needs_milp:
        result = fixed_radius_milp(
            instance, nominal, k, float(radius_exact), time_limit=time_limit
        )
        witness_certified = None
        if result.revised_demand is not None and result.outside_path is not None:
            prefix = nominal[: k + 1]
            witness = certify_strong_witness(
                exact_inst, prefix, result.outside_path, list(result.revised_demand)
            )
            witness_certified = witness is not None and witness.radius <= radius_exact
            if witness_certified:
                payload["certified_triage"] = {
                    **triage,
                    "classification": "certified_destabilising_witness_exists",
                    "basis": "the MILP witness was re-verified in exact arithmetic",
                }
                payload["certified_milp_witness"] = _witness_public(witness)
        payload["milp_escalation"] = {
            "assurance": "solver_level_only_not_exactly_certified",
            "radius": float(radius_exact),
            "decision": result.decision,
            "status": result.status,
            "solver_status": result.solver_status,
            "solver_message": result.solver_message,
            "minimum_gap_upper_bound": result.minimum_gap_upper_bound,
            "minimum_gap_lower_bound": result.minimum_gap_lower_bound,
            "mip_gap": result.mip_gap,
            "mip_node_count": result.mip_node_count,
            "outside_path": path_to_public(result.outside_path),
            "witness_exactly_verified": witness_certified,
        }
    _write(payload, output)


if __name__ == "__main__":
    app()
