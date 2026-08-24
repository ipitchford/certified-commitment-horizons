# Scope, assumptions and failure modes

## Two semantic layers

The universal graph results apply to a deterministic, single-item, forced-source directed acyclic path model with non-negative floors and ordered reduced slopes.

The ordinary uncapacitated Wagner–Whitin interpretation applies only in `classical_active_horizon` mode, which requires a strictly positive first-period demand floor and strictly positive later setup costs. The semantic-bridge theorem then identifies optimal graph paths with optimal physical setup patterns. Outside those conditions, graph conclusions remain valid as graph statements and must not be promoted to classical lot-sizing claims.

## Protected object

The radius certifies setup epochs and replenishment-cycle boundaries. Quantities may adjust within a retained cycle. It does not certify fixed quantities, service levels, supplier capacity or transport reservations.

## Outside the theorem

Capacity constraints, minimum order quantities, backlogging, perishability, substitution, joint setups, multi-item coupling and endogenous forecast revisions alter the feasible family or cost geometry. The current formulas and certificates do not automatically survive those changes.

## Nominal degeneracy

The software reports the common prefix of every nominal optimum and whether the requested prefix lies within it. A nominal outside tie gives radius zero. A complete comparator selected by a secondary rule affects the frozen lower certificate, although the strong radius depends only on the protected node prefix.

## Exact complexity

The fixed-competitor inverse problem is a compact linear programme. The strong radius is a finite disjunction over outside paths and has a polynomial-size mixed-integer formulation. The released enumerator is worst-case exponential. This proves a property of that algorithm, not NP-hardness of the decision problem.

The exact complexity of the demand-induced, ordered-slope one-protected-arc restriction remains open. Generic partial inverse shortest-path hardness results modify arc weights independently and do not transfer automatically.

## Numerical certification

Every certified value is computed or re-verified in exact rational arithmetic with zero tolerances. Floating SciPy/HiGHS optimisation may propose candidates but cannot decide topology, zero, tie, infinity or a certified class. The independent checker replays records without importing the package.

Remaining assurance limits:

- no proof-assistant verification;
- for `T > 12`, the independent checker does not rederive global frozen-minimality by complete enumeration;
- mixed-integer negative results remain solver-level unless a certified bound closes them;
- all code and producer audits arise from one workflow.

## Statistical scope

The conformal theorem is one-step and marginal under exchangeability. It is not conditional, adaptive, time-uniform or automatically simultaneous across many products and replans. Distribution shift can cause undercoverage, as the negative-control simulations demonstrate.

## Evidence boundary

Synthetic and exact finite audits test implementation behaviour, theorem identities on bounded corpora and edge cases. They do not estimate industrial prevalence. The UCI case uses real demand but reconstructed forecasts and stylised costs. No prospective field benefit has been established.

## Novelty boundary

The supplied Richter–Vörös (1989) scan was inspected page by page and bound to its SHA-256. No protected-prefix, moving-continuation or simultaneous weighted demand-ball theorem was found in that article. The targeted corpus now also includes polynomial interval-demand minimax-regret lot sizing (Zhang, 2011; Li & Romero Morales, 2013), robust uncertainty-range models (Li & Romero Morales, 2017) and inverse cost elicitation for lot sizing (Egri et al., 2014). These are direct comparators but have different decision variables, quantifier order and objectives. The conclusion remains a bounded contribution comparison, not exhaustive priority; adjacent sources remain less completely inspected, and no independent bibliographic attestation is included.
