#!/usr/bin/env python3
"""Create publication figures from frozen raw results.

Each figure is a separate plot.  The palette uses aubergine, petrol, saffron,
coral and slate to remain legible without relying on standard red/blue pairs.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import ROOT

OUT = ROOT / "paper/figures"
OUT.mkdir(parents=True, exist_ok=True)

AUBERGINE = "#5B2A86"
PETROL = "#087E8B"
SAFFRON = "#D89B00"
CORAL = "#C8553D"
SLATE = "#44546A"
PALE = "#D8D2E1"

plt.rcParams.update(
    {
        "font.size": 9.5,
        "axes.titlesize": 10.5,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.2,
        "figure.dpi": 160,
        "savefig.dpi": 320,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def save(fig: plt.Figure, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", bbox_inches="tight")
    plt.close(fig)


def certificate_brackets() -> None:
    df = pd.read_csv(ROOT / "results/raw/certificate_audit.csv")
    keep = df[
        df["is_partial_prefix"].astype(bool)
        & np.isfinite(df["lp_radius"])
        & np.isfinite(df["exact_radius"])
        & (df["exact_radius"] > 0)
    ].copy()
    keep["conditioned"] = keep["conditioned_strict_gap"].astype(bool)
    fig, ax = plt.subplots(figsize=(5.6, 4.35))
    for conditioned, label, colour, marker in (
        (False, "broad synthetic stratum", PETROL, "o"),
        (True, "conditioned strict-gap stratum", CORAL, "^"),
    ):
        sub = keep[keep["conditioned"] == conditioned]
        ax.scatter(
            sub["exact_radius"],
            sub["lp_radius"],
            s=24 if conditioned else 18,
            alpha=0.70 if conditioned else 0.52,
            label=f"{label} (n={len(sub)})",
            marker=marker,
            color=colour,
            linewidths=0,
        )
    positive = np.concatenate([keep["exact_radius"].to_numpy(), keep["lp_radius"].to_numpy()])
    lo = max(np.min(positive[positive > 0]) * 0.8, 1e-4)
    hi = np.max(positive) * 1.2
    ax.plot([lo, hi], [lo, hi], linestyle="--", linewidth=1.1, color=SLATE, label="exact equality")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("Exact strong prefix radius")
    ax.set_ylabel("Frozen-comparator lower radius")
    ax.set_title("Polynomial lower certificates remain below the exact radius")
    ax.grid(True, which="major", linewidth=0.35, alpha=0.35)
    ax.legend(frameon=False, loc="lower right")
    save(fig, "certificate_brackets")


def exact_scaling() -> None:
    df = pd.read_csv(ROOT / "results/raw/exact_benchmark.csv")
    summary = (
        df.groupby("T")
        .agg(
            candidate_median=("candidate_generation_seconds", "median"),
            candidate_q25=("candidate_generation_seconds", lambda x: x.quantile(0.25)),
            candidate_q75=("candidate_generation_seconds", lambda x: x.quantile(0.75)),
            disjunct_median=("disjunct_solve_seconds", "median"),
            disjunct_q25=("disjunct_solve_seconds", lambda x: x.quantile(0.25)),
            disjunct_q75=("disjunct_solve_seconds", lambda x: x.quantile(0.75)),
        )
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(5.6, 4.1))
    x = summary["T"].to_numpy()
    ax.plot(x, summary["candidate_median"], marker="o", linewidth=1.7, color=AUBERGINE, label="generate and sort path lower bounds")
    ax.fill_between(x, summary["candidate_q25"], summary["candidate_q75"], color=AUBERGINE, alpha=0.16, linewidth=0)
    ax.plot(x, summary["disjunct_median"], marker="s", linewidth=1.7, color=SAFFRON, label="solve processed inverse disjuncts")
    ax.fill_between(x, summary["disjunct_q25"], summary["disjunct_q75"], color=SAFFRON, alpha=0.20, linewidth=0)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xlabel("Horizon length T")
    ax.set_ylabel("Wall time (seconds, log scale)")
    ax.set_title("Exact enumeration is dominated by candidate generation")
    ax.grid(True, axis="y", which="major", linewidth=0.35, alpha=0.4)
    ax.legend(frameon=False, loc="upper left")
    save(fig, "exact_scaling")


def calibration_coverage() -> None:
    df = pd.read_csv(ROOT / "results/raw/calibration_scenarios.csv")
    order = [
        "exchangeable_lognormal",
        "next_scale_1.25",
        "next_scale_1.50",
        "exchangeable_with_floor_admissibility",
        "five_decision_bonferroni_family",
    ]
    labels = [
        "exchangeable",
        "scale ×1.25\n(no guarantee)",
        "scale ×1.50\n(no guarantee)",
        "exchangeable + floors",
        "five-decision\nBonferroni",
    ]
    df = df.set_index("scenario").loc[order].reset_index()
    x = np.arange(len(df))
    y = df["coverage"].to_numpy()
    low = y - df["wilson_95_low"].to_numpy()
    high = df["wilson_95_high"].to_numpy() - y
    colours = [PETROL, CORAL, CORAL, AUBERGINE, SAFFRON]
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for i in range(len(df)):
        ax.errorbar(
            x[i], y[i], yerr=np.asarray([[low[i]], [high[i]]]),
            fmt="o", markersize=6, capsize=3, linewidth=1.2, color=colours[i]
        )
    ax.axhline(0.9, linestyle="--", linewidth=1.1, color=SLATE, label="nominal lower bound 0.90")
    ax.set_xticks(x, labels)
    ax.set_ylim(0.74, 0.95)
    ax.set_ylabel("Empirical coverage (95% Wilson interval)")
    ax.set_title("The ordinary conformal guarantee fails under scale shift")
    ax.grid(True, axis="y", linewidth=0.35, alpha=0.4)
    ax.legend(frameon=False, loc="lower left")
    save(fig, "calibration_coverage")


def rolling_bounds() -> None:
    df = pd.read_csv(ROOT / "results/raw/rolling_audit.csv")
    df = df[df["bellman_residual"] > 1e-10].copy()
    fig, ax = plt.subplots(figsize=(5.6, 4.35))
    ax.scatter(df["bellman_residual"], df["generic_bound"], s=22, alpha=0.42, color=SLATE, label="generic Lipschitz bound")
    ax.scatter(df["bellman_residual"], df["dead_zone_bound"], s=24, alpha=0.70, color=PETROL, label="radius dead-zone bound")
    values = np.concatenate([
        df["bellman_residual"].to_numpy(),
        df["generic_bound"].to_numpy(),
        df["dead_zone_bound"].to_numpy(),
    ])
    lo = max(values[values > 0].min() * 0.7, 1e-6)
    hi = values.max() * 1.25
    ax.plot([lo, hi], [lo, hi], linestyle="--", linewidth=1.0, color=CORAL, label="bound = realised regret")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("Realised structural regret")
    ax.set_ylabel("Deterministic upper bound")
    ax.set_title("The certified dead zone tightens the rolling bound")
    ax.grid(True, which="major", linewidth=0.35, alpha=0.35)
    ax.legend(frameon=False, loc="upper left")
    save(fig, "rolling_bounds")


def uci_policy_frontier() -> None:
    df = pd.read_csv(ROOT / "results/processed/uci_primary_policy_summary.csv")
    # In the primary scenario the old-plan one-cycle policy and the fixed
    # two-period fence coincide exactly; show them as one plotted point.
    df = df[~df["policy"].isin(["unrestricted_actual_benchmark", "old_plan_one_cycle"])].copy()
    names = {
        "certified_lower_only": "certified lower",
        "certified_with_exact_escalation": "certified + exact",
        "fixed_2_period_fence": "old cycle = fixed 2-period",
        "fixed_3_period_fence": "fixed 3-period",
        "fixed_4_period_fence": "fixed 4-period",
        "updated_plan_one_cycle": "updated-plan cycle",
    }
    colours = {
        "certified_lower_only": PETROL,
        "certified_with_exact_escalation": AUBERGINE,
        "fixed_2_period_fence": SAFFRON,
        "fixed_3_period_fence": CORAL,
        "fixed_4_period_fence": CORAL,
        "updated_plan_one_cycle": SLATE,
    }
    markers = {
        "certified_lower_only": "o",
        "certified_with_exact_escalation": "D",
        "fixed_2_period_fence": "s",
        "fixed_3_period_fence": "^",
        "fixed_4_period_fence": "v",
        "updated_plan_one_cycle": "P",
    }
    fig, ax = plt.subplots(figsize=(6.1, 4.3))
    for _, row in df.iterrows():
        ax.scatter(
            row["mean_committed_periods"],
            row["total_actual_structural_regret_gbp"],
            s=68,
            marker=markers[row["policy"]],
            color=colours[row["policy"]],
            label=names[row["policy"]],
            zorder=3,
        )
    ax.set_xlabel("Mean committed periods per eight-period window")
    ax.set_ylabel("Total realised structural regret (£; 12 windows)")
    ax.set_title("Illustrative real-demand case: commitment–regret frontier")
    ax.grid(True, linewidth=0.35, alpha=0.35)
    ax.legend(frameon=False, loc="upper left", ncol=1)
    save(fig, "uci_policy_frontier")


def main() -> None:
    certificate_brackets()
    exact_scaling()
    calibration_coverage()
    rolling_bounds()
    uci_policy_frontier()
    print(sorted(path.name for path in OUT.iterdir()))


if __name__ == "__main__":
    main()
