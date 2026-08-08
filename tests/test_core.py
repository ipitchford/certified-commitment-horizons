from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import linprog
from typer.testing import CliRunner

from wwprefix import (
    WWInstance,
    common_optimal_prefix,
    count_optimal_paths,
    exact_radius_enumeration,
    fixed_competitor_inverse_lp,
    fixed_radius_milp,
    frozen_certificate_exhaustive,
    frozen_certificate_lp,
    path_cost,
    shortest_path,
    verify_acyclic_nonnegative_circulation_property,
    verify_graph_bijection,
)
from wwprefix.cli import app
from wwprefix.graph import build_prefix_deviation_graph
from wwprefix.model import enumerate_paths, follows_prefix, path_coefficients
from wwprefix.pairwise import path_pairwise_radius


def strict_instance() -> WWInstance:
    return WWInstance.create(
        K=[0, 3, 2],
        q=[2, 1, 0],
        demand=[1, 5, 1],
        floor=[0.5, 0.5, 0.5],
        weights=[1, 1, 1],
    )


def random_instance(rng: np.random.Generator, T: int) -> WWInstance:
    return WWInstance.create(
        K=rng.uniform(0, 12, T),
        q=np.cumsum(rng.uniform(0.1, 1.8, T)[::-1])[::-1],
        demand=rng.uniform(0.8, 8, T),
        floor=rng.uniform(0, 0.5, T),
        weights=rng.uniform(0.5, 2, T),
    )


def test_instance_validation() -> None:
    with pytest.raises(ValueError):
        WWInstance.create(K=[1, 2], q=[0, 1], demand=[1, 1])
    with pytest.raises(ValueError):
        WWInstance.create(K=[1], q=[0], demand=[-1])
    with pytest.raises(ValueError):
        WWInstance.create(K=[1], q=[0], demand=[1], weights=[0])


def test_strict_example_path_costs_and_radii() -> None:
    inst = strict_instance()
    optimum, pstar = shortest_path(inst)
    assert pstar == (0, 1, 3)
    assert optimum == pytest.approx(11.0)
    costs = {p: path_cost(inst, inst.demand, p) for p in enumerate_paths(inst.T)}
    assert costs[(0, 3)] == pytest.approx(14)
    assert costs[(0, 1, 3)] == pytest.approx(11)
    assert costs[(0, 2, 3)] == pytest.approx(14)
    assert costs[(0, 1, 2, 3)] == pytest.approx(12)

    frozen = frozen_certificate_lp(inst, pstar, 1)
    exhaustive = frozen_certificate_exhaustive(inst, pstar, 1)
    exact = exact_radius_enumeration(inst, pstar, 1)
    assert frozen.radius == pytest.approx(1.5, abs=1e-7)
    assert frozen.safe_radius < frozen.radius
    assert exhaustive.radius == pytest.approx(1.5, abs=1e-9)
    assert exact.status == "optimal"
    assert exact.radius == pytest.approx(2.0, abs=1e-7)
    assert exact.lower_bound == pytest.approx(exact.radius)
    assert exact.outside_path == (0, 2, 3)
    assert exact.verified_difference is not None and exact.verified_difference <= 1e-7


def test_graph_bijection_and_acyclicity() -> None:
    rng = np.random.default_rng(4)
    for T in range(1, 8):
        inst = random_instance(rng, T)
        _, pstar = shortest_path(inst)
        for k in range(1, len(pstar)):
            assert verify_graph_bijection(inst, pstar, k)[0] == verify_graph_bijection(inst, pstar, k)[1]
            graph = build_prefix_deviation_graph(inst, pstar, k)
            assert verify_acyclic_nonnegative_circulation_property(graph)


def test_no_outside_path_t1() -> None:
    inst = WWInstance.create(K=[1], q=[0], demand=[2], floor=[0])
    _, pstar = shortest_path(inst)
    frozen = frozen_certificate_lp(inst, pstar, 1)
    exact = exact_radius_enumeration(inst, pstar, 1)
    milp = fixed_radius_milp(inst, pstar, 1, 100)
    assert frozen.status == "no_outside_path" and math.isinf(frozen.radius)
    assert exact.status == "no_outside_path" and math.isinf(exact.radius)
    assert milp.decision is False and milp.status == "no_outside_path"


