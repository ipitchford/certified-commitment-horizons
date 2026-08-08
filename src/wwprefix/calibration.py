"""One-step conformal calibration and explicit finite-horizon error allocation."""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, inf
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class ConformalResult:
    threshold: float
    rank: int
    n: int
    alpha: float
    finite_scores: int
    inadmissible_scores: int
    guarantee: str = "one_step_marginal_under_exchangeability"


def weighted_revision_score(revision: Sequence[float], weights: Sequence[float]) -> float:
    revision_arr = np.asarray(revision, dtype=float)
    weights_arr = np.asarray(weights, dtype=float)
    if revision_arr.shape != weights_arr.shape:
        raise ValueError("revision and weights must have matching shapes")
    if np.any(weights_arr <= 0):
        raise ValueError("weights must be strictly positive")
    if np.any(~np.isfinite(revision_arr)) or np.any(~np.isfinite(weights_arr)):
        raise ValueError("revision and weights must be finite")
    return float(np.max(weights_arr * np.abs(revision_arr)))


def admissibility_aware_score(
    revision: Sequence[float],
    base_forecast: Sequence[float],
    floor: Sequence[float],
    weights: Sequence[float],
    *,
    tol: float = 1e-12,
) -> float:
    """Return infinity when ``base_forecast + revision`` leaves the domain."""
    revision_arr = np.asarray(revision, dtype=float)
    forecast_arr = np.asarray(base_forecast, dtype=float)
    floor_arr = np.asarray(floor, dtype=float)
    if not (revision_arr.shape == forecast_arr.shape == floor_arr.shape):
        raise ValueError("revision, base forecast and floor must have matching shapes")
    if np.any(forecast_arr + revision_arr < floor_arr - tol):
        return inf
    return weighted_revision_score(revision_arr, weights)


def split_conformal_threshold(scores: Sequence[float], alpha: float) -> ConformalResult:
    """Finite-sample one-step order-statistic threshold.

    Under exchangeability of the calibration scores and the next score,
    ``P(S_next <= threshold) >= 1-alpha`` marginally over both calibration and
    next-score randomness. This is not a conditional, simultaneous, or
    time-uniform statement.
    """
    if not (0 < alpha < 1):
        raise ValueError("alpha must lie strictly between zero and one")
    arr = np.asarray(scores, dtype=float)
    if arr.ndim != 1 or arr.size == 0:
        raise ValueError("scores must be a non-empty one-dimensional sequence")
    if np.any(np.isnan(arr)) or np.any(arr < 0):
        raise ValueError("scores must be non-negative or positive infinity")
    n = int(arr.size)
    rank = int(ceil((n + 1) * (1 - alpha)))
    threshold = inf if rank == n + 1 else float(np.sort(arr)[rank - 1])
    return ConformalResult(
        threshold=threshold,
        rank=rank,
        n=n,
        alpha=float(alpha),
        finite_scores=int(np.isfinite(arr).sum()),
        inadmissible_scores=int(np.isinf(arr).sum()),
    )


def bonferroni_allocation(
    total_alpha: float,
    decisions: int,
    weights: Sequence[float] | None = None,
) -> np.ndarray:
    """Pre-specified per-decision levels whose sum equals ``total_alpha``."""
    if not (0 < total_alpha < 1):
        raise ValueError("total_alpha must lie strictly between zero and one")
    if decisions <= 0:
        raise ValueError("decisions must be positive")
    if weights is None:
        return np.full(decisions, total_alpha / decisions)
    allocation_weights = np.asarray(weights, dtype=float)
    if allocation_weights.shape != (decisions,) or np.any(allocation_weights <= 0):
        raise ValueError("allocation weights must be positive and match decisions")
    return total_alpha * allocation_weights / allocation_weights.sum()
