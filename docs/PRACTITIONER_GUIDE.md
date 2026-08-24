# Practitioner guide: certified commitment horizons

**Version:** 3.0.0, 24 August 2026  
**Audience:** production and supply planners, operations-research teams, and planning-system engineers

## Decision supported

The tool asks an item-specific question:

> How far can the current demand forecast move before an optimal setup schedule may change any protected replenishment-cycle boundary?

It replaces a calendar fence with a model-based stability calculation. The output is a decision record with an exact lower certificate, a feasible destabilising witness where one is known, and an explicit unresolved state where the evidence does not close.

## First choose the semantic contract

Use `classical_active_horizon` only when:

- the first-period demand floor is strictly positive, so period 1 must contain productive setup activity under every admissible revision; and
- every later setup cost is strictly positive, so a costless empty setup cannot create an operationally meaningless tie.

Under those conditions, the manuscript proves that the graph’s optimal path prefixes correspond to ordinary uncapacitated Wagner–Whitin setup schedules.

Use `forced_source_graph` only when a mandatory period-1 source setup and graph-distinct empty setup nodes are genuinely the intended decision semantics. A zero first-period demand instance is not automatically a classical lot-sizing instance.

## What a certificate protects

A certified lower radius protects:

- setup epochs; and
- replenishment-cycle boundaries.

It does not freeze order quantities. The guarantee assumes uncapacitated quantity recourse within each retained cycle. Capacity, minimum order quantities, shared setups, service constraints and transport reservations require additional modelling.

## Input mapping

| Field | Planning interpretation |
|---|---|
| `demand` | current forecast by period |
| `K` | fixed setup or ordering cost by period |
| `q` | reduced unit cost, required to be non-increasing |
| `floor` | lowest admissible forecast by period |
| `weights` | relative importance of movement in each period |
| `semantic_mode` | graph-only or classical active-horizon contract |

Use numeric strings for exact decimal data. A common scaling is `weight_t = 1 / typical_revision_t`, which measures the radius in units of typical forecast movement. The paper does not prescribe this choice; the planning team must justify and monitor it.

## Decision flow

```bash
wwprefix certify plan.json --k 2 --proposed-radius "0.8"
```

Interpret the result as follows:

1. **Certified safe inside the lower radius.** Every admissible revision strictly inside the exact lower radius retains the protected prefix.
2. **Witnessed unstable at or beyond an upper radius.** The record gives a concrete demand vector and outside path that tie or beat the best retaining continuation.
3. **Certified interval.** The lower and upper evidence are valid, but the nearest boundary is not closed.
4. **Refused or solver-level.** The computation has not established safety. Shorten the prefix, change the decision threshold, or preserve the unresolved state for human judgement.

Never recode unresolved, refused or time-limited output as safe.

## Escalation

The exact path disjunction has a closed-form exponential candidate count. The interface can refuse it before generation. At ordinary horizons, use the polynomial bracket first and the compact production-balance mixed-integer model only when the unresolved interval has enough decision value.

A finite mixed-integer witness is upgraded only after exact verification. A solver’s failure to find a destabilisation within a cap is not an infinity proof.

## Calibration

The optional conformal layer concerns the **next forecast revision**, not realised demand. Its theorem is one-step and marginal under exchangeability of the calibration scores and the next score. Repeated or adaptive deployment requires explicit error allocation or a different sequential method. A forecast-system change, promotion regime or missing-horizon pattern can invalidate the calibration exchangeability assumption.

## Evidence and deployment boundary

The included UCI exercise uses real observed demand, reconstructed forecast vintages and stylised costs. It demonstrates that the interface can return conservative, exact and unresolved decisions. It does not estimate financial savings or operational effectiveness.

A prospective evaluation should predeclare:

- genuine forecast vintages and information sets;
- actual setup, inventory, expediting and service costs;
- capacity and quantity constraints;
- incumbent fence policy;
- decision outcomes and overrides; and
- primary benefit and safety metrics.

Retain every JSON decision record, instance hash, checker result, timeout and manual override. That evidence is necessary to distinguish model failure from implementation failure or policy non-compliance.
