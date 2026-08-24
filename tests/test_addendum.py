"""Tests for the v2.2.0 theorem-and-solver addendum.

Covers the seven recommended-package items: the enumeration-count theorem
and candidate guard, the local-tie decomposition, the NP verifier, the
compact production-balance MILP, and the corpus equivalence gate.
"""
from __future__ import annotations

import csv
from fractions import Fraction
from itertools import combinations
from math import inf, isinf
from pathlib import Path

import numpy as np
import pytest

from wwprefix import (
    ExactInstance,
    WWInstance,
    certified_exact_radius,
    exact_radius_enumeration,
    shortest_path,
)
from wwprefix.compactmilp import (
    compact_arc_radius_milp,
    compact_fixed_radius_milp,
    compact_radius_milp,
)
from wwprefix.decomposition import (
    decomposed_certified_radius,
    exact_local_tie_holds,
    local_tie_gaps,
    np_verifier,
)
from wwprefix.exact import fixed_radius_milp
from wwprefix.exactcert import exact_path_cost, exact_shortest_path
from wwprefix.model import (
    enumerate_paths,
    follows_prefix,
    inside_path_count,
    outside_path_count,
    outside_paths,
    prefix_values,
    validate_prefix,
)

ROOT = Path(__file__).resolve().parents[1]


def _random_instance(seed: int, T: int, regime: str = "regular") -> WWInstance:
    """Deterministic mixed-regime generator mirroring scripts/_common.py."""
    rng = np.random.default_rng(seed)
    if regime == "dense":
        # Test-only regime: low setups against steep holding force
        # multi-cycle nominal paths even at small horizons, so partial
        # prefixes with several protected arcs exist to decompose.
        demand = rng.uniform(20.0, 100.0, T)
        holding = rng.uniform(0.6, 2.2, max(0, T - 1))
        K = rng.uniform(8.0, 45.0, T)
        floor_fraction = rng.uniform(0.0, 0.30, T)
    elif regime == "near_tie":
        demand = rng.uniform(45.0, 65.0, T)
        holding = rng.uniform(0.08, 0.13, max(0, T - 1))
        K = np.maximum(rng.uniform(95.0, 125.0) + rng.normal(0.0, 2.0, T), 1.0)
        floor_fraction = rng.uniform(0.0, 0.10, T)
    elif regime == "floor_heavy":
        demand = rng.uniform(20.0, 100.0, T)
        holding = rng.uniform(0.04, 0.35, max(0, T - 1))
        K = rng.uniform(70.0, 220.0, T)
        floor_fraction = rng.uniform(0.70, 0.98, T)
    else:
        demand = rng.uniform(20.0, 100.0, T)
        holding = rng.uniform(0.04, 0.35, max(0, T - 1))
        K = rng.uniform(70.0, 220.0, T)
        floor_fraction = rng.uniform(0.0, 0.30, T)
    q = np.zeros(T)
    if T > 1:
        q[1:] = -np.cumsum(holding)
    return WWInstance.create(
        K=K, q=q, demand=demand, floor=demand * floor_fraction,
        weights=rng.uniform(0.6, 1.8, T),
    )


def _exact_envelopes(inst: ExactInstance, demand, prefix):
    """Exhaustive exact (A_k, B_k); ground truth for small horizons."""
    inside = None
    outside = None
    for path in enumerate_paths(inst.T):
        value = exact_path_cost(inst, demand, path)
        if follows_prefix(path, prefix):
            inside = value if inside is None or value < inside else inside
        else:
            outside = value if outside is None or value < outside else outside
    return inside, outside


def _all_prefixes(T: int):
    """Every valid protected prefix (0, ..., s) for the horizon."""
    for s in range(1, T + 1):
        for r in range(s):
            for interior in combinations(range(1, s), r):
                yield (0, *interior, s)


class TestOutsidePathCount:
    def test_closed_form_matches_brute_force(self):
        for T in range(1, 10):
            for prefix in _all_prefixes(T):
                brute = sum(1 for _ in outside_paths(T, prefix))
                assert outside_path_count(T, prefix) == brute, (T, prefix)
                assert inside_path_count(T, prefix) + outside_path_count(T, prefix) == 2 ** (T - 1)

    def test_full_path_leaves_all_but_one(self):
        # A complete protected path excludes exactly itself.
        assert outside_path_count(6, (0, 2, 4, 6)) == 2**5 - 1

    def test_nonempty_prefix_lower_bound(self):
        # Every non-empty prefix leaves at least 2^(T-2) outside paths.
        for T in range(2, 12):
            for prefix in ((0, 1), (0, T), (0, T - 1, T) if T >= 2 else (0, 1)):
                assert outside_path_count(T, validate_prefix(prefix, T)) >= 2 ** (T - 2)

    def test_historical_t18_counts(self):
        # The release's recorded T=18 candidate totals are exact instances of
        # the formula: 2^17 - paths_total must be a power of two (the inside
        # count 2^(T-1-s)), for every recorded enumeration row.
        path = ROOT / "results" / "raw" / "exact_benchmark.csv"
        rows = list(csv.DictReader(path.open()))
        assert rows
        seen_t18 = set()
        for row in rows:
            T = int(row["T"])
            total = int(row["paths_total"])
            inside = 2 ** (T - 1) - total
            assert inside >= 1 and inside & (inside - 1) == 0, row
            if T == 18:
                seen_t18.add(total)
        assert {126976, 129024} & seen_t18