def test_polynomial_certificate_matches_exhaustive_random() -> None:
    rng = np.random.default_rng(20260804)
    checked = 0
    for T in range(2, 9):
        for _ in range(14):
            inst = random_instance(rng, T)
            _, pstar = shortest_path(inst)
            for k in range(1, len(pstar)):
                got = frozen_certificate_lp(inst, pstar, k)
                want = frozen_certificate_exhaustive(inst, pstar, k)
                if math.isinf(want.radius):
                    assert math.isinf(got.radius)
                else:
                    assert got.radius == pytest.approx(want.radius, rel=3e-6, abs=3e-6)
                    assert got.safe_radius <= want.radius + 1e-9
                checked += 1
    assert checked > 150


def test_full_path_frozen_equals_exact() -> None:
    rng = np.random.default_rng(101)
    checked = 0
    for T in range(2, 8):
        for _ in range(8):
            inst = random_instance(rng, T)
            _, pstar = shortest_path(inst)
            k = len(pstar) - 1
            lower = frozen_certificate_lp(inst, pstar, k).radius
            exact = exact_radius_enumeration(inst, pstar, k).radius
            if math.isinf(lower):
                assert math.isinf(exact)
            else:
                assert exact == pytest.approx(lower, rel=3e-6, abs=3e-6)
            checked += 1
    assert checked >= 40


def test_fixed_competitor_compact_lp_matches_explicit_inside_paths() -> None:
    rng = np.random.default_rng(11)
    comparisons = 0
    for T in range(3, 7):
        inst = random_instance(rng, T)
        _, pstar = shortest_path(inst)
        k = 1
        prefix = pstar[: k + 1]
        for qpath in (p for p in enumerate_paths(T) if not follows_prefix(p, prefix)):
            compact = fixed_competitor_inverse_lp(inst, pstar, k, qpath)
            kq, bq = path_coefficients(inst, qpath)
            objective = np.r_[np.zeros(T), 1.0]
            rows, rhs = [], []
            for t in range(T):
                row = np.zeros(T + 1)
                row[t], row[T] = 1.0, -1.0 / inst.weights[t]
                rows.append(row)
                rhs.append(inst.demand[t])
                row = np.zeros(T + 1)
                row[t], row[T] = -1.0, -1.0 / inst.weights[t]
                rows.append(row)
                rhs.append(-inst.demand[t])
            for inside in (p for p in enumerate_paths(T) if follows_prefix(p, prefix)):
                kp, bp = path_coefficients(inst, inside)
                row = np.zeros(T + 1)
                row[:T] = bq - bp
                rows.append(row)
                rhs.append(kp - kq)
            explicit = linprog(
                objective,
                A_ub=np.asarray(rows),
                b_ub=np.asarray(rhs),
                bounds=[(inst.floor[t], None) for t in range(T)] + [(0, None)],
                method="highs",
            )
            if explicit.success:
                assert compact.status == "optimal"
                assert compact.radius == pytest.approx(explicit.fun, rel=3e-7, abs=3e-7)
                assert compact.verified_difference is not None and compact.verified_difference <= 3e-6
            else:
                assert compact.status == "infeasible"
            comparisons += 1
    assert comparisons >= 10


def test_milp_boundary_on_strict_example() -> None:
    inst = strict_instance()
    _, pstar = shortest_path(inst)
    below = fixed_radius_milp(inst, pstar, 1, 1.99, time_limit=30)
    at = fixed_radius_milp(inst, pstar, 1, 2.0, time_limit=30)
    assert below.decision is False
    assert at.decision is True
    assert at.verified_difference is not None and at.verified_difference <= 1e-6


def test_nominal_degeneracy_common_prefix() -> None:
    inst = WWInstance.create(K=[0, 0, 0], q=[0, 0, 0], demand=[1, 1, 1])
    value, pstar = shortest_path(inst)
    assert value == 0
    assert count_optimal_paths(inst) == 4
    assert common_optimal_prefix(inst) == (0,)
    assert frozen_certificate_lp(inst, pstar, 1).radius == pytest.approx(0.0)
    assert exact_radius_enumeration(inst, pstar, 1).radius == pytest.approx(0.0)


