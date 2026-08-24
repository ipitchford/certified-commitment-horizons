# Response to reviewers — version 2.1.0 (5 August 2026)

> **Historical record.** This document describes the state at its own review round and is not updated. The Richter–Vörös (1989) full text was subsequently obtained and audited on 17–18 August 2026 with no theorem-level collision found; see `docs/literature_audit.md` and manuscript v2.2.0.

**Manuscript:** *Certified Commitment Horizons in Dynamic Lot Sizing*
**Previous version reviewed:** 2.0.0 (4 August 2026); review dated 5 August 2026, recommendation **major revisions**, confidence 0.92.
**This document:** point-by-point response. Section numbers refer to the review; line references to version 2.1.0.

We thank the reviewer for an exceptionally productive report. The false-infinity counterexample in comment 4.1 identified a genuine soundness defect in the released software, and the partial inverse literature in comment 4.2 identified the correct complexity context. Version 2.1.0 restructures the implementation around the first finding rather than patching the instance.

---

## Major comment 4.1 — false numerical certification

**Reviewer's finding.** The released software could return an infinite "safe" and "exact" radius for a valid two-period instance whose exact full-path radius is 1, and consequently labelled a proposed radius of 1.1 `certified_no_destabilisation`. The defect occurs before optimisation (a coefficient of 1e-9 is discarded under a 1e-8 absolute tolerance), so no post-hoc margin can repair it.

**Response: accepted in full; the reviewer's option (1) implemented.** We reproduced the failure exactly as reported, and found it worse than reported: on the same instance the `--exact` escalation *also* returned infinity, because the per-disjunct floating LP fails on the 1e-9/1e9 conditioning. We therefore rebuilt the decision layer rather than the tolerance:

