#!/usr/bin/env python3
"""Compute the authoritative source snapshot for release 3.0.0.

The digest deliberately excludes generated results, compiled artefacts, the
PDF, wheel, logs, quality receipts, external data/literature and release
metadata.  This avoids circularity while binding the source, tests, scripts,
manuscript source, documentation, examples and environment specifications.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    ".gitattributes",
    ".gitignore",
    "CITATION.cff",
    "LICENSE",
    "LICENSES.md",
    "PUBLIC_DOMAIN.md",
    "THIRD_PARTY_NOTICES.md",
    "AI_INDEX.md",
    ".zenodo.json",
    "README.md",
    "pyproject.toml",
    "requirements-lock.txt",
    "run_all.sh",
    "uv.lock",
}
SOURCE_DIRS = {"src", "scripts", "tests", "docs"}
PAPER_SOURCE_SUFFIXES = {".tex", ".bib"}
EXAMPLE_INPUTS = {
    "examples/benchmark_hard_instance_id26_T18.json",
    "examples/leading_zero_semantic_counterexample.json",
    "examples/reviewer_counterexample.json",
    "examples/reviewer_counterexample_decimal.json",
    "examples/strict_gap_instance.json",
}
SKIP_PARTS = {"__pycache__", ".pytest_cache", "build", "dist"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def authoritative_files(root: Path = ROOT) -> list[Path]:
    files: set[Path] = set()
    for name in ROOT_FILES:
        path = root / name
        if path.is_file():
            files.add(path)
    for directory in SOURCE_DIRS:
        base = root / directory
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(root)
            if any(part in SKIP_PARTS or part.endswith(".egg-info") for part in relative.parts):
                continue
            if path.suffix in {".pyc", ".pyo"}:
                continue
            files.add(path)
    paper = root / "paper"
    if paper.is_dir():
        files.update(
            path for path in paper.iterdir()
            if path.is_file() and path.suffix in PAPER_SOURCE_SUFFIXES
        )
    for name in EXAMPLE_INPUTS:
        path = root / name
        if path.is_file():
            files.add(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def snapshot(root: Path = ROOT) -> tuple[str, list[dict[str, str]]]:
    digest = hashlib.sha256()
    records: list[dict[str, str]] = []
    for path in authoritative_files(root):
        relative = path.relative_to(root).as_posix()
        file_hash = sha256_file(path)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\n")
        records.append({"path": relative, "sha256": file_hash})
    return digest.hexdigest(), records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit digest and records as JSON")
    parser.add_argument(
        "--check-provenance",
        action="store_true",
        help="compare the computed digest with release/provenance.json",
    )
    args = parser.parse_args()
    digest, records = snapshot()
    result: dict[str, object] = {
        "algorithm": "sha256(sorted(relative_path + NUL + file_sha256 + LF))",
        "file_count": len(records),
        "source_snapshot_sha256": digest,
    }
    if args.check_provenance:
        provenance = json.loads((ROOT / "release/provenance.json").read_text(encoding="utf-8"))
        expected = provenance.get("source_snapshot_sha256")
        result["provenance_expected"] = expected
        result["matches_provenance"] = expected == digest
        if expected != digest:
            print(json.dumps(result, indent=2, sort_keys=True))
            return 1
    if args.json:
        result["records"] = records
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
