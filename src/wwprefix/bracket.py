"""Polynomial lower/upper bracketing for the strong prefix radius.

The lower side freezes the nominal comparator.  The upper side takes the
outside path exposed by that lower certificate and solves its compact inverse
linear programme against the moving inside continuation.  Both computations
have polynomial-size formulations.  Equality, or a closing lower witness,
certifies the exact strong radius without enumerating all outside paths.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import inf, isfinite
from typing import Sequence

from .certificate import FrozenCertificateResult, frozen_certificate_lp
from .exact import FixedCompetitorResult, fixed_competitor_inverse_lp
from .model import Path, WWInstance, constrained_inside_path, path_cost, validate_complete_path


@dataclass(frozen=True)
class PolynomialBracketResult:
    lower_radius: float
    safe_lower_radius: float
    upper_radius: float
    exact_radius: float | None
    exact_certified: bool
    exact_reason: str | None
    lower_outside_path: Path | None
    lower_witness_closes: bool | None
    lower_witness_difference_to_inside: float | None
    lower_inside_path: Path | None
    upper_outside_path: Path | None
    upper_inside_path: Path | None
    upper_verified_difference: float | None
    status: str
    frozen: FrozenCertificateResult
    fixed_competitor: FixedCompetitorResult | None


def polynomial_radius_bracket(
    instance: WWInstance,
    nominal_path: Sequence[int],
    k: int,
    *,
    tol: float = 1e-8,
) -> PolynomialBracketResult:
    """Return a certified lower/feasible-upper bracket.

    Mathematically, ``lower_radius <= rho <= upper_radius``.  The lower value
    is the frozen-comparator certificate.  The upper value is the exact
    inverse radius for the lower certificate's exposed outside path.  If the
    frozen lower witness already beats the best prefix-retaining continuation,
    or if the two sides coincide, the strong radius is certified exactly.

    Floating-point output should be interpreted through the reported solver
    tolerances.  The manuscript's theorem is an exact rational statement.
    """
    pstar = validate_complete_path(nominal_path, instance.T)
    frozen = frozen_certificate_lp(instance, pstar, k, tol=tol)

    if frozen.status == "no_outside_path" or not isfinite(frozen.radius):
        return PolynomialBracketResult(
            lower_radius=inf,
            safe_lower_radius=inf,
            upper_radius=inf,
            exact_radius=inf,
            exact_certified=True,
            exact_reason="no finite frozen tie exists, so no strong destabilisation exists",
            lower_outside_path=None,
            lower_witness_closes=None,
            lower_witness_difference_to_inside=None,
            lower_inside_path=None,
            upper_outside_path=None,
            upper_inside_path=None,
            upper_verified_difference=None,
            status="exact_infinite",
            frozen=frozen,
            fixed_competitor=None,
        )

    if frozen.outside_path is None:
        return PolynomialBracketResult(
            lower_radius=frozen.radius,
            safe_lower_radius=frozen.safe_radius,
            upper_radius=inf,
            exact_radius=None,
            exact_certified=False,
            exact_reason=None,
            lower_outside_path=None,
            lower_witness_closes=None,
            lower_witness_difference_to_inside=None,
            lower_inside_path=None,
            upper_outside_path=None,
            upper_inside_path=None,
            upper_verified_difference=None,
            status="lower_without_recovered_path",
            frozen=frozen,
            fixed_competitor=None,
        )

    closes: bool | None = None
    close_difference: float | None = None
    lower_inside: Path | None = None
    if frozen.revised_demand is not None:
        prefix = pstar[: k + 1]
        inside_value, lower_inside = constrained_inside_path(
            instance, frozen.revised_demand, prefix, tol=tol
        )
        outside_value = path_cost(instance, frozen.revised_demand, frozen.outside_path)
        close_difference = float(outside_value - inside_value)
        scale = 1.0 + abs(inside_value)
        closes = close_difference <= 10.0 * tol * scale

    fixed = fixed_competitor_inverse_lp(
        instance, pstar, k, frozen.outside_path, tol=tol
    )
    upper = fixed.radius if fixed.status == "optimal" else inf

    exact = False
    reason: str | None = None
    exact_radius: float | None = None
    if closes:
        exact = True
        reason = "the frozen lower witness also beats the best prefix-retaining continuation"
        exact_radius = frozen.radius
    elif isfinite(upper):
        scale = 1.0 + max(abs(frozen.radius), abs(upper))
        if abs(upper - frozen.radius) <= 20.0 * tol * scale:
            exact = True
            reason = "polynomial lower and feasible upper radii coincide"
            exact_radius = 0.5 * (frozen.radius + upper)

    if exact:
        status = "exact_finite"
    elif isfinite(upper):
        status = "finite_bracket"
    else:
        status = "lower_only"

    return PolynomialBracketResult(
        lower_radius=frozen.radius,
        safe_lower_radius=frozen.safe_radius,
        upper_radius=upper,
        exact_radius=exact_radius,
        exact_certified=exact,
        exact_reason=reason,
        lower_outside_path=frozen.outside_path,
        lower_witness_closes=closes,
        lower_witness_difference_to_inside=close_difference,
        lower_inside_path=lower_inside,
        upper_outside_path=fixed.outside_path,
        upper_inside_path=fixed.inside_path,
        upper_verified_difference=fixed.verified_difference,
        status=status,
        frozen=frozen,
        fixed_competitor=fixed,
    )