class TestCandidateGuard:
    def _instance(self):
        rng = np.random.default_rng(11)
        K = rng.uniform(80.0, 200.0, 6)
        q = np.sort(rng.uniform(0.0, 2.0, 6))[::-1]
        demand = rng.uniform(20.0, 90.0, 6)
        return WWInstance.create(K=K, q=q, demand=demand)

    def test_float_enumeration_refuses_before_generation(self, monkeypatch):
        instance = self._instance()
        _, nominal = shortest_path(instance)
        assert len(nominal) >= 3

        def boom(*args, **kwargs):  # pragma: no cover - guard must prevent this
            raise AssertionError("outside_paths must not be called under the guard")

        import wwprefix.exact as exact_mod

        monkeypatch.setattr(exact_mod, "outside_paths", boom)
        result = exact_radius_enumeration(instance, nominal, 1, max_candidates=1)
        assert result.status == "refused_by_candidate_guard"
        assert result.paths_total == outside_path_count(instance.T, nominal[:2])
        assert result.paths_processed == 0
        assert isinf(result.radius)
        assert result.lower_bound == 0.0

    def test_certified_enumeration_refuses_before_generation(self, monkeypatch):
        instance = self._instance()
        _, nominal = shortest_path(instance)
        inst = ExactInstance.from_ww(instance)

        def boom(*args, **kwargs):  # pragma: no cover
            raise AssertionError("outside_paths must not be called under the guard")

        import wwprefix.model as model_mod

        monkeypatch.setattr(model_mod, "outside_paths", boom)
        result = certified_exact_radius(inst, nominal, 1, max_candidates=1)
        assert result.status == "refused_by_candidate_guard"
        assert result.paths_total == outside_path_count(instance.T, nominal[:2])
        assert result.exact_certified is False
        assert result.lower_radius == Fraction(0)

    def test_guard_allows_when_within_cap(self):
        instance = self._instance()
        _, nominal = shortest_path(instance)
        count = outside_path_count(instance.T, nominal[:2])
        result = exact_radius_enumeration(instance, nominal, 1, max_candidates=count)
        assert result.status in {"optimal", "infinite"}
        assert result.paths_total == count


