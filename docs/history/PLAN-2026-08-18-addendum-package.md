# Commitment-Horizons Theorem-and-Solver Addendum (v2.2.0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline execution chosen: the seven items share one mathematical context — the definitions of ρ, A_k, B_k, E_r, O_r — and fragmenting them across fresh subagents would force each to re-derive it). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the seven "Recommended package" items from the 2026-08-18 follow-on brief for the Evidence Press release *Certified Commitment Horizons in Dynamic Lot Sizing*, turning the ChatGPT/Sol complexity-and-prior-art audit into checked theorems, a compact exact solver, preregistered benchmarks, and a completed Richter–Vörös prior-art record — as release version 2.2.0 in the existing working tree.

**Architecture:** All work lands in `~/claude-sandbox/commitment-horizons/certified_commitment_horizons_v2.0.0/` (contents currently v2.1.1; 66 tests green at baseline). Mathematics goes into `paper/main.tex` as a new section plus surgical edits; code goes into `src/wwprefix/` as two new modules plus small additions to `model.py`/`exact.py`/`exactcert.py`; verification goes into `tests/test_addendum.py` plus two new deterministic scripts writing `results/raw/*.csv` in the release's established pattern. The float-searches/exact-rationals-certify architecture of v2.1.x is preserved: the new MILP is a search-and-upper-bound device; every claim entering the record is exactly re-verified or explicitly labelled solver-level.

**Tech Stack:** Python 3.13 (`.venv/bin/python`; the Trail-of-Bits hook rejects bare `python3` — use `.venv/bin/python` or `uv run python3`), NumPy, SciPy `milp`/`linprog` (HiGHS), `fractions.Fraction` exact layer, pytest, LaTeX (TinyTeX + biber, newtx chain already installed).

## Global Constraints

