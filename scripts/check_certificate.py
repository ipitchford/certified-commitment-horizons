#!/usr/bin/env python3
"""Independent certificate checker.

Re-verifies a ``wwprefix certify`` decision record from first principles in
exact rational arithmetic.  This file deliberately imports **nothing** from
the wwprefix package: path costs, shortest paths, the outside-path state
machine and the floor-aware halfspace walk are all reimplemented here, so a
defect in the package cannot silently certify its own output.

Verified for every record:
  * the instance parses exactly (numbers or exact numeric strings);
  * the published nominal path is exactly optimal;
  * every published witness satisfies the floors, lies within its claimed
    radius, and ties or beats the relevant comparator exactly;
  * closure and upper witnesses tie or beat the *best* prefix-retaining
    continuation (checked against this file's own suffix DP);
  * infinite statuses: 'no outside path' is checked structurally and
    'saturation' is re-proved with this file's own saturated arc data and
    outside-path DP;
  * the triage classification follows from the certified bounds;
  * for horizons T <= BRUTE_FORCE_LIMIT the frozen lower bound is re-derived
    by complete enumeration of outside paths with this file's own halfspace
    walk (full independent confirmation of minimality).

For larger horizons the minimality of the frozen lower bound rests on the
package's internally cross-checked parametric computation; the checker
reports which properties were fully re-verified.

Usage:
  python scripts/check_certificate.py DECISION.json INSTANCE.json
Exit code 0 iff every check passes.
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction
from itertools import combinations

BRUTE_FORCE_LIMIT = 12

failures: list[str] = []
notes: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def rat(value) -> Fraction:
    if isinstance(value, str):
        if value == "inf":
            raise ValueError("expected a finite rational")
        return Fraction(value)
    if isinstance(value, (int, float)):
        return Fraction(value)
    raise ValueError(f"not a rational: {value!r}")


def opt_rat(value) -> Fraction | None:
    if value is None or value == "inf":
        return None
    return rat(value)


def parse_instance(raw: dict) -> dict:
    def rats(key, default=None):
        if raw.get(key) is None:
            return default
        return [rat(v) for v in raw[key]]

    K = rats("K")
    q = rats("q")
    demand = rats("demand")
    T = len(demand)
    floor = rats("floor", [Fraction(0)] * T)
    weights = rats("weights", [Fraction(1)] * T)
    check(len(K) == len(q) == T == len(floor) == len(weights), "instance field lengths differ")
    check(all(v >= 0 for v in K), "negative setup cost")
    check(all(a >= b for a, b in zip(demand, floor)), "demand below floor")
    check(all(v > 0 for v in weights), "non-positive weight")
    check(all(q[t] >= q[t + 1] for t in range(T - 1)), "slopes not non-increasing")
    return {"K": K, "q": q, "demand": demand, "floor": floor, "weights": weights, "T": T}


def path_cost(inst: dict, demand: list[Fraction], path: tuple[int, ...]) -> Fraction:
    total = Fraction(0)
    for i, j in zip(path, path[1:]):
        total += inst["K"][i] + inst["q"][i] * sum(demand[i:j], Fraction(0))
    return total


def shortest_value(inst: dict, demand: list[Fraction], start: int = 0) -> Fraction:
    T = inst["T"]
    D = [Fraction(0)]
    for v in demand:
        D.append(D[-1] + v)
    best: list[Fraction | None] = [None] * (T + 1)
    best[start] = Fraction(0)
    for j in range(start + 1, T + 1):
        candidates = [
            best[i] + inst["K"][i] + inst["q"][i] * (D[j] - D[i])
            for i in range(start, j)
            if best[i] is not None
        ]
        best[j] = min(candidates)
    return best[T]


def inside_minimum(inst: dict, demand: list[Fraction], prefix: tuple[int, ...]) -> Fraction:
    return path_cost(inst, demand, prefix) + shortest_value(inst, demand, start=prefix[-1])


def follows(path: tuple[int, ...], prefix: tuple[int, ...]) -> bool:
    return path[: len(prefix)] == prefix


def all_paths(T: int):
    interior = tuple(range(1, T))
    for r in range(len(interior) + 1):
        for chosen in combinations(interior, r):
            yield (0, *chosen, T)


def weighted_distance(inst: dict, demand: list[Fraction]) -> Fraction:
    return max(
        w * abs(d - dn) for w, d, dn in zip(inst["weights"], demand, inst["demand"])
    )


def halfspace_radius(inst: dict, gap: Fraction, c: list[Fraction]) -> Fraction | None:
    """Independent reimplementation of the floor-aware halfspace walk."""
    if gap <= 0:
        return Fraction(0)
    if all(v == 0 for v in c):
        return None
    T = inst["T"]
    slack = [d - e for d, e in zip(inst["demand"], inst["floor"])]
    w = inst["weights"]
    points = sorted({w[t] * slack[t] for t in range(T) if c[t] > 0 and slack[t] > 0})
    left = Fraction(0)
    red = Fraction(0)
    for right in [*points, None]:
        slope = Fraction(0)
        for t in range(T):
            if c[t] > 0 and w[t] * slack[t] > left:
                slope += c[t] / w[t]
            elif c[t] < 0:
                slope += (-c[t]) / w[t]
        if slope > 0:
            cand = left + (gap - red) / slope
            if right is None or cand <= right:
                return cand
        if right is None:
            return None
        red += slope * (right - left)
        left = right
    return None


def pairwise_radius(inst: dict, competitor, comparator) -> Fraction | None:
    def coeffs(path):
        beta = [Fraction(0)] * inst["T"]
        kappa = Fraction(0)
        for i, j in zip(path, path[1:]):
            kappa += inst["K"][i]
            for t in range(i, j):
                beta[t] = inst["q"][i]
        return kappa, beta

    kq, bq = coeffs(competitor)
    kp, bp = coeffs(comparator)
    c = [x - y for x, y in zip(bq, bp)]
    gap = (kq - kp) + sum((cv * d for cv, d in zip(c, inst["demand"])), Fraction(0))
    return halfspace_radius(inst, gap, c)


def path_from_public(path) -> tuple[int, ...]:
    return tuple(int(v) - 1 for v in path)


def demand_from_block(block) -> list[Fraction]:
    return [rat(v) for v in block["exact"]]


def verify_witness_block(inst, block, prefix, label, radius_bound=None) -> None:
    demand = demand_from_block(block["demand"])
    outside = path_from_public(block["outside_path"])
    check(not follows(outside, prefix), f"{label}: witness path retains the prefix")
    check(
        all(d >= e for d, e in zip(demand, inst["floor"])),
        f"{label}: witness violates a floor",
    )
    distance = weighted_distance(inst, demand)
    claimed = rat(block["radius"]["exact"])
    check(distance == claimed, f"{label}: witness distance differs from claimed radius")
    if radius_bound is not None:
        check(distance <= radius_bound, f"{label}: witness distance exceeds its bound")
    outside_value = path_cost(inst, demand, outside)
    inside_value = inside_minimum(inst, demand, prefix)
    check(
        outside_value <= inside_value,
        f"{label}: witness does not tie or beat the best inside continuation",
    )


def verify_saturation_infinite(inst, nominal, prefix, residual: Fraction) -> None:
    """Re-prove the saturation-infinity claim with an independent DP."""
    T = inst["T"]

    def beta_star():
        beta = [Fraction(0)] * T
        for i, j in zip(nominal, nominal[1:]):
            for t in range(i, j):
                beta[t] = inst["q"][i]
        return beta

    bstar = beta_star()
    kappa_star = sum((inst["K"][i] for i in nominal[:-1]), Fraction(0))

    def arc_sat(i: int, j: int) -> Fraction | None:
        """Saturated arc value; None when the arc has an unbounded direction."""
        value = inst["K"][i]
        for t in range(i, j):
            c = inst["q"][i] - bstar[t]
            if c < 0:
                return None
            value += c * inst["floor"][t] if c > 0 else Fraction(0)
        return value

    # DP over (matched position r | deviated at node n).
    k = len(prefix) - 1
    INF = None
    best_dev: list[Fraction | None] = [INF] * (T + 1)

    def relax(current: Fraction | None, addition: Fraction | None) -> Fraction | None:
        if current is None or addition is None:
            return None
        return current + addition

    def better(a: Fraction | None, b: Fraction | None) -> Fraction | None:
        if a is None:
            return b
        if b is None:
            return a
        return min(a, b)

    matched: Fraction | None = Fraction(0)
    unbounded = False
    for r in range(k):
        i = prefix[r]
        expected = prefix[r + 1]
        for j in range(i + 1, T + 1):
            if j == expected:
                continue
            value = arc_sat(i, j)
            if value is None:
                unbounded = True
                continue
            if matched is not None:
                best_dev[j] = better(best_dev[j], relax(matched, value))
        if matched is not None:
            step = arc_sat(i, expected)
            matched = relax(matched, step)
            if step is None:
                unbounded = True
    for i in range(1, T):
        if best_dev[i] is None:
            continue
        for j in range(i + 1, T + 1):
            value = arc_sat(i, j)
            if value is None:
                unbounded = True
                continue
            best_dev[j] = better(best_dev[j], relax(best_dev[i], value))
    check(not unbounded, "saturation-infinity claim: an outside arc has an unbounded direction")
    check(best_dev[T] is not None, "saturation-infinity claim: no outside path found")
    if best_dev[T] is not None:
        check(
            best_dev[T] - kappa_star == residual,
            "saturation-infinity claim: residual gap mismatch",
        )
        check(best_dev[T] - kappa_star > 0, "saturation-infinity claim: residual not positive")


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    record = json.loads(open(sys.argv[1], encoding="utf-8").read())
    instance_doc = json.loads(open(sys.argv[2], encoding="utf-8").read())
    inst = parse_instance(instance_doc.get("instance", instance_doc))
    T = inst["T"]

    nominal = path_from_public(record["nominal"]["path"])
    k = int(record["protected_arcs"])
    prefix = nominal[: k + 1]

    # Nominal optimality.
    optimum = shortest_value(inst, inst["demand"])
    check(path_cost(inst, inst["demand"], nominal) == optimum, "nominal path is not exactly optimal")
    check(rat(record["nominal"]["optimum"]["exact"]) == optimum, "published optimum differs")

    bracket = record["certified_bracket"]
    lower = opt_rat(bracket["lower_radius"]["exact"])
    upper = opt_rat(bracket["upper_radius"]["exact"])
    frozen = bracket["frozen_certificate"]
    frozen_radius = opt_rat(frozen["radius"]["exact"])

    check(
        lower is None or upper is None or lower <= upper,
        "certified lower bound exceeds certified upper bound",
    )
    if bracket["exact_certified"] and bracket["infinity_status"] == "not_infinite":
        check(lower == upper, "exact_certified but bounds differ")

    if bracket["infinity_status"] == "proven_infinite_no_outside_path":
        check(T == 1, "no-outside-path infinity claimed but outside paths exist")
        notes.append("infinity (no outside path) verified structurally")
    elif bracket["infinity_status"] == "proven_infinite_saturation":
        residual = opt_rat(frozen["residual_gap"]["exact"])
        check(residual is not None, "saturation infinity without residual gap")
        if residual is not None:
            verify_saturation_infinite(inst, nominal, prefix, residual)
        notes.append("infinity (saturation) re-proved independently")
    else:
        check(frozen_radius is not None, "finite status without a frozen radius")
        if frozen_radius is not None:
            outside = path_from_public(frozen["outside_path"])
            check(not follows(outside, prefix), "frozen outside path retains the prefix")
            demand = demand_from_block(frozen["witness_demand"])
            check(
                all(d >= e for d, e in zip(demand, inst["floor"])),
                "frozen witness violates a floor",
            )
            check(
                weighted_distance(inst, demand) <= frozen_radius,
                "frozen witness exceeds the frozen radius",
            )
            check(
                path_cost(inst, demand, outside) == path_cost(inst, demand, nominal),
                "frozen witness does not tie the nominal path exactly",
            )
            check(
                pairwise_radius(inst, outside, nominal) == frozen_radius,
                "frozen radius differs from this checker's pairwise radius",
            )
            if T <= BRUTE_FORCE_LIMIT:
                best: Fraction | None = None
                for path in all_paths(T):
                    if follows(path, prefix):
                        continue
                    value = pairwise_radius(inst, path, nominal)
                    if value is not None and (best is None or value < best):
                        best = value
                check(
                    best == frozen_radius,
                    "brute-force frozen minimum differs from the published lower bound",
                )
                notes.append("frozen minimality re-derived by complete enumeration")
            else:
                notes.append(
                    "frozen minimality above the brute-force limit: relies on the "
                    "package's internally cross-checked parametric computation"
                )

        if bracket.get("upper_witness") is not None:
            verify_witness_block(inst, bracket["upper_witness"], prefix, "upper witness", upper)

    triage = record.get("proposed_radius_triage") or record.get("certified_triage")
    if triage is not None:
        proposed = rat(triage["radius_exact"])
        classification = triage["classification"]
        esc = record.get("certified_exact_escalation")
        esc_lower = opt_rat(esc["lower_radius"]["exact"]) if esc else None
        esc_upper = opt_rat(esc["upper_radius"]["exact"]) if esc else None
        best_lower = lower
        if esc and (esc_lower is None or (best_lower is not None and esc_lower > best_lower)):
            best_lower = esc_lower
        best_upper = upper
        if esc and esc_upper is not None and (best_upper is None or esc_upper < best_upper):
            best_upper = esc_upper
        if classification == "certified_no_destabilisation":
            check(
                best_lower is None or proposed < best_lower,
                "safe classification not implied by the certified lower bound",
            )
        elif classification == "certified_destabilising_witness_exists":
            check(
                best_upper is not None and proposed >= best_upper,
                "destabilising classification without a covering certified witness",
            )
        else:
            check(
                best_lower is not None and proposed >= best_lower
                and (best_upper is None or proposed < best_upper),
                "unresolved classification outside the certified gap",
            )

    esc = record.get("certified_exact_escalation")
    if esc is not None and esc.get("witness") is not None:
        verify_witness_block(
            inst, esc["witness"], prefix, "escalation witness",
            opt_rat(esc["upper_radius"]["exact"]),
        )
        if esc["exact_certified"]:
            check(
                opt_rat(esc["lower_radius"]["exact"]) == opt_rat(esc["upper_radius"]["exact"]),
                "escalation claims exactness but bounds differ",
            )

    print(f"checks failed: {len(failures)}")
    for message in failures:
        print(f"  FAIL {message}")
    for message in notes:
        print(f"  note {message}")
    if not failures:
        print("certificate record verified independently (exact arithmetic)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
