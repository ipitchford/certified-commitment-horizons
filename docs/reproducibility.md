# Reproducibility protocol

## Frozen software environment

The release lockfile specifies:

- NumPy 2.3.5;
- SciPy 1.17.0, using embedded HiGHS 1.8.0 (MIT licence) for floating search and mixed-integer optimisation;
- pandas 2.2.3;
- Matplotlib 3.10.8;
- Typer 0.26.3; and
- pytest 9.0.2.

Python 3.11 or later is supported. Certified rational results do not depend on floating tolerances; wall times, search proposals and mixed-integer trajectories can vary by platform. The optimal-face search rationally reconstructs bounded-denominator candidates before trying their exact binary encodings, but every accepted boundary still has to pass the exact strong-witness verifier.

The frozen HiGHS version was read from SciPy's embedded runtime constants;
HiGHS has no certification authority in this release. Its LP/MIP outputs are
search proposals or solver-level evidence until the exact rational layer
re-verifies the relevant witness or closes the bound.

All stochastic audit scripts declare their seeds. The main inherited corpus uses seed `20260804`; the semantic-bridge audit uses `2026081801`; the optimal-face audit uses `20260818`.

## Quick replay

```bash
bash run_all.sh --quick
```

The quick replay:

1. compiles source, scripts and tests;
2. runs 94 deterministic tests;
3. regenerates the semantic-bridge and optimal-face exact audits;
4. regenerates the strict-gap decision record;
5. rebuilds figures from frozen rows;
6. rebuilds the manuscript;
7. verifies required files, evidence counts, the wheel, PDF structure and the example certificate; and
8. writes a version-matched verification receipt.

Before a final seal exists, use `bash run_all.sh --quick --pre-seal`. Pre-seal
mode performs every non-circular check but defers the fresh-extraction receipt.
After `scripts/fresh_extract_replay.py` writes that receipt, ordinary final mode
requires and authenticates it.

## Full replay

```bash
bash run_all.sh --full
```

The full replay additionally reruns:

- certificate and graph audits;
- exact certification and adversarial audits;
- exact enumeration and mixed-integer benchmarks;
- calibration simulations;
- rolling-bound tests;
- the illustrative UCI reconstruction;
- the hard stress instance;
- the compact-model equivalence gate; and
- the preregistered scaling benchmark.

The scaling benchmark is machine-dependent and materially longer than the quick replay. Exact candidate generation is atomic in the present enumerator; the closed-form guard should be used to refuse oversized instances before generation.

## Raw-to-claim trace

| Claim layer | Main artefacts |
|---|---|
| Classical semantic bridge | `results/raw/semantic_bridge_audit.csv`, `results/processed/semantic_bridge_audit_summary.json` |
| Optimal-face edge theorem | `results/raw/optimal_face_edge_audit.csv`, `results/processed/optimal_face_edge_audit_summary.json` |
| Frozen certificate and bracket | `certificate_audit.csv`, `graph_bijection_audit.csv`, `fixed_competitor_audit.csv` |
| Exact certification | `exact_certification_audit.csv`, `exact_adversarial_audit.csv`, `exact_scaling_study.csv` |
| Exact and mixed-integer scaling | `exact_benchmark.csv`, `milp_benchmark.csv`, `addendum_benchmark.csv` |
| Compact equivalence | `addendum_equivalence.csv` and its processed summary |
| Calibration | `calibration_trials.csv`, `calibration_scenarios.csv` |
| Rolling theorem | `rolling_audit.csv` |
| Illustrative case | `uci_forecast_vintages.csv`, `uci_certificate_trace.csv`, `uci_policy_evaluation.csv` |

`release/claims.json` links claims to proofs and artefacts. `scripts/verify_release.py` recomputes load-bearing counts from raw rows rather than trusting summaries alone.

## Integrity checks

```bash
python scripts/verify_hashes.py release/SHA256SUMS
PYTHONPATH=src python scripts/verify_release.py --run-tests
```

The clean installed-wheel gate is:

```bash
python scripts/fresh_extract_replay.py --python /path/to/python3.12
```

It copies the clean release to a temporary extraction, creates a new virtual
environment, installs the exact lock and wheel, executes the quick replay with
the pre-seal verifier, then uses `python -I` from an unrelated directory to
prove that `wwprefix` resolves from the new environment's `site-packages`
rather than from `src`. It also exercises the installed CLI, creates a sample
certificate and checks it with the package-independent checker.

After final verification, seal and re-open the archive with:

```bash
python scripts/seal_release.py --output /path/to/certified_commitment_horizons_v3.0.0.zip
```

The sealer regenerates the complete-file manifest, creates a deterministic ZIP
outside the release tree, then verifies both the manifest and final verifier in
a new extraction of that ZIP.

The hash checker rejects missing, altered, duplicate, escaping and unlisted release files. The wheel checker compares every packaged Python source byte with the release source and verifies version 3.0.0. The provenance source snapshot can be recomputed independently:

```bash
python scripts/source_snapshot.py --check-provenance
```

The snapshot hashes sorted `relative-path\0file-SHA-256\n` records for source, tests, scripts, manuscript source, documentation, input examples and environment specifications. It excludes generated outputs, release metadata, external data and external literature, so the provenance record does not create a circular hash.

## Reproduction boundary

This is producer-side replay. It is not independent clean-room reproduction. A stronger assurance rung would add a separately authored implementation, independently generated instances, a proof-assistant formalisation of the semantic bridge and certificate theorem, and a signed third-party replay receipt.
