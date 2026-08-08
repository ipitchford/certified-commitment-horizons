# Publisher-side re-review: v2.1.2 candidate

**Date:** 8 August 2026  
**Basis:** the full v2.1.1 Evidence Press review, the v2.1.2 response matrix, revised manuscript, source, regenerated outputs and release metadata  
**Decision:** suitable for publication as an **unrefereed candidate**, not as an externally verified theorem or validated operational method

## Disposition of release-blocking findings

1. **Incorrect monotonicity test:** corrected. Monotonicity is tested only for finite exact certified radii; independently selected unresolved upper witnesses are not required to be monotone.
2. **Arbitrary iteration cap:** replaced by an exact source-to-sink path-count termination bound. The released parametric routine is described as finite, potentially exponential; the polynomial theorem is tied to the separate Charnes-Cooper construction.
3. **Third-party redistribution:** article PDFs and extracted text are absent from the public tree. Stable sources, access status and inspected-copy hashes remain in the notices and literature audit.
4. **Licence ambiguity:** original manuscript, documentation, figures and metadata are CC0-1.0; code is MIT; the UCI CSV remains CC BY 4.0. The split is explicit in `LICENSES.md` and `THIRD_PARTY_NOTICES.md`.
5. **Data provenance:** the official UCI archive was re-fetched and its sole CSV is byte-identical to the analysed file. URL, DOI, licence, byte count and SHA-256 are recorded.
6. **Assurance overstatement:** “independent checker” and “peer review” language was replaced by producer-side checking and internal/cross-model adversarial review. Independent reproduction, proof-assistant verification, journal review and field validation remain false or not assessed.
7. **Version and environment drift:** manuscript, README, CFF, claim ledger, provenance, wheel and verifier now identify v2.1.2. Runtime dependencies are identically pinned in `pyproject.toml`, `requirements-lock.txt` and `uv.lock`.
8. **Citation robustness:** all 31 bibliography records passed identifier or stable-route metadata checks. The adjacent Richter-Vörös EJOR DOI was added. The EIK full-text comparison remains unresolved and originality remains conditional.

## Re-review assessment

No fatal mathematical contradiction was found in the supplied review or the subsequent publisher-side replay. The revised package now supports the bounded claim that its exact-rational implementation and bundled witnesses pass the stated producer-side checks for the released inputs and audit designs. It does not support a claim of independent theorem verification, exhaustive novelty, industrial effectiveness, or general field validity.

On an internal REF-style screen, the work has potentially substantial originality and significance, but the inaccessible direct antecedent and absence of external review prevent a settled originality assessment. Rigour and transparency are materially strengthened by exact arithmetic, negative controls, explicit unresolved states, full replay and machine-readable scope records. Timeliness favours candidate publication now with the present qualifications.

## Residual high-value work

- obtain and compare the full Richter and Vörös (1989) EIK article;
- independently reimplement and replay the exact certificate layer;
- formalise the core graph/path and fractional-programming arguments;
- test the method with authentic forecast vintages, costs and operational constraints;
- improve the exact implementation's large-horizon performance without weakening certification.
