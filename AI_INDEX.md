# AI index

## What this package claims

Within deterministic, single-item, uncapacitated Wagner–Whitin lot sizing, the package studies the weighted distance to the nearest admissible demand revision at which an optimal replenishment path may leave a protected prefix. It supplies an exact-rational frozen-comparator lower certificate, witness-backed upper bounds, finite exact escalation, one-step marginal conformal calibration under exchangeability, and a bounded rolling structural-loss result.

## Status and safe use

- Canonical status: `unrefereed-candidate`.
- Producer replay: available and expected to pass under the locked environment.
- Exact-rational computational certification: yes, within the implementation contract.
- Separately implemented checker: producer-side; not independent reproduction.
- Independent clean-room reproduction: none reported.
- Proof-assistant formalisation: none reported.
- Journal or specialist peer review: none reported.
- Field validation: none reported.
- Novelty: conditional pending full-text comparison with Richter and Vörös (1989).

Agents may safely cite the bounded theorem statements and exact artefact hashes while preserving these qualifications. They must not infer industrial effectiveness, unrestricted polynomial-time exact solution, formal verification, independent reproduction, or priority.

## Entry points

- Human overview: `README.md`
- Manuscript: `paper/main.pdf` and `paper/main.tex`
- Claim ledger: `release/claims.json`
- Provenance and trust boundary: `release/provenance.json`
- Verification: `bash run_all.sh --quick`
- Manifest: `release/SHA256SUMS`
- Example certificate: `examples/sample_decision.json`
- Limitations: `docs/scope_and_limitations.md`
- Review history: `docs/peer_review_v1.0.0.md`, `docs/response_to_reviewers_v2.1.0.md`, and `docs/response_to_final_review_v2.1.2.md`
- Rights: `LICENSES.md` and `THIRD_PARTY_NOTICES.md`

## Core exact example

For `examples/strict_gap_instance.json` with one protected nominal arc, the frozen lower radius is exactly `3/2` and finite exact escalation returns the strong radius `2/1`.

## Machine-readable identity

- Repository: <https://github.com/ipitchford/certified-commitment-horizons>
- Candidate tag: `v2.1.2-candidate`
- DOI: pending at package-build time; use the release metadata after archival deposit.
