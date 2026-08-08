# Release notes: v2.1.2 candidate

**Date:** 8 August 2026
**Status:** unrefereed candidate; release-assurance correction.

- Corrected the test contract: monotonicity is asserted for certified exact strong radii, not for independently selected unresolved upper witnesses.
- Replaced the arbitrary parametric-Newton iteration cap with the exact finite number of source-to-sink paths in the deviation DAG. This is a finite, potentially exponential implementation bound; no polynomial iteration claim is made.
- Synchronised version, date, title, claim-ledger and assurance metadata.
- Replaced “adversarial peer review” and “independent checker” language with accurate internal/cross-model review and separately implemented producer-side checker language.
- Removed third-party article PDFs, extracted text, caches and bytecode from the public package; retained citations, source URLs and hashes.
- Verified the included UCI CSV byte-for-byte against the official UCI archive and recorded its CC BY 4.0 attribution.
- Added split licensing, third-party notices, an AI index, deterministic release-contract checks and this response to the final review.

# Release notes: v2.1.1

**Date:** 5 August 2026
**Status:** bibliographic correction release; no code changes.

- Richter–Vörös (1989): removed the non-resolving 10.5555 identifier (the DOI system's test prefix on an ACM Guide index stub) and replaced it with the verified citation (*Journal of Information Processing and Cybernetics: EIK*, 25(3), 67–73; Akademie-Verlag; ISSN 0863-0593; Zbl 0672.90033), triangulated across zbMATH, dblp and the ACM Guide.
- Established and documented that no lawful digital copy of the paper appears to exist (the journal's 1987–94 English-title run was never digitised; OpenAlex records no repository copy). A print-acquisition dossier (author offprint via J. Vörös, University of Pécs; British Library On Demand; Subito) ships in `docs/literature_audit.md`.
- Sharpened the novelty boundary using the zbMATH review: the 1989 paper derives fixed-solution stability regions, with the joint cost–demand case a two-parameter region — consistent with scalar parametrisations, not a simultaneous weighted demand ball with floors; theorem-level exclusion still requires the print text.
- Cited the accessible same-programme instalments: Richter (1987), *EJOR 31*, 61–65; Richter & Vörös (1989), *EJOR 41*(2), 169–173 (metadata verified, full text not inspected).
- Updated the assurance box, corpus-boundary section, novelty table, scope section, claims ledger (C11) and response-to-reviewers accordingly.

# Release notes: v2.1.0

**Date:** 5 August 2026
**Status:** revised preprint and producer-side reproducibility release, responding to the 5 August 2026 machine peer review (major revisions).

## Main changes from v2.0.0

- **Exact rational certification layer** (`src/wwprefix/exactcert.py`): every certified value is computed, or a posteriori verified, in exact rational arithmetic with zero tolerances. The frozen certificate is computed by breakpoint binary search plus finitely terminating parametric shortest paths — no LP and no tolerance in the certified path. This repairs the review's decisive finding (comment 4.1): the v2.0.0 implementation could certify a destabilisable radius as safe by discarding a 1e-9 coefficient under a 1e-8 tolerance.
- **Floating point demoted to search.** HiGHS LPs propose witnesses and dual mixtures; the exact layer re-verifies before use. Float outputs appear only under a `float_search` key labelled diagnostic.
- **Proven-infinity taxonomy:** `proven_infinite_no_outside_path` and `proven_infinite_saturation` (with a certified residual gap); solver-presumed infinities are never published as proven.
- **Certified escalation:** exact pairwise lower bounds order and prune the finite disjunction; per-disjunct certificates (binding-comparator pairwise radii, dual mixtures, separating-mixture probes for infeasible disjuncts) return point-exact radii or certified intervals with published width.
- **Independent checker** `scripts/check_certificate.py`: re-verifies decision records from first principles without importing the package; wired into tests and the release verifier.
- **Exact decimal inputs:** instance arrays and radius options accept numeric strings parsed as exact decimals or `p/q` rationals.
- **New audits:** `run_exact_certification_audit.py` with agreement (complete-enumeration equality), adversarial (review counterexample in both semantics, tiny slope gaps to 1e-15, extreme weights, near-coincident breakpoints, huge-K instances) and rescaling-invariance (hard zero-flip assertion) strata, plus certified runtimes at T = 50/100/200/365.
- **Literature repositioning:** partial inverse and partial anti-inverse shortest paths added (Gassner 2009; Ley & Merkert 2025) with a comparison table; the open-complexity claim narrowed to the demand-induced restriction.
- **Estimand separation:** old forecast, revised forecast and realised demand are distinguished notationally; the conformal result is titled and stated as one-step calibration of forecast revisions; a table assigns each guarantee to its estimand.
- **Manuscript minor repairs** per review comments 1–15 (Prop 2.1 wording, O_k nonempty assumption, potential notation u, boxed assurance statement, executable bit, four-period fence row, stylised-cost labelling, overlapping-windows prominence, Wilson intervals, timing separation, infinity taxonomy, title, conclusion wording, reference accents).
- **New documents:** `docs/response_to_reviewers_v2.1.0.md`, `docs/PRACTITIONER_GUIDE.md`.
- Test suite grown from 20 to 63 tests, including the reviewer-counterexample regression family.

## Assurance boundary

Certified values are exact-rational and witness-backed, and the shipped checker re-verifies records independently of the package; but there is no journal peer review, no independent clean-room reproduction of the full pipeline, no proof-assistant verification, and no field validation. For T > 12 the checker relies on the package's internally cross-checked parametric computation for lower-bound minimality. MILP negatives remain solver-level evidence. The full Richter–Vörös (1989) article was not obtained; theorem-level novelty remains conditional. Exact enumeration remains worst-case exponential.
