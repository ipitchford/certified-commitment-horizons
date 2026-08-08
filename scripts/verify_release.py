#!/usr/bin/env python3
"""Deterministically verify the frozen v2.1.2 candidate artefacts.

This checker recomputes key counts and numerical comparisons from raw rows. It
is a producer-side integrity check, not independent replication or formal proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from verify_hashes import SKIP_DIRS

ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "2.1.2"
RELEASE_DATE = "2026-08-08"
WHEEL_NAME = f"wwprefix-{RELEASE_VERSION}-py3-none-any.whl"


class VerificationFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationFailure(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run(command: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src if not env.get("PYTHONPATH") else src + os.pathsep + env["PYTHONPATH"]
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, env=env)


def check_required() -> dict[str, Any]:
    required = [
        "paper/main.pdf",
        "paper/main.tex",
        "paper/references.bib",
        "README.md",
        "LICENSE",
        "LICENSES.md",
        "THIRD_PARTY_NOTICES.md",
        "AI_INDEX.md",
        "CITATION.cff",
        "requirements-lock.txt",
        "examples/strict_gap_instance.json",
        "examples/sample_decision.json",
        "docs/peer_review_v1.0.0.md",
        "docs/response_to_reviewers.md",
        "docs/response_to_reviewers_v2.1.0.md",
        "docs/PRACTITIONER_GUIDE.md",
        "docs/literature_audit.md",
        "docs/reference_verification_v2.1.2.md",
        "docs/pdf_visual_review_v2.1.2.md",
        "docs/re_review_v2.1.2.md",
        "docs/final_integrity_v2.1.2.md",
        "docs/reproducibility.md",
        "docs/data_provenance.md",
        "docs/scope_and_limitations.md",
        "docs/response_to_final_review_v2.1.2.md",
        "docs/final_review_v2.1.1_for_evidence_press.md",
        "release/claims.json",
        "release/provenance.json",
        "scripts/verify_hashes.py",
        "scripts/check_certificate.py",
        "scripts/check_python_syntax.py",
        f"release/{WHEEL_NAME}",
    ]
    missing = [path for path in required if not (ROOT / path).is_file()]
    require(not missing, f"missing required files: {missing}")
    partial = sorted((ROOT / "results/raw").glob("*.partial.csv"))
    require(not partial, f"partial result files remain: {[p.name for p in partial]}")
    return {"required_files": len(required), "missing": missing, "partial_files": []}


def check_json() -> dict[str, Any]:
    paths = sorted(ROOT.glob("results/processed/*.json")) + sorted(ROOT.glob("release/*.json"))
    paths += sorted(ROOT.glob("examples/*.json"))
    for path in paths:
        json.loads(path.read_text(encoding="utf-8"))
    return {"json_files_parsed": len(paths)}


def check_certificate() -> dict[str, Any]:
    cert = pd.read_csv(ROOT / "results/raw/certificate_audit.csv")
    graph = pd.read_csv(ROOT / "results/raw/graph_bijection_audit.csv")
    fixed = pd.read_csv(ROOT / "results/raw/fixed_competitor_audit.csv")
    require(len(cert) == 512, f"certificate rows {len(cert)} != 512")
    require(cert["instance_id"].nunique() == 258, "certificate instance count != 258")
    max_error = float(cert["absolute_error"].fillna(0).abs().max())
    require(max_error <= 1e-9, f"certificate max error {max_error}")
    require(bool(cert["exact_contained"].fillna(False).all()), "an exact radius lies outside its bracket")
    finite_monotone = cert["monotone_from_previous"].dropna()
    require(bool(finite_monotone.astype(bool).all()), "prefix monotonicity failure")
    full = cert[cert["is_full_path"].astype(bool)]
    full_error = float((full["lp_radius"] - full["exact_radius"]).abs().max())
    require(full_error <= 2e-9, f"full-path endpoint error {full_error}")

    require(len(graph) == 62, f"graph rows {len(graph)} != 62")
    require(bool(graph["acyclic"].astype(bool).all()), "a prefix-deviation graph is cyclic")
    require(bool((graph["expanded_paths"] == graph["outside_paths"]).all()), "graph path bijection failure")

    require(len(fixed) == 96, f"fixed competitor rows {len(fixed)} != 96")
    finite_fixed = fixed[fixed["compact_status"] == "optimal"]
    infeasible_fixed = fixed[fixed["compact_status"] == "infeasible"]
    require(len(finite_fixed) == 72 and len(infeasible_fixed) == 24, "unexpected fixed-competitor status counts")
    require(bool(finite_fixed["explicit_success"].astype(bool).all()), "a finite explicit comparator LP failed")
    require(bool((~infeasible_fixed["explicit_success"].astype(bool)).all()), "an infeasible compact LP was feasible explicitly")
    fixed_error = float(finite_fixed["absolute_error"].abs().max())
    require(fixed_error <= 1e-9, f"fixed-competitor LP error {fixed_error}")

    positive_partial = cert[
        cert["is_partial_prefix"].astype(bool)
        & np.isfinite(cert["exact_radius"])
        & (cert["exact_radius"] > 1e-10)
    ]
    closed = int(positive_partial["bracket_exact_certified"].astype(bool).sum())
    require(len(positive_partial) == 254, f"positive partial count {len(positive_partial)} != 254")
    require(closed == 153, f"polynomial exact closures {closed} != 153")
    return {
        "certificate_rows": len(cert),
        "instances": int(cert["instance_id"].nunique()),
        "max_certificate_error": max_error,
        "graph_cases": len(graph),
        "fixed_competitor_cases": len(fixed),
        "max_fixed_competitor_error": fixed_error,
        "full_path_max_error": full_error,
        "positive_partial_cases": len(positive_partial),
        "polynomial_exact_closures": closed,
    }


def check_exact() -> dict[str, Any]:
    exact = pd.read_csv(ROOT / "results/raw/exact_benchmark.csv")
    milp = pd.read_csv(ROOT / "results/raw/milp_benchmark.csv")
    require(len(exact) == 30, f"exact rows {len(exact)} != 30")
    require(set(exact["exact_status"]) == {"optimal"}, f"unexpected exact statuses {set(exact['exact_status'])}")
    require(int(exact["solver_failures"].sum()) == 0, "exact benchmark solver failures")
    require(bool((exact["exact_radius_upper_bound"] >= exact["exact_radius_lower_bound"] - 1e-8).all()), "negative exact brackets")

    require(len(milp) == 24, f"MILP rows {len(milp)} != 24")
    resolved = milp[milp["decision"].notna()]
    unresolved = milp[milp["decision"].isna()]
    require(len(resolved) == 22, f"resolved MILP rows {len(resolved)} != 22")
    require(len(unresolved) == 2, f"unresolved MILP rows {len(unresolved)} != 2")
    require(bool(resolved["decision_matches_when_resolved"].astype(bool).all()), "resolved MILP decision mismatch")
    return {
        "exact_instances": len(exact),
        "exact_statuses": exact["exact_status"].value_counts().to_dict(),
        "milp_probes": len(milp),
        "milp_resolved": len(resolved),
        "milp_unresolved": len(unresolved),
        "T18_median_paths": float(exact.loc[exact["T"] == 18, "paths_total"].median()),
        "T18_median_candidate_seconds": float(exact.loc[exact["T"] == 18, "candidate_generation_seconds"].median()),
    }


def check_calibration() -> dict[str, Any]:
    scenarios = pd.read_csv(ROOT / "results/raw/calibration_scenarios.csv")
    trials = pd.read_csv(ROOT / "results/raw/calibration_trials.csv")
    require(len(scenarios) == 5, "calibration scenario count != 5")
    require(len(trials) == 85000, f"calibration trial rows {len(trials)} != 85000")
    for row in scenarios.itertuples(index=False):
        require(int(row.covered) == int(round(row.coverage * row.trials)), f"coverage count mismatch: {row.scenario}")
    exch = scenarios.set_index("scenario").loc["exchangeable_lognormal"]
    require(exch.wilson_95_low <= 0.9 <= exch.wilson_95_high, "exchangeable target outside Wilson interval")
    require(
        scenarios.set_index("scenario").loc["next_scale_1.50", "coverage"]
        < scenarios.set_index("scenario").loc["exchangeable_lognormal", "coverage"],
        "scale-shift negative control did not reduce coverage",
    )
    family = scenarios.set_index("scenario").loc["five_decision_bonferroni_family"]
    require(family.wilson_95_low <= 0.9 <= family.wilson_95_high, "Bonferroni family target outside interval")
    return {
        "scenario_rows": len(scenarios),
        "trial_rows": len(trials),
        "exchangeable_coverage": float(exch.coverage),
        "scale_1_5_coverage": float(scenarios.set_index("scenario").loc["next_scale_1.50", "coverage"]),
        "bonferroni_family_coverage": float(family.coverage),
    }


def check_rolling() -> dict[str, Any]:
    df = pd.read_csv(ROOT / "results/raw/rolling_audit.csv")
    require(len(df) == 462, f"rolling rows {len(df)} != 462")
    require(bool(df["theorem_holds"].astype(bool).all()), "rolling theorem violation")
    require(bool(df["dead_le_generic"].astype(bool).all()), "dead-zone bound exceeds generic bound")
    inside = df[df["inside_dead_zone"].astype(bool)]
    require(len(inside) == 254, f"inside dead-zone count {len(inside)} != 254")
    require(bool(inside["zero_residual_inside_dead_zone"].astype(bool).all()), "nonzero residual inside dead zone")
    return {
        "cases": len(df),
        "inside_dead_zone": len(inside),
        "positive_residual_cases": int((df["bellman_residual"] > 1e-10).sum()),
        "max_residual_minus_bound": float((df["bellman_residual"] - df["dead_zone_bound"]).max()),
    }


def check_uci() -> dict[str, Any]:
    path = ROOT / "data/external/Daily_Demand_Forecasting_Orders.csv"
    df = pd.read_csv(path, sep=";")
    # The source file has a trailing empty column under some parsers; the frozen
    # analysis script normalises it. Use the processed summary as the schema receipt.
    summary = json.loads((ROOT / "results/processed/uci_case_summary.json").read_text())
    require(summary["data"]["rows"] == 60, "UCI row count != 60")
    require(summary["data"]["columns"] == 13, "UCI column count != 13")
    require(summary["data"]["missing_cells"] == 0, "UCI missing cells != 0")
    expected = "adf8dda021beae76b13b1cbb5b3c075d064f03b3353a711c1ddc357c6f89e924"
    actual = sha256(path)
    require(actual == expected, f"UCI SHA-256 mismatch: {actual}")
    vintages = pd.read_csv(ROOT / "results/raw/uci_forecast_vintages.csv")
    trace = pd.read_csv(ROOT / "results/raw/uci_certificate_trace.csv")
    policies = pd.read_csv(ROOT / "results/raw/uci_policy_evaluation.csv")
    require(len(vintages) == 248, "UCI vintage rows != 248")
    require(len(trace) == 371, "UCI certificate trace rows != 371")
    require(len(policies) == 864, "UCI policy rows != 864")
    return {
        "sha256": actual,
        "rows": 60,
        "columns": 13,
        "missing_cells": 0,
        "forecast_vintage_rows": len(vintages),
        "certificate_trace_rows": len(trace),
        "policy_rows": len(policies),
        "raw_parser_shape": list(df.shape),
    }


def check_exact_certification() -> dict[str, Any]:
    agreement = pd.read_csv(ROOT / "results/raw/exact_certification_audit.csv")
    adversarial = pd.read_csv(ROOT / "results/raw/exact_adversarial_audit.csv")
    scaling = pd.read_csv(ROOT / "results/raw/exact_scaling_study.csv")
    summary = json.loads(
        (ROOT / "results/processed/exact_certification_summary.json").read_text()
    )
    require(
        bool(agreement["brute_force_match"].astype(bool).all()),
        "an exact frozen certificate disagreed with complete enumeration",
    )
    require(
        int(agreement["float_false_finite"].sum()) == 0,
        "the float layer reported finite where the exact layer proved infinite",
    )
    binary_rows = adversarial[
        (adversarial["family"] == "reviewer_counterexample_binary")
        & (adversarial["proposal"] == 1.1)
    ]
    require(
        set(binary_rows["classification"]) == {"certified_destabilising_witness_exists"},
        "reviewer counterexample triage regression",
    )
    require(
        summary["adversarial"]["rescaling_flips"] == 0,
        "rescaling invariance violated",
    )
    widths = agreement["enumeration_interval_relative_width"].dropna()
    max_width = float(widths.max()) if len(widths) else 0.0
    require(max_width <= 1e-9, f"certified enumeration interval too wide: {max_width}")
    require(365 in set(scaling["T"]), "scaling study missing T=365")
    return {
        "agreement_rows": int(len(agreement)),
        "brute_force_matches": int(agreement["brute_force_match"].sum()),
        "float_false_infinite": int(agreement["float_false_infinite"].sum()),
        "adversarial_rows": int(len(adversarial)),
        "max_interval_relative_width": max_width,
        "scaling_horizons": sorted(int(v) for v in set(scaling["T"])),
    }


def check_example() -> dict[str, Any]:
    sample = json.loads((ROOT / "examples/sample_decision.json").read_text())
    bracket = sample["certified_bracket"]
    frozen = bracket["frozen_certificate"]
    escalation = sample["certified_exact_escalation"]
    require(frozen["radius"]["exact"] == "3/2", "strict example frozen radius != 3/2 exactly")
    require(
        escalation["exact_radius"]["exact"] == "2/1",
        "strict example certified exact radius != 2/1 exactly",
    )
    require(escalation["exact_certified"] is True, "strict example escalation not certified")
    require(sample["nominal"]["path"] == [1, 2, 4], "public nominal path mismatch")
    require(
        sample["nominal"]["verified_exactly_optimal"] is True,
        "nominal path not exactly verified",
    )
    require(
        sample["float_search"]["role"].startswith("diagnostic"),
        "float search block is not labelled diagnostic",
    )
    checker = run(
        [
            sys.executable,
            "scripts/check_certificate.py",
            "examples/sample_decision.json",
            "examples/strict_gap_instance.json",
        ]
    )
    require(
        checker.returncode == 0,
        f"producer-side checker failed: {checker.stdout}{checker.stderr}",
    )
    return {
        "frozen_radius_exact": frozen["radius"]["exact"],
        "exact_radius_exact": escalation["exact_radius"]["exact"],
        "producer_side_checker": "passed",
    }



def check_wheel() -> dict[str, Any]:
    wheel = ROOT / "release" / WHEEL_NAME
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        source_files = sorted((ROOT / "src/wwprefix").glob("*.py"))
        for source in source_files:
            member = f"wwprefix/{source.name}"
            require(member in names, f"wheel missing {member}")
            require(archive.read(member) == source.read_bytes(), f"wheel source differs: {member}")
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        require(len(metadata_names) == 1, "wheel metadata member count is not one")
        metadata = archive.read(metadata_names[0]).decode("utf-8", errors="replace")
        require(
            f"Version: {RELEASE_VERSION}\n" in metadata,
            f"wheel version is not {RELEASE_VERSION}",
        )
    return {
        "sha256": sha256(wheel),
        "package_source_files": len(source_files),
        "source_bytes_match": True,
        "version": RELEASE_VERSION,
    }


def check_release_contract() -> dict[str, Any]:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    tex = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    claims = json.loads((ROOT / "release/claims.json").read_text(encoding="utf-8"))
    provenance = json.loads((ROOT / "release/provenance.json").read_text(encoding="utf-8"))
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    requirements = (ROOT / "requirements-lock.txt").read_text(encoding="utf-8").splitlines()

    require(f"**Release:** {RELEASE_VERSION}" in readme, "README release version drift")
    require(f"Preprint v{RELEASE_VERSION}" in tex, "paper running-header version drift")
    require(f"Preprint version {RELEASE_VERSION}" in tex, "paper title-page version drift")
    require(f"version: {RELEASE_VERSION}" in cff, "CITATION.cff version drift")
    require(claims.get("release") == RELEASE_VERSION, "claims release version drift")
    require(provenance.get("release") == RELEASE_VERSION, "provenance release version drift")
    for requirement in requirements:
        if requirement and not requirement.startswith("pytest=="):
            require(f'"{requirement}"' in pyproject, f"pyproject drift for {requirement}")
    require(provenance.get("status") == "unrefereed-candidate", "candidate status missing")
    require(
        provenance.get("assurance", {}).get("exact_rational_computational_certification") is True,
        "exact-rational computational assurance flag missing",
    )
    require(
        provenance.get("assurance", {}).get("independent_clean_room_reproduction") is False,
        "independent reproduction must remain false",
    )
    forbidden = [
        "two rounds of adversarial peer review",
        "an independently written checker",
        "Numerical lower radii subtract a disclosed safety margin",
    ]
    combined = readme + "\n" + tex
    require(not [term for term in forbidden if term in combined], "stale assurance wording remains")

    literature_files = [path for path in (ROOT / "literature").rglob("*") if path.is_file()]
    require(
        all(path.name == "README.md" for path in literature_files),
        "third-party literature full text remains in the public tree",
    )
    public_bytecode = [
        path
        for path in ROOT.rglob("*.pyc")
        if not any(part in SKIP_DIRS or part.endswith(".egg-info") for part in path.relative_to(ROOT).parts)
    ]
    require(not public_bytecode, "compiled Python bytecode remains in the public tree")
    require(not (ROOT / ".pytest_cache").exists(), "pytest cache remains")
    return {
        "version": RELEASE_VERSION,
        "date": RELEASE_DATE,
        "status": "unrefereed-candidate",
        "third_party_full_text_files": 0,
        "compiled_artifacts": 0,
    }

def check_pdf() -> dict[str, Any]:
    pdf = ROOT / "paper/main.pdf"
    info = run(["pdfinfo", str(pdf)])
    require(info.returncode == 0, f"pdfinfo failed: {info.stderr}")
    fields: dict[str, str] = {}
    for line in info.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    require(int(fields.get("Pages", "0")) >= 29, f"PDF pages {fields.get('Pages')} < 29")
    require("A4" in fields.get("Page size", ""), "PDF is not A4")

    fonts = run(["pdffonts", str(pdf)])
    require(fonts.returncode == 0, f"pdffonts failed: {fonts.stderr}")
    lines = fonts.stdout.splitlines()[2:]
    require(lines, "no fonts listed")
    require(all(" yes " in f" {line} " for line in lines), "a PDF font is not embedded")
    require(not any("Type 3" in line for line in lines), "Type 3 fonts remain in PDF")

    log_candidates = [ROOT / "paper/main.log", ROOT / "logs/final_latex_build.log"]
    log = next((candidate for candidate in log_candidates if candidate.is_file()), None)
    require(log is not None, "no LaTeX build log found; compile before verification")
    text = log.read_text(errors="replace")
    bad = [
        "Overfull \\hbox",
        "Overfull \\vbox",
        "Float too large",
        "undefined references",
        "undefined citations",
    ]
    found = [needle for needle in bad if needle in text]
    require(not found, f"critical LaTeX warnings: {found}")

    extracted = run(["pdftotext", str(pdf), "-"])
    require(extracted.returncode == 0 and len(extracted.stdout) > 50000, "PDF text extraction failed")
    require("Certified Commitment Horizons" in extracted.stdout, "PDF title not extractable")
    require("\ufffd" not in extracted.stdout, "replacement glyph in extracted PDF text")
    return {
        "pages": int(fields["Pages"]),
        "page_size": fields["Page size"],
        "bytes": pdf.stat().st_size,
        "sha256": sha256(pdf),
        "fonts": len(lines),
        "all_fonts_embedded": True,
        "type3_fonts": 0,
        "critical_latex_warnings": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    provenance = json.loads((ROOT / "release/provenance.json").read_text(encoding="utf-8"))
    receipt: dict[str, Any] = {
        "status": "pass",
        "release": provenance.get("release"),
        "generated_at_utc": f"{RELEASE_DATE}T00:00:00+00:00",
        "upstream_source_snapshot_commit": provenance.get("upstream_source_snapshot_commit"),
        "verification_command": "PYTHONPATH=src python scripts/verify_release.py --run-tests",
        "full_quick_replay_command": "./run_all.sh --quick",
        "checks": {},
    }
    try:
        receipt["checks"]["required"] = check_required()
        receipt["checks"]["release_contract"] = check_release_contract()
        receipt["checks"]["json"] = check_json()
        receipt["checks"]["certificate"] = check_certificate()
        receipt["checks"]["exact"] = check_exact()
        receipt["checks"]["exact_certification"] = check_exact_certification()
        receipt["checks"]["calibration"] = check_calibration()
        receipt["checks"]["rolling"] = check_rolling()
        receipt["checks"]["uci"] = check_uci()
        receipt["checks"]["example"] = check_example()
        receipt["checks"]["wheel"] = check_wheel()
        receipt["checks"]["pdf"] = check_pdf()
        if args.run_tests:
            test = run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"])
            require(test.returncode == 0, f"pytest failed:\n{test.stdout}\n{test.stderr}")
            receipt["checks"]["pytest"] = {"status": "pass", "output": test.stdout.strip()}
    except Exception as exc:
        receipt["status"] = "fail"
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 1

    receipt["limitations"] = [
        "Producer-side verification; not an independent clean-room reproduction.",
        "Certified values are exact-rational and witness-backed, and the separately "
        "implemented producer-side checker re-verifies records, but neither implementation has proof-assistant "
        "verification; for T>12 frozen-minimality relies on the package's internally "
        "cross-checked parametric computation.",
        "Illustrative UCI forecasts and costs are reconstructed; the case is not field validation.",
        "Richter and Voros (1989) full text was not inspected, so the novelty boundary remains conditional.",
    ]
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
