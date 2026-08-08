# Reproducibility protocol

## Frozen environment

The producer run used Python 3.13.5 on Linux x86-64 with NumPy 2.3.5, SciPy 1.17.0, pandas 2.2.3, Matplotlib 3.10.8 and pytest 9.0.2. `requirements-lock.txt` records these versions. The package declares Python 3.11 or later; exact numerical output can vary slightly across solver and platform versions.

All stochastic scripts use base seed `20260804`. Each raw row records its stratum, instance identifiers and solver status. Conditioned adversarial strata are labelled and are never interpreted as prevalence samples.

The quick replay exports `SOURCE_DATE_EPOCH=1785801600` (4 August 2026 00:00 UTC), `FORCE_SOURCE_DATE=1` and `TZ=UTC`. The manuscript and Matplotlib PDF figures therefore have stable embedded dates and were byte-identical across two consecutive rebuilds. The example decision omits wall-clock fields unless `--include-timing` is requested. Raw benchmark timing remains intentionally machine-dependent.

## Quick verification

```bash
bash run_all.sh --quick
```

The command:

1. compiles all Python files;
2. runs the deterministic tests;
3. regenerates `examples/sample_decision.json`;
4. regenerates publication figures from frozen raw data;
5. rebuilds `paper/main.pdf` with `latexmk`;
6. checks row counts, key numerical identities, hashes, PDF structure, fonts and LaTeX warnings.

## Full replay

```bash
./run_all.sh --full
```

This reruns, in order:

- `scripts/run_certificate_audit.py`;
- `scripts/run_exact_certification_audit.py`;
- `scripts/run_exact_benchmark.py`;
- `scripts/run_calibration_audit.py`;
- `scripts/run_rolling_audit.py`;
- `scripts/run_uci_case.py`;
- `scripts/run_stress_instance.py`;
- `scripts/make_figures.py`;
- tests, manuscript compilation and release verification.

Exact candidate generation is atomic in the current implementation and can exceed a nominal time limit before the first inverse disjunct begins. The hard T=18 example records this limitation explicitly.

## Raw-to-claim trace

- Certificate and bracket claims: `results/raw/certificate_audit.csv`, `graph_bijection_audit.csv`, `fixed_competitor_audit.csv`.
- Exact scaling: `exact_benchmark.csv`, `milp_benchmark.csv`, `results/processed/exact_stress_case.json`.
- Exact certification layer: `exact_certification_audit.csv`, `exact_adversarial_audit.csv`, `exact_scaling_study.csv`, `results/processed/exact_certification_summary.json`.
- Calibration: `calibration_trials.csv`, `calibration_scenarios.csv`.
- Rolling theorem: `rolling_audit.csv`.
- Illustrative data case: `uci_forecast_vintages.csv`, `uci_certificate_trace.csv`, `uci_policy_evaluation.csv`.
- Paper summaries: `results/processed/*.json` and `*.csv`.

`release/claims.json` links each paper-level claim to proof sections and computational artefacts. `scripts/verify_release.py` recomputes key counts and checks rather than trusting the summaries alone.

The packaged archive also contains `release/SHA256SUMS`. `scripts/verify_hashes.py` checks every manifest entry, rejects duplicate or escaping paths, and reports files in the clean release tree that are not covered by the manifest.

## Numerical boundary

Certified values are exact-rational (`wwprefix.exactcert`); SciPy/HiGHS floating-point solves appear only as search proposals and diagnostics, and every certified witness is re-verified in the original cost equations in exact arithmetic. `scripts/check_certificate.py` re-verifies decision records without importing the package. It is a separately implemented producer-side checker, not independent reproduction. These measures are much stronger than the previous safe-margin scheme but still do not constitute proof-assistant verification.

## Independence boundary

All code, tests, audits and this verification protocol were produced in one workflow. No independent clean-room replay has been completed. A high-assurance release should add a separately authored implementation, independently generated instances and a signed reproduction report.
