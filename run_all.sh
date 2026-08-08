#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1785801600}"
export FORCE_SOURCE_DATE="${FORCE_SOURCE_DATE:-1}"
export TZ="${TZ:-UTC}"
export PYTHONDONTWRITEBYTECODE=1
MODE="${1:---quick}"

case "$MODE" in
  --quick|--full) ;;
  *) echo "usage: ./run_all.sh [--quick|--full]" >&2; exit 2 ;;
esac

if [[ "$MODE" == "--full" ]]; then
  python scripts/run_certificate_audit.py
  python scripts/run_exact_certification_audit.py
  python scripts/run_exact_benchmark.py
  python scripts/run_calibration_audit.py
  python scripts/run_rolling_audit.py
  python scripts/run_uci_case.py
  python scripts/run_stress_instance.py
  python scripts/clear_partial_results.py
fi

python scripts/check_python_syntax.py
python -m pytest -q -p no:cacheprovider
python -m wwprefix.cli certify examples/strict_gap_instance.json --k 1 --exact \
  --output examples/sample_decision.json
python scripts/make_figures.py
(
  cd paper
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex | tee ../logs/final_latex_build.log
)
python scripts/verify_release.py --run-tests --json-output release/verification_receipt.json

echo "Verification complete: release/verification_receipt.json"
