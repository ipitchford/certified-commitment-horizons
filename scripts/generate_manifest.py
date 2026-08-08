#!/usr/bin/env python3
"""Regenerate the release SHA-256 manifest from the clean public tree."""
from __future__ import annotations

from pathlib import Path

from verify_hashes import release_file, sha256

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "release/SHA256SUMS"


def main() -> int:
    paths = sorted(
        path
        for path in ROOT.rglob("*")
        if release_file(path, ROOT, MANIFEST)
    )
    lines = [f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}" for path in paths]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} entries to {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
