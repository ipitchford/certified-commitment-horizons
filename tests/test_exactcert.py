"""Exact certification layer: regression, adversarial and invariance tests.

The decisive requirement (peer review v2.0.0, comment 4.1) is that no valid
instance can receive a false one-sided safety classification, and that
positive rescalings and unit changes can never flip a certificate between
finite and infinite or reverse a commitment decision.
"""
from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from wwprefix import WWInstance, shortest_path
from wwprefix.cli import app
from wwprefix.exactcert import (
    CertificationError,
    ExactInstance,
    certified_exact_radius,
    certify_strong_witness,
    exact_frozen_certificate,
    exact_halfspace_radius,
    exact_pairwise_radius,
    exact_polynomial_bracket,
    exact_shortest_path,
    exact_triage,
    exact_verify_nominal_optimal,
)
from wwprefix.model import outside_paths
from wwprefix.serialization import exact_instance_from_mapping


REVIEWER_COUNTEREXAMPLE = {
    "K": [0.0, 1.000000001],
    "q": [1.0, 0.999999999],
    "demand": [1.0, 1.0],
    "floor": [1.0, 1.0],
    "weights": [1.0, 1e-09],
}


def random_instance(rng: np.random.Generator, T: int) -> WWInstance:
    return WWInstance.create(
        K=rng.uniform(0, 12, T),
        q=np.cumsum(rng.uniform(0.1, 1.8, T)[::-1])[::-1],
        demand=rng.uniform(0.8, 8, T),
        floor=rng.uniform(0, 0.5, T),
        weights=rng.uniform(0.5, 2, T),
    )


def brute_frozen(ei: ExactInstance, pstar, k):
    best = None
    for path in outside_paths(ei.T, pstar[: k + 1]):
        r = exact_pairwise_radius(ei, path, pstar).radius
        if r is not None and (best is None or r < best):
            best = r
    return best


# ---------------------------------------------------------------------------
# Reviewer counterexample regression (review v2.0.0, comment 4.1)
# ---------------------------------------------------------------------------


def test_reviewer_counterexample_binary_semantics() -> None:
    ei = exact_instance_from_mapping(REVIEWER_COUNTEREXAMPLE)
    _, nominal = exact_shortest_path(ei)
    assert nominal == (0, 2)
    bracket = exact_polynomial_bracket(ei, nominal, 1)
    assert bracket.exact_certified
    assert bracket.exact_radius is not None
    # The exact radius of the binary-float instance is close to, not equal
    # to, one; what matters is the certified classification of 1.1 and 0.9.
    assert abs(float(bracket.exact_radius) - 1.0) < 1e-7
    assert exact_triage(bracket, Fraction(11, 10))["classification"] == (
        "certified_destabilising_witness_exists"
    )
    assert exact_triage(bracket, Fraction(9, 10))["classification"] == (
        "certified_no_destabilisation"
    )


def test_reviewer_counterexample_decimal_semantics() -> None:
    decimal_form = {
        "K": ["0", "1.000000001"],
        "q": ["1", "0.999999999"],
        "demand": ["1", "1"],
        "floor": ["1", "1"],
        "weights": ["1", "0.000000001"],
    }
    ei = exact_instance_from_mapping(decimal_form)
    _, nominal = exact_shortest_path(ei)
    bracket = exact_polynomial_bracket(ei, nominal, 1)
    assert bracket.exact_certified
    assert bracket.exact_radius == Fraction(1)
    assert exact_triage(bracket, Fraction(11, 10))["classification"] == (
        "certified_destabilising_witness_exists"
    )


