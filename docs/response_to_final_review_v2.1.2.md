# Response to the final Evidence Press review — version 2.1.2

**Reviewed package:** v2.1.1, 5 August 2026  
**Review recommendation:** major revisions before Evidence Press release; no fatal mathematical concern identified  
**Response version:** v2.1.2 candidate, 8 August 2026

The full review is preserved verbatim in `docs/final_review_v2.1.1_for_evidence_press.md`. Version 2.1.2 treats it as a release-blocking review and changes no theorem or numerical result merely to obtain a favourable decision.

## Traceability matrix

| Review concern | Response | Verification | Residual boundary |
|---|---|---|---|
| Quick replay failed in the reviewer environment because unresolved upper-witness bounds were asserted monotone | Corrected `tests/test_exactcert.py`: monotonicity is tested only for certified exact strong radii. Every unresolved upper endpoint is still required to lie above its certified lower endpoint. No numerical tolerance was introduced. | Locked-environment tests and fresh-archive replay | Upper witnesses may vary non-monotonically; that is now explicit rather than hidden. |
| Parametric implementation was described as polynomial and used an arbitrary iteration cap | Corrected the exact-layer docstring and paper/release language. The implementation now computes the deviation DAG's exact source-to-sink path count and uses it as a finite, potentially exponential correctness bound. | Unit tests, exact audits and release-contract text checks | The polynomial result belongs to the separate Charnes–Cooper construction. No polynomial iteration bound is claimed for the released parametric routine. |
| Public archive redistributed third-party papers without a demonstrated right | Removed all third-party article PDFs and extracted article text from the public tree. Retained citations, lawful source links and hashes in `THIRD_PARTY_NOTICES.md`. | Clean-tree release-contract check | Readers must obtain the cited works through publishers, repositories or document delivery. |
| Manuscript, code, metadata and data licensing were conflated | Added `LICENSES.md`: original research content and release metadata are CC0 1.0; source code is MIT; UCI data remains CC BY 4.0; other third-party rights are reserved. | Required-file and clean-tree checks | The package cannot waive rights it does not own. |
| UCI acquisition URL was missing | Re-fetched the official UCI archive. Its sole CSV is byte-identical to the analysed file and the exact URL, date, DOI, licence and SHA-256 are recorded. | `check_uci`, provenance record and third-party notice | Forecast vintages and costs remain reconstructed and the case remains illustrative. |
| Version and title metadata conflicted | Synchronised README, paper header and title page, CFF, Python package, wheel, claims and provenance to 2.1.2 dated 8 August 2026. Added a release-contract verifier that fails on drift. | `check_release_contract` and wheel inspection | Historical v1.0.0/v2.0.0/v2.1.0 documents retain their historical identifiers. |
| “Adversarial peer review” and “independent checker” overstated assurance | Replaced these with “internal and cross-model adversarial review” and “separately implemented producer-side checker”. Split exact-rational computational certification from proof-assistant verification and independent clean-room reproduction. | Text drift checks and provenance fields | No external peer review, independent reproduction or formal verification is claimed. |
| Novelty could overlap Richter and Vörös (1989) | Preserved the conditional novelty statement and print-acquisition route; no first-result claim was added. | Claim C11, literature audit and AI index | Theorem-level comparison remains open until the complete 1989 article is inspected. |
| Generated caches and bytecode polluted the archive | Excluded caches, bytecode, egg metadata and LaTeX auxiliaries from the clean public tree; added checks that fail if compiled Python artefacts return. | Manifest coverage and release-contract check | Build environments may recreate these locally, but they are not release artefacts. |

## Assurance statement after revision

Version 2.1.2 supports an **unrefereed candidate** designation with producer-side exact-rational replay. It does not support claims of independent reproduction, proof-assistant verification, external scholarly peer review, field validation, operational effectiveness or settled novelty.
