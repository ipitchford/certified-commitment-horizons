# Final integrity report: v2.1.2 candidate

**Date:** 8 August 2026  
**Release decision:** PASS for candidate publication  
**Claim boundary:** unrefereed, producer-side certificate-backed candidate

## Replay evidence

- Fresh locked environment: Python 3.11.14; NumPy 2.3.5; SciPy 1.17.0; pandas 2.2.3; Matplotlib 3.10.8; Typer 0.26.3; pytest 9.0.2.
- Full regeneration: `uv run ./run_all.sh --full` completed successfully.
- Tests: 66 passed normally; 66 passed under `python -O` with the expected pytest warning that test-module assertions are disabled.
- Exact certification: 330 agreement rows, all equal to brute-force enumeration; 34 adversarial rows; zero false-infinite classifications; 16 scaling rows through horizon 365.
- Main audit: 512 certificate comparisons from 258 instances; 62 acyclic graph/bijection checks; 96 fixed-competitor checks; 462 rolling-bound cases; no stated theorem violation.
- Exact benchmark: all 30 enumerated instances optimal; 22 of 24 MILP probes resolved correctly and two remained explicitly unresolved at the time limit.
- Data: official UCI archive CSV matched the analysed file byte-for-byte, SHA-256 `adf8dda021beae76b13b1cbb5b3c075d064f03b3353a711c1ddc357c6f89e924`.
- PDF: 30 A4 pages, SHA-256 `59c98c7ea271051b01f5e314bba8d6cd5bab9d50db7469fadb4171971d4666c0`; fonts embedded; no Type 3 fonts or critical LaTeX warnings; representative pages visually inspected.
- Wheel: source bytes match all 12 package modules; SHA-256 `bf61d898d9d90bfd27a159124e14d3ec9eafe958a5518ef1f56c9c63864442dc`.
- Bibliography: all 31 records verified for existence and metadata correspondence using Crossref, DataCite or stable primary/index routes as recorded in `docs/reference_verification_v2.1.2.md`.

## Seven failure-mode audit

| Failure mode | Result | Evidence or remaining boundary |
|---|---|---|
| Content-integrity mismatch | Pass | Versions, wheel/source bytes, JSON, PDF, required files and final manifest are machine-checked. |
| Analytic-to-code translation error | Pass within released checks | Exact small-instance enumeration, graph bijections, witnesses and adversarial regressions agree; no formal proof or independent implementation. |
| Reproducibility failure | Pass producer-side | Full and quick replay pass in the publisher environment; no unaffiliated clean-room reproduction. |
| Overclaiming | Pass | Candidate status and separate assurance dimensions are enforced; no peer-review, formal-verification, field-validation or novelty-certification claim. |
| Citation failure | Pass for metadata; conditional for novelty | All records exist; the directly relevant 1989 EIK full text remains unavailable to this bounded search. |
| Data provenance failure | Pass | Official UCI bytes, DOI, licence and hash now close the earlier acquisition gap; forecasts and costs remain reconstructed. |
| Licence or redistribution failure | Pass | Third-party article full text excluded; CC0/MIT/UCI CC BY terms are separated and attributed. |

## Residual limitations

The checks establish properties of the released rational inputs, programs, witnesses and frozen audit designs. They do not establish independent theorem correctness, proof-assistant soundness, literature priority, external specialist acceptance, field effectiveness, or coverage under distribution shift. The producer-side checker shares Python and integer arithmetic with the package; for horizons above 12 its lower-bound minimality check relies on the internally cross-checked parametric computation.
