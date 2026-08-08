#!/usr/bin/env python3
"""Remove only interrupted raw-result fragments created by this package."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    partials = sorted((ROOT / "results" / "raw").glob("*.partial.csv"))
    for path in partials:
        path.unlink()
    print(f"Cleared partial result files: {len(partials)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
