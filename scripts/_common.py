"""Shared deterministic experiment utilities."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from math import sqrt
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from wwprefix import WWInstance  # noqa: E402

SEED = 20260804


def random_ww_instance(
    rng: np.random.Generator,
    T: int,
    *,
    regime: str = "regular",
) -> WWInstance:
    """Generate a positive-demand ordered-slope instance with multiple cycles likely."""
    if regime == "regular":
        demand = rng.uniform(20.0, 100.0, T)
        holding = rng.uniform(0.04, 0.35, max(0, T - 1))
        K = rng.uniform(70.0, 220.0, T)
        floor_fraction = rng.uniform(0.0, 0.30, T)
    elif regime == "near_tie":
        demand = rng.uniform(45.0, 65.0, T)
        holding = rng.uniform(0.08, 0.13, max(0, T - 1))
        base = rng.uniform(95.0, 125.0)
        K = base + rng.normal(0.0, 2.0, T)
        K = np.maximum(K, 1.0)
        floor_fraction = rng.uniform(0.0, 0.10, T)
    elif regime == "floor_heavy":
        demand = rng.uniform(20.0, 100.0, T)
        holding = rng.uniform(0.04, 0.35, max(0, T - 1))
        K = rng.uniform(70.0, 220.0, T)
        floor_fraction = rng.uniform(0.70, 0.98, T)
    elif regime == "strict_gap":
        if T < 3:
            raise ValueError("strict_gap requires T >= 3")
        # Perturb the three-period analytical counterexample, then append a
        # common, strongly separated suffix.  Rejection in
        # ``draw_strict_gap_instance`` retains only genuine strict-gap cases.
        K = np.full(T, 1.0e5, dtype=float)
        K[:3] = np.maximum(
            np.asarray([0.0, 3.0, 2.0]) + rng.normal(0.0, [0.0, 0.45, 0.45]),
            0.0,
        )
        holding = np.maximum(
            np.asarray([1.0, 1.0]) + rng.normal(0.0, 0.16, 2),
            0.08,
        )
        q = np.empty(T, dtype=float)
        q[:3] = [holding.sum(), holding[1], 0.0]
        demand = np.empty(T, dtype=float)
        demand[:3] = np.maximum(
            np.asarray([1.0, 5.0, 1.0]) + rng.normal(0.0, [0.22, 0.90, 0.22]),
            0.15,
        )
        floor = np.empty(T, dtype=float)
        floor[:3] = np.maximum(
            0.0,
            np.minimum(
                demand[:3],
                np.asarray([0.5, 0.5, 0.5]) + rng.normal(0.0, 0.10, 3),
            ),
        )
        weights = np.empty(T, dtype=float)
        weights[:3] = np.exp(rng.normal(0.0, 0.12, 3))
        if T > 3:
            K[3] = 0.0
            q[3:] = -10.0
            demand[3:] = np.maximum(1.0, 20.0 + rng.normal(0.0, 1.0, T - 3))
            floor[3:] = 0.5 * demand[3:]
            weights[3:] = np.exp(rng.normal(0.0, 0.05, T - 3))
        return WWInstance.create(K=K, q=q, demand=demand, floor=floor, weights=weights)
    else:
        raise ValueError(f"unknown regime {regime!r}")
    q = np.zeros(T, dtype=float)
    if T > 1:
        q[1:] = -np.cumsum(holding)
    floor = demand * floor_fraction
    weights = rng.uniform(0.6, 1.8, T)
    return WWInstance.create(K=K, q=q, demand=demand, floor=floor, weights=weights)


def draw_strict_gap_instance(
    rng: np.random.Generator,
    T: int,
    *,
    max_attempts: int = 2_000,
) -> tuple[WWInstance, int]:
    """Draw a verified partial-prefix case with a strict lower/exact gap.

    This generator deliberately conditions on the property under study.  It is
    therefore used only as an adversarial test stratum, never to estimate the
    prevalence of strictness in an external population.
    """
    from wwprefix import polynomial_radius_bracket, shortest_path

    for attempt in range(1, max_attempts + 1):
        instance = random_ww_instance(rng, T, regime="strict_gap")
        _, nominal = shortest_path(instance)
        if len(nominal) < 2 or nominal[1] != 1:
            continue
        bracket = polynomial_radius_bracket(instance, nominal, 1)
        if (
            np.isfinite(bracket.lower_radius)
            and np.isfinite(bracket.upper_radius)
            and bracket.upper_radius > bracket.lower_radius + 1e-6
        ):
            return instance, attempt
    raise RuntimeError(f"failed to draw a strict-gap instance for T={T}")


def wilson_interval(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    The release uses the 95% value explicitly.  A compact inverse-normal
    approximation is included for the few other conventional levels used in
    sensitivity checks, avoiding an additional dependency.
    """
    if trials <= 0 or not (0 <= successes <= trials):
        raise ValueError("invalid binomial counts")
    if confidence == 0.95:
        z = 1.959963984540054
    elif confidence == 0.90:
        z = 1.6448536269514722
    elif confidence == 0.99:
        z = 2.5758293035489004
    else:
        raise ValueError("supported confidence levels are 0.90, 0.95 and 0.99")
    p = successes / trials
    denom = 1.0 + z * z / trials
    centre = (p + z * z / (2.0 * trials)) / denom
    half = z / denom * sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials))
    return max(0.0, centre - half), min(1.0, centre + half)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format="%.12g")


def strict_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): strict_json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [strict_json_value(v) for v in value]
    if isinstance(value, np.ndarray):
        return [strict_json_value(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        return strict_json_value(value.item())
    if isinstance(value, float):
        if np.isnan(value):
            return None
        if np.isposinf(value):
            return "Infinity"
        if np.isneginf(value):
            return "-Infinity"
    return value


def write_json(value: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(strict_json_value(value), indent=2, sort_keys=True) + "\n")


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def environment_record() -> dict[str, Any]:
    import matplotlib
    import pandas
    import scipy

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pandas.__version__,
        "matplotlib": matplotlib.__version__,
        "git_commit": git_commit(),
        "seed": SEED,
    }