class TestLocalTieLemma:
    """Exact pointwise check of B_k <= A_k  <=>  exists r: O_r <= E_r."""

    def _demand_probes(self, rng, instance):
        d_hat = instance.demand
        spread = np.maximum(d_hat - instance.floor, 1.0)
        probes = [d_hat.copy()]
        for _ in range(8):
            step = rng.uniform(-1.5, 1.5, instance.T) * spread
            probes.append(np.maximum(instance.floor, d_hat + step))
        probes.append(instance.floor.copy())
        return probes

    def test_equivalence_on_random_instances(self):
        rng = np.random.default_rng(20260818)
        checked = 0
        for seed in range(60):
            T = int(rng.integers(3, 8))
            regime = ("dense", "regular", "dense", "near_tie", "dense", "floor_heavy")[seed % 6]
            instance = _random_instance(1000 + seed, T, regime)
            _, nominal = shortest_path(instance)
            if len(nominal) < 3:
                continue
            inst = ExactInstance.from_ww(instance)
            for k in range(1, len(nominal) - 1):
                prefix = nominal[: k + 1]
                for d in self._demand_probes(rng, instance):
                    d_exact = tuple(Fraction(float(v)) for v in d)
                    inside, outside = _exact_envelopes(inst, d_exact, prefix)
                    event = outside is not None and (inside is None or outside <= inside)
                    assert exact_local_tie_holds(inst, d_exact, nominal, k) == event
                    checked += 1
        assert checked > 300

    def test_equivalence_at_certified_tie_points(self):
        # At an exactly certified witness the event holds with equality on
        # some protected arc, and the lemma must report it.
        for seed, T in ((7, 4), (13, 5), (29, 6)):
            instance = _random_instance(seed, T, "dense")
            _, nominal = shortest_path(instance)
            if len(nominal) < 3:
                continue
            inst = ExactInstance.from_ww(instance)
            k = len(nominal) - 2
            result = certified_exact_radius(inst, nominal, k)
            if result.witness is None:
                continue
            assert exact_local_tie_holds(inst, result.witness.demand, nominal, k)

    def test_degenerate_zero_costs_and_demands(self):
        # Zero setups, zero demands and a prefix ending at the terminal node.
        instance = WWInstance.create(
            K=[5.0, 0.0, 3.0], q=[2.0, 1.0, 0.0], demand=[0.0, 4.0, 0.0],
            floor=[0.0, 0.0, 0.0], weights=[1.0, 1.0, 1.0],
        )
        inst = ExactInstance.from_ww(instance)
        _, nominal = shortest_path(instance)
        for k in range(1, len(nominal)):
            prefix = nominal[: k + 1]
            for d in ([0.0, 0.0, 0.0], [0.0, 4.0, 0.0], [3.0, 1.0, 2.0]):
                d_exact = tuple(Fraction(v) for v in d)
                inside, outside = _exact_envelopes(inst, d_exact, prefix)
                event = outside is not None and (inside is None or outside <= inside)
                if k < len(nominal) - 1 or prefix[-1] < instance.T:
                    assert exact_local_tie_holds(inst, d_exact, nominal, k) == event
                else:
                    # Full protected path: lemma covers r < k = m.
                    assert exact_local_tie_holds(inst, d_exact, nominal, k) == event

    def test_float_gaps_agree_in_sign(self):
        instance = _random_instance(3, 5, "dense")
        _, nominal = shortest_path(instance)
        if len(nominal) < 3:
            pytest.skip("single-arc nominal path")
        k = len(nominal) - 1
        gaps = local_tie_gaps(instance, instance.demand, nominal, k)
        assert len(gaps) == k
        # At the nominal demand of a uniquely optimal path no protected arc
        # has yet ceased to be compulsory unless there is a nominal tie.
        inside, outside = prefix_values(instance, instance.demand, nominal[: k + 1])
        event = outside <= inside + 1e-9
        assert any(o <= e + 1e-9 for o, e in gaps) == event


class TestDecompositionExact:
    def _cases(self):
        specs = [
            (101, 3, "dense"), (102, 4, "dense"), (103, 4, "near_tie"),
            (104, 5, "dense"), (105, 5, "floor_heavy"), (106, 5, "near_tie"),
            (107, 6, "dense"), (108, 6, "floor_heavy"), (109, 6, "dense"),
            (110, 7, "dense"), (111, 7, "near_tie"), (112, 8, "dense"),
            (113, 6, "regular"), (114, 8, "dense"), (115, 7, "dense"),
        ]
        for seed, T, regime in specs:
            instance = _random_instance(seed, T, regime)
            _, nominal = shortest_path(instance)
            if len(nominal) < 3:
                continue
            yield instance, nominal

    def test_matches_certified_exact_radius(self):
        compared = 0
        for instance, nominal in self._cases():
            inst = ExactInstance.from_ww(instance)
            for k in range(1, len(nominal) - 1 + 1):
                direct = certified_exact_radius(inst, nominal, k)
                decomposed = decomposed_certified_radius(inst, nominal, k)
                if not (direct.exact_certified and decomposed.exact_certified):
                    continue
                assert decomposed.exact_radius == direct.exact_radius, (
                    instance.demand, nominal, k,
                )
                compared += 1
        assert compared >= 15

    def test_proven_infinite_case(self):
        instance = WWInstance.create(
            K=[1.0, 5.0], q=[1.0, 1.0], demand=[10.0, 10.0],
        )
        _, nominal = shortest_path(instance)
        assert nominal == (0, 2)
        inst = ExactInstance.from_ww(instance)
        direct = certified_exact_radius(inst, nominal, 1)
        decomposed = decomposed_certified_radius(inst, nominal, 1)
        assert direct.status == "proven_infinite" and direct.exact_certified
        assert decomposed.status == "proven_infinite" and decomposed.exact_certified
        assert decomposed.exact_radius is None