def test_duplicate_zero_breakpoints_and_witness() -> None:
    inst = WWInstance.create(
        K=[0, 2, 4, 1],
        q=[4, 3, 2, 1],
        demand=[1, 1, 2, 2],
        floor=[1, 0, 1, 0],
        weights=[1, 1, 1, 0.5],
    )
    _, pstar = shortest_path(inst)
    for k in range(1, len(pstar)):
        got = frozen_certificate_lp(inst, pstar, k)
        want = frozen_certificate_exhaustive(inst, pstar, k)
        if math.isinf(want.radius):
            assert math.isinf(got.radius)
        else:
            assert got.radius == pytest.approx(want.radius, abs=3e-6)
            if got.revised_demand is not None:
                assert np.all(got.revised_demand >= inst.floor - 1e-9)
                assert got.witness_difference is not None and got.witness_difference <= 1e-5


def test_pairwise_infinite_zero_denominator() -> None:
    inst = WWInstance.create(K=[0, 1], q=[1, 1], demand=[2, 3], floor=[0, 0])
    result = path_pairwise_radius(inst, (0, 1, 2), (0, 2))
    assert math.isinf(result.radius)


def test_exact_prefix_radius_is_nonincreasing_in_k() -> None:
    rng = np.random.default_rng(2718)
    for T in range(3, 8):
        for _ in range(5):
            inst = random_instance(rng, T)
            _, pstar = shortest_path(inst)
            radii = [exact_radius_enumeration(inst, pstar, k).radius for k in range(1, len(pstar))]
            assert all(b <= a + 5e-6 for a, b in zip(radii, radii[1:]))


def test_cli_smoke(tmp_path: Path) -> None:
    input_path = tmp_path / "instance.json"
    input_path.write_text(json.dumps({
        "instance": {
            "K": [0, 3, 2], "q": [2, 1, 0], "demand": [1, 5, 1],
            "floor": [0.5, 0.5, 0.5], "weights": [1, 1, 1]
        }
    }))
    output_path = tmp_path / "result.json"
    result = CliRunner().invoke(app, ["certify", str(input_path), "--k", "1", "--exact", "-o", str(output_path)])
    assert result.exit_code == 0, result.output
    payload = json.loads(output_path.read_text())
    bracket = payload["certified_bracket"]
    assert bracket["frozen_certificate"]["radius"]["float"] == pytest.approx(1.5)
    assert bracket["frozen_certificate"]["radius"]["exact"] == "3/2"
    escalation = payload["certified_exact_escalation"]
    assert escalation["exact_radius"]["float"] == pytest.approx(2.0)
    assert payload["nominal"]["verified_exactly_optimal"] is True
    for section, key in [
        ("certified_bracket", "frozen_certificate"),
        ("certified_exact_escalation", "witness"),
    ]:
        path = payload[section][key]["outside_path"]
        if path is not None:
            assert path[0] == 1 and path[-1] == 4
    assert payload["nominal"]["path"] == [1, 2, 4]


def test_polynomial_bracket_strict_and_exact_closure() -> None:
    from wwprefix import polynomial_radius_bracket

    inst = strict_instance()
    _, pstar = shortest_path(inst)
    bracket = polynomial_radius_bracket(inst, pstar, 1)
    assert bracket.lower_radius == pytest.approx(1.5, abs=1e-7)
    assert bracket.upper_radius == pytest.approx(2.0, abs=1e-7)
    assert bracket.exact_certified is False
    assert bracket.lower_witness_closes is False

    full = polynomial_radius_bracket(inst, pstar, len(pstar) - 1)
    assert full.exact_certified is True
    assert full.exact_radius == pytest.approx(full.lower_radius, abs=1e-7)


def test_polynomial_bracket_contains_exact_random() -> None:
    from wwprefix import polynomial_radius_bracket

    rng = np.random.default_rng(808)
    checked = 0
    exact_by_polynomial = 0
    for T in range(3, 8):
        for _ in range(8):
            inst = random_instance(rng, T)
            _, pstar = shortest_path(inst)
            for k in range(1, len(pstar)):
                bracket = polynomial_radius_bracket(inst, pstar, k)
                exact = exact_radius_enumeration(inst, pstar, k)
                assert bracket.lower_radius <= exact.radius + 5e-6
                assert exact.radius <= bracket.upper_radius + 5e-6
                if bracket.exact_certified:
                    assert bracket.exact_radius == pytest.approx(exact.radius, rel=3e-6, abs=3e-6)
                    exact_by_polynomial += 1
                checked += 1
    assert checked >= 30
    assert exact_by_polynomial > 0
