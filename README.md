# Certified Commitment Horizons in Dynamic Lot Sizing

**Release:** 2.1.2, 8 August 2026
**Status:** unrefereed candidate research release
**Model:** deterministic, single-item, uncapacitated Wagner-Whitin lot sizing
**Licence:** CC0 1.0 for original manuscript, figures, documentation and release metadata; MIT for source code; UCI data remains CC BY 4.0. See `LICENSES.md` and `THIRD_PARTY_NOTICES.md`.

**What changed in 2.1.2.** Release-assurance correction responding to the
5 August final Evidence Press review. The invalid monotonicity requirement on
unresolved upper witnesses was removed; the parametric exact routine now uses
the finite source-to-sink path count instead of an arbitrary iteration cap;
version and assurance metadata were synchronised; third-party literature files
were removed from the public tree; UCI provenance was restored to the exact
official download; and deterministic rights, metadata and clean-tree checks
were added. No theorem statement or numerical result was strengthened.

**What changed in 2.1.1.** Bibliographic correction release: the Richter–Vörös
(1989) entry no longer prints the non-resolving DOI test-prefix identifier and now
carries the verified EIK citation (ISSN 0863-0593, Zbl 0672.90033); the novelty
boundary is restated on triangulated zbMATH/dblp/ACM evidence with a documented
print-acquisition dossier; the accessible same-programme EJOR instalments are cited.
No code changes.

**What changed in 2.1.0.** The 2.0.0 floating-point implementation could return a
false infinite "safe" radius on a valid instance (peer review, comment 4.1). Version
2.1.0 computes every certified value in exact rational arithmetic with zero
tolerances (`src/wwprefix/exactcert.py`), demotes floating point to a search
heuristic whose proposals are exactly re-verified, ships an independent certificate
checker (`scripts/check_certificate.py`), accepts exact decimal inputs as numeric
strings, and adds regression, adversarial, rescaling-invariance and scaling audits.
See `docs/response_to_reviewers_v2.1.0.md` and `docs/PRACTITIONER_GUIDE.md`.

## Decision object

The package studies `WW-Prefix-Radius-infinity`: how far a current demand forecast must move, in a weighted infinity norm and subject to demand floors, before an optimal lot-sizing path may leave a protected prefix of replenishment cycles.

For nominal demand `d_hat`, coordinate weights `w > 0`, floors `ell`, and the first `k` arcs of a selected nominal optimum, the strong radius is the distance to the nearest admissible demand vector at which some optimal path lies outside that prefix class. The implementation returns a **certified decision record**, with every certified value computed or a posteriori verified in exact rational arithmetic:

- an exact frozen-comparator lower certificate (breakpoint binary search plus
  finitely terminating parametric shortest paths; no LP, no tolerances);
- an exactly verified upper witness when one exists (floating-point LPs propose,
  the exact layer verifies);
- exact closure when the witnesses or bounds coincide as rationals;
- proven infinity statuses (structural or saturation, with a certified residual gap);
- otherwise an explicit unresolved state and certified exact escalation.

The certificate protects **setup epochs and cycle boundaries**, not literal order quantities. It assumes uncapacitated quantity recourse within each retained cycle.

## Strongest supported contribution

Within the stated Wagner-Whitin model, the release provides:

1. reduced affine arc costs `K_i + q_i (D_j - D_i)` with ordered slopes;
2. an exact floor-aware distance to a fixed path tie;
3. a formally specified prefix-deviation directed acyclic graph;
4. a polynomial frozen-comparator certificate, including zero/repeated breakpoints, zero denominators, infinite radii and witness recovery;
5. a polynomial lower-upper bracket and exact closure conditions;
6. exact fixed-competitor inverse linear programmes, a finite disjunction, and a fixed-radius mixed-integer model;
7. a floor-aware one-step marginal conformal rule and a prespecified finite-family Bonferroni extension;
8. a deterministic rolling structural-loss bound with a certified dead zone.