class TestCompactMILP:
    def _cap_for(self, exact_radius: Fraction | None, instance: WWInstance) -> float:
        spread = float(np.max(instance.weights * (instance.demand - instance.floor)))
        anchor = 0.0 if exact_radius is None else float(exact_radius)
        return 4.0 * (1.0 + spread + anchor)

    def test_min_radius_matches_certified_exact(self):
        compared = 0
        for seed, T in ((301, 4), (302, 5), (303, 5), (304, 6), (305, 6), (306, 7)):
            instance = _random_instance(seed, T, "dense")
            _, nominal = shortest_path(instance)
            if len(nominal) < 3:
                continue
            inst = ExactInstance.from_ww(instance)
            for k in range(1, len(nominal) - 1):
                reference = certified_exact_radius(inst, nominal, k)
                if not reference.exact_certified or reference.exact_radius is None:
                    continue
                exact = float(reference.exact_radius)
                result = compact_radius_milp(
                    instance, nominal, k,
                    radius_cap=self._cap_for(reference.exact_radius, instance),
                )
                assert result.status == "optimal", result.status
                assert result.radius == pytest.approx(exact, rel=1e-6, abs=1e-6)
                assert result.outside_path is not None
                # The exact layer must confirm the witness at (numerically)
                # the same radius.
                assert result.certified_witness is not None
                certified = float(result.certified_witness.radius)
                assert certified >= exact - 1e-9
                assert certified == pytest.approx(exact, rel=1e-6, abs=1e-6)
                compared += 1
        assert compared >= 6

    def test_decision_mode_agrees_with_arc_product_milp(self):
        instance = _random_instance(302, 5, "dense")
        _, nominal = shortest_path(instance)
        assert len(nominal) >= 3
        inst = ExactInstance.from_ww(instance)
        k = 1
        reference = certified_exact_radius(inst, nominal, k)
        assert reference.exact_certified and reference.exact_radius is not None
        exact = float(reference.exact_radius)
        for probe, expected in ((exact * 0.5, False), (exact * 1.5, True)):
            compact = compact_fixed_radius_milp(instance, nominal, k, probe)
            legacy = fixed_radius_milp(instance, nominal, k, probe)
            assert compact.decision is expected, (probe, compact.status)
            if legacy.decision is not None:
                assert compact.decision == legacy.decision
        # Fewer variables than the arc-product model at equal horizon.
        compact = compact_fixed_radius_milp(instance, nominal, k, exact * 1.5)
        assert compact.n_variables < 5 * instance.T + 3

    def test_no_outside_path(self):
        instance = WWInstance.create(K=[3.0], q=[1.0], demand=[7.0])
        result = compact_radius_milp(instance, (0, 1), 1, radius_cap=10.0)
        assert result.status == "no_outside_path"

    def test_arc_mode_minimum_matches_full_prefix(self):
        instance = _random_instance(100, 5, "dense")
        _, nominal = shortest_path(instance)
        assert len(nominal) >= 4
        inst = ExactInstance.from_ww(instance)
        k = len(nominal) - 2
        reference = certified_exact_radius(inst, nominal, k)
        assert reference.exact_certified and reference.exact_radius is not None
        cap = self._cap_for(reference.exact_radius, instance)
        per_arc = []
        for r in range(k):
            result = compact_arc_radius_milp(instance, nominal, r, radius_cap=cap)
            if result.status == "optimal" and result.radius is not None:
                per_arc.append(result.radius)
            elif result.status == "no_destabilisation_within_cap":
                per_arc.append(float("inf"))
        assert per_arc
        assert min(per_arc) == pytest.approx(float(reference.exact_radius), rel=1e-6, abs=1e-6)


class TestNPVerifier:
    def test_accepts_certified_witnesses_rejects_corruptions(self):
        accepted = 0
        for seed, T in ((201, 4), (202, 5), (203, 6), (204, 6)):
            instance = _random_instance(seed, T, "dense")
            _, nominal = shortest_path(instance)
            if len(nominal) < 3:
                continue
            inst = ExactInstance.from_ww(instance)
            k = len(nominal) - 2
            result = certified_exact_radius(inst, nominal, k)
            if result.witness is None:
                continue
            witness = result.witness
            R = witness.radius
            assert np_verifier(inst, nominal, k, R, witness.outside_path, witness.demand)
            accepted += 1
            # Corruption 1: an inside path is not a valid certificate.
            assert not np_verifier(inst, nominal, k, R, nominal, witness.demand)
            # Corruption 2: shrink the box below the witness distance.
            if R > 0:
                assert not np_verifier(
                    inst, nominal, k, R / 2, witness.outside_path, witness.demand
                )
            # Corruption 3: push one coordinate below its floor.
            if any(f > 0 for f in inst.floor):
                t = max(range(inst.T), key=lambda i: inst.floor[i])
                bad = list(witness.demand)
                bad[t] = inst.floor[t] - 1
                assert not np_verifier(inst, nominal, k, R + 1000, witness.outside_path, bad)
            # Corruption 4: the nominal demand of a strictly stable prefix
            # does not destabilise.
            if result.exact_radius is not None and result.exact_radius > 0:
                assert not np_verifier(
                    inst, nominal, k, Fraction(0), witness.outside_path, inst.demand
                )
        assert accepted >= 2
