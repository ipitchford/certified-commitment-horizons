"""Floor-aware weighted-L-infinity distance to a fixed affine half-space."""
from __future__ import annotations

from dataclasses import dataclass
from math import inf, isfinite
from typing import Sequence

import numpy as np

from .model import WWInstance, path_coefficients


@dataclass(frozen=True)
class PairwiseRadiusResult:
    radius: float
    nominal_gap: float
    coefficient_difference: np.ndarray
    revised_demand: np.ndarray | None
    achieved_difference: float | None
    status: str


def maximum_reduction(
    coefficients: Sequence[float],
    radius: float,
    nominal: Sequence[float],
    floor: Sequence[float],
    weights: Sequence[float],
) -> float:
    """Maximum reduction in ``b @ d`` over the floor-truncated box."""
    b = np.asarray(coefficients, dtype=float)
    d = np.asarray(nominal, dtype=float)
    ell = np.asarray(floor, dtype=float)
    w = np.asarray(weights, dtype=float)
    positive = b > 0
    negative = b < 0
    return float(
        np.sum(b[positive] * np.minimum(radius / w[positive], d[positive] - ell[positive]))
        + radius * np.sum((-b[negative]) / w[negative])
    )


def adversarial_demand(
    coefficients: Sequence[float],
    radius: float,
    nominal: Sequence[float],
    floor: Sequence[float],
    weights: Sequence[float],
) -> np.ndarray:
    b = np.asarray(coefficients, dtype=float)
    d = np.asarray(nominal, dtype=float).copy()
    ell = np.asarray(floor, dtype=float)
    w = np.asarray(weights, dtype=float)
    positive = b > 0
    negative = b < 0
    d[positive] = np.maximum(ell[positive], d[positive] - radius / w[positive])
    d[negative] += radius / w[negative]
    return d


def fixed_halfspace_radius(
    gap: float,
    coefficients: Sequence[float],
    nominal: Sequence[float],
    floor: Sequence[float],
    weights: Sequence[float],
    *,
    tol: float = 1e-11,
) -> PairwiseRadiusResult:
    """Solve ``inf{r >= 0: Psi_b(r) >= gap}`` by exact breakpoint logic."""
    b = np.asarray(coefficients, dtype=float)
    d = np.asarray(nominal, dtype=float)
    ell = np.asarray(floor, dtype=float)
    w = np.asarray(weights, dtype=float)
    if not (b.shape == d.shape == ell.shape == w.shape):
        raise ValueError("all vectors must have matching shapes")
    if np.any(w <= 0) or np.any(d < ell - tol):
        raise ValueError("invalid weights or demand floor")
    if gap <= tol:
        return PairwiseRadiusResult(0.0, float(gap), b.copy(), d.copy(), float(gap), "nominal_tie")
    if np.all(np.abs(b) <= tol):
        return PairwiseRadiusResult(inf, float(gap), b.copy(), None, None, "parallel_unreachable")

    slack = d - ell
    breakpoints = sorted(
        {
            float(w[t] * slack[t])
            for t in range(b.size)
            if b[t] > tol and slack[t] > tol
        }
    )
    left = 0.0
    reduction_left = 0.0
    for right in [*breakpoints, inf]:
        unsaturated_positive = (b > tol) & (w * slack > left + tol)
        negative = b < -tol
        slope = float(
            np.sum(b[unsaturated_positive] / w[unsaturated_positive])
            + np.sum((-b[negative]) / w[negative])
        )
        if reduction_left >= gap - tol:
            radius = left
            revised = adversarial_demand(b, radius, d, ell, w)
            achieved = float(gap + b @ (revised - d))
            return PairwiseRadiusResult(radius, float(gap), b.copy(), revised, achieved, "finite")
        if slope > tol:
            candidate = left + (gap - reduction_left) / slope
            if candidate <= right + tol:
                radius = max(left, float(candidate))
                revised = adversarial_demand(b, radius, d, ell, w)
                achieved = float(gap + b @ (revised - d))
                return PairwiseRadiusResult(radius, float(gap), b.copy(), revised, achieved, "finite")
        if not isfinite(right):
            break
        left = float(right)
        reduction_left = maximum_reduction(b, left, d, ell, w)
    return PairwiseRadiusResult(inf, float(gap), b.copy(), None, None, "unreachable")


def path_pairwise_radius(
    instance: WWInstance,
    competitor: Sequence[int],
    comparator: Sequence[int],
    *,
    tol: float = 1e-11,
) -> PairwiseRadiusResult:
    k_q, beta_q = path_coefficients(instance, competitor)
    k_p, beta_p = path_coefficients(instance, comparator)
    b = beta_q - beta_p
    gap = float((k_q - k_p) + b @ instance.demand)
    return fixed_halfspace_radius(
        gap,
        b,
        instance.demand,
        instance.floor,
        instance.weights,
        tol=tol,
    )