1. **Exact rational certification layer** (`src/wwprefix/exactcert.py`). Every value labelled certified is computed, or a posteriori verified, in exact rational arithmetic with **zero tolerances**. Binary floats convert losslessly to rationals; no tolerance participates in any zero test, saturation decision, breakpoint comparison, tie classification or infinity claim.
2. **No LP in the certified frozen path.** The frozen certificate is computed by binary search over exact breakpoints (the minimal frozen gap is globally non-increasing in the radius) plus a finitely terminating Newton–Dinkelbach parametric shortest-path iteration inside the crossing interval. Interval location costs O(log T) exact shortest paths.
3. **Floating point demoted to search.** HiGHS LPs propose witness demands and dual mixtures; the exact layer re-verifies every proposal before it can influence a certified value. Unverifiable proposals degrade to explicit `unresolved`/diagnostic statuses — never to certification.
4. **Independent analytic confirmation before returning infinity** (as required): infinity is published only as `proven_infinite_no_outside_path` (structural) or `proven_infinite_saturation` (a certified positive residual gap at maximal admissible reduction, re-proved by the independent checker's own dynamic programme). Solver-presumed infinities are never published as proven.
5. **Independent checker** (`scripts/check_certificate.py`): a standalone script that imports nothing from the package and re-verifies decision records from first principles — nominal optimality, witnesses, floors, distances, exact ties, inside-envelope domination, saturation-infinity, triage logic — and, for T ≤ 12, re-derives frozen minimality by complete enumeration.
6. **Regression tests from the counterexample** (`tests/test_exactcert.py`): the reviewer's instance in binary-float and exact-decimal semantics, rescaled equivalents, tiny slope gaps to 1e-15, extreme weights 1e-12–1e12, near-coincident breakpoints (one ulp apart), and huge setup costs with 1e-12 slope gaps.
7. **Decisive acceptance test implemented as an audit invariant:** exact power-of-two rescalings of costs and units (with compensating weights) can never flip finite/infinite or reverse a triage classification; the audit asserts zero flips and fails loudly otherwise.
8. **Decimal semantics.** The input schema now accepts exact numeric strings. The reviewer's counterexample under decimal semantics certifies radius exactly 1 and classifies 1.1 as `certified_destabilising_witness_exists`; under binary-float semantics the exact radius of the instance actually supplied is 43556142965880130871761129887381/43556141734028273151137175044096 ≈ 1.0000000283, with the same classification of 1.1 and `certified_no_destabilisation` for 0.9. Both semantics are documented; the discrepancy is the IEEE-754 representation of the decimal literals, not arithmetic error.
9. **Whole-release re-execution.** All stored audits were re-run after the correction; the new exact-certification audit re-derives every frozen certificate by complete enumeration in rational arithmetic (zero disagreements) and records certified runtimes up to T = 365.

The operational language now matches the guarantee: `certified_*` values are exact-rational and witness-backed; `float_search` values are labelled diagnostic estimates; MILP negatives are labelled `solver_level_only_not_exactly_certified`.

## Major comment 4.2 — partial inverse and partial anti-inverse literature

**Response: accepted.** Section 3 adds the omitted body of work with full-text-verified citations to Gassner (2009, TU Graz Technical Report 2009-15; strong NP-hardness of partial anti-inverse shortest paths under L1 and L∞) and Ley & Merkert (2025, *Journal of Global Optimization* 93:263–298; NP-completeness of partial inverse shortest paths on DAGs with increase-only weights and one required arc). A new comparison table (Table 2) maps the present problem against complete inverse, partial inverse and partial anti-inverse shortest paths across target object, perturbed data, induced dependence, norm, graph structure and known complexity.

The complexity claim is now stated as the reviewer required: the exact complexity of WW-Prefix-Radius-∞ is open **only for the demand-induced, ordered-slope Wagner–Whitin restriction**; the generic arc-weight analogues are already hard, and the polynomial certificate bounds rather than solves the exact partial anti-inverse quantity. Section 16's open-problem paragraph was rewritten accordingly. We do not currently have a reduction in either direction and say so.

The Richter–Vörös (1989) full text remains uninspected — and the position is now precise: no lawful digital copy appears to exist (the quoted 10.5555 identifier is the DOI test prefix on an ACM index stub; the journal's 1987–94 run was never digitised; OpenAlex lists no repository copy). Bibliographic details are triangulated across zbMATH (Zbl 0672.90033), dblp and the ACM Guide; the zbMATH review describes fixed-solution stability regions with the joint cost–demand case a two-parameter region, consistent with scalar parametrisations and containing no indication of a prefix-class object. A concrete acquisition dossier (author offprint via J. Vörös at Pécs; British Library On Demand; Subito) ships in `docs/literature_audit.md`, and the accessible same-programme EJOR instalments are now cited. The priority claim remains explicitly conditional until the print text is read.

## Major comment 4.3 — estimand separation

**Response: accepted.** Section 11 now opens by defining the three objects F_old, F_new = F_old + E_{n+1}, and D_real, with a table (Table: "Which result controls which arrow") assigning each arrow to its controlling theorem and the nature of its guarantee. Corollary 11.2 is retitled "One-decision calibrated commitment **against the next forecast revision**" and restated in terms of F_new; the phrase "next demand" is gone. A closing paragraph states explicitly that a commitment surviving every forecast revision can still be costly if the forecasts are poor, and that this risk is priced only in the worst-case pathwise sense by the rolling theorem. The section title and the paper's subtitle now say "one-step calibration of forecast revisions". The abstract states that no result calibrates realised-demand coverage, realised structural regret, service outcomes, or repeated rolling deployment.

The UCI case remains, as the reviewer allowed, an interface demonstration: the text now states prominently that the 12 evaluation windows overlap and are not independent replicates, and that regret is in stylised cost units parameterised in pounds.

## Major comment 4.4 — computational verification vs. operational claims

**Response: accepted; new audit stratum added.** The release adds `scripts/run_exact_certification_audit.py` with three pre-specified strata:

- **Agreement:** every frozen certificate re-derived by complete enumeration in exact arithmetic (equality required, zero tolerance), floating-estimate error recorded, bracket/enumeration containment checked, certified interval widths published.
- **Adversarial:** the review counterexample in both semantics, tiny slope gaps (1e-15…1e-3), extreme weights (1e-12…1e12), near-coincident breakpoints, huge-K/small-slope instances, and the power-of-two rescaling invariance sweep with a hard zero-flip assertion. These families were chosen to lie **outside** the previous generators' numerical range and inside the documented input domain — precisely the gap the reviewer identified.
- **Scaling:** certified bracket runtimes at T = 50, 100, 200, 365 with shortest-path evaluation counts and Newton iteration counts. Candidate-generation and disjunct-solve timings remain separated in the enumeration benchmarks.

Monte Carlo coverage estimates now carry Wilson intervals in the text (comment: minor 10). The infinity taxonomy distinguishes proven-structural, proven-saturation, and solver-presumed states (minor 12). The independently written checker requested in 4.4 is `scripts/check_certificate.py`, described above; its scope and its limits (T > 12 minimality relies on the package's internally cross-checked computation) are stated in the paper rather than implied away.

We report honestly that exact escalation remains worst-case exponential and that the certified frozen bracket at T = 365 takes minutes, not seconds, in the current pure-Python rational implementation; both facts are in the audit section with measured numbers.

## Minor comments

1. **Prop 2.1 wording** — fixed: the arc's physical cost is stated as its reduced cost plus its *local* carrying term, with the path-independent sum assembled only along complete paths.
2. **No-outside-path case** — Theorem (bracket) now assumes O_k ≠ ∅ and finite frozen radius explicitly, deferring the other cases to the positive-radius criterion.
3. **Notation collision** — suffix potentials renamed π → u throughout Section 10 and the MILP.
4. **Boxed formal-vs-numerical statement** — added at the head of the new "Exact rational implementation and machine-checked certificates" subsection in Section 7.
5. **Executable permission** — `run_all.sh` ships with the executable bit set, and the README documents `bash run_all.sh --quick` as the portable invocation.
6. **Data provenance** — the acquisition-manifest gap is retained as a disclosed limitation; the release still hash-locks the analysed bytes and instructs clean reproducers to fetch from the DOI-backed UCI record. (No new acquisition was performed in this cycle; the gap remains flagged rather than silently closed.)
7. **Four-period fence** — added to Table (case) with its committed-length difference and identical regret explained.
8. **Currency notation** — all case-study monetary quantities are labelled "stylised cost units parameterised in pounds".
9. **Overlapping windows** — stated prominently in the case section and table caption.
10. **Monte Carlo intervals** — Wilson 95% intervals added for all coverage estimates in the audit table.
11. **Exact benchmark timing** — candidate-generation and disjunct-solve times remain separated; the certified enumeration additionally reports per-disjunct certification counts.
12. **Infinity status** — the published taxonomy distinguishes: proven infinite (no outside path), proven infinite (saturation, with certified residual gap), not infinite, and solver-presumed states that are never published as proven.
13. **Title** — subtitle now reads "One-Step Calibration of Forecast Revisions".
14. **Conclusion** — "bounded operational method" replaced by "bounded decision architecture … whose certified outputs are computed in exact rational arithmetic and shipped with independently checkable witnesses", with operational reach explicitly deferred to field evidence.
15. **Reference hygiene** — Richter & Vörös accents corrected (ö, not ő); the entry retains its abstract-only inspection note; new entries added for Gassner (2009), Ley & Merkert (2025), Cheung–Gleixner–Steffy (2017) and Eifler–Gleixner (2021).

## Additional assurance beyond the review's requests

A second, independent cross-model adversarial review of the *repair itself* was obtained from GPT-5.6 Sol (a different vendor's model), prompted to refute the eight soundness claims underlying the exact layer. It found no refutation of any certified classification as implemented, and produced four caveats (weight/finiteness preconditions; a flat-zero-segment edge case at breakpoints; mixture ties must not be promoted to strong witnesses; scoping of binary-performed rescaling invariance), each of which was verified against the code and locked with regression tests or claim-language scoping. Full record: `docs/adversarial_review_sol_v2.1.0.md`.

## What we did not do, and why

- **No field dataset was added.** Following the reviewer's own guidance, the empirical claims were narrowed instead; the UCI case is explicitly an interface demonstration.
- **No proof-assistant verification.** The trusted base is now the ~400-line exact layer plus the independent checker, which is a large reduction from "all floating-point code paths", but it is not formal verification and the paper says so.
- **Richter–Vörös full text** — established to have no lawful digital copy anywhere; print acquisition routes documented (author offprint, BL On Demand, Subito); the novelty claim remains conditional and the limitation prominent.
- **No exact MILP.** Mixed-integer "no" answers remain solver-level; the certified route to a "no" is the exact bracket or certified enumeration. The labelling now makes this impossible to misread.
