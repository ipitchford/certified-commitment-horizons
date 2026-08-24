# Licensing exception review and closure

**Trigger:** repository overlay exposed three derived text extracts under `literature/text/` after the first publication-ready confirmation. This was genuinely new information: the initial rights check rejected literature PDFs but did not reject derived text.

**Finding:** P1 publication-integrity defect, not a scientific defect. Publishing extracted text without an established redistribution basis would violate the intended third-party boundary.

**Repair:** moved all three extracts to the private excluded-materials folder; changed the release verifier to reject every file under `literature/` except `README.md`; updated the licence map, notices, literature README and release notes; rebuilt the wheel; reran pre-seal, fresh installed-wheel and final verification; resealed the archive; and strengthened the external fast gate to inspect the complete `literature/` subtree.

**Final object:** `certified_commitment_horizons_v3.0.0.zip`, SHA-256 `4d09e03fc3146018e6c11d3dce8ac9e3cb74bcc07bf4564583207a7c01784744`.

**Closure:** repaired. Unresolved Critical 0; Major 0; Minor 0. Scientific source, tests, results and manuscript claims are unchanged. The editorial ACCEPT decision remains within the same anonymous unrefereed candidate ceiling.
