#!/usr/bin/env python3
"""Verify the SHA-256 manifest and its coverage of the clean release tree."""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

AUX_SUFFIXES = {".aux", ".bcf", ".blg", ".bbl", ".fdb_latexmk", ".fls", ".log", ".out", ".run.xml", ".toc"}
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", "build", "dist"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def release_file(path: Path, root: Path, manifest: Path) -> bool:
    if path == manifest or not path.is_file():
        return False
    relative = path.relative_to(root)
    if any(part in SKIP_DIRS or part.endswith(".egg-info") for part in relative.parts):
        return False
    if path.suffix in {".pyc", ".zip"} or path.name.endswith(".partial.csv"):
        return False
    if relative.parts and relative.parts[0] == "paper" and any(path.name.endswith(suffix) for suffix in AUX_SUFFIXES):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    manifest = args.manifest.resolve()
    root = manifest.parents[1]
    seen: set[str] = set()
    failures: list[str] = []
    checked = 0

    for line_no, raw in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        try:
            expected, relative = raw.split("  ", 1)
        except ValueError:
            failures.append(f"line {line_no}: malformed entry")
            continue
        if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
            failures.append(f"line {line_no}: invalid SHA-256")
            continue
        relative = relative.strip()
        if relative in seen:
            failures.append(f"line {line_no}: duplicate path {relative}")
            continue
        seen.add(relative)
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            failures.append(f"line {line_no}: path escapes release root: {relative}")
            continue
        if not path.is_file():
            failures.append(f"missing: {relative}")
            continue
        actual = sha256(path)
        if actual != expected:
            failures.append(f"mismatch: {relative}: expected {expected}, got {actual}")
            continue
        checked += 1

    expected_paths = {path.relative_to(root).as_posix() for path in root.rglob("*") if release_file(path, root, manifest)}
    unlisted = sorted(expected_paths - seen)
    stale = sorted(seen - expected_paths)
    if unlisted:
        failures.extend(f"unlisted release file: {path}" for path in unlisted)
    if stale:
        failures.extend(f"manifest entry is outside the clean release set: {path}" for path in stale)
    if not seen:
        failures.append("manifest contains no file entries")

    if failures:
        print("SHA-256 verification failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"SHA-256 verification passed for {checked} files; manifest coverage is complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
