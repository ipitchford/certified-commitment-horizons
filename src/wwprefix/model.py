"""Core Wagner--Whitin shortest-path model.

Internal indices are zero based. Periods are ``0,...,T-1`` and the terminal
node is ``T``. Public JSON helpers expose one-based node labels.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterator, Sequence

import numpy as np

ArrayLike = Sequence[float] | np.ndarray
Path = tuple[int, ...]


@dataclass(frozen=True)
class WWInstance:
    """Reduced uncapacitated Wagner--Whitin instance.

    ``q`` contains the reduced arc slopes and must be non-increasing. Demand
    revisions are restricted to ``d >= floor``. The weighted infinity norm is
    ``max_t weights[t] * |d[t] - demand[t]|``.
    """

    K: np.ndarray
    q: np.ndarray
    demand: np.ndarray
    floor: np.ndarray
    weights: np.ndarray

    @classmethod
    def create(
        cls,
        K: ArrayLike,
        q: ArrayLike,
        demand: ArrayLike,
        floor: ArrayLike | None = None,
        weights: ArrayLike | None = None,
        *,
        check_ordered: bool = True,
        tol: float = 1e-10,
    ) -> "WWInstance":
        K_arr = np.asarray(K, dtype=float)
        q_arr = np.asarray(q, dtype=float)
        d_arr = np.asarray(demand, dtype=float)
        if K_arr.ndim != 1 or q_arr.ndim != 1 or d_arr.ndim != 1:
            raise ValueError("K, q and demand must be one-dimensional")
        if not (K_arr.size == q_arr.size == d_arr.size):
            raise ValueError("K, q and demand must have equal lengths")
        if K_arr.size == 0:
            raise ValueError("the horizon must contain at least one period")
        ell = np.zeros_like(d_arr) if floor is None else np.asarray(floor, dtype=float)
        w = np.ones_like(d_arr) if weights is None else np.asarray(weights, dtype=float)
        if ell.shape != d_arr.shape or w.shape != d_arr.shape:
            raise ValueError("floor and weights must match demand")
        if any(np.any(~np.isfinite(x)) for x in (K_arr, q_arr, d_arr, ell, w)):
            raise ValueError("all instance coefficients must be finite")
        if np.any(K_arr < -tol):
            raise ValueError("setup costs must be non-negative")
        if np.any(ell < -tol):
            raise ValueError("demand floors must be non-negative")
        if np.any(d_arr < ell - tol):
            raise ValueError("nominal demand must lie above the floor")
        if np.any(w <= 0):
            raise ValueError("weights must be strictly positive")
        if check_ordered and np.any(q_arr[:-1] < q_arr[1:] - tol):
            raise ValueError("reduced slopes q must be non-increasing")
        return cls(K_arr.copy(), q_arr.copy(), d_arr.copy(), ell.copy(), w.copy())

    @property
    def T(self) -> int:
        return int(self.demand.size)

    def with_demand(self, demand: ArrayLike) -> "WWInstance":
        return WWInstance.create(
            self.K,
            self.q,
            demand,
            self.floor,
            self.weights,
            check_ordered=False,
        )


def cumulative_demand(demand: ArrayLike) -> np.ndarray:
    d = np.asarray(demand, dtype=float)
    return np.concatenate(([0.0], np.cumsum(d)))


def validate_complete_path(path: Sequence[int], T: int) -> Path:
    p = tuple(int(v) for v in path)
    if len(p) < 2 or p[0] != 0 or p[-1] != T:
        raise ValueError("a complete path must start at 0 and end at T")
    if any(i >= j for i, j in zip(p, p[1:])):
        raise ValueError("path nodes must be strictly increasing")
    return p


def validate_prefix(prefix: Sequence[int], T: int) -> Path:
    p = tuple(int(v) for v in prefix)
    if len(p) < 2 or p[0] != 0 or p[-1] > T:
        raise ValueError("a protected prefix must start at 0 and remain in the horizon")
    if any(i >= j for i, j in zip(p, p[1:])):
        raise ValueError("prefix nodes must be strictly increasing")
    return p


def arc_cost(instance: WWInstance, demand: ArrayLike, i: int, j: int) -> float:
    if not (0 <= i < j <= instance.T):
        raise ValueError(f"invalid arc ({i},{j}) for T={instance.T}")
    d = np.asarray(demand, dtype=float)
    if d.shape != instance.demand.shape:
        raise ValueError("demand has the wrong shape")
    return float(instance.K[i] + instance.q[i] * np.sum(d[i:j]))


def path_coefficients(instance: WWInstance, path: Sequence[int]) -> tuple[float, np.ndarray]:
    """Return ``kappa,beta`` such that ``C_path(d)=kappa+beta @ d``.

    Complete paths and protected prefixes are both accepted. Coefficients are
    zero outside the periods covered by a partial path.
    """
    p = tuple(int(v) for v in path)
    if len(p) < 2 or any(i >= j for i, j in zip(p, p[1:])):
        raise ValueError("path or prefix must contain increasing nodes")
    if p[0] < 0 or p[-1] > instance.T:
        raise ValueError("path nodes lie outside the horizon")
    beta = np.zeros(instance.T, dtype=float)
    kappa = 0.0
    for i, j in zip(p, p[1:]):
        if i >= instance.T:
            raise ValueError("terminal node cannot have an outgoing arc")
        kappa += float(instance.K[i])
        beta[i:j] = instance.q[i]
    return kappa, beta


def path_cost(instance: WWInstance, demand: ArrayLike, path: Sequence[int]) -> float:
    kappa, beta = path_coefficients(instance, path)
    d = np.asarray(demand, dtype=float)
    if d.shape != instance.demand.shape:
        raise ValueError("demand has the wrong shape")
    return float(kappa + beta @ d)


def enumerate_paths(T: int) -> Iterator[Path]:
    """Enumerate all ``2^(T-1)`` complete paths deterministically."""
    if T < 1:
        raise ValueError("T must be positive")
    interior = tuple(range(1, T))
    for r in range(len(interior) + 1):
        for chosen in combinations(interior, r):
            yield (0, *chosen, T)


def follows_prefix(path: Sequence[int], prefix: Sequence[int]) -> bool:
    p = tuple(path)
    pref = tuple(prefix)
    return len(p) >= len(pref) and p[: len(pref)] == pref


def outside_paths(T: int, prefix: Sequence[int]) -> Iterator[Path]:
    for path in enumerate_paths(T):
        if not follows_prefix(path, prefix):
            yield path


def inside_paths(T: int, prefix: Sequence[int]) -> Iterator[Path]:
    for path in enumerate_paths(T):
        if follows_prefix(path, prefix):
            yield path


def _prefer(cost: float, path: Path, best_cost: float, best_path: Path | None, tol: float) -> bool:
    if best_path is None or cost < best_cost - tol:
        return True
    if abs(cost - best_cost) <= tol:
        # Reproducible tie-break: fewer setup arcs, then lexicographic nodes.
        return (len(path), path) < (len(best_path), best_path)
    return False


def shortest_path(
    instance: WWInstance,
    demand: ArrayLike | None = None,
    *,
    start: int = 0,
    tol: float = 1e-10,
) -> tuple[float, Path]:
    """Shortest suffix path from ``start`` to ``T`` with deterministic ties."""
    d = instance.demand if demand is None else np.asarray(demand, dtype=float)
    if d.shape != instance.demand.shape:
        raise ValueError("demand has the wrong shape")
    T = instance.T
    if start == T:
        return 0.0, (T,)
    if not (0 <= start < T):
        raise ValueError("start must lie in 0,...,T")
    D = cumulative_demand(d)
    value = np.full(T + 1, np.inf)
    paths: list[Path | None] = [None] * (T + 1)
    value[start] = 0.0
    paths[start] = (start,)
    for j in range(start + 1, T + 1):
        best = np.inf
        best_path: Path | None = None
        for i in range(start, j):
            if paths[i] is None:
                continue
            cand = float(value[i] + instance.K[i] + instance.q[i] * (D[j] - D[i]))
            candidate_path = (*paths[i], j)
            if _prefer(cand, candidate_path, float(best), best_path, tol):
                best = cand
                best_path = candidate_path
        value[j] = best
        paths[j] = best_path
    if paths[T] is None:
        raise RuntimeError("complete lot-sizing DAG unexpectedly has no path")
    return float(value[T]), paths[T]


def constrained_inside_path(
    instance: WWInstance,
    demand: ArrayLike,
    prefix: Sequence[int],
    *,
    tol: float = 1e-10,
) -> tuple[float, Path]:
    pref = validate_prefix(prefix, instance.T)
    d = np.asarray(demand, dtype=float)
    prefix_value = path_cost(instance, d, pref)
    suffix_value, suffix = shortest_path(instance, d, start=pref[-1], tol=tol)
    return float(prefix_value + suffix_value), (*pref, *suffix[1:])


def forward_backward_values(
    instance: WWInstance,
    demand: ArrayLike | None = None,
) -> tuple[np.ndarray, np.ndarray, float]:
    d = instance.demand if demand is None else np.asarray(demand, dtype=float)
    D = cumulative_demand(d)
    T = instance.T
    forward = np.full(T + 1, np.inf)
    forward[0] = 0.0
    for j in range(1, T + 1):
        forward[j] = min(
            forward[i] + instance.K[i] + instance.q[i] * (D[j] - D[i])
            for i in range(j)
        )
    backward = np.full(T + 1, np.inf)
    backward[T] = 0.0
    for i in range(T - 1, -1, -1):
        backward[i] = min(
            instance.K[i] + instance.q[i] * (D[j] - D[i]) + backward[j]
            for j in range(i + 1, T + 1)
        )
    return forward, backward, float(forward[T])


def optimal_arc_dag(
    instance: WWInstance,
    demand: ArrayLike | None = None,
    *,
    tol: float = 1e-9,
) -> dict[int, tuple[int, ...]]:
    d = instance.demand if demand is None else np.asarray(demand, dtype=float)
    D = cumulative_demand(d)
    forward, backward, optimum = forward_backward_values(instance, d)
    scale = 1.0 + abs(optimum)
    out: dict[int, list[int]] = {i: [] for i in range(instance.T)}
    for i in range(instance.T):
        for j in range(i + 1, instance.T + 1):
            total = forward[i] + instance.K[i] + instance.q[i] * (D[j] - D[i]) + backward[j]
            if abs(float(total - optimum)) <= tol * scale:
                out[i].append(j)
    return {i: tuple(v) for i, v in out.items()}


def common_optimal_prefix(
    instance: WWInstance,
    demand: ArrayLike | None = None,
    *,
    tol: float = 1e-9,
) -> Path:
    """Longest node prefix shared by all optimal paths."""
    dag = optimal_arc_dag(instance, demand, tol=tol)
    node = 0
    prefix = [0]
    while node < instance.T:
        successors = dag.get(node, ())
        if len(successors) != 1:
            break
        node = successors[0]
        prefix.append(node)
        if node == instance.T:
            break
    return tuple(prefix)


def count_optimal_paths(
    instance: WWInstance,
    demand: ArrayLike | None = None,
    *,
    tol: float = 1e-9,
    cap: int | None = None,
) -> int:
    dag = optimal_arc_dag(instance, demand, tol=tol)
    counts = [0] * (instance.T + 1)
    counts[instance.T] = 1
    for i in range(instance.T - 1, -1, -1):
        total = sum(counts[j] for j in dag.get(i, ()))
        if cap is not None:
            total = min(total, cap)
        counts[i] = total
    return int(counts[0])


def prefix_values(
    instance: WWInstance,
    demand: ArrayLike,
    prefix: Sequence[int],
) -> tuple[float, float]:
    """Return best inside and outside values for a small horizon.

    This exhaustive helper is intended for audit and illustration, not the
    polynomial algorithms.
    """
    d = np.asarray(demand, dtype=float)
    inside = np.inf
    outside = np.inf
    for path in enumerate_paths(instance.T):
        value = path_cost(instance, d, path)
        if follows_prefix(path, prefix):
            inside = min(inside, value)
        else:
            outside = min(outside, value)
    return float(inside), float(outside)


def to_one_based(path: Sequence[int]) -> tuple[int, ...]:
    return tuple(int(v) + 1 for v in path)


def from_one_based(path: Sequence[int]) -> tuple[int, ...]:
    return tuple(int(v) - 1 for v in path)
