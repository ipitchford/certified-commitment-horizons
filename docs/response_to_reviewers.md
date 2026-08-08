# Response to the v1.0.0 peer review

**Revised version:** 2.0.0, 4 August 2026  
**Decision on review:** all eight major concerns were acted on; two remain bounded rather than eliminated: full-text novelty comparison with Richter and Vörös (1989), and realistic-scale exact computation.

## Major concerns

| No. | Review concern | Revision made | Location | Status after revision |
|---:|---|---|---|---|
| 1 | Direct 1989 antecedent omitted; novelty unsecured. | Added a corpus and theorem-level contribution boundary. The paper now identifies demand-vector stability, fixed-solution sensitivity and generic stability radii as prior art; treats the full-path endpoint as adjacent to the fixed-solution literature; and restricts candidate novelty to the moving prefix face, floor-aware polynomial lower certificate and layered integration. The search record and access limit are preserved. | Manuscript Section 3 and Table 1; `docs/literature_audit.md`; `literature/`. | **Bounded, unresolved.** Indexed abstract evidence was inspected, but the 1989 full text was not obtained. The manuscript states that originality remains conditional. |
| 2 | Claimed code and raw results were not supplied. | Added installable Python package, CLI, raw row-level outputs, processed summaries, locked dependencies, deterministic tests, replay scripts, verification script, claim ledger, provenance, hashes and release notes. Failures, infinities and unresolved solver statuses remain in the rows. | `src/`, `tests/`, `scripts/`, `results/`, `release/`, `run_all.sh`, `requirements-lock.txt`. | **Addressed producer-side.** No independent clean-room reproduction has occurred, and the release says so. |
| 3 | Charnes-Cooper proof had a positivity gap and omitted graph/edge cases. | Formally defined the prefix-deviation directed acyclic graph, proved path bijection, added a no-nonnegative-circulation lemma to force `tau>0`, added a path-flow decomposition argument, and stated handling of repeated/zero breakpoints, endpoint ties, zero denominators, infinite radii, bit complexity and witness recovery. | Manuscript Sections 6-7 and Appendix A; `src/wwprefix/graph.py`; `src/wwprefix/certificate.py`; graph and certificate audits. | **Addressed.** Formal proof-assistant verification remains absent. |
| 4 | “Operationally complete” exceeded model scope and evidence. | Replaced the claim with “methodologically integrated within the stated Wagner-Whitin model”; made the protocol bounded and three-way; added explicit scope/failure modes; labelled the UCI analysis illustrative, with observed demand but reconstructed forecast vintages and stylised costs. | Abstract, Sections 14-17, Table 4; `docs/scope_and_limitations.md`; `docs/data_provenance.md`. | **Addressed by narrowing.** No field validation or demonstrated service/financial impact is claimed. |
| 5 | Conformal guarantee needed admissible-domain and sequential precision. | Defined floor-aware scores that assign infinity to inadmissible revisions; stated probability as one-step and marginal over calibration data and the next revision; denied conditional, simultaneous and time-uniform interpretations; added a prespecified finite Bonferroni family experiment and scale-shift negative controls. | Manuscript Section 11; `src/wwprefix/calibration.py`; calibration raw and summary files. | **Addressed within one-step scope.** Adaptive or long-run deployment needs a separate procedure and theorem. |
| 6 | Practical exact escalation was untested beyond toy horizons. | Added exact-disjunction benchmarks through T=18, absolute path counts, candidate-generation and disjunct timings, 24 MILP probes with statuses/gaps/nodes, a recorded hard instance, and a polynomial lower-upper bracket that returns an unresolved state when exact closure fails. | Manuscript Sections 8, 10, 13 and Figure 1(b); exact raw files; `examples/benchmark_hard_instance_id26_T18.json`; `results/processed/exact_stress_case.json`. | **Bounded, unresolved.** Exact candidate generation remains exponential and can dominate runtime. The protocol never treats timeout as safe. |
| 7 | Certificate depended on an arbitrarily selected nominal optimum. | Added optimal-arc graph analysis, count of nominal optima, longest common optimal prefix, positive-radius criterion, deterministic tie-break and CLI fields reporting whether the protected prefix is common to all nominal optima. | Manuscript Section 4; `src/wwprefix/model.py`; CLI output and tests. | **Addressed for auditability.** A user may still select a different optimum under a disclosed secondary criterion; the resulting conditional radius must be labelled. |
| 8 | Rolling theorem lacked domain, information, quantity and infinity semantics. | Restated the theorem for admissible demand, separated finite and infinite radius cases, proved zero residual on the closed ball, handled `rho=0`, used suffix-specific weighted norms, and specified structural setup decisions with uncapacitated quantity recourse and cycle-boundary replanning. | Manuscript Section 12; `src/wwprefix/rolling.py`; 462-case rolling audit. | **Addressed within structural scope.** Fixed quantities, service outcomes and capacity reservations remain outside the theorem. |

## Minor comments

| Review point | Revision |
|---|---|
| NP promise ambiguity | Proposition 2.3 now states that nominal optimality can be a promise or checked by shortest path. |
| “Asymmetric” weighted norm wording | Removed the unsupported claim; weights are directionally symmetric. |
| Graph definition and indexing | Added explicit vertex/arc sets and public/internal index documentation. |
| Breakpoints, zero denominators and infinity | Added theorem and implementation treatment. |
| Notation for lower versus exact radius | Frozen lower radius is now written `rho^fr`, with lower/upper bracket symbols separated. |
| Formal versus numerical certificate | The paper distinguishes exact rational theorems, floating-point optima and safe one-sided numerical lower radii. |
| Zero demand | Floors and zero breakpoint handling are explicit; positive floors are used in the strict example. |
| Computational denominators and exclusions | Tables and raw files report denominators, strata, failures, infinities, timeouts and status codes. |
| Calibration sample sizes | Added 20,000 trial counts, n=49, finite-family size and Wilson intervals. |
| Runtime reporting | Added raw wall time, model-reported time, quantiles, paths, nodes and gaps. |
| Rolling raw scale | Added realised residual, bound, slack and bound-to-residual summaries. |
| Weight selection and units | Added input contract and an illustrative scale estimated on prespecified windows. |
| Witness language | CLI returns public paths, revised demand, verified differences and solver status. |
| Release citation | Added `CITATION.cff`, licence and versioned metadata; permanent DOI remains to be assigned at deposit. |
| References | Added Richter-Vörös, Richter-Weber and sequential/beyond-exchangeability conformal sources. |
| Assumptions/failure modes | Added Table 4 and `docs/scope_and_limitations.md`. |

## New evidence added in v2.0.0

- 512 frozen-certificate comparisons from 258 generated instances, with maximum stored absolute error zero against exhaustive enumeration.
- 62 exhaustive graph-bijection checks and 96 compact inverse-LP checks.
- 512 exact small-horizon bracket-containment checks; 153 of 254 positive partial-prefix cases closed polynomially.
- 30 exact-disjunction benchmark instances and 24 fixed-radius MILP probes, including two disclosed unresolved time-limit results.
- 85,000 calibration trial rows across exchangeable, shifted, floor-aware and finite-family scenarios.
- 462 rolling-bound cases, including zero-radius and infinite-radius edge cases.
- An end-to-end illustrative case on 60 observed demand values, with reconstructed vintages, stylised costs and explicit provenance limits.

## Claims deliberately not made

Version 2.0.0 does not claim absolute novelty, unrestricted polynomial-time exact solution, independent reproduction, formal verification, field validation, conditional conformal coverage, time-uniform control, or protection of literal order quantities.
