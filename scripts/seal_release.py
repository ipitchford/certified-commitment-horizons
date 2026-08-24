#!/usr/bin/env python3
"""Create the complete SHA-256 manifest and deterministic v3 release ZIP."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from verify_hashes import release_file, sha256

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "release/SHA256SUMS"
PREFIX = "certified_commitment_horizons_v3.0.0"


class SealFailure(RuntimeError):
    pass


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    if result.returncode:
        raise SealFailure(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout


def clean_files(root: Path, manifest: Path) -> list[Path]:
    return sorted(
        (path for path in root.rglob("*") if release_file(path, root, manifest)),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def write_manifest() -> int:
    paths = clean_files(ROOT, MANIFEST)
    lines = [f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}" for path in paths]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(paths)


def zip_timestamp() -> tuple[int, int, int, int, int, int]:
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "1787011200"))
    value = dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc)
    year = min(max(value.year, 1980), 2107)
    return (year, value.month, value.day, value.hour, value.minute, value.second - value.second % 2)


def write_zip(output: Path) -> int:
    paths = [*clean_files(ROOT, MANIFEST), MANIFEST]
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    timestamp = zip_timestamp()
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(paths, key=lambda item: item.relative_to(ROOT).as_posix()):
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(f"{PREFIX}/{relative}", date_time=timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    temporary.replace(output)
    return len(paths)


def verify_extracted(output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="cch-v3-seal-check-") as temporary:
        directory = Path(temporary)
        with zipfile.ZipFile(output) as archive:
            archive.extractall(directory)
        extracted = directory / PREFIX
        run(
            [sys.executable, "scripts/verify_hashes.py", "release/SHA256SUMS"],
            cwd=extracted,
        )
        env = os.environ.copy()
        env["PYTHONPATH"] = str(extracted / "src")
        verifier = run(
            [sys.executable, "scripts/verify_release.py", "--run-tests"],
            cwd=extracted,
            env=env,
        )
        parsed = json.loads(verifier)
        if parsed.get("status") != "pass" or parsed.get("verification_mode") != "final":
            raise SealFailure("extracted final verifier did not return a final-mode pass")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--skip-extracted-verifier", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    try:
        output.relative_to(ROOT)
    except ValueError:
        pass
    else:
        raise SealFailure("the release ZIP must be written outside the release tree")

    receipt_path = ROOT / "release/verification_receipt.json"
    if not receipt_path.is_file():
        raise SealFailure("final verification receipt is absent")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("status") != "pass" or receipt.get("verification_mode") != "final":
        raise SealFailure("final verification receipt is not a final-mode pass")

    entries = write_manifest()
    run([sys.executable, "scripts/verify_hashes.py", "release/SHA256SUMS"], cwd=ROOT)
    members = write_zip(output)
    if not args.skip_extracted_verifier:
        verify_extracted(output)
    print(json.dumps({
        "status": "pass",
        "manifest_entries": entries,
        "zip_members": members,
        "zip": str(output),
        "zip_sha256": sha256(output),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
