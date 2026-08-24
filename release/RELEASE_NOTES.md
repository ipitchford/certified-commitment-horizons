# Release notes: 3.0.0

**Date:** 24 August 2026  
**Role:** unrefereed theoretical–computational candidate  
**Decision:** coherent rebuild after major review; producer replay required before distribution

## Research changes

1. **Separated graph semantics from classical lot sizing.** Every instance declares `forced_source_graph` or `classical_active_horizon`. The manuscript now proves a sufficient graph-to-classical bridge under a positive first-period demand floor and strictly positive later setup costs. The leading-zero counterexample is retained as a negative control: the graph costs 101, the ordinary physical model costs 1, and classical mode rejects it.
2. **Defined empty-setup semantics.** Graph paths that differ through zero-quantity, zero-cost setup nodes remain distinct only in graph mode. Classical mode excludes encoding-only optimal ties through its bridge conditions.
3. **Corrected the monotonicity test.** The theorem concerns true strong radii. The suite now tests monotonicity only between adjacent exactly certified radii and checks only lower-bound ≤ feasible-upper consistency for unresolved intervals.
4. **Added a single-detour optimal-face theorem.** Every finite nearest prefix-loss boundary contains adjacent co-optimal retaining and leaving paths that differ on one divergence–remergence interval. A new exact audit found witnesses in all 254 finite boundaries from 315 prefix cases; the other 61 cases were proven infinite.
5. **Strengthened the semantic audit.** An implementation independent of the path solver enumerates physical setup patterns. It matches graph optima and optimal setup sets in 320/320 active-horizon cases and finds no empty later optimal setup.
6. **Retained the complexity frontier.** The exact demand-induced one-protected-arc problem remains open. The released disjunction is exponential, but the release does not infer NP-hardness from the algorithm.
7. **Expanded the adjacent-literature boundary.** Forecast-horizon, robust-cost, forecast-evolution and lead-time-uncertainty work are positioned as distinct comparators. Zhang (2011) and Li–Romero Morales (2013) are now treated as the closest polynomial interval-demand minimax-regret comparators, and Egri et al. (2014) as the direct inverse-lot-sizing precedent. Their quantifier order, decision variables and objectives are distinguished from the nearest protected-prefix crossing. The Richter–Vörös conclusion remains source-specific and conditional.

## Assurance changes

- Replaced ambiguous `complete` statuses with exact, interval, refusal and solver-level states.
- Stratified the 627-row equivalence corpus: 305 exact-match certified, 247 exact rational decomposition equalities, a 55-row platform-sensitive floating-search/reference-unresolved partition, and 20 unresolved pairs. In the frozen macOS replay the search partition was 27 exact-witness matches and 28 reference-unresolved.
- Replaced theorem-level “machine checked” language with finite-audit descriptions and explicit denominators.
- Added `release/operating_model.json` with the semantic-bridge state, multidimensional assurance, human gates, remaining risks, next targets and a no-evidence impact record.
- Added stable `work_id` and `attempt_id`, a version-matched claims ledger, provenance, inspection receipt, verification receipt and manifest.
- Added a direct response to the full review at `docs/response_to_full_review_v3.0.0.md`.
- Added `release/prior_art_corpus.json`, including access states, hashes, comparison dimensions, missingness and the bounded novelty conclusion.
- Rebuilt the wheel from the exact source and added byte-for-byte source/wheel verification.
- Added PDF font, warning, text-extraction and page-image preflight.
- Made floating-search proposal recovery portable by rationally reconstructing bounded-denominator candidates before exact verification; no floating proposal is accepted without an exact strong-witness check.
- Added a non-circular pre-seal/final verification protocol and an isolated installed-wheel replay in a newly created environment.
- Normalised the standing scholarly creator to `Anonymous`, applied the CC0-for-original-research/MIT-for-code rights split, and removed third-party literature PDFs and derived text extracts from the redistributable package while retaining citations, source URLs and hashes.

## Evidence denominators

| Gate | Result |
|---|---|
| Semantic bridge | 320/320 exact matches; 0 empty later optimal setups |
| Optimal-face witness | 254/254 finite boundaries; 61 proven infinite; 0 failures |
| Frozen certificate | 512 rows; maximum stored exact discrepancy 0 |
| Polynomial bracket | 411 exact closures; 101 certified intervals |
| Exact certification | 330/330 frozen matches; 305 exact strong radii; 25 intervals |
| Compact equivalence | 627 stratified rows; 0 warranted disagreements |
| Exact enumeration benchmark | 28/30 optimal; 2 atomic candidate-generation timeouts before any disjunct; 0 solver failures |
| Mixed-integer decision | 22 resolved/correct; 2 time-limit unresolved |
| Rolling theorem | 462 cases; 0 violations; 254/254 dead-zone residuals zero |
| Deterministic tests | 94 passed |

## Claim ceiling

Release 3.0.0 supports exact graph-theoretic results and a conditional classical active-horizon corollary. It does not claim independent replication, proof-assistant verification, exhaustive novelty, polynomial-time exact solution, industrial benefit, adaptive conformal validity, or an official REF grade.

## Historical states

Earlier review and response records are preserved under `docs/history/`. Their version numbers and assurance states describe their own snapshots and do not override this release’s metadata.
