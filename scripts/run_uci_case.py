#!/usr/bin/env python3
"""Illustrative forecast-vintage case using the UCI daily-order series.

The observed demand is real.  Forecast vintages, cost coefficients and all
commitment decisions are reconstructed for methodological illustration; this
is not a field validation or a claim about the original distributor's costs.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from _common import ROOT, SEED, environment_record, sha256, write_csv, write_json
from wwprefix import (
    WWInstance,
    bellman_residual,
    common_optimal_prefix,
    constrained_inside_path,
    count_optimal_paths,
    exact_radius_enumeration,
    outside_shortest_path,
    polynomial_radius_bracket,
    shortest_path,
    split_conformal_threshold,
    weighted_revision_score,
)

DATA_PATH = ROOT / "data/external/Daily_Demand_Forecasting_Orders.csv"
TARGET = "Target (Total orders)"
WEEK = "Week of the month (first week, second, third, fourth or fifth week"
DAY = "Day of the week (Monday to Friday)"
HORIZON = 8
RIDGE = 0.75


@dataclass(frozen=True)
class ForecastWindow:
    window_id: int
    start: int
    old_cutoff: int
    new_cutoff: int
    old: np.ndarray
    new: np.ndarray
    actual: np.ndarray


def _feature_vector(
    y: np.ndarray,
    week: np.ndarray,
    day: np.ndarray,
    origin: int,
    target: int,
) -> np.ndarray:
    """Causal pooled direct-forecast features known at ``origin``."""
    h = target - origin
    last = y[origin]
    mean5 = y[max(0, origin - 4) : origin + 1].mean()
    mean10 = y[max(0, origin - 9) : origin + 1].mean()
    continuous = [
        1.0,
        target / 59.0,
        h / 10.0,
        (h / 10.0) ** 2,
        last / 300.0,
        mean5 / 300.0,
        mean10 / 300.0,
    ]
    # Drop one category from each calendar set; target calendar is known.
    day_dummies = [float(day[target] == code) for code in (3, 4, 5, 6)]
    week_dummies = [float(week[target] == code) for code in (2, 3, 4, 5)]
    return np.asarray([*continuous, *day_dummies, *week_dummies], dtype=float)


def _fit_at_cutoff(
    y: np.ndarray,
    week: np.ndarray,
    day: np.ndarray,
    cutoff: int,
) -> np.ndarray:
    rows: list[np.ndarray] = []
    targets: list[float] = []
    for origin in range(9, cutoff):
        for h in range(1, HORIZON + 3):
            target = origin + h
            if target > cutoff:
                break
            rows.append(_feature_vector(y, week, day, origin, target))
            targets.append(float(y[target]))
    X = np.vstack(rows)
    response = np.asarray(targets)
    penalty = np.eye(X.shape[1]) * RIDGE
    penalty[0, 0] = 0.0
    return np.linalg.solve(X.T @ X + penalty, X.T @ response)


def _forecast_window(
    y: np.ndarray,
    week: np.ndarray,
    day: np.ndarray,
    cutoff: int,
    targets: np.ndarray,
) -> np.ndarray:
    beta = _fit_at_cutoff(y, week, day, cutoff)
    predictions = np.asarray(
        [_feature_vector(y, week, day, cutoff, int(t)) @ beta for t in targets]
    )
    return np.maximum(0.0, predictions)


def _construct_windows(df: pd.DataFrame) -> list[ForecastWindow]:
    y = df[TARGET].to_numpy(float)
    week = df[WEEK].to_numpy(int)
    day = df[DAY].to_numpy(int)
    windows: list[ForecastWindow] = []
    for window_id, start in enumerate(range(22, 53), start=1):
        targets = np.arange(start, start + HORIZON)
        old_cutoff = start - 3
        new_cutoff = start - 2
        windows.append(
            ForecastWindow(
                window_id=window_id,
                start=start,
                old_cutoff=old_cutoff,
                new_cutoff=new_cutoff,
                old=_forecast_window(y, week, day, old_cutoff, targets),
                new=_forecast_window(y, week, day, new_cutoff, targets),
                actual=y[targets].copy(),
            )
        )
    return windows


def _instance(forecast: np.ndarray, setup_cost: float, holding_cost: float, weights: np.ndarray) -> WWInstance:
    q = -holding_cost * np.arange(HORIZON, dtype=float)
    return WWInstance.create(
        K=np.full(HORIZON, setup_cost, dtype=float),
        q=q,
        demand=forecast,
        floor=np.zeros(HORIZON),
        weights=weights,
    )


def _fixed_fence_k(path: tuple[int, ...], periods: int) -> int:
    for k, endpoint in enumerate(path[1:], start=1):
        if endpoint >= periods:
            return k
    return len(path) - 1


def _retained_after_revision(
    instance: WWInstance,
    nominal: tuple[int, ...],
    k: int,
    revised: np.ndarray,
) -> bool | None:
    if k == 0:
        return None
    prefix = nominal[: k + 1]
    inside_value, _ = constrained_inside_path(instance, revised, prefix)
    outside_value, _ = outside_shortest_path(instance, revised, nominal, k)
    tolerance = 1e-8 * (1.0 + abs(inside_value))
    return bool(outside_value > inside_value + tolerance)


def _certified_commitment(
    instance: WWInstance,
    nominal: tuple[int, ...],
    threshold: float,
    *,
    escalate: bool,
) -> tuple[int, int, int, list[dict[str, object]]]:
    """Return k, unresolved count, exact escalations and per-k audit rows."""
    common_arcs = len(common_optimal_prefix(instance)) - 1
    committed = 0
    unresolved = 0
    escalations = 0
    audit: list[dict[str, object]] = []
    for k in range(1, common_arcs + 1):
        bracket = polynomial_radius_bracket(instance, nominal, k)
        decision = "unresolved"
        exact_radius: float | None = bracket.exact_radius
        safe = False
        if threshold < bracket.safe_lower_radius:
            safe = True
            decision = "safe_by_polynomial_lower"
        elif isfinite(bracket.upper_radius) and threshold >= bracket.upper_radius:
            safe = False
            decision = "unsafe_by_polynomial_witness"
        elif bracket.exact_certified and bracket.exact_radius is not None:
            safe = threshold < bracket.exact_radius
            decision = "safe_by_polynomial_closure" if safe else "unsafe_by_polynomial_closure"
        elif escalate:
            escalations += 1
            exact = exact_radius_enumeration(instance, nominal, k, time_limit=10.0)
            if exact.status == "optimal":
                exact_radius = exact.radius
                safe = threshold < exact.radius
                decision = "safe_by_exact_escalation" if safe else "unsafe_by_exact_escalation"
            else:
                unresolved += 1
                decision = f"unresolved_{exact.status}"
                safe = False
        else:
            unresolved += 1
            safe = False
        audit.append(
            {
                "k": k,
                "lower": bracket.safe_lower_radius,
                "upper": bracket.upper_radius,
                "exact_radius": exact_radius,
                "decision": decision,
            }
        )
        if safe:
            committed = k
        else:
            # Exact radii are non-increasing with k; the safe set is a prefix.
            break
    return committed, unresolved, escalations, audit


def _policy_row(
    *,
    window: ForecastWindow,
    split: str,
    setup_cost: float,
    holding_cost: float,
    weights: np.ndarray,
    threshold: float,
    policy: str,
    selected_path: tuple[int, ...] | None,
    k: int,
    base_instance: WWInstance,
    nominal_old: tuple[int, ...],
    exact_escalations: int = 0,
    unresolved: int = 0,
    certificate_trace: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    if k == 0 or selected_path is None:
        periods = 0
        arcs = 0
        regret = 0.0
        retained = None
    else:
        prefix = selected_path[: k + 1]
        periods = int(prefix[-1])
        arcs = k
        regret = float(bellman_residual(base_instance, window.actual, prefix))
        if selected_path == nominal_old:
            retained = _retained_after_revision(base_instance, nominal_old, k, window.new)
        else:
            retained = True  # the policy is formed after seeing the new vintage
    return {
        "window_id": window.window_id,
        "split": split,
        "start_row_zero_based": window.start,
        "setup_cost": setup_cost,
        "holding_cost_per_order_day": holding_cost,
        "policy": policy,
        "committed_arcs": arcs,
        "committed_periods": periods,
        "new_revision_retains_commitment": retained,
        "actual_structural_regret_gbp": regret,
        "exact_escalations": exact_escalations,
        "unresolved_boundaries": unresolved,
        "certificate_trace": certificate_trace,
        "conformal_threshold": threshold,
    }


def main() -> None:
    df = pd.read_csv(DATA_PATH, sep=";")
    if df.shape != (60, 13):
        raise RuntimeError(f"unexpected data shape {df.shape}")
    windows = _construct_windows(df)
    revisions = np.vstack([window.new - window.old for window in windows])

    # Frozen design: eight windows estimate coordinate scale; eleven calibrate;
    # twelve evaluate.  The calibration threshold is reused in evaluation, so
    # only the first evaluation window has the literal one-step interpretation.
    n_weight, n_calibration = 8, 11
    # The scale sample is small (eight windows).  Pooling coordinates avoids
    # fitting eight unstable horizon-specific scales and keeps the norm
    # directionally transparent.  The common factor changes units, not the
    # ordering of unweighted L-infinity revisions.
    pooled_scale = float(np.quantile(np.abs(revisions[:n_weight]).ravel(), 0.90))
    weights = np.full(HORIZON, 1.0 / max(pooled_scale, 1.0))
    scores = np.asarray([weighted_revision_score(r, weights) for r in revisions])
    calibration_slice = slice(n_weight, n_weight + n_calibration)
    conformal = split_conformal_threshold(scores[calibration_slice], alpha=0.20)
    threshold = conformal.threshold

    vintage_rows: list[dict[str, object]] = []
    for window, revision, score in zip(windows, revisions, scores):
        split = (
            "weight_estimation"
            if window.window_id <= n_weight
            else "calibration"
            if window.window_id <= n_weight + n_calibration
            else "evaluation"
        )
        for t in range(HORIZON):
            vintage_rows.append(
                {
                    "window_id": window.window_id,
                    "split": split,
                    "start_row_zero_based": window.start,
                    "old_cutoff_zero_based": window.old_cutoff,
                    "new_cutoff_zero_based": window.new_cutoff,
                    "horizon_coordinate": t + 1,
                    "old_forecast": window.old[t],
                    "new_forecast": window.new[t],
                    "actual_demand": window.actual[t],
                    "revision": revision[t],
                    "weight": weights[t],
                    "weighted_revision_score": score,
                }
            )
    write_csv(pd.DataFrame(vintage_rows), ROOT / "results/raw/uci_forecast_vintages.csv")

    cost_grid = [(K, h) for K in (60.0, 120.0, 240.0) for h in (0.06, 0.12, 0.24)]
    policy_rows: list[dict[str, object]] = []
    trace_rows: list[dict[str, object]] = []
    evaluation_windows = windows[n_weight + n_calibration :]
    for setup_cost, holding_cost in cost_grid:
        for window in evaluation_windows:
            instance = _instance(window.old, setup_cost, holding_cost, weights)
            _, nominal_old = shortest_path(instance)
            optimal_count = count_optimal_paths(instance, cap=1_000_000)
            common_arcs = len(common_optimal_prefix(instance)) - 1
            _, nominal_new = shortest_path(instance, window.new)

            k_lower, unresolved_lower, escalations_lower, trace_lower = _certified_commitment(
                instance, nominal_old, threshold, escalate=False
            )
            k_exact, unresolved_exact, escalations_exact, trace_exact = _certified_commitment(
                instance, nominal_old, threshold, escalate=True
            )
            for trace_kind, trace in (("lower_only", trace_lower), ("escalated", trace_exact)):
                for item in trace:
                    trace_rows.append(
                        {
                            "window_id": window.window_id,
                            "setup_cost": setup_cost,
                            "holding_cost_per_order_day": holding_cost,
                            "trace_kind": trace_kind,
                            "nominal_optimal_paths_capped": optimal_count,
                            "common_optimal_arcs": common_arcs,
                            **item,
                        }
                    )

            policy_rows.append(
                _policy_row(
                    window=window,
                    split="evaluation",
                    setup_cost=setup_cost,
                    holding_cost=holding_cost,
                    weights=weights,
                    threshold=threshold,
                    policy="unrestricted_actual_benchmark",
                    selected_path=None,
                    k=0,
                    base_instance=instance,
                    nominal_old=nominal_old,
                )
            )
            policy_rows.append(
                _policy_row(
                    window=window,
                    split="evaluation",
                    setup_cost=setup_cost,
                    holding_cost=holding_cost,
                    weights=weights,
                    threshold=threshold,
                    policy="certified_lower_only",
                    selected_path=nominal_old,
                    k=k_lower,
                    base_instance=instance,
                    nominal_old=nominal_old,
                    exact_escalations=escalations_lower,
                    unresolved=unresolved_lower,
                    certificate_trace=trace_lower,
                )
            )
            policy_rows.append(
                _policy_row(
                    window=window,
                    split="evaluation",
                    setup_cost=setup_cost,
                    holding_cost=holding_cost,
                    weights=weights,
                    threshold=threshold,
                    policy="certified_with_exact_escalation",
                    selected_path=nominal_old,
                    k=k_exact,
                    base_instance=instance,
                    nominal_old=nominal_old,
                    exact_escalations=escalations_exact,
                    unresolved=unresolved_exact,
                    certificate_trace=trace_exact,
                )
            )
            policy_rows.append(
                _policy_row(
                    window=window,
                    split="evaluation",
                    setup_cost=setup_cost,
                    holding_cost=holding_cost,
                    weights=weights,
                    threshold=threshold,
                    policy="old_plan_one_cycle",
                    selected_path=nominal_old,
                    k=1,
                    base_instance=instance,
                    nominal_old=nominal_old,
                )
            )
            policy_rows.append(
                _policy_row(
                    window=window,
                    split="evaluation",
                    setup_cost=setup_cost,
                    holding_cost=holding_cost,
                    weights=weights,
                    threshold=threshold,
                    policy="updated_plan_one_cycle",
                    selected_path=nominal_new,
                    k=1,
                    base_instance=instance,
                    nominal_old=nominal_old,
                )
            )
            for fence in (2, 3, 4):
                policy_rows.append(
                    _policy_row(
                        window=window,
                        split="evaluation",
                        setup_cost=setup_cost,
                        holding_cost=holding_cost,
                        weights=weights,
                        threshold=threshold,
                        policy=f"fixed_{fence}_period_fence",
                        selected_path=nominal_old,
                        k=_fixed_fence_k(nominal_old, fence),
                        base_instance=instance,
                        nominal_old=nominal_old,
                    )
                )

    policy_df = pd.DataFrame(policy_rows)
    # Nested JSON traces are written in a separate audit file; keep CSV scalar.
    scalar_policy_df = policy_df.drop(columns=["certificate_trace"])
    write_csv(scalar_policy_df, ROOT / "results/raw/uci_policy_evaluation.csv")
    write_csv(pd.DataFrame(trace_rows), ROOT / "results/raw/uci_certificate_trace.csv")

    evaluation_scores = scores[n_weight + n_calibration :]
    primary = scalar_policy_df[
        (scalar_policy_df["setup_cost"] == 120.0)
        & (scalar_policy_df["holding_cost_per_order_day"] == 0.12)
    ]
    policy_summary = (
        primary.groupby("policy", sort=True)
        .agg(
            windows=("window_id", "count"),
            mean_committed_periods=("committed_periods", "mean"),
            median_committed_periods=("committed_periods", "median"),
            mean_committed_arcs=("committed_arcs", "mean"),
            total_actual_structural_regret_gbp=("actual_structural_regret_gbp", "sum"),
            mean_actual_structural_regret_gbp=("actual_structural_regret_gbp", "mean"),
            median_actual_structural_regret_gbp=("actual_structural_regret_gbp", "median"),
            max_actual_structural_regret_gbp=("actual_structural_regret_gbp", "max"),
            exact_escalations=("exact_escalations", "sum"),
            unresolved_boundaries=("unresolved_boundaries", "sum"),
        )
        .reset_index()
    )
    retention_source = primary.dropna(subset=["new_revision_retains_commitment"]).copy()
    # Pandas may preserve object/bool dtype when a group has one row.  Cast to
    # integer before aggregation so machine-readable counts are always numbers.
    retention_source["new_revision_retains_commitment"] = (
        retention_source["new_revision_retains_commitment"].astype(bool).astype(int)
    )
    retention = (
        retention_source.groupby("policy")["new_revision_retains_commitment"]
        .agg(["count", "sum", "mean"])
        .reset_index()
        .rename(
            columns={
                "count": "nonzero_commitment_windows",
                "sum": "retained_windows",
                "mean": "retention_fraction",
            }
        )
    )
    retention["nonzero_commitment_windows"] = retention["nonzero_commitment_windows"].astype(int)
    retention["retained_windows"] = retention["retained_windows"].astype(int)
    policy_summary = policy_summary.merge(retention, on="policy", how="left")
    write_csv(policy_summary, ROOT / "results/processed/uci_primary_policy_summary.csv")

    sensitivity = (
        scalar_policy_df.groupby(["setup_cost", "holding_cost_per_order_day", "policy"], sort=True)
        .agg(
            windows=("window_id", "count"),
            mean_committed_periods=("committed_periods", "mean"),
            total_actual_structural_regret_gbp=("actual_structural_regret_gbp", "sum"),
            mean_actual_structural_regret_gbp=("actual_structural_regret_gbp", "mean"),
            exact_escalations=("exact_escalations", "sum"),
            unresolved_boundaries=("unresolved_boundaries", "sum"),
        )
        .reset_index()
    )
    write_csv(sensitivity, ROOT / "results/processed/uci_sensitivity_summary.csv")

    summary = {
        "environment": environment_record(),
        "data": {
            "path": str(DATA_PATH.relative_to(ROOT)),
            "sha256": sha256(DATA_PATH),
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "missing_cells": int(df.isna().sum().sum()),
            "target_min": float(df[TARGET].min()),
            "target_mean": float(df[TARGET].mean()),
            "target_max": float(df[TARGET].max()),
            "status": (
                "real observed demand; version 2.1.2 re-fetched the official UCI archive "
                "and its sole CSV was byte-identical; forecasts and costs are reconstructed"
            ),
        },
        "forecast_design": {
            "horizon": HORIZON,
            "windows": len(windows),
            "window_start_rows_zero_based": [22, 52],
            "old_vintage_lag_to_first_target": 3,
            "new_vintage_lag_to_first_target": 2,
            "model": "causal pooled direct ridge using target lags and target calendar only",
            "ridge_penalty": RIDGE,
            "weight_estimation_windows": n_weight,
            "calibration_windows": n_calibration,
            "evaluation_windows": len(evaluation_windows),
        },
        "calibration": {
            "alpha": conformal.alpha,
            "rank": conformal.rank,
            "threshold": conformal.threshold,
            "weights": weights.tolist(),
            "pooled_90th_percentile_revision_scale": pooled_scale,
            "weight_design": "equal coordinate weights scaled by a pooled 90th percentile from the eight frozen scale windows",
            "calibration_scores": scores[calibration_slice].tolist(),
            "evaluation_scores": evaluation_scores.tolist(),
            "evaluation_covered": int(np.sum(evaluation_scores <= threshold)),
            "evaluation_total": int(evaluation_scores.size),
            "evaluation_coverage": float(np.mean(evaluation_scores <= threshold)),
            "interpretation": (
                "one-step marginal under exchangeability; repeated retrospective use over the "
                "12 evaluation windows has no simultaneous guarantee"
            ),
        },
        "cost_design": {
            "setup_costs_gbp": [60.0, 120.0, 240.0],
            "holding_costs_gbp_per_order_day": [0.06, 0.12, 0.24],
            "primary": {"setup_cost_gbp": 120.0, "holding_cost_gbp_per_order_day": 0.12},
            "status": "stylised, not estimated from the source organisation",
        },
        "primary_policy_summary": policy_summary.to_dict("records"),
        "sensitivity_rows": int(len(sensitivity)),
        "decision_scope": (
            "structural setup epochs/cycle boundaries with uncapacitated quantity recourse; "
            "the unrestricted-actual row is a zero-regret theoretical benchmark"
        ),
    }
    write_json(summary, ROOT / "results/processed/uci_case_summary.json")
    print(summary)


if __name__ == "__main__":
    main()
