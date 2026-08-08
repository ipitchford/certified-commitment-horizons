# Scope, assumptions and failure modes

## Proven model scope

The theory applies to a deterministic, single-item, uncapacitated Wagner-Whitin shortest-path model with non-negative demand floors and ordered reduced slopes. It certifies a prefix of setup epochs and cycle boundaries. Realised or revised quantities may adjust within those retained cycles.

## Outside the theorem

The current results do not automatically cover capacity constraints, fixed order quantities, minimum order quantities, backlogging, perishability, substitution, service-level constraints, transport slots, shared setups, multi-item coupling or endogenous forecast revisions. These features alter the feasible path family or the cost geometry and may invalidate the certificate.

## Nominal degeneracy

A radius attached to a selected nominal path can depend on arbitrary tie-breaking. The software therefore reports the number of nominal optima up to a cap, computes the longest prefix common to all nominal optima, and states whether the requested protected prefix is common. The paper recommends protecting the common prefix unless a disclosed secondary criterion selects an optimum. A nominal outside tie gives radius zero.

## Statistical scope

The conformal theorem is one-step and marginal over the calibration sample and next revision under exchangeability. It is not conditional on the realised calibration set, time-uniform, or automatically simultaneous across products or replans. Repeated prespecified decisions require an explicit error allocation; adaptive selection or distribution shift requires a different theorem and procedure.

## Rolling-loss semantics

The rolling theorem prices structural setup commitments with uncapacitated quantity recourse and replanning at disclosed cycle boundaries. It does not price service failures, capacity reservations or fixed quantities unless they enter the optimisation model. The realised demand must remain in the floor-constrained admissible domain.

## Exact computation

The fixed outside-path inverse problem is a compact linear programme. The exact strong radius is a finite disjunction over outside paths, and fixed-radius decision has a polynomial-size mixed-integer formulation. These are exact formulations, not polynomial-time algorithms; generic partial inverse and anti-inverse shortest-path analogues are NP-hard (Gassner 2009; Ley & Merkert 2025), and only the demand-induced Wagner-Whitin restriction remains open. Candidate generation is exponential in the current enumerator; time limits leave a certified but unresolved bracket, never a silent answer.

## Numerical certification

Every value the software labels certified is computed, or a posteriori verified, in exact rational arithmetic with zero tolerances (`wwprefix.exactcert`); floating-point optimisation only proposes witnesses and dual mixtures, which are exactly re-verified before use. Decision records carry witnesses that `scripts/check_certificate.py` re-verifies without importing the package (complete re-derivation of frozen minimality for T <= 12). Remaining boundary: for larger horizons lower-bound minimality relies on the package's internally cross-checked parametric computation; mixed-integer "no" answers are solver-level evidence only; neither implementation is proof-assistant verified. Plain JSON numbers are decided at their exact binary values; decimal-exact semantics require numeric strings.

## Evidence boundary

Synthetic tests probe correctness, conservatism and edge cases. They do not estimate industrial prevalence. The illustrative UCI case uses real demand but reconstructed forecast vintages and stylised costs. No field decision, service outcome or financial saving has been validated.

## Novelty boundary

Indexed evidence shows that Richter and Vörös (1989) analysed demand-vector parameterisation and stability regions preserving a Wagner-Whitin solution. This release did not obtain the full article, so it cannot exclude theorem-level overlap. The claimed candidate novelty is the moving prefix-face object, the floor-aware polynomial lower certificate and its integration with exact brackets, calibration and rolling loss. That boundary remains conditional until the 1989 full text is inspected.
