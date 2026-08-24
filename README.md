# Certified Commitment Horizons in Dynamic Lot Sizing

**Release:** 3.0.0 — 24 August 2026  
**Status:** unrefereed theoretical–computational candidate  
**Licence:** CC0-1.0 for original research content and metadata; MIT for original software; third-party material retains its source terms
**Version DOI:** [10.5281/zenodo.22086554](https://doi.org/10.5281/zenodo.22086554)  
**Concept DOI:** [10.5281/zenodo.21853901](https://doi.org/10.5281/zenodo.21853901)

## What this release establishes

The package studies `WW-Prefix-Radius-infinity`: the weighted, floor-truncated demand-space distance at which an optimal Wagner–Whitin-type replenishment path may cease to share a protected setup prefix.

Release 3.0.0 separates two semantic layers that earlier versions conflated:

- **`forced_source_graph`** is the abstract path model. Every complete path begins at period 1. An empty zero-cost setup node remains a distinct graph decision.
- **`classical_active_horizon`** is the ordinary uncapacitated lot-sizing interpretation. It is accepted only when the first-period demand floor is strictly positive and every later setup cost is strictly positive. Under those conditions, the manuscript proves a cost-preserving bijection between optimal physical setup patterns and optimal graph paths.

This distinction repairs the leading-zero-demand counterexample: with `K=(100,1)`, `q=(1,0)` and `d=(0,1)`, the forced-source graph costs 101 while the ordinary physical model can wait until period 2 and costs 1. The instance remains valid in graph mode and is rejected in classical mode.

Demand floors are declared inputs, not quantities estimated by the software.
Their provenance must say whether they encode empirical or physical support, a
contractual/planning minimum, or a conservative truncation. These meanings are
mathematically compatible with the same lower-bound constraint but are not
operationally interchangeable.

## Principal contributions

The manuscript proves, within the declared semantic domain:

1. reduced affine arc costs `K_i + q_i(D_j-D_i)` under ordered reduced slopes;
2. an exact, floor-aware distance to a tie with any fixed path;
3. a prefix-deviation directed acyclic graph representing exactly the paths that leave a protected prefix;
4. a polynomial exact-rational frozen-comparator lower certificate;
5. a polynomial lower–upper bracket with exact closure conditions;
6. a canonical common-optimal-prefix safeguard against arbitrary nominal tie-breaking;
7. an exact prefix-to-arc decomposition: a `k`-arc strong radius is the minimum of at most `k` one-protected-arc suffix radii;
8. a **single-detour optimal-face theorem**: every finite nearest loss of compulsory prefix optimality admits adjacent co-optimal inside/outside paths differing on one divergence–remergence interval;
9. exact finite-disjunction and fixed-radius formulations, plus a polynomial-size production-balance mixed-integer formulation;
10. one-step marginal conformal calibration under exchangeability; and
11. a deterministic rolling structural-loss bound under uncapacitated quantity recourse.

The exact complexity of the demand-induced one-protected-arc problem remains open. The released enumerator is provably exponential, but that fact does not classify the decision problem.

## What changed in 3.0.0

- Added the classical active-horizon semantic bridge and explicit graph-only mode.
- Added edge-case regressions for leading-zero demand, interior zero demand, zero setup cost and empty setup nodes.
- Corrected the invalid test that demanded monotonicity of independently found unresolved upper witnesses. True-radius monotonicity is now tested only when adjacent radii are exactly certified; unresolved intervals are checked for lower ≤ upper consistency.
- Replaced ambiguous `complete` statuses with `exact_certified`, `enumeration_completed_with_certified_interval`, refusal and solver-level states.
- Added the single-detour optimal-face theorem, implementation and exact finite audit.
- Added an independent physical-enumeration audit of the semantic bridge.
- Stratified the 627-row compact-model corpus into exact, floating-search, reference-unresolved and pair-unresolved classes rather than calling all rows exact validations.
- Reconciled the Richter–Vörös (1989) record through a hash-bound, page-specific inspection receipt. The result is a source-specific negative reading, not an exhaustive priority claim.
- Added the closest omitted algorithmic and inverse-lot-sizing comparators: Zhang (2011), Li–Romero Morales (2013, 2017) and Egri et al. (2014), with explicit quantifier and objective differences.
- Rebuilt the package as one version-matched source, wheel, manuscript, claims ledger, provenance record, verification receipt and SHA-256 manifest.

## Quick start

Requirements: Python 3.11 or later. Rebuilding the manuscript also requires a LaTeX installation with `latexmk` and `biber`.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
python -m pip install . --no-build-isolation

wwprefix certify examples/strict_gap_instance.json --k 1 --exact \
  --output examples/sample_decision.json
```

The strict-gap example is in `classical_active_horizon` mode. It returns:

- frozen lower certificate: exactly `3/2`;
- exact strong radius: exactly `2/1`;
- one-based public nominal path `[1, 2, 4]`.

Certified quantities appear as `{"float": ..., "exact": "p/q"}`. The rational string is authoritative. Floating-point values appear only under `float_search` and never decide a certified classification.

### Input semantics

A minimal instance contains `K`, `q`, `demand`, `floor`, `weights` and `semantic_mode`:

```json
{
  "semantic_mode": "classical_active_horizon",
  "K": ["0", "3", "2"],
  "q": ["2", "1", "0"],
  "demand": ["1", "5", "1"],
  "floor": ["0.5", "0.5", "0.5"],
  "weights": ["1", "1", "1"]
}
```

Use numeric strings where decimal-exact semantics matter. Plain JSON numbers are converted from their exact binary values. See `docs/input_schema.md`.

## Output states

The interface does not collapse unresolved evidence into a binary answer.

| Status | Warranted interpretation |
|---|---|
| `exact_certified` | The exact strong radius is closed to one rational value. |
| `certified_interval` | Exact lower and feasible upper witnesses are valid; the nearest value is not closed. |
| `enumeration_completed_with_certified_interval` | Candidate processing completed, but one or more disjuncts remain unresolved. |
| `refused_by_candidate_guard` | The closed-form candidate count exceeded the predeclared cap; no safety conclusion follows. |
| `solver_level_only` | A mixed-integer result lacks the exact witness or closing bound required for certification. |
| proven infinity | No outside path exists, or a certified positive residual gap survives full admissible saturation. |

A certified lower radius protects **setup epochs and replenishment-cycle boundaries**, not fixed order quantities. The model assumes quantities can adjust within retained cycles.

## Verification

Quick deterministic replay:

```bash
bash run_all.sh --quick
```

Full computational replay:

```bash
bash run_all.sh --full
```

Release checks:

```bash
python scripts/fresh_extract_replay.py --python /path/to/python3.12
python scripts/verify_hashes.py release/SHA256SUMS
PYTHONPATH=src python scripts/verify_release.py --run-tests
python scripts/source_snapshot.py --check-provenance
python scripts/seal_release.py --output /path/to/certified_commitment_horizons_v3.0.0.zip
```

The fresh-extraction replay builds an unrelated virtual environment, installs
the locked dependencies and wheel, runs the quick replay in pre-seal mode, and
then imports the wheel with isolated Python from outside the source tree. The
final verifier accepts the resulting receipt; this two-stage protocol avoids a
circular gate in which a receipt would have to claim the final verifier passed
before the final verifier could run.
The sealing command regenerates the complete manifest, writes a deterministic
ZIP outside the release tree, extracts it again, verifies manifest coverage and
runs the final release verifier on the extracted archive.

Independent record check:

```bash
python scripts/check_certificate.py \
  examples/sample_decision.json \
  examples/strict_gap_instance.json
```

The independent checker does not import `wwprefix`. For horizons above 12 it checks achievability, consistency and infinity evidence but does not independently rederive global frozen-minimality.

## Evidence ledger

| Evidence gate | Denominator | Result |
|---|---:|---|
| Semantic bridge | 320 exact active-horizon instances, `T=1..10` | 320 optimal-cost and optimal-setup-set matches; no empty later optimal setup; negative control 101 versus 1 |
| Optimal-face edge witness | 315 prefix cases from 84 exact instances | 254/254 finite boundaries exposed a single-detour adjacent crossing pair; 61 were proven infinite |
| Frozen certificate | 512 comparisons from 258 instances | maximum discrepancy from exhaustive frozen enumeration 0 |
| Polynomial bracket | 512 cases | 411 exact closures; 101 certified intervals |
| Exact certification | 330 brute-force comparisons | 330/330 frozen matches; 305 exact strong radii; 25 certified intervals |
| Compact equivalence | 627 rows | 305 exact matches; 247 exact decomposition equalities; 55 platform-sensitive search rows (27 floating-search matches with exact witness checks and 28 reference-unresolved in the frozen macOS replay); 20 unresolved pairs; zero warranted disagreements |
| Exact enumeration benchmark | 30 instances | 28 optimal; 2 `T=18` atomic candidate-generation timeouts before any disjunct; 0 solver failures |
| Fixed-radius mixed integer | 24 probes | 22 resolved/correct; 2 time-limit unresolved |
| Rolling bound | 462 cases | no theorem violation; all 254 dead-zone cases had zero residual |
| Test suite | 94 deterministic tests | pass |

These are producer-side finite audits. They test implementation identities and can refute defects; they do not machine-prove universal theorems.

## Literature boundary

The supplied seven-page Richter–Vörös (1989) scan was read page by page and bound to SHA-256 `bd5ee5a82e399e11572b44d2bf334672be6bc6b47499271e636cf3a8f04aa255`. It studies one- and two-scalar stability regions for one fixed Wagner–Whitin regeneration-point solution. No protected-prefix class, moving inside continuation, simultaneous weighted demand ball, coordinate floors or complexity classification was found in that source.

The rebuilt boundary also includes the closest robust-complexity comparator: Zhang (2011) and Li–Romero Morales (2013) solve interval-demand minimax-regret lot sizing in polynomial time, with an $O(T^5)$ demand-only algorithm. Their model chooses one setup vector before uncertainty and minimises worst-case regret; this release searches for the nearest scenario where two adaptive prefix-restricted value envelopes cross. Egri et al. (2014) provide a direct inverse lot-sizing precedent by inferring cost ratios from observed demand–optimal-plan pairs, but do not perturb demand or protect a prefix.

See `docs/literature_audit.md`, `release/prior_art_corpus.json`, `docs/richter_voros_inspection_receipt.md` and `release/literature_inspection_receipt.json`. The Richter–Vörös scan itself is not redistributed. The search remains targeted rather than systematic; exhaustive priority and independent bibliographic attestation remain open.

## Claim ceiling

This release supports a theoretical and computational contribution in single-item uncapacitated lot sizing. It does **not** establish:

- capacity-, service- or multi-item guarantees;
- fixed-order-quantity robustness;
- polynomial-time exact solution of the partial-prefix problem;
- adaptive, conditional or time-uniform conformal coverage;
- industrial cost savings;
- independent clean-room reproduction;
- proof-assistant verification; or
- exhaustive novelty.

The UCI exercise uses observed demand but reconstructed forecast vintages and stylised costs. It demonstrates the interface and conservative behaviour; it is not field validation.

## Rights and scholarly identity

The scholarly creator of this candidate is **Anonymous**. Original manuscript text, figures, documentation, release metadata, claim records and original result tables are dedicated under CC0 1.0. Original source code is licensed under MIT. The included UCI data retain CC BY 4.0. Literature PDFs used during review are not redistributed; citations, source URLs and hashes identify the inspected materials. See `LICENSES.md`, `PUBLIC_DOMAIN.md` and `THIRD_PARTY_NOTICES.md`.
