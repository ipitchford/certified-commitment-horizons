# Release notes: version 1.0.0

**Frozen:** 4 August 2026

This release turns the proposed research programme into a complete producer-side preprint and reproducible software artefact.

## Principal results

1. It defines the rational decision problem `WW-Prefix-Radius-infinity` for the smallest weighted infinity-norm demand revision that permits an optimal path to leave a selected Wagner-Whitin prefix.
2. It derives the reduced cumulative-demand arc form `K_i + q_i(D_j-D_i)`, the ordered-slope Monge inequality and affine path coefficients.
3. It gives an exact floor-aware distance formula for one fixed competitor.
4. It proves a polynomial frozen-comparator lower certificate, computable by at most `T+1` polynomial-size shortest-path and Charnes-Cooper linear programmes.
5. It proves that the lower certificate is exact for a full path and can be strict for a partial prefix. The supplied positive-floor instance has lower radius `1.5` and exact radius `2.0`.
6. It gives an exact fixed-competitor inverse linear programme, an exact finite disjunction over outside paths and an exact fixed-radius mixed-integer decision formulation.
7. It proves membership of the decision problem in NP. It does not claim NP-hardness or a polynomial unrestricted exact algorithm.
8. It calibrates deterministic certificates with a split-conformal revision threshold under exchangeability.
9. It proves a telescoping rolling-horizon regret bound with a certified stability dead zone.

## Assurance status

The release passed 20 deterministic tests and the one-command release verifier. The polynomial implementation matched exhaustive enumeration in 569 frozen cases. The rolling theorem had no frozen numerical violation above `2.28e-13` in 220 synthetic cases. The final PDF has 22 A4 pages, embedded fonts, resolved citations and references, and no detected clipping or overfull boxes.

External peer review, independent clean-room reproduction and proof-assistant verification remain outstanding. The synthetic calculations test implementation; they do not establish empirical representativeness.
