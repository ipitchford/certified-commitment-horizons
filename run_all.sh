#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1787011200}"
export FORCE_SOURCE_DATE="${FORCE_SOURCE_DATE:-1}"
export TZ="${TZ:-UTC}"
MODE="${1:---quick}"
VERIFY_MODE="${2:---final}"

case "$MODE" in
  --quick|--full) ;;
  *) echo "usage: bash run_all.sh [--quick|--full] [--pre-seal|--final]" >&2; exit 2 ;;
esac
case "$VERIFY_MODE" in
  --pre-seal|--final) ;;
  *) echo "usage: bash run_all.sh [--quick|--full] [--pre-seal|--final]" >&2; exit 2 ;;
esac

if [[ "$MODE" == "--full" ]]; then
  python scripts/run_certificate_audit.py
  python scripts/run_exact_certification_audit.py
  python scripts/run_exact_benchmark.py
  python scripts/run_calibration_audit.py
  python scripts/run_rolling_audit.py
  python scripts/run_uci_case.py
  python scripts/run_stress_instance.py
  python scripts/run_addendum_equivalence.py
  python scripts/run_addendum_benchmark.py
fi

# New semantic and structural gates are fast enough to rerun in both modes.
python scripts/run_semantic_bridge_audit.py
python scripts/run_optimal_face_audit.py
rm -f results/raw/*.partial.csv

python -m compileall -q src scripts tests
python -m pytest -q
python -m wwprefix.cli certify examples/strict_gap_instance.json --k 1 --exact \
  --output examples/sample_decision.json
python scripts/make_figures.py
(
  cd paper
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex | tee ../logs/final_latex_build.log
  cp main.log ../logs/final_latex_pass.log
)
if [[ "$VERIFY_MODE" == "--pre-seal" ]]; then
  python scripts/verify_release.py --run-tests --pre-seal \
    --json-output release/preseal_verification_receipt.json
else
  python scripts/verify_release.py --run-tests \
    --json-output release/verification_receipt.json
fi

echo "Verification complete ($VERIFY_MODE)"