def test_reviewer_counterexample_cli_triage(tmp_path: Path) -> None:
    input_path = tmp_path / "instance.json"
    input_path.write_text(json.dumps({"instance": REVIEWER_COUNTEREXAMPLE}))
    output_path = tmp_path / "decision.json"
    result = CliRunner().invoke(
        app,
        ["certify", str(input_path), "--k", "1", "--proposed-radius", "1.1",
         "-o", str(output_path)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(output_path.read_text())
    assert payload["certified_bracket"]["exact_certified"] is True
    assert payload["certified_bracket"]["infinity_status"] == "not_infinite"
    assert payload["proposed_radius_triage"]["classification"] == (
        "certified_destabilising_witness_exists"
    )


# ---------------------------------------------------------------------------
# Rescaling and unit invariance (review v2.0.0, decisive acceptance test)
# ---------------------------------------------------------------------------


def _scaled_instance(base: dict, cost_scale: float, unit_scale: float) -> dict:
    return {
        "K": [v * cost_scale for v in base["K"]],
        "q": [v * cost_scale / unit_scale for v in base["q"]],
        "demand": [v * unit_scale for v in base["demand"]],
        "floor": [v * unit_scale for v in base["floor"]],
        "weights": [v / unit_scale for v in base["weights"]],
    }


@pytest.mark.parametrize("cost_scale", [2.0**-20, 2.0**-3, 1.0, 2.0**7, 2.0**24])
@pytest.mark.parametrize("unit_scale", [2.0**-8, 1.0, 2.0**9])
def test_rescaling_never_flips_the_certificate(cost_scale, unit_scale) -> None:
    base = REVIEWER_COUNTEREXAMPLE
    scaled = _scaled_instance(base, cost_scale, unit_scale)
    ei = exact_instance_from_mapping(scaled)
    _, nominal = exact_shortest_path(ei)
    bracket = exact_polynomial_bracket(ei, nominal, 1)
    reference = exact_polynomial_bracket(
        exact_instance_from_mapping(base),
        nominal,
        1,
    )
    # Power-of-two rescalings are exact in binary floating point, so the
    # certified radius must transform exactly and the classification of a
    # correspondingly scaled proposal must be identical.
    assert bracket.exact_certified == reference.exact_certified
    assert bracket.exact_radius == reference.exact_radius  # weights absorb units
    for proposal in (Fraction(9, 10), Fraction(11, 10)):
        assert (
            exact_triage(bracket, proposal)["classification"]
            == exact_triage(reference, proposal)["classification"]
        )


def test_rescaling_random_instances() -> None:
    rng = np.random.default_rng(31)
    for T in (3, 5, 7):
        inst = random_instance(rng, T)
        base = {
            "K": list(map(float, inst.K)),
            "q": list(map(float, inst.q)),
            "demand": list(map(float, inst.demand)),
            "floor": list(map(float, inst.floor)),
            "weights": list(map(float, inst.weights)),
        }
        ei = exact_instance_from_mapping(base)
        _, nominal = exact_shortest_path(ei)
        for k in range(1, len(nominal) - 1 + 1):
            reference = exact_polynomial_bracket(ei, nominal, k)
            for cost_scale, unit_scale in ((2.0**11, 1.0), (2.0**-13, 2.0**5), (1.0, 2.0**-6)):
                scaled = exact_instance_from_mapping(
                    _scaled_instance(base, cost_scale, unit_scale)
                )
                other = exact_polynomial_bracket(scaled, nominal, k)
                assert other.exact_certified == reference.exact_certified
                assert (other.lower_radius is None) == (reference.lower_radius is None)
                assert other.lower_radius == reference.lower_radius
                assert (other.upper_radius is None) == (reference.upper_radius is None)


# ---------------------------------------------------------------------------
# Adversarial families (review v2.0.0, comment 4.1 required tests)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gap_exp", [-15, -12, -9, -6, -3])
def test_tiny_slope_differences_never_vanish(gap_exp: int) -> None:
    """Slope gaps far below any absolute tolerance must stay decisions.

    Near the unit of least precision the binary values legitimately deviate
    from the decimal notation, so the reference value is computed a priori
    from the exact rationals actually supplied, not from the decimals.
    """
    epsilon = 10.0**gap_exp
    ei = exact_instance_from_mapping(
        {
            "K": [0.0, 1.0 + epsilon],
            "q": [1.0, 1.0 - epsilon],
            "demand": [1.0, 1.0],
            "floor": [1.0, 1.0],
            "weights": [1.0, epsilon],
        }
    )
    _, nominal = exact_shortest_path(ei)
    bracket = exact_polynomial_bracket(ei, nominal, 1)
    assert bracket.lower_radius is not None, "a finite radius was promoted to infinity"
    assert bracket.exact_certified
    # Single competing path (0,1,2): gap closes only by raising d_2, so the
    # exact radius is gap / slope for the supplied binary rationals.
    gap = ei.K[1] + (ei.q[1] - ei.q[0]) * ei.demand[1]
    slope = (ei.q[0] - ei.q[1]) / ei.weights[1]
    assert slope > 0
    assert bracket.exact_radius == gap / slope


@pytest.mark.parametrize("weight_exp", [-12, -6, 0, 6, 12])
def test_extreme_weights(weight_exp: int) -> None:
    scale = 10.0**weight_exp
    ei = exact_instance_from_mapping(
        {
            "K": [0.0, 3.0, 2.0],
            "q": [2.0, 1.0, 0.0],
            "demand": [1.0, 5.0, 1.0],
            "floor": [0.5, 0.5, 0.5],
            "weights": [scale, scale, scale],
        }
    )
    _, nominal = exact_shortest_path(ei)
    frozen = exact_frozen_certificate(ei, nominal, 1)
    assert frozen.radius == Fraction(3, 2) * Fraction(scale)


def test_near_coincident_breakpoints() -> None:
    """Breakpoints separated by one ulp stay distinct interval endpoints."""
    d2 = 1.0 + 2.0**-50
    ei = exact_instance_from_mapping(
        {
            "K": [0.0, 2.0, 4.0, 1.0],
            "q": [4.0, 3.0, 2.0, 1.0],
            "demand": [1.0, d2, 2.0, 2.0],
            "floor": [0.0, 0.0, 1.0, 0.0],
            "weights": [1.0, 1.0, 1.0, 0.5],
        }
    )
    _, nominal = exact_shortest_path(ei)
    for k in range(1, len(nominal)):
        frozen = exact_frozen_certificate(ei, nominal, k)
        assert frozen.radius == brute_frozen(ei, nominal, k)


def test_huge_setup_with_tiny_slope_gap() -> None:
    ei = exact_instance_from_mapping(
        {
            "K": [0.0, 1e9],
            "q": [1.0 + 1e-12, 1.0],
            "demand": [10.0, 10.0],
            "floor": [0.0, 0.0],
            "weights": [1.0, 1.0],
        }
    )
    _, nominal = exact_shortest_path(ei)
    frozen = exact_frozen_certificate(ei, nominal, 1)
    # The gap of roughly 1e9 must be closed through a slope of roughly 1e-12
    # per unit; the certified radius is astronomically large but finite.
    assert frozen.status == "finite"
    assert frozen.radius is not None and float(frozen.radius) > 1e19


def test_proven_infinite_saturation_is_reported_as_proof() -> None:
    # Both slopes equal: no direction ever separates the two paths except
    # the setup cost, which cannot be closed; the frozen radius is provably
    # infinite (this is the v2.0.0 pairwise zero-denominator example).
    ei = exact_instance_from_mapping(
        {"K": [0.0, 1.0], "q": [1.0, 1.0], "demand": [2.0, 3.0], "floor": [0.0, 0.0]}
    )
    _, nominal = exact_shortest_path(ei)
    bracket = exact_polynomial_bracket(ei, nominal, 1)
    assert bracket.status == "exact_infinite_saturation"
    assert bracket.exact_certified
    assert bracket.frozen.residual_gap == Fraction(1)
    assert exact_triage(bracket, Fraction(10**12))["classification"] == (
        "certified_no_destabilisation"
    )


# ---------------------------------------------------------------------------
# Structural agreement with brute force and the float layer
# ---------------------------------------------------------------------------


def test_exact_frozen_matches_brute_force_random() -> None:
    rng = np.random.default_rng(20260805)
    checked = 0
    for T in range(2, 8):
        for _ in range(8):
            inst = random_instance(rng, T)
            _, pstar = shortest_path(inst)
            ei = ExactInstance.from_ww(inst)
            assert exact_verify_nominal_optimal(ei, pstar)
            for k in range(1, len(pstar)):
                frozen = exact_frozen_certificate(ei, pstar, k)
                assert frozen.radius == brute_frozen(ei, pstar, k)
                checked += 1
    assert checked > 100


def test_certified_enumeration_brackets_and_monotonicity() -> None:
    rng = np.random.default_rng(2718)
    for T in range(3, 7):
        for _ in range(4):
            inst = random_instance(rng, T)
            _, pstar = shortest_path(inst)
            ei = ExactInstance.from_ww(inst)
            uppers = []
            for k in range(1, len(pstar)):
                result = certified_exact_radius(ei, pstar, k)
                bracket = exact_polynomial_bracket(ei, pstar, k)
                if result.upper_radius is not None and bracket.lower_radius is not None:
                    assert not (result.upper_radius < bracket.lower_radius)
                if result.exact_certified and result.upper_radius is not None:
                    assert result.lower_radius == result.upper_radius
                uppers.append(result.upper_radius)
            # Monotonicity is a theorem about the true radii, not about
            # independently found feasible upper witnesses for unresolved
            # disjuncts.  Check it only where both adjacent radii are exactly
            # certified; for intervals, check only lower <= upper.
            results = [
                certified_exact_radius(ei, pstar, k)
                for k in range(1, len(pstar))
            ]
            for result in results:
                if result.lower_radius is not None and result.upper_radius is not None:
                    assert result.lower_radius <= result.upper_radius
            for previous, current in zip(results, results[1:]):
                if previous.exact_certified and current.exact_certified:
                    if previous.exact_radius is None:
                        continue  # any finite value is <= +infinity
                    assert current.exact_radius is not None
                    assert current.exact_radius <= previous.exact_radius


def test_exact_and_float_layers_agree_on_benign_instances() -> None:
    from wwprefix.certificate import frozen_certificate_lp

    rng = np.random.default_rng(99)
    agreements = 0
    for T in range(2, 8):
        for _ in range(6):
            inst = random_instance(rng, T)
            _, pstar = shortest_path(inst)
            ei = ExactInstance.from_ww(inst)
            for k in range(1, len(pstar)):
                exact = exact_frozen_certificate(ei, pstar, k)
                estimate = frozen_certificate_lp(inst, pstar, k)
                if exact.radius is None:
                    assert math.isinf(estimate.radius)
                else:
                    assert estimate.radius == pytest.approx(
                        float(exact.radius), rel=3e-6, abs=3e-6
                    )
                agreements += 1
    assert agreements > 90


# ---------------------------------------------------------------------------
# Primitive-level checks
# ---------------------------------------------------------------------------


def test_halfspace_radius_hand_computed() -> None:
    ei = ExactInstance.from_rationals(
        K=[0, 0], q=[1, 1], demand=[4, 6], floor=[1, 0], weights=[2, 1]
    )
    # gap 5, coefficients (1, -1): reduce d1 toward the floor at rate 1/2
    # until the breakpoint 2*(4-1)=6, and raise d2 at rate 1 throughout.
    result = exact_halfspace_radius(ei, Fraction(5), [Fraction(1), Fraction(-1)])
    assert result.radius == Fraction(10, 3)
    assert result.witness is not None
    # Witness sits inside the truncated box and closes the gap exactly.
    d1, d2 = result.witness
    assert d1 == Fraction(4) - Fraction(10, 3) / 2
    assert d2 == Fraction(6) + Fraction(10, 3)


def test_halfspace_saturated_then_infinite() -> None:
    ei = ExactInstance.from_rationals(
        K=[0], q=[1], demand=[3], floor=[2], weights=[1]
    )
    finite = exact_halfspace_radius(ei, Fraction(1, 2), [Fraction(1)])
    assert finite.radius == Fraction(1, 2)
    infinite = exact_halfspace_radius(ei, Fraction(2), [Fraction(1)])
    assert infinite.radius is None and infinite.status == "proven_infinite"


def test_strong_witness_rejects_bad_demands() -> None:
    ei = ExactInstance.from_rationals(
        K=[0, 3, 2], q=[2, 1, 0], demand=[1, 5, 1], floor=[Fraction(1, 2)] * 3,
        weights=[1, 1, 1],
    )
    _, nominal = exact_shortest_path(ei)
    prefix = nominal[:2]
    below_floor = [Fraction(0), Fraction(5), Fraction(1)]
    assert certify_strong_witness(ei, prefix, (0, 2, 3), below_floor) is None
    nominal_demand = list(ei.demand)
    assert certify_strong_witness(ei, prefix, (0, 2, 3), nominal_demand) is None


def test_supplied_nominal_must_be_exactly_optimal(tmp_path: Path) -> None:
    input_path = tmp_path / "instance.json"
    input_path.write_text(
        json.dumps(
            {
                "instance": {"K": [0, 3, 2], "q": [2, 1, 0], "demand": [1, 5, 1]},
                "nominal_path": [1, 4],
            }
        )
    )
    result = CliRunner().invoke(app, ["certify", str(input_path), "--k", "1"])
    assert result.exit_code != 0
    assert "not exactly optimal" in result.output


def test_disordered_slopes_rejected_exactly() -> None:
    with pytest.raises(ValueError, match="non-increasing"):
        exact_instance_from_mapping(
            {"K": [0, 0], "q": [1.0, 1.0 + 1e-13], "demand": [1, 1]}
        )


# ---------------------------------------------------------------------------
# CLI and independent checker integration
# ---------------------------------------------------------------------------


def test_cli_strict_instance_certified_schema(tmp_path: Path) -> None:
    input_path = tmp_path / "instance.json"
    input_path.write_text(json.dumps({
        "instance": {
            "K": [0, 3, 2], "q": [2, 1, 0], "demand": [1, 5, 1],
            "floor": [0.5, 0.5, 0.5], "weights": [1, 1, 1]
        }
    }))
    output_path = tmp_path / "decision.json"
    result = CliRunner().invoke(
        app,
        ["certify", str(input_path), "--k", "1", "--exact",
         "--proposed-radius", "1.75", "-o", str(output_path)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(output_path.read_text())
    bracket = payload["certified_bracket"]
    assert bracket["lower_radius"]["exact"] == "3/2"
    assert bracket["upper_radius"]["exact"] == "2/1"
    assert bracket["exact_certified"] is False
    escalation = payload["certified_exact_escalation"]
    assert escalation["exact_certified"] is True
    assert escalation["exact_radius"]["exact"] == "2/1"
    # 1.75 sits inside the polynomial bracket but the certified escalation
    # proves the exact radius is 2, so the triage refines to safe.
    assert payload["proposed_radius_triage"]["classification"] == (
        "certified_no_destabilisation"
    )
    assert payload["float_search"]["role"].startswith("diagnostic")


def test_independent_checker_passes_on_generated_records(tmp_path: Path) -> None:
    import subprocess
    import sys

    instance = {
        "instance": {
            "K": [0, 3, 2], "q": [2, 1, 0], "demand": [1, 5, 1],
            "floor": [0.5, 0.5, 0.5], "weights": [1, 1, 1]
        }
    }
    input_path = tmp_path / "instance.json"
    input_path.write_text(json.dumps(instance))
    output_path = tmp_path / "decision.json"
    result = CliRunner().invoke(
        app,
        ["certify", str(input_path), "--k", "1", "--exact",
         "--proposed-radius", "2.5", "-o", str(output_path)],
    )
    assert result.exit_code == 0, result.output
    checker = Path(__file__).resolve().parents[1] / "scripts" / "check_certificate.py"
    run = subprocess.run(
        [sys.executable, str(checker), str(output_path), str(input_path)],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "verified independently" in run.stdout


def test_decide_uses_certificate_before_milp(tmp_path: Path) -> None:
    input_path = tmp_path / "instance.json"
    input_path.write_text(json.dumps({
        "instance": {
            "K": [0, 3, 2], "q": [2, 1, 0], "demand": [1, 5, 1],
            "floor": [0.5, 0.5, 0.5], "weights": [1, 1, 1]
        }
    }))
    output_path = tmp_path / "decide.json"
    result = CliRunner().invoke(
        app, ["decide", str(input_path), "--k", "1", "--radius", "1.25",
              "-o", str(output_path)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(output_path.read_text())
    assert payload["certified_triage"]["classification"] == "certified_no_destabilisation"
    assert "milp_escalation" not in payload

    unresolved_path = tmp_path / "decide2.json"
    result = CliRunner().invoke(
        app, ["decide", str(input_path), "--k", "1", "--radius", "1.75",
              "-o", str(unresolved_path)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(unresolved_path.read_text())
    milp = payload["milp_escalation"]
    assert milp["assurance"] == "solver_level_only_not_exactly_certified"
    assert payload["certified_triage"]["classification"] == (
        "unresolved_requires_exact_escalation"
    )
    assert milp["decision"] is False
    # A solver-level negative answer must never surface as a certificate.
    assert milp["witness_exactly_verified"] is not True

    witness_path = tmp_path / "decide3.json"
    result = CliRunner().invoke(
        app, ["decide", str(input_path), "--k", "1", "--radius", "2",
              "-o", str(witness_path)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(witness_path.read_text())
    assert payload["certified_triage"]["classification"] == (
        "certified_destabilising_witness_exists"
    )


# ---------------------------------------------------------------------------
# Regressions motivated by the Sol adversarial review of the repair (2026-08-05)
# ---------------------------------------------------------------------------


def test_flat_zero_segment_after_crossing_lands_on_first_crossing() -> None:
    """F(r) = 1 - r on [0,1] then identically 0: the crossing coincides with a
    breakpoint and a flat-zero segment follows.  The certified radius must be
    exactly the first crossing (Sol review, item 3)."""
    ei = ExactInstance.from_rationals(
        K=[0, 0], q=[1, 0], demand=[0, 1], floor=[0, 0], weights=[1, 1]
    )
    _, nominal = exact_shortest_path(ei)
    assert nominal == (0, 1, 2)
    frozen = exact_frozen_certificate(ei, nominal, 1)
    assert frozen.radius == Fraction(1)
    bracket = exact_polynomial_bracket(ei, nominal, 1)
    assert bracket.exact_certified and bracket.exact_radius == Fraction(1)


def test_nan_and_infinity_inputs_rejected_by_both_layers() -> None:
    """Sol review, item 8: non-finite inputs must never reach certification."""
    from wwprefix.serialization import instance_from_mapping

    for bad in (float("nan"), float("inf"), -float("inf")):
        mapping = {"K": [0.0, 1.0], "q": [1.0, 1.0], "demand": [1.0, bad]}
        with pytest.raises((ValueError, OverflowError)):
            instance_from_mapping(mapping)
        with pytest.raises((ValueError, OverflowError)):
            exact_instance_from_mapping(mapping)


def test_checker_verifies_saturation_infinity_record(tmp_path: Path) -> None:
    """The independent checker must re-prove a saturation-infinity claim
    (Sol review, item 9 exercises the checker's own dynamic programme)."""
    import subprocess
    import sys

    instance = {
        "instance": {"K": [0.0, 1.0], "q": [1.0, 1.0], "demand": [2.0, 3.0],
                      "floor": [0.0, 0.0]}
    }
    input_path = tmp_path / "instance.json"
    input_path.write_text(json.dumps(instance))
    output_path = tmp_path / "decision.json"
    result = CliRunner().invoke(
        app,
        ["certify", str(input_path), "--k", "1", "--proposed-radius", "1e9",
         "-o", str(output_path)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(output_path.read_text())
    assert payload["certified_bracket"]["infinity_status"] == "proven_infinite_saturation"
    assert payload["proposed_radius_triage"]["classification"] == (
        "certified_no_destabilisation"
    )
    checker = Path(__file__).resolve().parents[1] / "scripts" / "check_certificate.py"
    run = subprocess.run(
        [sys.executable, str(checker), str(output_path), str(input_path)],
        capture_output=True, text=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "saturation" in run.stdout
