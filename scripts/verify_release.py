#!/usr/bin/env python3
"""Verify the frozen 3.0.0 release from raw artefacts.

This is a producer-side integrity and replay checker. It recomputes selected
load-bearing counts and comparisons; it is not independent replication or
formal proof.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
VERSION = "3.0.0"
WHEEL = ROOT / f"release/wwprefix-{VERSION}-py3-none-any.whl"
RICHTER_HASH = "bd5ee5a82e399e11572b44d2bf334672be6bc6b47499271e636cf3a8f04aa255"
LI_MRULS_HASH = "4b970c6228b34e49d47ee460f37e11095299c1ab0351a7b351b553f123d7b86b"
EGRI_INVERSE_HASH = "9043ec932b8a0ba21647d49eddaef0c2e31c20640da8dfd2db6545f44d0150e9"


class VerificationFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationFailure(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src if not env.get("PYTHONPATH") else src + os.pathsep + env["PYTHONPATH"]
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, env=env)


def generated_time() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        return dt.datetime.fromtimestamp(int(epoch), tz=dt.timezone.utc).isoformat()
    return dt.datetime.now(dt.timezone.utc).isoformat()


def check_required(*, require_fresh_receipt: bool = True) -> dict[str, Any]:
    required = [
        "paper/main.pdf",
        "paper/main.tex",
        "paper/references.bib",
        "README.md",
        "LICENSE",
        "LICENSES.md",
        "PUBLIC_DOMAIN.md",
        "THIRD_PARTY_NOTICES.md",
        "AI_INDEX.md",
        "CITATION.cff",
        "requirements-lock.txt",
        "examples/strict_gap_instance.json",
        "examples/leading_zero_semantic_counterexample.json",
        "examples/sample_decision.json",
        "docs/PRACTITIONER_GUIDE.md",
        "docs/input_schema.md",
        "docs/literature_audit.md",
        "docs/richter_voros_inspection_receipt.md",
        "docs/reproducibility.md",
        "docs/scope_and_limitations.md",
        "docs/verification_matrix.md",
        "release/claims.json",
        "release/provenance.json",
        "release/operating_model.json",
        "release/literature_inspection_receipt.json",
        "release/prior_art_corpus.json",
        "literature/README.md",
        "scripts/verify_hashes.py",
        "scripts/source_snapshot.py",
        "scripts/check_certificate.py",
        "scripts/run_semantic_bridge_audit.py",
        "scripts/run_optimal_face_audit.py",
        f"release/wwprefix-{VERSION}-py3-none-any.whl",
        "results/raw/semantic_bridge_audit.csv",
        "results/raw/optimal_face_edge_audit.csv",
        "quality/pdffonts.txt",
        "quality/pdfinfo.txt",
        "quality/pdf_visual_inspection.md",
        "quality/preflight.json",
        "quality/preflight.txt",
    ]
    if require_fresh_receipt:
        required.append("quality/fresh_extract_replay.txt")
    missing = [name for name in required if not (ROOT / name).is_file()]
    require(not missing, f"missing required files: {missing}")
    partial = sorted((ROOT / "results/raw").glob("*.partial.csv"))
    require(not partial, f"partial result files remain: {[p.name for p in partial]}")
    forbidden = [ROOT / ".venv", ROOT / ".git", ROOT / "__MACOSX"]
    present = [p.relative_to(ROOT).as_posix() for p in forbidden if p.exists()]
    require(not present, f"forbidden release directories present: {present}")
    return {"required_files": len(required), "missing": [], "partial_files": [], "forbidden_present": []}



def check_source_snapshot() -> dict[str, Any]:
    from source_snapshot import snapshot

    provenance = json.loads((ROOT / "release/provenance.json").read_text(encoding="utf-8"))
    actual, records = snapshot(ROOT)
    expected = provenance.get("source_snapshot_sha256")
    require(expected not in {None, "", "PENDING_FINAL_SOURCE_SNAPSHOT"}, "source snapshot is not frozen")
    require(actual == expected, f"source snapshot mismatch: expected {expected}, got {actual}")
    return {"sha256": actual, "file_count": len(records), "matches_provenance": True}

def check_versions() -> dict[str, Any]:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    init = (ROOT / "src/wwprefix/__init__.py").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manuscript = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
    require(f'version = "{VERSION}"' in pyproject, "pyproject version mismatch")
    require(f"version: {VERSION}" in cff, "CITATION.cff version mismatch")
    require(f'__version__ = "{VERSION}"' in init, "package __version__ mismatch")
    require(f"**Release:** {VERSION}" in readme, "README release mismatch")
    require(f"Preprint version {VERSION}" in manuscript, "manuscript version mismatch")
    provenance = json.loads((ROOT / "release/provenance.json").read_text())
    claims = json.loads((ROOT / "release/claims.json").read_text())
    operating = json.loads((ROOT / "release/operating_model.json").read_text())
    for label, obj in [("provenance", provenance), ("claims", claims), ("operating model", operating)]:
        require(obj.get("release_version") == VERSION, f"{label} release version mismatch")
    return {"version": VERSION, "metadata_files_consistent": True}



def check_metadata_contract() -> dict[str, Any]:
    provenance = json.loads((ROOT / "release/provenance.json").read_text(encoding="utf-8"))
    claims = json.loads((ROOT / "release/claims.json").read_text(encoding="utf-8"))
    operating = json.loads((ROOT / "release/operating_model.json").read_text(encoding="utf-8"))
    literature = json.loads((ROOT / "release/literature_inspection_receipt.json").read_text(encoding="utf-8"))

    identity = (provenance.get("work_id"), provenance.get("attempt_id"), provenance.get("release_version"))
    require(identity == ("cch-wwprefix", "cch-wwprefix-v3.0.0-20260818", VERSION), "provenance identity mismatch")
    require(
        (claims.get("work_id"), claims.get("attempt_id"), claims.get("release_version")) == identity,
        "claims identity mismatch",
    )
    require(
        (operating.get("work_id"), operating.get("attempt_id"), operating.get("release_version")) == identity,
        "operating-model identity mismatch",
    )
    require(literature.get("work_id") == identity[0] and literature.get("release_version") == VERSION, "literature identity mismatch")

    entries = claims.get("claims", [])
    ids = [entry.get("id") for entry in entries]
    require(len(entries) == 17 and len(set(ids)) == 17 and all(ids), "claims ledger IDs are incomplete or duplicated")
    required_claim_fields = {
        "id", "claim", "status", "domain", "proof_locator",
        "computational_evidence", "nonclaims", "remaining_uncertainty",
    }
    for entry in entries:
        missing = required_claim_fields - set(entry)
        require(not missing, f"claim {entry.get('id')} missing fields: {sorted(missing)}")
        require(bool(entry["claim"].strip()) and bool(entry["domain"].strip()), f"claim {entry['id']} is empty")
        require(bool(entry["proof_locator"].strip()), f"claim {entry['id']} lacks a proof locator")
        require(entry["nonclaims"], f"claim {entry['id']} lacks bounded nonclaims")
        require(entry["remaining_uncertainty"], f"claim {entry['id']} lacks uncertainty disclosure")
        for evidence in entry["computational_evidence"]:
            value = evidence.get("artefact", "")
            require(value, f"claim {entry['id']} has evidence without an artefact")
            for target in value.split(" and "):
                path = ROOT / target.strip()
                require(path.exists(), f"claim {entry['id']} cites missing artefact: {target}")

    require(claims.get("global_nonclaims"), "global nonclaims are absent")
    require(operating.get("semantic_bridge", {}).get("state"), "semantic-bridge state is absent")
    gates = operating.get("human_judgement_gates", [])
    require(len(gates) >= 5 and all(gate.get("status") == "open" for gate in gates), "human gates are incomplete or falsely closed")
    require(operating.get("impact_evidence", {}).get("state") == "none", "impact evidence is overstated")
    publication = operating.get("publication_decision", {})
    require(publication.get("state") == "candidate_release_eligible_after_internal_replay", "publication state mismatch")
    required_limits = {"peer reviewed", "independently replicated", "formally verified", "field validated", "REF 4-star adjudicated"}
    require(required_limits.issubset(set(publication.get("not_equivalent_to", []))), "publication authority limits incomplete")
    return {
        "identity": {"work_id": identity[0], "attempt_id": identity[1], "release_version": identity[2]},
        "claims": len(entries),
        "claim_ids_unique": True,
        "human_gates_open": len(gates),
        "impact_evidence": "none",
        "publication_state": publication["state"],
    }

def check_json() -> dict[str, Any]:
    paths = sorted(ROOT.glob("results/processed/*.json"))
    paths += sorted(ROOT.glob("release/*.json"))
    paths += sorted(ROOT.glob("examples/*.json"))
    for path in paths:
        json.loads(path.read_text(encoding="utf-8"))
    return {"json_files_parsed": len(paths)}


def check_semantic_bridge() -> dict[str, Any]:
    raw = pd.read_csv(ROOT / "results/raw/semantic_bridge_audit.csv")
    summary = json.loads((ROOT / "results/processed/semantic_bridge_audit_summary.json").read_text())
    require(len(raw) == 320, f"semantic bridge rows {len(raw)} != 320")
    require(bool(raw["exact_match"].astype(bool).all()), "semantic bridge mismatch")
    require(int(raw["empty_optimal_graph_paths"].sum()) == 0, "empty later setup in classical optimum")
    neg = summary["negative_control"]
    require(neg["forced_source_graph_optimum"] == "101", "negative-control graph cost mismatch")
    require(neg["ordinary_physical_optimum"] == "1", "negative-control physical cost mismatch")
    require(neg["classical_mode_admissible"] is False, "negative control accepted in classical mode")
    return {
        "instances": len(raw),
        "exact_matches": int(raw["exact_match"].astype(bool).sum()),
        "empty_optimal_graph_paths": int(raw["empty_optimal_graph_paths"].sum()),
        "negative_control": {"graph": "101", "physical": "1", "classical_admissible": False},
    }


def check_optimal_face() -> dict[str, Any]:
    raw = pd.read_csv(ROOT / "results/raw/optimal_face_edge_audit.csv")
    summary = json.loads((ROOT / "results/processed/optimal_face_edge_audit_summary.json").read_text())
    require(len(raw) == 315, f"optimal-face rows {len(raw)} != 315")
    applicable = raw[raw["edge_witness_found"].astype(str).str.lower() == "true"]
    require(len(applicable) == 254, f"finite edge-witness rows {len(applicable)} != 254")
    require(summary["single_detour_edge_witnesses_found"] == 254, "edge-witness summary mismatch")
    require(int((raw["status"] == "proven_infinite").sum()) == 61, "proven-infinite denominator mismatch")
    require(summary["failures"] == 0, "edge-witness audit reports failure")
    require(bool((applicable["divergence_node"] < applicable["remergence_node"]).all()), "invalid detour endpoints")
    return {"prefix_cases": len(raw), "finite_exact_boundaries": len(applicable), "witnesses_found": len(applicable)}


def check_certificate() -> dict[str, Any]:
    cert = pd.read_csv(ROOT / "results/raw/certificate_audit.csv")
    graph = pd.read_csv(ROOT / "results/raw/graph_bijection_audit.csv")
    fixed = pd.read_csv(ROOT / "results/raw/fixed_competitor_audit.csv")
    require(len(cert) == 512, f"certificate rows {len(cert)} != 512")
    require(cert["instance_id"].nunique() == 258, "certificate instance count != 258")
    max_error = float(cert["absolute_error"].fillna(0).abs().max())
    require(max_error == 0.0, f"certificate max stored error {max_error} != 0")
    require(bool(cert["exact_contained"].fillna(False).astype(bool).all()), "exact radius outside a bracket")
    full = cert[cert["is_full_path"].astype(bool)]
    require(len(full) == 258, f"full-path cases {len(full)} != 258")
    positive_partial = cert[
        cert["is_partial_prefix"].astype(bool)
        & np.isfinite(cert["exact_radius"])
        & (cert["exact_radius"] > 1e-10)
    ]
    closures = int(positive_partial["bracket_exact_certified"].astype(bool).sum())
    require(len(positive_partial) == 254, f"positive partial cases {len(positive_partial)} != 254")
    require(closures == 153, f"partial exact closures {closures} != 153")
    require(len(graph) == 62, f"graph rows {len(graph)} != 62")
    require(bool(graph["acyclic"].astype(bool).all()), "cyclic prefix graph")
    require(bool((graph["expanded_paths"] == graph["outside_paths"]).all()), "prefix graph bijection failure")
    require(len(fixed) == 96, f"fixed-competitor rows {len(fixed)} != 96")
    finite = fixed[fixed["compact_status"] == "optimal"]
    max_fixed_error = float(finite["absolute_error"].abs().max())
    require(max_fixed_error <= 1e-9, f"fixed-competitor error {max_fixed_error}")
    return {
        "certificate_rows": len(cert),
        "instances": 258,
        "max_stored_absolute_error": max_error,
        "graph_cases": len(graph),
        "fixed_competitor_cases": len(fixed),
        "partial_cases": len(positive_partial),
        "partial_exact_closures": closures,
        "total_exact_closures": closures + len(full),
        "certified_intervals": len(cert) - closures - len(full),
    }


def check_exact_certification() -> dict[str, Any]:
    agreement = pd.read_csv(ROOT / "results/raw/exact_certification_audit.csv")
    adversarial = pd.read_csv(ROOT / "results/raw/exact_adversarial_audit.csv")
    scaling = pd.read_csv(ROOT / "results/raw/exact_scaling_study.csv")
    require(len(agreement) == 330, f"exact-certification rows {len(agreement)} != 330")
    require(bool(agreement["brute_force_match"].astype(bool).all()), "exact frozen mismatch")
    require(int(agreement["float_false_infinite"].sum()) == 0, "float false-infinite classification")
    require(int(agreement["float_false_finite"].sum()) == 0, "float false-finite classification")
    exact_count = int(agreement["enumeration_exact_certified"].astype(bool).sum())
    require(exact_count == 305, f"point-exact strong radii {exact_count} != 305")
    widths = agreement["enumeration_interval_relative_width"].dropna()
    max_width = float(widths.max()) if len(widths) else 0.0
    require(max_width <= 1e-9, f"certified interval too wide: {max_width}")
    binary = adversarial[(adversarial["family"] == "reviewer_counterexample_binary") & (adversarial["proposal"] == 1.1)]
    require(set(binary["classification"]) == {"certified_destabilising_witness_exists"}, "counterexample regression")
    require(365 in set(scaling["T"]), "exact scaling missing T=365")
    return {
        "comparisons": len(agreement),
        "brute_force_matches": int(agreement["brute_force_match"].astype(bool).sum()),
        "point_exact": exact_count,
        "certified_intervals": len(agreement) - exact_count,
        "max_interval_relative_width": max_width,
        "adversarial_rows": len(adversarial),
    }


def check_equivalence() -> dict[str, Any]:
    raw = pd.read_csv(ROOT / "results/raw/addendum_equivalence.csv")
    invariant = {
        "exact_match_certified": 305,
        "exact_rational_equality": 247,
        "unresolved_pair": 20,
    }
    counts = {str(k): int(v) for k, v in raw["match_class"].value_counts().items()}
    require(len(raw) == 627, f"equivalence rows {len(raw)} != 627")
    for name, expected in invariant.items():
        require(counts.get(name) == expected, f"equivalence invariant {name} differs: {counts}")
    search_partition = counts.get("float_match_certified", 0) + counts.get("reference_unresolved", 0)
    require(search_partition == 55, f"platform-sensitive search partition is {search_partition}, expected 55")
    require(set(counts) == {*invariant, "float_match_certified", "reference_unresolved"}, f"unexpected equivalence classes: {counts}")
    summary = json.loads((ROOT / "results/processed/addendum_equivalence_summary.json").read_text())
    require(summary["match_class_counts"] == counts, "equivalence raw/summary class counts differ")
    require(summary["zero_disagreements"] is True and not summary["failures"], "equivalence gate failure")
    return {
        "rows": len(raw),
        "match_class_counts": counts,
        "platform_sensitive_search_partition": search_partition,
        "warranted_disagreements": 0,
    }


def check_benchmarks() -> dict[str, Any]:
    exact = pd.read_csv(ROOT / "results/raw/exact_benchmark.csv")
    milp = pd.read_csv(ROOT / "results/raw/milp_benchmark.csv")
    require(len(exact) == 30, f"exact benchmark rows {len(exact)} != 30")
    exact_statuses = {str(k): int(v) for k, v in exact["exact_status"].value_counts().items()}
    require(
        exact_statuses == {"optimal": 28, "time_limit_before_disjuncts": 2},
        f"unexpected exact benchmark statuses: {exact_statuses}",
    )
    require(int(exact["solver_failures"].sum()) == 0, "exact benchmark solver failure")
    exact_resolved = exact[exact["exact_status"] == "optimal"]
    exact_unresolved = exact[exact["exact_status"] == "time_limit_before_disjuncts"]
    require(bool((exact_unresolved["paths_processed"] == 0).all()), "pre-disjunct timeout processed a disjunct")
    require(float(exact_resolved["witness_difference"].fillna(0).max()) <= 1e-9, "exact benchmark witness mismatch")
    require(len(milp) == 24, f"MILP rows {len(milp)} != 24")
    resolved = milp[milp["decision"].notna()]
    unresolved = milp[milp["decision"].isna()]
    require(len(resolved) == 22 and len(unresolved) == 2, "MILP resolution counts differ")
    require(bool(resolved["decision_matches_when_resolved"].astype(bool).all()), "resolved MILP mismatch")
    return {
        "exact_instances": 30,
        "exact_resolved": len(exact_resolved),
        "exact_time_limit_before_disjuncts": len(exact_unresolved),
        "milp_probes": 24,
        "milp_resolved": 22,
        "milp_unresolved": 2,
    }


def check_calibration() -> dict[str, Any]:
    scenarios = pd.read_csv(ROOT / "results/raw/calibration_scenarios.csv")
    trials = pd.read_csv(ROOT / "results/raw/calibration_trials.csv")
    require(len(scenarios) == 5 and len(trials) == 85000, "calibration denominator mismatch")
    indexed = scenarios.set_index("scenario")
    exchangeable = indexed.loc["exchangeable_lognormal"]
    shifted = indexed.loc["next_scale_1.50"]
    family = indexed.loc["five_decision_bonferroni_family"]
    require(exchangeable.wilson_95_low <= 0.9 <= exchangeable.wilson_95_high, "exchangeable target outside interval")
    require(shifted.coverage < exchangeable.coverage, "shift control did not under-cover")
    require(family.wilson_95_low <= 0.9 <= family.wilson_95_high, "Bonferroni target outside interval")
    return {
        "trials": len(trials),
        "exchangeable_coverage": float(exchangeable.coverage),
        "scale_1_5_coverage": float(shifted.coverage),
        "bonferroni_family_coverage": float(family.coverage),
    }


def check_rolling() -> dict[str, Any]:
    raw = pd.read_csv(ROOT / "results/raw/rolling_audit.csv")
    require(len(raw) == 462, f"rolling rows {len(raw)} != 462")
    require(bool(raw["theorem_holds"].astype(bool).all()), "rolling theorem audit violation")
    inside = raw[raw["inside_dead_zone"].astype(bool)]
    require(len(inside) == 254, f"inside-dead-zone rows {len(inside)} != 254")
    require(bool(inside["zero_residual_inside_dead_zone"].astype(bool).all()), "nonzero residual inside dead zone")
    return {
        "cases": len(raw),
        "inside_dead_zone": len(inside),
        "max_output_excess": float((raw["bellman_residual"] - raw["dead_zone_bound"]).max()),
    }


def check_uci() -> dict[str, Any]:
    data = ROOT / "data/external/Daily_Demand_Forecasting_Orders.csv"
    expected = "adf8dda021beae76b13b1cbb5b3c075d064f03b3353a711c1ddc357c6f89e924"
    require(sha256(data) == expected, "UCI data hash mismatch")
    summary = json.loads((ROOT / "results/processed/uci_case_summary.json").read_text())
    require(summary["data"]["rows"] == 60 and summary["data"]["columns"] == 13, "UCI schema mismatch")
    require(summary["data"]["missing_cells"] == 0, "UCI missing cells")
    return {"sha256": expected, "rows": 60, "columns": 13, "missing_cells": 0, "evaluation_windows": 12}


def check_literature_receipt() -> dict[str, Any]:
    receipt = json.loads((ROOT / "release/literature_inspection_receipt.json").read_text())
    corpus = json.loads((ROOT / "release/prior_art_corpus.json").read_text(encoding="utf-8"))
    require(receipt["release_version"] == VERSION, "literature receipt version mismatch")
    require(receipt["source"]["sha256"] == RICHTER_HASH, "Richter source hash mismatch")
    require(receipt["claim_ceiling"] == "source_specific_negative_reading_not_exhaustive_priority", "literature claim ceiling mismatch")
    require(receipt["independent_attestation"] is False, "literature receipt falsely claims independence")
    require(corpus.get("release_version") == VERSION and corpus.get("work_id") == "cch-wwprefix", "prior-art corpus identity mismatch")
    require(corpus.get("review_type") == "targeted_not_systematic", "prior-art review type overstated")
    require(corpus.get("claim_ceiling") == "bounded_contribution_comparison_not_exhaustive_priority", "prior-art claim ceiling mismatch")
    sources = {entry["id"]: entry for entry in corpus.get("sources", [])}
    required_ids = {
        "richter_voros_1989", "van_hoesel_wagelmans_1993", "chakravarti_wagelmans_1998",
        "zhang_2011", "li_romero_morales_2013", "li_romero_morales_2017",
        "egri_et_al_2014", "gassner_2009", "ley_merkert_2025",
    }
    require(required_ids.issubset(sources), f"prior-art corpus missing sources: {sorted(required_ids - set(sources))}")
    require(sources["li_romero_morales_2013"].get("sha256") == LI_MRULS_HASH, "Li-Romero Morales corpus hash mismatch")
    require(sources["li_romero_morales_2013"].get("redistributed") is False, "Li-Romero Morales redistribution boundary mismatch")
    redistributed_literature = [
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "literature").rglob("*")
        if path.is_file() and path.name != "README.md"
    ]
    require(not redistributed_literature, f"third-party literature derivatives must not be redistributed: {redistributed_literature}")
    require(sources["egri_et_al_2014"].get("sha256") == EGRI_INVERSE_HASH, "Egri corpus hash mismatch")
    require(sources["richter_voros_1989"].get("sha256") == RICHTER_HASH, "Richter corpus hash mismatch")
    require(corpus.get("missingness") and "No exhaustive priority" in " ".join(corpus["missingness"]), "prior-art missingness incomplete")
    docs = (ROOT / "docs/richter_voros_inspection_receipt.md").read_text(encoding="utf-8")
    manuscript = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
    require(RICHTER_HASH in docs and RICHTER_HASH in manuscript, "Richter hash not synchronised")
    require("LiRomeroMorales2013" in manuscript and "EgriEtAl2014" in manuscript, "direct prior-art comparators absent from manuscript")
    return {
        "richter_source_sha256": RICHTER_HASH,
        "li_mruls_sha256": LI_MRULS_HASH,
        "egri_external_sha256": EGRI_INVERSE_HASH,
        "sources": len(sources),
        "claim_ceiling": corpus["claim_ceiling"],
    }


def check_example() -> dict[str, Any]:
    sample = json.loads((ROOT / "examples/sample_decision.json").read_text())
    require(sample["schema_version"] == "3.0", "sample schema is not 3.0")
    require(sample["model_semantics"]["mode"] == "classical_active_horizon", "sample semantic mode mismatch")
    bracket = sample["certified_bracket"]
    escalation = sample["certified_exact_escalation"]
    require(bracket["frozen_certificate"]["radius"]["exact"] == "3/2", "sample frozen radius mismatch")
    require(escalation["exact_radius"]["exact"] == "2/1", "sample exact radius mismatch")
    require(escalation["status"] == "exact_certified", f"sample status {escalation['status']} is not exact_certified")
    checker = run([sys.executable, "scripts/check_certificate.py", "examples/sample_decision.json", "examples/strict_gap_instance.json"])
    require(checker.returncode == 0, f"independent checker failed: {checker.stdout}{checker.stderr}")
    return {"frozen_radius": "3/2", "exact_radius": "2/1", "semantic_mode": "classical_active_horizon", "independent_checker": "pass"}


def check_wheel() -> dict[str, Any]:
    require(WHEEL.is_file(), f"wheel missing: {WHEEL.name}")
    with zipfile.ZipFile(WHEEL) as archive:
        names = set(archive.namelist())
        source_files = sorted((ROOT / "src/wwprefix").glob("*.py"))
        for source in source_files:
            member = f"wwprefix/{source.name}"
            require(member in names, f"wheel missing {member}")
            require(archive.read(member) == source.read_bytes(), f"wheel source differs: {member}")
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        require(len(metadata_names) == 1, "wheel metadata member count is not one")
        metadata = archive.read(metadata_names[0]).decode("utf-8", errors="replace")
        require(f"Version: {VERSION}\n" in metadata, "wheel version mismatch")
    return {"version": VERSION, "sha256": sha256(WHEEL), "source_files": len(source_files), "source_bytes_match": True}



def check_fresh_extract_receipt() -> dict[str, Any]:
    path = ROOT / "quality/fresh_extract_replay.txt"
    text = path.read_text(encoding="utf-8")
    provenance = json.loads((ROOT / "release/provenance.json").read_text(encoding="utf-8"))
    expected = provenance.get("source_snapshot_sha256")
    required_lines = {
        "status: PASS",
        f"source_snapshot_sha256: {expected}",
        "pytest: 94 passed",
        "wheel_install: PASS",
        "isolated_wheel_import: PASS",
        "cli_help: PASS",
        "sample_certification: PASS",
        "independent_checker: PASS",
        "preseal_release_verifier: PASS",
        "quick_replay_preseal: PASS",
        f"pdf_sha256: {sha256(ROOT / 'paper/main.pdf')}",
        f"wheel_sha256: {sha256(WHEEL)}",
    }
    missing = sorted(line for line in required_lines if line not in text)
    require(not missing, f"fresh-extraction receipt incomplete: {missing}")
    return {
        "status": "pass",
        "source_snapshot_sha256": expected,
        "pytest": 94,
        "wheel_install": "pass",
        "isolated_wheel_import": "pass",
        "preseal_release_verifier": "pass",
        "quick_replay_preseal": "pass",
        "pdf_sha256": sha256(ROOT / "paper/main.pdf"),
        "wheel_sha256": sha256(WHEEL),
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
    pages = int(fields.get("Pages", "0"))
    require(pages >= 30, f"PDF unexpectedly short: {pages} pages")
    require("A4" in fields.get("Page size", ""), "PDF is not A4")
    fonts = run(["pdffonts", str(pdf)])
    require(fonts.returncode == 0, f"pdffonts failed: {fonts.stderr}")
    font_lines = fonts.stdout.splitlines()[2:]
    require(font_lines, "no PDF fonts listed")
    require(all(" yes " in f" {line} " for line in font_lines), "a PDF font is not embedded")
    require(not any("Type 3" in line for line in font_lines), "Type 3 font remains")
    log = ROOT / "logs/final_latex_pass.log"
    require(log.is_file(), "final LaTeX pass log missing")
    text = log.read_text(errors="replace")
    bad = ["Overfull \\hbox", "Overfull \\vbox", "Float too large", "undefined references", "undefined citations"]
    found = [item for item in bad if item in text]
    require(not found, f"critical LaTeX warnings: {found}")
    extracted = run(["pdftotext", str(pdf), "-"])
    require(extracted.returncode == 0 and len(extracted.stdout) > 50000, "PDF text extraction failed")
    require("Certified Commitment Horizons" in extracted.stdout, "PDF title not extractable")
    require("Classical active-horizon bridge" in extracted.stdout, "semantic bridge absent from PDF text")
    require("Single-detour optimal-face witness" in extracted.stdout, "edge theorem absent from PDF text")
    require("\ufffd" not in extracted.stdout, "replacement glyph in PDF text")
    return {
        "pages": pages,
        "page_size": fields["Page size"],
        "bytes": pdf.stat().st_size,
        "sha256": sha256(pdf),
        "fonts": len(font_lines),
        "all_fonts_embedded": True,
        "type3_fonts": 0,
        "critical_latex_warnings": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument(
        "--pre-seal",
        action="store_true",
        help="verify every non-circular gate before a fresh-extraction receipt exists",
    )
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    provenance = json.loads((ROOT / "release/provenance.json").read_text(encoding="utf-8"))
    receipt: dict[str, Any] = {
        "schema_version": "2.0",
        "status": "pass",
        "release_version": VERSION,
        "work_id": provenance.get("work_id"),
        "attempt_id": provenance.get("attempt_id"),
        "generated_at_utc": generated_time(),
        "source_snapshot_sha256": provenance.get("source_snapshot_sha256"),
        "verification_mode": "pre-seal" if args.pre_seal else "final",
        "verification_command": (
            "PYTHONPATH=src python scripts/verify_release.py --run-tests --pre-seal"
            if args.pre_seal
            else "PYTHONPATH=src python scripts/verify_release.py --run-tests"
        ),
        "quick_replay_command": "bash run_all.sh --quick",
        "checks": {},
    }
    try:
        receipt["checks"]["required"] = check_required(require_fresh_receipt=not args.pre_seal)
        receipt["checks"]["versions"] = check_versions()
        receipt["checks"]["source_snapshot"] = check_source_snapshot()
        receipt["checks"]["json"] = check_json()
        receipt["checks"]["metadata_contract"] = check_metadata_contract()
        receipt["checks"]["semantic_bridge"] = check_semantic_bridge()
        receipt["checks"]["optimal_face"] = check_optimal_face()
        receipt["checks"]["certificate"] = check_certificate()
        receipt["checks"]["exact_certification"] = check_exact_certification()
        receipt["checks"]["equivalence"] = check_equivalence()
        receipt["checks"]["benchmarks"] = check_benchmarks()
        receipt["checks"]["calibration"] = check_calibration()
        receipt["checks"]["rolling"] = check_rolling()
        receipt["checks"]["uci"] = check_uci()
        receipt["checks"]["literature"] = check_literature_receipt()
        receipt["checks"]["example"] = check_example()
        receipt["checks"]["wheel"] = check_wheel()
        if args.pre_seal:
            receipt["checks"]["fresh_extract"] = {
                "status": "deferred_until_final_seal",
                "reason": "pre-seal mode breaks the receipt/verifier dependency cycle",
            }
        else:
            receipt["checks"]["fresh_extract"] = check_fresh_extract_receipt()
        receipt["checks"]["pdf"] = check_pdf()
        if args.run_tests:
            test = run([sys.executable, "-m", "pytest", "-q"])
            require(test.returncode == 0, f"pytest failed:\n{test.stdout}\n{test.stderr}")
            match = re.search(r"(\d+) passed", test.stdout)
            require(match is not None and int(match.group(1)) == 94, f"unexpected pytest count: {test.stdout}")
            receipt["checks"]["pytest"] = {"status": "pass", "tests": 94, "output": test.stdout.strip()}
    except Exception as exc:
        receipt["status"] = "fail"
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 1

    receipt["limitations"] = [
        "Producer-side verification; not independent clean-room reproduction.",
        "Universal mathematical claims rest on manuscript proofs; finite audits test implementations and bounded instances but do not machine-prove the theorems.",
        "Neither the exact implementation nor the independent checker has proof-assistant verification; for T>12 the checker does not independently enumerate global frozen-minimality.",
        "Mixed-integer negative results remain solver-level unless a certified bracket or exact proof closes them.",
        "The Richter-Vörös conclusion is source-specific and the literature search is targeted, not exhaustive; no second attestation is included.",
        "The UCI case uses reconstructed forecast vintages and stylised costs and is not field validation.",
        "The exact complexity of the demand-induced one-protected-arc problem remains open.",
    ]
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
