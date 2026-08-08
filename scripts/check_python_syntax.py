#!/usr/bin/env python3
"""Parse every released Python source file without writing bytecode caches."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (ROOT / "src", ROOT / "scripts", ROOT / "tests")


def main() -> int:
    files = sorted(path for root in SOURCE_ROOTS for path in root.rglob("*.py"))
    for path in files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"Python syntax check passed: {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