- Definitions are the paper's (one-based): periods 1..T, nodes 1..T+1, prefix π_k = (v_0=1,...,v_k), s = v_k; code is zero-based (nodes 0..T, s_code = s−1). Every count formula must state its convention.
- Strong radius semantics: ρ_{k,w}(d̂) = inf{‖d−d̂‖_{∞,w} : d ≥ ℓ, B_k(d) ≤ A_k(d)} (ties destabilise; infimum attained when finite — paper prop:geometry(b)).
- Exact claims (radii, equalities, infinity) enter the record only through the `fractions.Fraction` layer or a-posteriori exact verification; float MILP outputs are labelled solver-level and re-verified via `certify_strong_witness` before being called certified.
- The Richter–Vörös scan is a personal research copy: record its SHA-256 (`642b0886807ad2e8e686c4e7ccd1ed366569724356f98ce1ca25e6225f826e13`) and page-specific findings; do NOT copy the PDF into the release tree.
- Verified bibliographic facts from the scan header: *J. Inf. Process. Cybern. EIK* **25** (1989) **3**, 67–73; received 11 Nov 1987; stationary costs s, h; scalar-ray parametrisations only; fixed regeneration-point solution retained. (Issue "1" in the first audit doc was ChatGPT's error; the release was already correct at 25(3).)
- Benchmark caps (preregistered before any run): per-solve time limit 120 s; enumeration attempted only when the closed-form candidate count N_out ≤ 2^21 = 2,097,152, else recorded `refused_by_candidate_guard`; grid T ∈ {18,25,35,50,75,100}; families regular / near_tie / adversarial(strict_gap-derived + floor_heavy); 2 replicates per cell; seed lineage from `scripts/_common.py` SEED = 20260804 with documented offsets.
- Existing 66 tests must stay green; every new module gets tests; suite must pass with `.venv/bin/python -m pytest tests/ -q`.
- Version bump 2.1.1 → 2.2.0 (pyproject.toml, CITATION.cff, `wwprefix.__version__` if present, RELEASE_NOTES.md).
- No publication actions (no GitHub push, no Zenodo, no EP page deploy) — package completion only; publication is a separate user-gated step.

---

### Task 0: Version-control safety net

**Files:** none inside the release tree (a nested repo is created only if none exists).

- [ ] Check for an existing `.git` in the working tree; if absent, `git init` a nested repo (pattern precedent: doc-search-mcp), add a baseline commit of the v2.1.1 state.
- [ ] Commit after each completed task with `feat(addendum): ...` messages.

### Task 1 (Item 1): Enumeration-complexity theorem

**Files:**
- Modify: `src/wwprefix/model.py` (add `inside_path_count`, `outside_path_count`)
- Modify: `src/wwprefix/exact.py` (candidate-count disclosure + `max_candidates` guard in `exact_radius_enumeration`)
- Modify: `src/wwprefix/exactcert.py` (same guard in `certified_exact_radius`)
- Test: `tests/test_addendum.py::TestOutsidePathCount`
- Paper: new subsection "Exact size and cost of the released disjunction" with Theorem (outside-path count) + Corollary (Ω(2^{T−2}) candidate generation/storage; 2^{O(T)}poly(L) upper bound; polynomial contrast cases).

**Interfaces:**
- Produces: `outside_path_count(T: int, prefix: Sequence[int]) -> int` (zero-based, exact closed form `2**(T-1) - 2**max(T-1-s,0)` with s = prefix[-1]); `exact_radius_enumeration(..., max_candidates: int | None = None)` raising/returning status `refused_by_candidate_guard` when the closed-form count exceeds the cap BEFORE generation; new `ExactRadiusResult` construction unchanged otherwise.

**Steps:**
- [ ] Write failing tests: closed form equals `len(list(outside_paths(T, prefix)))` for every T ≤ 10 and every valid prefix; historical checks 126976 = 2^17 − 2^12 and 129024 = 2^17 − 2^11 against `results/raw/exact_benchmark.csv` rows with T=18; guard refuses before generation (monkeypatch `outside_paths` to fail loudly if called).
- [ ] Implement count + guards; run tests.
- [ ] Paper: theorem + proof (bijection: complete paths ↔ subsets of internal nodes {2..T}; inside paths ↔ subsets of {s+1..T}; subtraction; first-divergence partition P_T(v_r) − P_T(v_{r+1}) telescopes), corollary on the released routine (quote the atomic generation + sort from `exact.py`), contrast lemma (full path polynomial via frozen certificate = exact there; fixed competitor polynomial).
- [ ] Commit.

### Task 2 (Item 2): Prefix-to-arc decomposition — prove and machine-check

**Files:**
- Create: `src/wwprefix/decomposition.py`
- Test: `tests/test_addendum.py::TestLocalTieLemma`, `::TestDecompositionExact`
- Paper: subsection "Local-tie decomposition of the strong radius": Lemma (pointwise), Theorem (radius decomposition), Corollary (reduction to ≤ k one-arc instances; the one-arc radius is the strong radius of a suffix sub-instance with k=1), Remark (per-arc radii are not monotone in r; worked example where an interior link fails first), Remark (both O_r ≤ E_r with unconstrained V and O_r ≤ W_r with constrained continuation characterise the event; the V-form is the local one).

**Interfaces:**
- Produces:
  - `local_tie_gaps(instance, demand, nominal_path, k) -> list[tuple[float,float]]` returning (O_r, E_r) per protected arc r (float, for fuzz tests);
  - `exact_local_tie_holds(inst: ExactInstance, demand, nominal_path, k) -> bool` (rational, zero-tolerance ∃r O_r ≤ E_r);
  - `sub_instance_for_arc(inst_or_instance, nominal_path, r)` returning (sub_instance, sub_nominal_path) on periods v_r..T−1 with the protected arc first;
  - `decomposed_certified_radius(inst: ExactInstance, nominal_path, k, *, max_paths=None) -> CertifiedEnumerationResult`-like min over r of `certified_exact_radius(sub_r, sub_path_r, 1)` with exact Fraction min and provenance of the minimising arc.

**Mathematical content to write (the actual proofs):**
- Bellman split V_{v_r} = min(E_r, O_r) (first-arc partition, V_{T+1}=0; O_r = +∞ when v_r's only successor is v_{r+1}).
- (⇐) O_r ≤ E_r at some r: the path (prefix to v_r) ⊕ (argmin arc j ≠ v_{r+1}) ⊕ (optimal suffix from j) is outside and costs P_r + O_r ≤ P_r + E_r ≤ P_r + W_r = A_k, so B_k ≤ A_k. (W_r = protected-continuation value; P_r + W_r = A_k telescoping; E_r ≤ W_r since V ≤ W.)
- (⇒) contrapositive: if O_r > E_r for all r < k then V_{v_r} = E_r for all r, so backward induction gives V_{v_r} = W_r; any outside path first diverging at r costs ≥ P_r + O_r > P_r + E_r = P_r + V_{v_r} = P_r + W_r = A_k; hence B_k > A_k.
- Radius corollary: {d : B_k ≤ A_k} = ⋃_{r<k}{d : O_r ≤ E_r}, distance to a finite union = min of distances; each local set closed (finite union of polyhedra via the extended LP description), so attained; ρ_r depends only on coordinates ≥ v_r → suffix sub-instance equivalence.
- Edge cases explicitly: ties (all inequalities weak; consistent with tie-destabilises semantics), zero demands/setups (pure LP algebra, no positivity used), prefix ending at the terminal node (v_k = T+1: A_k = P_k; O/E defined for r < k unchanged), later-link-fails-first (handled by the induction; worked example), some-vs-every optimum (B_k ≤ A_k ⇔ some optimum leaves ⇔ prefix not compulsory for every optimum).

**Steps:**
- [ ] Failing fuzz test (float): 200 seeded random instances (mixed regimes, T ∈ {3..8}), random admissible d in boxes of varied radii: assert `(B ≤ A + tol) == any(O_r ≤ E_r + tol)` with prefix_values as ground truth; plus exact spot-check on 25 instances via `exact_local_tie_holds` vs exact enumeration of inside/outside minima.
- [ ] Failing exact-decomposition test: for the deterministic corpus (regenerate with `random_ww_instance`, regimes regular/near_tie/floor_heavy/strict_gap, T ∈ {3,4,5,6,8,10,12}, ≥ 40 instances, partial prefixes k ≥ 2 where available): `decomposed_certified_radius(...)` == `certified_exact_radius(...)` as exact rationals (both finite equal, or both infinite).
- [ ] Implement `decomposition.py`; run tests.
- [ ] Paper: write the lemma/theorem/corollary/remarks with full proofs; include the worked interior-arc example (construct a T=4 instance during testing where argmin_r is r=1, not r=0; print its data into the paper example).
- [ ] Commit.

### Task 3 (Item 3): NP-membership proposition, strengthened

**Files:**
- Modify: `paper/main.tex` prop:np — replace the terse proof with a full one; add a Lemma (witness size).
- Create: `np_verifier` in `src/wwprefix/decomposition.py` (exact rational verifier realising the proposition).
- Test: `tests/test_addendum.py::TestNPVerifier`.

**Content:** Decision problem WWR (paper prob:decision). Certificate: outside path Q (≤ T+1 nodes) + rational d with encoding length poly(L). Verifier (all in Fraction arithmetic, poly time): validate Q outside π_k; check d ≥ ℓ and w_t|d_t − d̂_t| ≤ R; compute A_k(d) = C_{π_k}(d) + V_s(d) by suffix DP (O(T²) exact operations on rationals whose bit length stays poly — sums of ≤ T+1 products of input rationals); accept iff C_Q(d) ≤ A_k(d). Witness-size lemma: feasibility of the event for fixed Q is feasibility of the extended LP {d, π : box/floor rows, π_s = 0, π_j − π_i ≤ c_ij(d), C_Q(d) ≤ C_{π_k}(d) + π_{T+1}} with O(T²) rows, coefficients of the input; a nonempty rational polyhedron contains a basic (vertex/basic feasible) point whose entries are quotients of subdeterminants, hence encoding length ≤ poly(L) (Cramer + Hadamard bound); cite Schrijver Thm 10.1/Cor 10.2 (add bib entry). Optionality of the promise: nominal optimality checkable by one exact shortest path.

**Steps:**
- [ ] Failing test: `np_verifier` accepts every certified witness in the corpus (from `certified_exact_radius` results with finite radius: witness demand + outside path at R = witness radius) and rejects (a) inside paths, (b) d outside the box, (c) d below floor, (d) non-destabilising d.
- [ ] Implement `np_verifier(inst, nominal_path, k, R: Fraction, Q, d) -> bool`.
- [ ] Paper edits (proposition + lemma + proof; bib entry `Schrijver1986`).
- [ ] Commit.

### Task 4 (Item 4): Compact production-balance MILP

**Files:**
- Create: `src/wwprefix/compactmilp.py`
- Modify: `src/wwprefix/__init__.py` (exports)
- Test: `tests/test_addendum.py::TestCompactMILP` (unit level; corpus equivalence is Task 5)
- Paper: subsection "A compact production-balance exact model": model display, Conversion Lemma with proof, Theorem (exact representation: for every fixed admissible d, min deviating-plan cost = B_k(d); hence the fixed-radius decision and min-radius models are exact), size accounting (T binaries, O(T) continuous, O(T²) rows, no bilinear products), scope note (solver-level unless witness-certified; big-M and R_cap semantics disclosed).

**Model (zero-based, s = prefix[-1]):** variables d_t (T), y_i ∈ {0,1} (T, y_0 = 1), x_i ≥ 0 (T), I_t ≥ 0 (T, I_{T−1} = 0), π_j (j = s..T, π_s = 0); optional radius variable r.
Constraints: I_t = I_{t−1} + x_t − d_t (I_{−1}=0); x_i ≤ M y_i with M = Σ_t upper_d_t (decision mode) or Σ_t (d̂_t + R_cap/w_t) (min-radius mode); deviation row Σ_{i∈gaps(π)} y_i + Σ_{v∈interior protected nodes, v<T} (1 − y_v) ≥ 1 where gaps(π) = {i < s, i ∉ π} and interior protected nodes = π \ {0} minus the terminal if s = T; suffix potentials π_j − π_i ≤ K_i + q_i Σ_{t=i}^{j−1} d_t for s ≤ i < j ≤ T; coupling Σ K_i y_i + Σ q_i x_i ≤ κ_π + β_π·d + π_T + gap-slack (objective in decision mode) ; box rows w_t(d_t − d̂_t) ≤ r, w_t(d̂_t − d_t) ≤ r, d_t ≥ ℓ_t (min-radius mode; fixed bounds in decision mode).

**Conversion Lemma (to prove in paper and encode in docstring):** for any feasible (y, x, I) with y_0 = 1, reassigning every unit of period-t demand to the latest open setup ≤ t yields the zero-inventory plan of the path whose nodes are exactly {i : y_i = 1} ∪ {T}; ordered slopes give cost ≤ Σ K_i y_i + Σ q_i x_i (unit moved from setup i to setup i' ∈ (i, t] has q_{i'} ≤ q_i; unused setups become zero-quantity cycles at identical cost K_i); y is untouched, so the linear deviation row certifies the induced path is outside. Conversely every outside path is a feasible deviating plan of equal cost. Hence min over deviating plans = B_k(d) exactly, including zero demands and zero setup costs.

**API:**
```python
@dataclass(frozen=True)
class CompactMILPResult:
    radius: float | None            # min-radius mode
    decision: bool | None           # decision mode
    minimum_gap_upper_bound: float | None
    revised_demand: np.ndarray | None
    outside_path: Path | None       # induced path from y (conversion lemma)
    inside_path: Path | None
    verified_difference: float | None
    certified_witness: CertifiedWitness | None  # exact re-verification when available
    status: str
    solver_status: int
    mip_gap: float | None
    mip_node_count: int | None
    runtime_seconds: float
    n_variables: int
    n_constraints: int

def compact_fixed_radius_milp(instance, nominal_path, k, radius, *, time_limit=60.0, mip_rel_gap=1e-9, tol=1e-7) -> CompactMILPResult
def compact_radius_milp(instance, nominal_path, k, *, radius_cap, time_limit=60.0, mip_rel_gap=1e-9, tol=1e-7) -> CompactMILPResult
def compact_arc_radius_milp(instance, nominal_path, r, *, radius_cap, ...) -> CompactMILPResult   # one-protected-arc mode via sub-instance
```
Every finite result attempts exact witness certification (`certify_strong_witness` on the snapped rational demand with a repair ladder like `_repair_ladder`); `certified_witness` non-None marks the certified upper bound.

**Steps:**
- [ ] Failing unit tests: 3-period hand instance with known radius (reuse an existing test fixture from test_exactcert.py); decision mode matches `fixed_radius_milp` on both sides of the radius; induced path reconstruction (zero-quantity setup kept as node); infeasible-deviation instance (T=1) → no_outside_path.
- [ ] Implement; run tests.
- [ ] Paper subsection with lemma + theorem + proofs.
- [ ] Commit.

### Task 5 (Item 5): Corpus equivalence gate

**Files:**
- Create: `scripts/run_addendum_equivalence.py` (deterministic; writes `results/raw/addendum_equivalence.csv` + `results/processed/addendum_equivalence_summary.json`)
- Test: `tests/test_addendum.py::TestCorpusEquivalence` (a fast subset; the script covers the full corpus)

**Protocol (the brief's sanity check made executable):** regenerate the exact-certification corpus deterministically (same generators/seed lineage as `run_exact_certification_audit.py`, T ≤ 18 strata) plus the exact-benchmark instances (T ∈ {6,10,14,16,18} × {regular, near_tie, strict_gap} × 2 replicates). For every instance and protected k tested by the release: run `compact_radius_milp` (radius_cap from the certified bracket upper/frozen value ×4 + spread) and `decomposed` check where T ≤ 12; assert (a) finite cases: |milp − exact| ≤ 1e-6·(1+exact) AND certified_witness.radius (exact rational) ≥ exact lower AND ≤ exact + 1e-9 slack ⇒ report `exact_match` when certify closes; (b) infinite cases: decision MILP at probe radius 4·(1+spread+frozen-anchor) returns decision False (consistent, labelled solver-level; exact ∞ certificates remain with the exact layer); (c) full-path cases included. Output columns: instance_id, stratum, T, k, exact_radius, milp_radius, certified_upper, match_class, runtimes, nodes. **Gate: zero disagreements before Task 6 may run** (the brief: no scalability claim until every existing exact T ≤ 18 radius, witness and infinite-radius result is reproduced).

**Steps:**
- [ ] Write script + fast pytest subset; run subset.
- [ ] Run full script; inspect summary; fix model bugs if any disagreement (systematic-debugging if needed); re-run to zero disagreements.
- [ ] Commit (script + results CSVs).

### Task 6 (Item 6): Preregistered scaling benchmark

**Files:**
- Create: `docs/benchmark_preregistration_addendum.md` (FROZEN BEFORE RUNS; SHA-256 of the frozen text recorded in the results JSON)
- Create: `scripts/run_addendum_benchmark.py` → `results/raw/addendum_benchmark.csv`, `results/processed/addendum_benchmark_summary.json`
- Paper: audit-section subsection reporting the benchmark with the prereg hash.

**Preregistration content (fixed now):** grid T ∈ {18,25,35,50,75,100}; families: regular, near_tie, adversarial (floor_heavy at all T + strict_gap-derived where the generator supports T); 2 replicates; prefix selection: nominal optimal path, k = ceil(m/2) partial prefix (plus full-path row at T=18 for the polynomial contrast); methods: (M1) exhaustive `exact_radius_enumeration` — attempted only when N_out ≤ 2^21, else `refused_by_candidate_guard` (count disclosed from closed form); (M2) existing arc-product `fixed_radius_milp` at the certified bracket midpoint (decision probe); (M3) `compact_radius_milp` (min-radius); (M3b) `compact_fixed_radius_milp` at the same probe radius as M2; (M4) polynomial certificate alone (`exact_polynomial_bracket`). Caps: 120 s per solve (M1: 300 s + candidate guard); memory measured via `resource.getrusage` deltas (not enforced); record wall time, peak-RSS delta, `mip_node_count`, `mip_gap`, bounds, status, unresolved-under-cap. Primary comparisons preregistered: (P1) largest T with exact resolution per method; (P2) M3 vs M2 wall time and node count at common resolved cells; (P3) M4 bracket width vs exact where known. Analysis: descriptive tables only, no significance tests. Seeds: SEED + 7000 + index. Hard instances included by family construction (near_tie, floor_heavy), acknowledged not adversarially optimised beyond the release's existing generators.
**Honesty rule:** any deviation from the prereg (crash, cap change) is recorded in the results JSON `deviations` list, never silently.

**Steps:**
- [ ] Write prereg doc; hash it; commit BEFORE the benchmark script runs.
- [ ] Write runner; smoke-test at T=18 only (`--smoke`); then full run in background; monitor.
- [ ] Summarise into processed JSON + paper table; note M1 refusals as findings (the practicality settlement).
- [ ] Commit results.

### Task 7 (Item 7): Richter–Vörös prior-art matrix + bibliography

**Files:**
- Modify: `docs/literature_audit.md` (move R–V 1989 to "Full text inspected"; page-specific comparison matrix; scan hash + no-redistribution note; retire the acquisition dossier to an archival subsection marked resolved; keep Richter 1987 EJOR + R&V EJOR-programme papers as metadata-only, now explicitly lower priority)
- Modify: `paper/main.tex` sec:literature paragraph (full-text inspection result), sec:scope "Novelty uncertainty" paragraph (retire the conditional-originality caveat; new wording per the audit's verified verdict), assurance/conclusion touches where "pending print acquisition" appears
- Modify: `paper/references.bib` (RichterVoros1989 entry: confirm 25(3) 67–73, add inspection note; add Schrijver1986 if not present from Task 3)
- Modify: `docs/voros_offprint_request_draft.md` (mark resolved — full text obtained 2026-08-17/18; keep for the record)
- Test: none (docs); but grep-gate: no remaining "full text was unavailable"/"pending print acquisition"/"conditional pending" phrasing anywhere in paper/docs except historical-record sections explicitly marked as superseded.

**Matrix rows (verified against the scan by direct reading, 2026-08-18):** model (stationary s,h vs period-dependent K_i, q_i); parametrisation (scalar a for costs, scalar b along d̂ for demand, joint (a,b) region vs simultaneous T-dimensional weighted L∞ ball with floors); retained object (fixed regeneration-point solution {k(t)} vs protected prefix face with moving best continuation); stability semantics (parameter region where the fixed solution stays optimal vs strong compulsory-prefix radius with tie destabilisation); algorithmics (systems of inequalities per regeneration point, IBM-XT timings T ≤ 15 vs certified brackets, parametric SP, exact escalation, complexity classification); complexity theory (none vs NP-membership + exponential-enumeration theorem + open one-arc core). Verdict: direct antecedent, no theorem-level collision; novelty wording narrowed accordingly.

**Steps:**
- [ ] Rewrite literature_audit.md; update bib; update paper paragraphs; grep-gate.
- [ ] Commit.

### Task 8: Paper assembly, version bump, full verification, adversarial review

**Files:**
- Modify: `paper/main.tex` (new addendum section integrated after sec:exact; sec:scope "Open exact complexity" rewritten around the one-arc core; audit section extended; conclusion updated; notation table additions E_r, O_r, N_out)
- Modify: `pyproject.toml`, `CITATION.cff`, `release/RELEASE_NOTES.md` (v2.2.0 entry listing the seven items)
- Modify: `README.md` (assurance-relevant statements: exponential enumeration disclosed, compact model, R–V resolved)

**Steps:**
- [ ] Compile paper (latexmk + biber); fix LaTeX errors; visual sanity of new section.
- [ ] Full test suite + both new scripts' summaries green; `outside_path_count` cross-checked against every historical paths_total.
- [ ] Version bump + release notes.
- [ ] Sol adversarial review (standing permission; OpenAI `/v1/responses`, model gpt-5.6-sol, refute-framing) on: Theorem (count), Lemma+Theorem (decomposition), Conversion Lemma, NP proposition. Verify each claim in any reply computationally before acting (audit discipline). Record outcome in docs.
- [ ] Final commit; session report.

## Self-Review

- Spec coverage: items 1→Task 1, 2→Task 2, 3→Task 3, 4→Task 4, 5→Task 5, 6→Task 6, 7→Task 7; the brief's "Immediate correction" (25(3)) is Task 7 + already-correct release confirmed; the brief's sanity check (no scalability claim before equivalence) is the Task 5 gate blocking Task 6. The audit's operational recommendations (N_out disclosure + refusal guard) are Task 1 code.
- Type consistency: `CompactMILPResult` consumed by Tasks 5/6; `outside_path_count` consumed by Tasks 1/6; `decomposed_certified_radius` consumed by Tasks 2/5; `CertifiedWitness` reused from exactcert.
- No placeholders: theorem statements, proofs obligations, model rows, column schemas, caps and seeds are specified above.
