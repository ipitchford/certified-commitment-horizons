"""Bellman residuals and the certified dead-zone rolling bound."""
from __future__ import annotations

from math import isinf
from typing import Sequence

import numpy as np

from .model import WWInstance, path_cost, shortest_path


def coefficient_diameter(instance: WWInstance, start: int = 0) -> float:
    """Exact weighted dual-norm diameter of suffix path coefficients."""
    if start == instance.T:
        return 0.0
    if not (0 <= start < instance.T):
        raise ValueError("start must lie in 0,...,T")
    return float(
        np.sum(
            (instance.q[start] - instance.q[start : instance.T])
            / instance.weights[start : instance.T]
        )
    )


def bellman_residual(
    instance: WWInstance,
    realised_demand: Sequence[float],
    committed_block: Sequence[int],
) -> float:
    """Structural regret of fixed setup arcs with uncapacitated quantity recourse."""
    block = tuple(int(v) for v in committed_block)
    if len(block) < 2 or any(i >= j for i, j in zip(block, block[1:])):
        raise ValueError("committed_block must contain increasing nodes")
    start, end = block[0], block[-1]
    if not (0 <= start < end <= instance.T):
        raise ValueError("committed_block lies outside the horizon")
    d = np.asarray(realised_demand, dtype=float)
    if d.shape != instance.demand.shape:
        raise ValueError("realised demand has the wrong shape")
    if np.any(d < instance.floor - 1e-10):
        raise ValueError("realised demand lies below the admissible floor")
    block_value = path_cost(instance, d, block)
    suffix_value, _ = shortest_path(instance, d, start=end)
    optimum_value, _ = shortest_path(instance, d, start=start)
    residual = float(block_value + suffix_value - optimum_value)
    return max(0.0, residual) if residual > -1e-8 else residual


def revision_norm(
    instance: WWInstance,
    forecast: Sequence[float],
    realised_demand: Sequence[float],
    start: int = 0,
) -> float:
    f = np.asarray(forecast, dtype=float)
    d = np.asarray(realised_demand, dtype=float)
    if f.shape != instance.demand.shape or d.shape != instance.demand.shape:
        raise ValueError("forecast and realised demand must match the horizon")
    return float(np.max(instance.weights[start:] * np.abs(d[start:] - f[start:])))


def generic_lipschitz_bound(
    instance: WWInstance,
    forecast: Sequence[float],
    realised_demand: Sequence[float],
    start: int = 0,
) -> float:
    return coefficient_diameter(instance, start) * revision_norm(instance, forecast, realised_demand, start)


def dead_zone_bound(
    instance: WWInstance,
    forecast: Sequence[float],
    realised_demand: Sequence[float],
    start: int,
    radius: float,
) -> float:
    """Bound structural regret by diameter times revision beyond the radius.

    ``radius`` may be the exact prefix radius or any certified lower bound on
    it. The statement concerns setup epochs/cycle boundaries; literal order
    quantities remain adjustable to realised demand.
    """
    f = np.asarray(forecast, dtype=float)
    d = np.asarray(realised_demand, dtype=float)
    if f.shape != instance.demand.shape or d.shape != instance.demand.shape:
        raise ValueError("forecast and realised demand must match the horizon")
    if np.any(f < instance.floor - 1e-10) or np.any(d < instance.floor - 1e-10):
        raise ValueError("forecast and realised demand must lie in the admissible domain")
    if radius < 0:
        raise ValueError("radius must be non-negative")
    if isinf(radius):
        return 0.0
    norm = revision_norm(instance, f, d, start)
    return coefficient_diameter(instance, start) * max(0.0, norm - radius)


def radial_projection(
    instance: WWInstance,
    forecast: Sequence[float],
    realised_demand: Sequence[float],
    start: int,
    radius: float,
) -> np.ndarray:
    """Project realised demand radially to the closed weighted radius ball."""
    if isinf(radius):
        return np.asarray(realised_demand, dtype=float).copy()
    f = np.asarray(forecast, dtype=float)
    d = np.asarray(realised_demand, dtype=float)
    norm = revision_norm(instance, f, d, start)
    if norm <= radius or norm == 0:
        return d.copy()
    projected = f.copy()
    projected[start:] = f[start:] + (radius / norm) * (d[start:] - f[start:])
    return projected