The exact complexity classification of the demand-induced restriction remains open (generic partial inverse analogues are NP-hard). A full-text theorem-level comparison with Richter and Vörös (1989) also remains unresolved: the bounded search documented for this release located no lawful digital full text (the journal's 1987–94 run is not known to have been digitised and the quoted ACM identifier is a DOI test-prefix stub); triangulated review evidence indicates a fixed-solution stability-region antecedent, and a print-acquisition dossier ships in `docs/literature_audit.md`. These limits are part of the contribution boundary, not hidden caveats.

## Quick start

Requirements: Python 3.11 or later and a LaTeX installation with `latexmk` for rebuilding the paper.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
python -m pip install -e . --no-build-isolation

wwprefix certify examples/strict_gap_instance.json --k 1 --exact \
  --output examples/sample_decision.json
```

The expected strict-gap result is:

- certified frozen lower radius: exactly `3/2`;
- certified exact strong radius (escalation): exactly `2/1`;
- public paths use one-based nodes, so `[1, 2, 4]` denotes the internal path `(0, 1, 3)`.

Certified values appear as `{"float": ..., "exact": "p/q"}` pairs. Floating-point
diagnostics appear only under `float_search` and never influence a certified
classification. Radius options are parsed exactly: `--proposed-radius "1.1"` means
the decimal 11/10, not its binary approximation. Instance arrays may contain numeric
strings for exact decimal semantics.

Fixed-radius decision:

```bash
wwprefix decide examples/strict_gap_instance.json --k 1 --radius 1.75
wwprefix decide examples/strict_gap_instance.json --k 1 --radius 2.00
```

The certified bracket decides whenever it can; the MILP runs only for unresolved
radii and its results are labelled `solver_level_only_not_exactly_certified`
(affirmative witnesses are re-verified exactly and upgraded when they check out).
The interface never recodes an unresolved result as safe.

Verify any decision record independently of the package:

```bash
python scripts/check_certificate.py examples/sample_decision.json examples/strict_gap_instance.json
```

## One-command verification

```bash
bash run_all.sh --quick
```

(The executable bit is set in the release, so `./run_all.sh --quick` also works;
the `bash` form is robust to archive tools that drop permissions.)

This compiles the Python sources, runs the test suite, regenerates the example decision and figures, rebuilds the manuscript, and checks the frozen artefacts. The complete computational replay is:

```bash
./run_all.sh --full
```

`--full` reruns all synthetic audits, exact benchmarks, calibration simulations, rolling tests and the illustrative UCI case before performing the quick verification. Runtime is machine-dependent; exact candidate generation grows rapidly.

After downloading a packaged release, verify every frozen file against the signed-off manifest:

```bash
python scripts/verify_hashes.py release/SHA256SUMS
PYTHONPATH=src python scripts/verify_release.py --run-tests
```

The hash checker rejects missing, altered and duplicate manifest entries. The release verifier can use the archived final LaTeX build log, so it does not require auxiliary build files.

## Input schema

See [`docs/input_schema.md`](docs/input_schema.md). A minimal input has arrays `K`, `q`, `demand`, `floor` and `weights`, all of equal length. `q` must be non-increasing, demand must lie above the floor, and weights must be strictly positive. A supplied nominal path must be nominally optimal.

## Evidence and audit boundary

The release contains raw rows rather than success-only summaries:

- 512 frozen-certificate comparisons from 258 generated instances;
- 62 exhaustive graph-bijection checks;
- 96 compact-versus-explicit fixed-competitor linear-programme checks;
- 512 exact small-horizon bracket-containment checks;
- 30 exact-disjunction benchmark instances;
- 24 fixed-radius mixed-integer probes, including two unresolved time-limit cases;
- 85,000 calibration trial rows across five scenarios;
- 462 rolling-bound cases;
- 31 reconstructed forecast-vintage windows from a 60-observation public demand dataset.

These are **producer-side checks** created in the same workflow as the code. They establish internal consistency and boundary behaviour, not independent replication or industrial effectiveness. The UCI case uses real observed demand but reconstructed forecasts and stylised costs; it is not field validation.

## Repository map

- `paper/` — LaTeX source, bibliography, final PDF and publication figures.
- `src/wwprefix/` — model, graph, certificate, bracket, exact, calibration, rolling and CLI code.
- `tests/` — deterministic unit and integration tests.
- `scripts/` — frozen audit, benchmark, figure and verification scripts.
- `results/raw/` — row-level computational outputs, including failures and unresolved statuses.
- `results/processed/` — summaries used in the paper.
- `data/external/` — frozen illustrative demand data.
- `docs/` — literature boundary, response to review, provenance, schemas and limitations.
- `release/` — claim ledger, provenance record, verification receipt and hashes.
- `archive/v1.0.0/` — pre-revision manuscript snapshot.

## Assurance status

The mathematical claims were revised after internal and cross-model adversarial review and checked by producer-side tests, exact small-instance oracles and replayable scripts. Every value labelled certified is computed or re-verified in exact rational arithmetic with zero tolerances. A separately implemented producer-side checker re-verifies decision records without importing the package; for horizons above 12 it still relies on the package's internally cross-checked parametric result for frozen-minimality. The release has **not** received journal peer review, independent clean-room reproduction, proof-assistant verification, or field validation.

## Citation

Use `CITATION.cff`. The GitHub release and archived DOI identify the public candidate package; the exact release ZIP is bound by `release/SHA256SUMS` and its published checksum.
