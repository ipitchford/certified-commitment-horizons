#!/usr/bin/env python3
"""Monte Carlo audit of one-step conformal and finite-horizon allocation claims."""
from __future__ import annotations

from math import ceil

import numpy as np
import pandas as pd

from _common import ROOT, SEED, environment_record, wilson_interval, write_csv, write_json


def row_threshold(calibration: np.ndarray, alpha: float) -> tuple[np.ndarray, int]:
    n = calibration.shape[-1]
    rank = int(ceil((n + 1) * (1.0 - alpha)))
    if rank == n + 1:
        return np.full(calibration.shape[:-1], np.inf), rank
    return np.partition(calibration, rank - 1, axis=-1)[..., rank - 1], rank


def scenario_record(name: str, covered: np.ndarray, *, target: float | None, metadata: dict) -> dict:
    successes = int(np.sum(covered))
    trials = int(covered.size)
    lo, hi = wilson_interval(successes, trials)
    return {
        "scenario": name,
        "trials": trials,
        "covered": successes,
        "coverage": successes / trials,
        "wilson_95_low": lo,
        "wilson_95_high": hi,
        "target_or_bound": target,
        **metadata,
    }


def main() -> None:
    rng = np.random.default_rng(SEED + 202)
    trial_rows: list[pd.DataFrame] = []
    summaries: list[dict] = []

    trials = 20_000
    n = 49
    alpha = 0.10
    all_scores = rng.lognormal(mean=0.0, sigma=0.75, size=(trials, n + 1))
    threshold, rank = row_threshold(all_scores[:, :n], alpha)
    covered = all_scores[:, n] <= threshold
    summaries.append(scenario_record(
        "exchangeable_lognormal",
        covered,
        target=rank / (n + 1),
        metadata={"n_calibration": n, "alpha": alpha, "rank": rank, "next_scale": 1.0},
    ))
    trial_rows.append(pd.DataFrame({
        "scenario": "exchangeable_lognormal",
        "trial": np.arange(trials),
        "threshold": threshold,
        "next_score": all_scores[:, n],
        "covered": covered,
    }))

    # Same calibration law, larger next-score scale: an explicit distribution-shift failure mode.
    base_cal = rng.lognormal(mean=0.0, sigma=0.75, size=(trials, n))
    next_base = rng.lognormal(mean=0.0, sigma=0.75, size=trials)
    shifted_threshold, shifted_rank = row_threshold(base_cal, alpha)
    for scale in (1.25, 1.50):
        next_score = scale * next_base
        covered_shift = next_score <= shifted_threshold
        name = f"next_scale_{scale:.2f}"
        summaries.append(scenario_record(
            name,
            covered_shift,
            target=None,
            metadata={
                "n_calibration": n,
                "alpha": alpha,
                "rank": shifted_rank,
                "next_scale": scale,
                "guarantee_applies": False,
            },
        ))
        trial_rows.append(pd.DataFrame({
            "scenario": name,
            "trial": np.arange(trials),
            "threshold": shifted_threshold,
            "next_score": next_score,
            "covered": covered_shift,
        }))

    # Exchangeable vector revisions with an admissibility floor.  Inadmissible
    # forecasts receive +infinity exactly as in the implementation.
    dim = 4
    base = np.full(dim, 2.0)
    floor = np.zeros(dim)
    weights = np.asarray([1.0, 1.2, 0.8, 1.5])
    revisions = rng.normal(0.0, 1.0, size=(trials, n + 1, dim))
    revised = base + revisions
    scores = np.max(weights * np.abs(revisions), axis=-1)
    scores[np.any(revised < floor, axis=-1)] = np.inf
    floor_threshold, floor_rank = row_threshold(scores[:, :n], alpha)
    floor_covered = scores[:, n] <= floor_threshold
    summaries.append(scenario_record(
        "exchangeable_with_floor_admissibility",
        floor_covered,
        target=floor_rank / (n + 1),
        metadata={
            "n_calibration": n,
            "alpha": alpha,
            "rank": floor_rank,
            "dimension": dim,
            "calibration_inadmissible_fraction": float(np.isinf(scores[:, :n]).mean()),
            "next_inadmissible_fraction": float(np.isinf(scores[:, n]).mean()),
        },
    ))
    trial_rows.append(pd.DataFrame({
        "scenario": "exchangeable_with_floor_admissibility",
        "trial": np.arange(trials),
        "threshold": floor_threshold,
        "next_score": scores[:, n],
        "covered": floor_covered,
    }))

    # Five pre-specified decisions with Bonferroni allocation.  Each decision
    # has its own exchangeable calibration set; no adaptive re-use occurs.
    family_trials = 5_000
    decisions = 5
    total_alpha = 0.10
    per_alpha = total_alpha / decisions
    n_family = 99
    family_scores = rng.lognormal(
        mean=0.0,
        sigma=0.75,
        size=(family_trials, decisions, n_family + 1),
    )
    family_threshold, family_rank = row_threshold(family_scores[:, :, :n_family], per_alpha)
    point_covered = family_scores[:, :, n_family] <= family_threshold
    family_covered = np.all(point_covered, axis=1)
    summaries.append(scenario_record(
        "five_decision_bonferroni_family",
        family_covered,
        target=1.0 - total_alpha,
        metadata={
            "n_calibration_per_decision": n_family,
            "decisions": decisions,
            "total_alpha": total_alpha,
            "per_decision_alpha": per_alpha,
            "rank": family_rank,
            "mean_pointwise_coverage": float(point_covered.mean()),
        },
    ))
    trial_rows.append(pd.DataFrame({
        "scenario": "five_decision_bonferroni_family",
        "trial": np.arange(family_trials),
        "threshold": np.nan,
        "next_score": np.nan,
        "covered": family_covered,
    }))

    raw = pd.concat(trial_rows, ignore_index=True)
    summary_df = pd.DataFrame(summaries)
    write_csv(raw, ROOT / "results" / "raw" / "calibration_trials.csv")
    write_csv(summary_df, ROOT / "results" / "raw" / "calibration_scenarios.csv")
    payload = {
        "environment": environment_record(),
        "claims_tested": {
            "exchangeable": "one-step marginal rank coverage",
            "floor": "inadmissible revisions scored as positive infinity",
            "repeated_use": "pre-specified five-decision Bonferroni family bound",
            "shift": "negative control; ordinary exchangeable guarantee does not apply",
        },
        "scenarios": summaries,
    }
    write_json(payload, ROOT / "results" / "processed" / "calibration_audit_summary.json")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
