#!/usr/bin/env python3
"""Run the v3 quick replay and installed-wheel checks in a clean extraction.

The script deliberately uses two import contexts.  Source tests and the
pre-seal release verifier run from the extracted tree with ``PYTHONPATH=src``.
The wheel probe runs with isolated Python from an unrelated working directory,
so a source-tree import cannot masquerade as a successful wheel installation.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "3.0.0"
WHEEL_NAME = f"wwprefix-{VERSION}-py3-none-any.whl"
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", "build", "dist"}
AUX_SUFFIXES = {".aux", ".bcf", ".blg", ".bbl", ".fdb_latexmk", ".fls", ".log", ".out", ".run.xml", ".toc"}
SKIP_FILES = {
    "quality/fresh_extract_replay.txt",
    "release/SHA256SUMS",
    "release/verification_receipt.json",
    "release/preseal_verification_receipt.json",
}


class ReplayFailure(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_release(source: Path, destination: Path) -> None:
    def ignore(directory: str, names: list[str]) -> set[str]:
        base = Path(directory)
        ignored: set[str] = set()
        for name in names:
            path = base / name
            relative = path.relative_to(source).as_posix()
            if name in SKIP_DIRS or name.endswith(".egg-info"):
                ignored.add(name)
            elif relative in SKIP_FILES or name.endswith((".pyc", ".pyo", ".partial.csv")):
                ignored.add(name)
            elif relative.startswith("paper/") and any(name.endswith(suffix) for suffix in AUX_SUFFIXES):
                ignored.add(name)
        return ignored

    shutil.copytree(source, destination, ignore=ignore, symlinks=False)


def run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    label: str,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ReplayFailure(
            f"{label} failed with exit {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", default=sys.executable, help="Python executable used to create the clean venv")
    parser.add_argument(
        "--receipt",
        type=Path,
        default=ROOT / "quality/fresh_extract_replay.txt",
        help="receipt written only after every clean-extraction gate passes",
    )
    args = parser.parse_args()

    provenance = json.loads((ROOT / "release/provenance.json").read_text(encoding="utf-8"))
    source_snapshot = provenance["source_snapshot_sha256"]
    wheel = ROOT / "release" / WHEEL_NAME
    if not wheel.is_file():
        raise ReplayFailure(f"missing wheel: {wheel}")

    with tempfile.TemporaryDirectory(prefix="cch-v3-fresh-") as temporary:
        temp = Path(temporary)
        extracted = temp / "certified_commitment_horizons_v3.0.0"
        external = temp / "outside-source-tree"
        environment_dir = temp / "venv"
        external.mkdir()
        copy_release(ROOT, extracted)

        venv.EnvBuilder(with_pip=True, clear=True).create(environment_dir)
        bin_dir = environment_dir / ("Scripts" if os.name == "nt" else "bin")
        python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        cli = bin_dir / ("wwprefix.exe" if os.name == "nt" else "wwprefix")
        clean_env = os.environ.copy()
        clean_env.pop("PYTHONPATH", None)
        clean_env["PYTHONNOUSERSITE"] = "1"
        clean_env["PATH"] = str(bin_dir) + os.pathsep + clean_env.get("PATH", "")
        clean_env.setdefault("SOURCE_DATE_EPOCH", "1787011200")
        clean_env.setdefault("FORCE_SOURCE_DATE", "1")
        clean_env.setdefault("TZ", "UTC")

        run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(extracted / "requirements-lock.txt")],
            cwd=external,
            env=clean_env,
            label="locked dependency installation",
        )
        run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-deps", "--force-reinstall", str(extracted / "release" / WHEEL_NAME)],
            cwd=external,
            env=clean_env,
            label="wheel installation",
        )

        quick = run(
            ["bash", "run_all.sh", "--quick", "--pre-seal"],
            cwd=extracted,
            env=clean_env,
            label="clean-extraction quick replay",
        )
        if "94 passed" not in quick.stdout:
            raise ReplayFailure("clean-extraction quick replay did not report 94 passing tests")

        origin_result = run(
            [str(python), "-I", "-c", "import json, wwprefix; print(json.dumps({'origin': wwprefix.__file__, 'version': wwprefix.__version__}))"],
            cwd=external,
            env=clean_env,
            label="isolated wheel import",
        )
        origin_data = json.loads(origin_result.stdout.strip())
        origin = Path(origin_data["origin"]).resolve()
        if origin_data["version"] != VERSION:
            raise ReplayFailure(f"isolated wheel version mismatch: {origin_data['version']}")
        try:
            origin.relative_to(environment_dir.resolve())
        except ValueError as error:
            raise ReplayFailure(f"wheel imported outside clean venv: {origin}") from error
        try:
            origin.relative_to(extracted.resolve())
        except ValueError:
            pass
        else:
            raise ReplayFailure(f"wheel import was contaminated by extracted source: {origin}")

        run([str(cli), "--help"], cwd=external, env=clean_env, label="installed CLI help")
        generated = external / "sample_decision.json"
        run(
            [str(cli), "certify", str(extracted / "examples/strict_gap_instance.json"), "--k", "1", "--exact", "--output", str(generated)],
            cwd=external,
            env=clean_env,
            label="installed-wheel sample certification",
        )
        run(
            [str(python), "-I", str(extracted / "scripts/check_certificate.py"), str(generated), str(extracted / "examples/strict_gap_instance.json")],
            cwd=external,
            env=clean_env,
            label="independent sample checker",
        )

        rebuilt_pdf = extracted / "paper/main.pdf"
        if sha256(rebuilt_pdf) != sha256(ROOT / "paper/main.pdf"):
            raise ReplayFailure("fresh-extraction PDF hash differs from the active deterministic build")
        snapshot_check = run(
            [str(python), str(extracted / "scripts/source_snapshot.py"), "--check-provenance"],
            cwd=extracted,
            env=clean_env,
            label="source snapshot check",
        )

        receipt_lines = [
            "Certified Commitment Horizons v3.0.0 fresh-extraction replay",
            f"generated_at_utc: {dt.datetime.now(dt.timezone.utc).isoformat()}",
            "status: PASS",
            f"source_snapshot_sha256: {source_snapshot}",
            f"python: {args.python}",
            "locked_dependency_install: PASS",
            "pytest: 94 passed",
            "wheel_install: PASS",
            "isolated_wheel_import: PASS",
            f"wheel_import_origin: {origin}",
            "cli_help: PASS",
            "sample_certification: PASS",
            "independent_checker: PASS",
            "preseal_release_verifier: PASS",
            "quick_replay_preseal: PASS",
            f"pdf_sha256: {sha256(ROOT / 'paper/main.pdf')}",
            f"wheel_sha256: {sha256(wheel)}",
            "source_snapshot_check_output: " + snapshot_check.stdout.strip().replace("\n", " "),
            "authority_limit: Producer fresh-extraction replay; not independent reproduction or peer review.",
        ]
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text("\n".join(receipt_lines) + "\n", encoding="utf-8")
        print("\n".join(receipt_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
