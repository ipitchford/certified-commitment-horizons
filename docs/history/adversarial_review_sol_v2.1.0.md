# Cross-model adversarial review of the v2.1.0 exact-certification repair

**Reviewer:** GPT-5.6 Sol (OpenAI `/v1/responses`), 5 August 2026, prompted to refute.
**Scope:** the eight soundness claims (C1–C8) underlying `wwprefix.exactcert`, plus the
independent checker's saturation-infinity re-proof and the nominal-optimality inferences.
**Verbatim reply:** `docs/adversarial_review_sol_v2.1.0_verbatim.md`.
**Headline:** no refutation of any certified-safe or certified-destabilising soundness
claim as implemented; four caveats, each verified against the code and dispositioned below.

| # | Sol's finding | Verification against the code | Disposition |
|---|---|---|---|
| 1 | C1 breaks if zero/negative weights are accepted (division by `w`), and non-finite inputs are undefined. | Both layers reject `w <= 0` and non-finite values (`WWInstance.create` finiteness check; `Fraction(nan/inf)` raises). | Locked with `test_nan_and_infinity_inputs_rejected_by_both_layers`; preconditions stated in the schema doc. |
| 3 | "No flat-zero segment" is false globally: `F(r) = 1-r` then identically 0 is realisable; a crossing exactly at a breakpoint must be returned as the answer. | Constructed Sol's instance: the breakpoint binary search returns the first breakpoint with `F <= 0` and the Newton loop terminates immediately when the seed value is exactly 0 — certified radius exactly `1/1`. The in-code no-flat-zero argument applies only within the crossing interval, whose left endpoint has `F > 0` by the search invariant, where it is valid. | Locked with `test_flat_zero_segment_after_crossing_lands_on_first_crossing`; the paper's description states the interval-local scope of the argument. |
| 6 | A mixture-boundary tie must not be promoted to a strong (destabilising) witness. | Mixtures feed only `note_lower`; every published witness passes `certify_strong_witness`, which re-checks `C_Q <= inside minimum` by exact suffix DP. | No change needed; invariant documented here. |
| 8 | Power-of-two rescaling invariance is overstated: binary under/overflow (e.g. subnormals) can delete a coefficient before ingestion; unit rescaling requires `q -> q/s`, not weight changes alone. | The audit's rescaling family applies the full transformation (`K x c`, `q x c/s`, `d,floor x s`, `w / s`) in the normal range, so the assertion is sound as executed; the general claim is now scoped: invariance is unconditional when rescaling is performed in exact rationals, and holds for binary-performed rescalings only in the absence of under/overflow. | Claim C14 and the manuscript sentence scoped accordingly. |
| 9 | Checker's saturation re-proof must count only arcs on complete outside paths. | In the complete lot-sizing DAG every reached deviated node extends to the sink, so reached-arc scanning equals on-a-complete-path scanning; prefix arcs contribute zero coefficients. | Exercised end-to-end with `test_checker_verifies_saturation_infinity_record`. |

Findings 2, 4, 5, 7, 10, 11: "no refutation found" (with the breakpoint-equality
handling of finding 3, which the implementation already had). Sol's reply is treated as
a hypothesis set, not a verdict; every claim above was re-verified against HEAD before
disposition, per the project's audit-verification rules.
