# Response to the 18 August 2026 full review

**Reviewed object:** mixed v2.0.0/v2.1.1/v2.2.0 working archive  
**Rebuilt object:** 3.0.0  
**Decision sought:** bounded unrefereed candidate release, not peer-review acceptance or an official REF judgement

## Disposition

The review found a potentially original graph-theoretic core but required a coherent rebuild before release. Version 3.0.0 treats every major point as a release gate.

| Review finding | Resolution in 3.0.0 | Decisive evidence |
|---|---|---|
| Forced period-1 setup misrepresented classical instances with zero first-period demand. | Split the model into `forced_source_graph` and `classical_active_horizon`. Proved a sufficient bridge for `floor[0] > 0` and positive later setup costs. Retained the 101-versus-1 instance as an excluded negative control. | Theorem “Classical active-horizon bridge”; `bridge.py`; 320/320 exact graph/physical matches; semantic regressions. |
| Empty zero-cost setups could create graph-only ties. | Defined them as distinct only in graph mode. Classical mode rejects zero later setup costs, and the bridge proof removes empty later setups from every optimum. | `model.py` validation; `empty_setup_nodes`; 0 empty later optimal setups in 320 audited instances. |
| Archive, source, wheel, manuscript, hashes and receipts represented different versions. | Rebuilt one 3.0.0 tree, wheel, manuscript, claims ledger, provenance, operating-model record, receipt and manifest. Historical records moved under `docs/history/`. | `verify_release.py`; wheel/source byte comparison; manifest check; fresh-extraction replay. |
| Test suite failed because unresolved upper witnesses were incorrectly required to be monotone. | Restricted monotonicity assertions to exactly certified adjacent radii. Unresolved rows check only warranted bracket relations. | Corrected `test_certified_enumeration_brackets_and_monotonicity`; 94 tests pass. |
| `complete` status was semantically ambiguous. | Replaced it with `exact_certified`, `enumeration_completed_with_certified_interval`, explicit refusal and solver-level states. | Schema 3.0, README status table and status regressions. |
| Richter–Vörös evidence was contradictory. | Bound the supplied seven-page source to one SHA-256, recorded pages 67–73, reconciled manuscript/bibliography/ledger/provenance and retained a source-specific negative reading. | `richter_voros_inspection_receipt.md`; `literature_inspection_receipt.json`; synchronised hash. |
| Finite tests were described as theorem verification. | Replaced “machine checked” claims with exact denominators, evidence strata and authority limits. | Manuscript audit table; `claims.json`; verification matrix. |
| The 627-row gate was over-compressed. | Reported five classes separately: 305 exact-match certified, 247 exact rational equalities, a 55-row platform-sensitive search partition, and 20 unresolved pairs. The frozen macOS replay split the 55 rows into 27 floating-search matches with exact witness checks and 28 reference-unresolved. | Raw equivalence CSV and processed summary. |
| Practical and statistical language exceeded the evidence. | Reframed the UCI layer as an interface demonstration; stated reconstructed vintages, stylised costs, overlapping windows and one-step marginal coverage. | Abstract, Sections 11–15, claims C14–C17 and no-evidence impact record. |
| Operating-model metadata was absent. | Added semantic-bridge state, stable IDs, multidimensional assurance, human gates, remaining risks and next-assurance targets. | `release/operating_model.json` and `release/provenance.json`. |
| The theoretical contribution needed a clearer world-leading spine. | Added the optimal-face formulation and proved that every finite nearest boundary has a two-path, single-detour adjacent witness. This compresses the geometry without overstating computational tractability. | Theorem “Single-detour optimal-face witness”; 254/254 applicable finite exact audits, with the other 61 audited cases proven infinite. |

## Additional corrections

- Corrected the variable typo in the fixed-path optimisation.
- Added one-based manuscript/zero-based software indexing guidance.
- Distinguished setup epoch, productive setup, open setup variable, path node and cycle boundary.
- Distinguished empirical/physical demand support, contractual or planning minima and conservative truncation as non-interchangeable operational meanings of the declared floor.
- Added a theorem-dependency table and a glossary.
- Recorded solver roles, exact post-verification, caps, seeds, data provenance and missingness, including the embedded HiGHS 1.8.0 runtime and MIT licence.
- Repaired platform-sensitive optimal-face proposal recovery by trying bounded-denominator rational reconstruction before the exact binary float; every accepted proposal still passes exact witness verification. The audit now closes 254 finite cases reproducibly under ordinary and optimized Python.
- Replaced the circular final-verifier/fresh-replay dependency with explicit pre-seal and final modes, plus an isolated installed-wheel import from outside the source tree.
- Replaced platform-specific verifier assumptions for the equivalence and exact-enumeration benchmarks: the macOS full replay preserved zero warranted disagreements but changed the search partition from 30/25 to 27/28, and two `T=18` enumeration cases timed out during atomic candidate generation before any disjunct was processed.
- Expanded adjacent literature to include forecast/decision horizons, robust cost uncertainty, forecast evolution and lead-time uncertainty, plus the closer interval-demand minimax-regret algorithms of Zhang (2011) and Li–Romero Morales (2013), and Egri et al.’s (2014) domain-specific inverse lot-sizing model.

## Residual open states

The release deliberately leaves the following open:

1. the exact complexity of the demand-induced one-protected-arc core;
2. independent operations-research and mathematical specialist review;
3. a separately authored clean-room implementation;
4. proof-assistant verification;
5. exhaustive prior-art assurance, including second attestation of Richter–Vörös; and
6. prospective operational validation with genuine vintages, actual costs and realised outcomes.

These are visible assurance targets. None is silently promoted to “passed”.
