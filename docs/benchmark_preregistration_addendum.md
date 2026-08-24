# Preregistered scaling benchmark: compact model versus released escalation

**Status:** FROZEN before any benchmark execution (addendum item 6). The
SHA-256 of this file at freeze time is recorded in
`results/processed/addendum_benchmark_summary.json`; any later deviation is
listed in that file's `deviations` array, never silently absorbed.

**Precondition (gate):** `scripts/run_addendum_equivalence.py` must report
`zero_disagreements: true` on the full corpus before this benchmark may
run. No scalability claim attaches to the compact model until it has
reproduced every existing exact T ≤ 18 radius, witness and infinite-radius
result (the brief's sanity check).

## Question

At operational horizons, which exact escalation mechanisms resolve the
strong prefix radius under fixed resource caps: the released exhaustive
outside-path disjunction, the released arc-product fixed-radius MILP, the
addendum's compact production-balance MILP, or the polynomial certificate
bracket alone?

## Design (fixed in advance)

- **Horizons:** T ∈ {18, 25, 35, 50, 75, 100}.
- **Families:** `regular`, `near_tie` (both from `scripts/_common.py`
  `random_ww_instance`), and `adversarial` = `floor_heavy` at every T plus
  `strict_gap` (via `draw_strict_gap_instance`) at every T. The near-tie
  and adversarial families are the hard strata by construction; no
  instance is tuned post hoc.
- **Replicates:** 2 per (T, family) cell. Seed lineage:
  `np.random.default_rng(SEED + 7000 + cell_index)` with SEED = 20260804,
  cell_index enumerated in the fixed loop order (T outer, family middle,
  replicate inner).
- **Protected prefix:** the nominal optimal path P* with k = ⌈m/2⌉
  protected arcs (partial prefix), plus one full-path row (k = m) at T = 18
  only, as the polynomial contrast case.
- **Methods per instance:**
  - M1 `exact_radius_enumeration` — attempted only when the closed-form
    candidate count N_out(T, s) ≤ 2^21 = 2,097,152; otherwise recorded as
    `refused_by_candidate_guard` with the disclosed count and not run.
    Time limit 180 s when attempted.
  - M2 released arc-product `fixed_radius_milp`, decision probe at the
    midpoint of the certified bracket (or at the frozen lower bound when
    the bracket is one-sided); time limit 60 s.
  - M3 compact `compact_radius_milp` (minimum radius); radius cap
    4·(1 + weighted floor spread + certified-bracket anchor); time limit
    60 s.
  - M3b compact `compact_fixed_radius_milp` at the same probe radius as
    M2; time limit 60 s.
  - M4 polynomial certificate alone: `exact_polynomial_bracket`
    (exact rational frozen lower bound + witness upper bound), no cap
    beyond its own runtime.
- **Recorded per solve:** wall seconds, peak-RSS delta
  (`resource.getrusage`, measurement only), solver status,
  `mip_node_count`, `mip_gap`, radius / decision / bounds, certified
  witness radius when the exact layer re-verifies, and
  unresolved-under-cap flags.
- **Primary comparisons (declared):**
  - P1: largest T at which each method resolves its task within caps.
  - P2: M3 versus M2 wall time and node count on cells both resolve.
  - P3: M4 bracket width relative to the best certified value where any
    exact value is known.
- **Analysis:** descriptive tables only; no hypothesis tests; no
  extrapolation beyond the grid. Refusals and timeouts are results, not
  missing data.

## Honesty rules

- The M1 refusal threshold implements the addendum theorem: the candidate
  count is known in closed form before generation, so refusal is
  principled, not a timeout artefact.
- `no_destabilisation_within_cap` from M3 is solver-level evidence, never
  an infinity certificate; exact infinity claims remain with the exact
  layer (M4 saturation proofs).
- Any crash, cap change, or grid change after freezing is recorded under
  `deviations` with a timestamp and reason.
