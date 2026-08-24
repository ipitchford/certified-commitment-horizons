# Full peer-review report

**Manuscript:** *Certified Commitment Horizons in Dynamic Lot Sizing: Prefix Stability, Inverse Shortest Paths and Calibrated Forecast Revisions*
**Version reviewed:** Preprint v1.0.0, 4 August 2026
**Review date:** 4 August 2026
**Editorial recommendation:** **Major revisions**
**Confidence:** **High, 0.86**
**Concern classification:** No fatal defect identified; eight major concerns; minor reporting and presentation issues listed separately.

## 1. Executive assessment

This preprint develops a strong prefix-stability radius for deterministic single-item Wagner–Whitin lot sizing: the smallest admissible demand revision at which an optimal schedule may leave the first (k) cycles of a selected nominal optimum. Its strongest feature is the layered construction. The manuscript moves from exact fixed-competitor geometry, through a polynomial frozen-comparator lower certificate and exact disjunctive formulations, to one-step conformal calibration and a rolling structural-loss bound. The three-period example is effective, and my independent recalculations reproduce its path costs and the 1.5-versus-2 certificate gap.

I recommend **major revisions**, with high confidence. I found no fatal mathematical contradiction, and the central prefix-face idea appears potentially publishable. The decisive weaknesses are nevertheless substantial. First, originality is not yet secured: a directly relevant 1989 paper studies parametric dynamic lot sizing, including demand-vector changes and stability regions, but is absent from the review; available evidence is abstract-only, so a full-text theorem-level comparison is essential. ([ACM Digital Library][1]) Second, the code, raw results and replay environment claimed in the manuscript were not supplied, leaving all computational claims unreproduced. Third, the proof of the central polynomial certificate contains a repairable but genuine logical gap and omits algorithmic edge cases. Finally, “operationally complete” overstates what is established by a one-item, uncapacitated, synthetic study, a one-step marginal conformal guarantee and a rolling theorem that commits structure rather than literal quantities. These matters may change the novelty, credibility and scope of the conclusions.

## 2. Scope and evidence limits

| Item                         | Review assessment                                                                                                                                                                                                                                                                                     |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Manuscript type**          | Theoretical and computational operations research paper, with an applied decision-support interpretation.                                                                                                                                                                                             |
| **Primary field**            | Dynamic lot sizing, inverse optimisation, combinatorial sensitivity analysis and rolling-horizon planning.                                                                                                                                                                                            |
| **Materials inspected**      | The complete 22-page manuscript PDF, including appendices, figures, tables and references; and the supplied 12-point REF calibration rubric.                                                                                                                                                          |
| **Materials not supplied**   | The claimed command-line release, source code, raw comma-separated data, frozen environment files, solver logs, machine-readable test manifests, search record and independent reproduction report. Their absence does not establish that they were not created; it means they could not be reviewed. |
| **Journal standard applied** | A selective international operations research or operations management journal. No journal-specific criteria were supplied.                                                                                                                                                                           |
| **Manuscript evidence**      | The mathematical statements, examples, numerical summaries and disclosures in the PDF.                                                                                                                                                                                                                |
| **External evidence**        | Live literature and REF searches documented in Section 6.                                                                                                                                                                                                                                             |
| **Reviewer inference**       | Judgements about novelty, likely operational usefulness, repairability and editorial priority. These are identified where uncertainty matters.                                                                                                                                                        |
| **Numerical access limit**   | I could recalculate quantities from the reported equations and construct independent small tests, but I did not have the authors’ raw simulation rows or computational implementation.                                                                                                                |

The paper is best assessed primarily as a **theoretical contribution with a computational audit**, not yet as a validated operational system. Its synthetic calculations are relevant to implementation correctness but do not establish external validity or industrial value.

## 3. Contribution and positioning

### 3.1 Strongest defensible thesis

The strongest thesis supported by the submitted manuscript is:

> For the deterministic, single-item, uncapacitated Wagner–Whitin model, one can measure the weighted demand-space distance to the nearest instance on which an optimal path may leave a selected nominal prefix. Although the exact moving-prefix problem is left open in complexity, a floor-aware frozen-comparator lower bound is polynomially computable; exact finite disjunctive formulations are available; and the same deterministic radius can be combined, under additional assumptions, with one-step revision calibration and a structural rolling-loss bound.

That is a substantial and coherent thesis. It is narrower than the manuscript’s concluding claim of an “operationally complete” system.

### 3.2 Claim-to-evidence map

| Main claim                                                                                                           | Manuscript evidence                                                 | Assessment                                                                                                                               |
| -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| The strong prefix-stability radius is a well-defined distance to loss of compulsory-prefix optimality.               | Definition 1.1 and Proposition 1.3, pp. 3–4.                        | Clear and mathematically well motivated. The dependence on a selected nominal optimum requires more treatment.                           |
| Ordered Wagner–Whitin slopes give affine path costs and Monge structure.                                             | Propositions 3.1–3.2, pp. 5–6.                                      | Algebraically correct on review. The manuscript appropriately does not claim that Monge structure alone solves the exact radius problem. |
| The fixed-path tie radius is exactly computable under weighted boxes and demand floors.                              | Theorem 4.1, pp. 6–7.                                               | Correct coordinate-separable construction.                                                                                               |
| A polynomial frozen-comparator lower certificate exists and is exact for a protected full path.                      | Theorems 5.1–5.2, pp. 7–9; Appendix A, p. 19.                       | Central and potentially important, but its proof and algorithm specification need repair and expansion.                                  |
| The lower certificate may be strict for a partial prefix.                                                            | Proposition 6.1 and Figure 1, pp. 9–10.                             | Convincing; independently reproduced.                                                                                                    |
| Exact analysis is possible by fixed-competitor inverse linear programmes and a fixed-radius mixed-integer programme. | Theorems 7.1–7.2, pp. 10–12.                                        | Structurally sound, but practical exact scalability is not demonstrated beyond very small horizons.                                      |
| A conformal threshold converts revision history into a one-step marginal commitment guarantee.                       | Theorem 8.1 and Corollary 8.2, pp. 12–13.                           | The rank argument is standard and valid under its assumptions, but the domain and sequential interpretation need tightening.             |
| Bellman residuals yield a rolling loss bound with a radius-dependent dead zone.                                      | Lemmas 9.1–9.2 and Theorem 9.3, pp. 13–14.                          | Mathematically plausible and supported by independent small tests; its operational semantics and edge cases are incompletely stated.     |
| The method has been computationally audited.                                                                         | Section 10, Figure 2 and Table 1, pp. 14–16; Appendix C, pp. 19–20. | Reported audit is useful but could not be reproduced from the supplied materials.                                                        |

### 3.3 Originality and significance

The likely distinctive contribution is not the generic concept of a stability radius, nor demand-vector sensitivity of a fixed lot-sizing solution. It is the focus on a **prefix face**, where the best prefix-retaining continuation may switch, together with the floor-aware frozen lower certificate and its integration with exact inverse formulations and a dead-zone rolling bound.

That originality is presently **plausible but unproven**. The literature review overlooks earlier work explicitly described as finding stability regions for parameterised dynamic lot sizing, including demand-vector parameterisation. Moreover, the cited 1993 lot-sizing sensitivity paper itself explains that preceding papers considered simultaneous parameter changes and maximal stability regions. ([RePub][2]) The manuscript therefore needs to identify exactly which components are inherited, specialised, strengthened or genuinely new.

The practical question is significant: production and supply plans can be destabilised by repeated forecast revisions. However, the present evidence establishes theoretical and prototype significance, not demonstrated operational impact. Current applied work evaluates forecast evolution or plan stability on real data and with service, inventory or delivery measures, providing a substantially higher external-validity benchmark than the synthetic audit here. ([IDEAS/RePEc][3])

## 4. Major comments

### 1. The novelty claim is not secure because a directly relevant antecedent is omitted

**Issue.**
The external positioning does not adequately cover prior parametric and simultaneous-perturbation analysis of dynamic lot sizing. This is a **major** concern because it could alter which theorem is actually novel.

**Manuscript evidence.**
Section 2, pp. 4–5, calls van Hoesel and Wagelmans (1993) the closest deterministic antecedent and reports that a search frozen on 4 August 2026 did not locate a source combining the paper’s components. Richter and Vörös (1989) is absent from the manuscript’s discussion and reference list.

**Why it matters.**
The available abstract for Richter and Vörös states that the paper considers three parameterisations, one of which is the demand vector, and derives parameter stability regions within which a Wagner–Whitin solution remains valid. This assessment is abstract-only and does not establish that the current prefix-face result is subsumed. It does, however, make the omission decision-relevant. ([ACM Digital Library][1]) The full-text 1993 sensitivity paper explicitly characterises preceding work as studying simultaneous parameter changes and maximal regions preserving an optimal solution. ([RePub][2]) Generic stability-radius work also already provides polynomial algorithms for fixed optimal min-sum solutions when the underlying combinatorial problem is polynomially solvable. ([Tinbergen Papers][4])

The manuscript’s likely novelty may survive: a prefix class with a moving best continuation is materially different from preserving one fixed path. But that distinction must be demonstrated, not inferred from a bounded negative search that missed an indexed paper with an almost exact topic description.

**Required revision or decisive test.**

1. Obtain and analyse the full Richter–Vörös paper and the closely related sequential-stability literature.
2. Add a theorem-by-theorem comparison covering:

   * fixed solution versus prefix face;
   * simultaneous demand-vector changes;
   * weighted (L_\infty) geometry and demand floors;
   * correlated arc-cost perturbations induced by demand;
   * exact radius versus conservative lower certificate;
   * computational complexity;
   * horizon or prefix monotonicity.
3. Explain whether full-path exactness in Theorem 5.1 is a specialisation or extension of existing fixed-solution stability-radius results.
4. Replace the present priority-style search statement with a narrower claim until the comparison is complete.
5. Treat substantial subsumption of the prefix result by the earlier literature as a decision-changing outcome.

### 2. The claimed computational release was not supplied, so the audit cannot be verified

**Issue.**
All computational evidence is presently manuscript-reported rather than independently inspectable. This is a **major reproducibility concern**, not an allegation that the computations were not performed.

**Manuscript evidence.**
The verification disclosure on p. 1 says that the release includes deterministic tests, raw synthetic results and one-command replay. Section 10 and Appendix C describe a frozen environment, named scripts and cross-checks. The operational protocol on pp. 16–17 refers to command-line operations. None of these artefacts was included in the supplied review package, and the PDF provides no usable archive identifier, repository commit or supplemental bundle.

**Why it matters.**
The numerical claims are central to four parts of the argument:

* exact agreement in 569 lower-certificate checks;
* the distribution of lower-to-exact ratios over 129 finite instances;
* practical scaling to (T=160);
* the conformal and rolling-bound simulations.

Without raw rows, generator specifications and executable code, it is impossible to check whether reported totals correspond to all generated instances, how infinite or failed cases were handled, whether solver statuses were filtered, or whether reported tolerances reproduce the claimed boundaries. The phrase “129 finite instances” is especially important: excluding infinite, unresolved or failed cases can be appropriate, but the total generated count and exclusion manifest are not reported. This is a selective-reporting **risk indicator**, not evidence of selective reporting.

**Required revision or decisive test.**

Provide a permanently archived release containing:

* source code and exact commit hash;
* licence and citation metadata;
* environment lockfile or container;
* raw data underlying every table and figure;
* the complete instance manifest, including infinite, infeasible, failed and timed-out cases;
* exact random-number generation logic and all distribution parameters;
* sample sizes for every experiment;
* solver names, versions, tolerances, status codes and retained logs;
* hardware and thread settings;
* commands that reconstruct all tables and figures from a clean environment;
* directly checkable witnesses for feasible exact-radius decisions;
* certificates, bounds or carefully qualified status for negative mixed-integer results.

At least one clean-room execution by someone not involved in creating the implementation should be reported. Until then, describe the evidence as a **producer-side computational audit**, which the manuscript itself partly acknowledges.

### 3. The proof and algorithm specification for the polynomial certificate are incomplete

**Issue.**
Theorem 5.2 is the central algorithmic result, but its proof contains a logical gap and leaves several boundary cases implicit. The result appears repairable; I did not find a counterexample.

**Manuscript evidence.**
Theorem 5.2, pp. 8–9, transforms a linear-fractional path problem using Charnes–Cooper. Appendix A, p. 19, states that a feasible ((y,\tau)) has (\tau>0) “because ((b^\ell)^\top y=1)”.

**Why it matters.**
That normalisation establishes (y\neq0), but does not by itself imply (\tau>0). If (\tau=0), the flow equation becomes (Ny=0). To exclude this case, the proof must invoke a property of the expanded network: because it is acyclic and (y\ge0), it has no non-zero non-negative circulation, so (Ny=0) forces (y=0), contradicting the normalisation. This is probably the intended argument, but it is not written.

The proof also relies on several under-specified elements:

* a formal definition of every state and arc of the prefix-deviation graph;
* a proof of one-to-one correspondence between its source–sink paths and (O_k);
* treatment of coincident and zero floor breakpoints;
* endpoint conventions between adjacent intervals;
* paths whose denominator is zero;
* the final interval and the condition for an infinite radius;
* extraction of an actual path and adversarial revision from a possibly non-unique LP optimum;
* rational encoding length and the precise polynomial-time claim;
* the distinction between an exact rational theorem and a floating-point implementation.

**Required revision or decisive test.**

1. Insert a formal graph definition, preferably with pseudocode and a small diagram.
2. Add a lemma proving that (Ny=0,;y\ge0) has only the zero solution in the expanded directed acyclic graph.
3. State and prove the interval endpoint, repeated-breakpoint, zero-denominator and infinite-radius cases.
4. Give an explicit input-size complexity bound, not only graph dimensions and the number of linear programmes.
5. Explain how an optimal path, radius and worst revision are recovered and checked.
6. Supply at least one rational primal–dual certificate example or an outward-rounded implementation protocol consistent with Remark 5.3.

### 4. “Operationally complete” is not supported by the model scope or validation evidence

**Issue.**
The conclusion overstates the level of operational validation. This is a **major inference and significance concern** rather than a defect in the mathematical core.

**Manuscript evidence.**
Section 10 explicitly says that the synthetic generators are not models of industrial demand. Section 12 lists omitted capacities, lead times, minimum order quantities, service constraints, multiple items and other features. Nevertheless, p. 18 describes the layered result as “operationally complete”, and Section 11 presents a deployment protocol.

**Why it matters.**
The paper establishes a certificate for one uncapacitated item under no speculative motive, no backlogging and structural zero-inventory-ordering schedules. It does not demonstrate that the certificate improves a realised business outcome, how weights and floors would be estimated, or how often exact escalation is computationally usable.

Relevant applied work sets a higher empirical benchmark. Forel and Grunow evaluate rolling-horizon forecast-evolution models on synthetic and real-world data and report realised-cost comparisons. ([IDEAS/RePEc][3]) Weijers and co-authors evaluate plan stability, on-time delivery and inventory position using real semiconductor data. ([informs-sim.org][5]) These studies do not invalidate the present theoretical contribution, but they show what evidence is needed for strong operational claims.

**Required revision or decisive test.**

Choose one of two defensible routes:

* **Theory/prototype route:** replace “operationally complete” with wording such as “methodologically integrated within the stated Wagner–Whitin model”; qualify Section 11 as a proposed protocol; and remove implications of validated deployment.
* **Operational-evidence route:** add at least one forecast-vintage case study using aligned historical revisions and realised demand. Compare the proposed policy with a fixed time fence, unrestricted reoptimisation and at least one conventional rolling-horizon alternative. Report commitment length, number and magnitude of structural plan changes, realised cost, service consequences, frequency and runtime of exact escalation, and sensitivity to (w), (\ell) and (\alpha).

A stylised case is useful but would not by itself justify “operationally complete”.

### 5. The conformal result needs a more precise domain and sequential interpretation

**Issue.**
Theorem 8.1 is a valid one-step rank statement, but Corollary 8.2 is presented more broadly than its assumptions support.

**Manuscript evidence.**
The calibration scores are (S_i=|E_i|_{\infty,w}), and Corollary 8.2 states that if the conformal threshold is strictly below the deterministic certificate, the probability that the next revised optimum can leave the protected cycles is at most (\alpha). The text correctly notes that exchangeability is an assumption and reports severe simulated degradation under scale shift.

**Why it matters.**

1. The guarantee is **marginal over the calibration data and next score**, not conditional on the realised calibration set, product state or current forecast.
2. Repeating the rule across many replans, products or decision dates does not give a time-uniform or family-wise guarantee at level (\alpha).
3. The deterministic implication is defined only for revised demand satisfying (d\ge\ell). Corollary 8.2 does not explicitly assume
   [
   \widehat d+E_{n+1}\ge\ell
   \quad\text{almost surely},
   ]
   or otherwise account for revisions outside the admissible domain.
4. Any adaptive choice of weights, product grouping, horizon alignment or missing-data treatment using the same calibration scores can invalidate the simple rank argument unless incorporated into the exchangeable scoring procedure.

Research on conformal prediction beyond exchangeability and adaptive online conformal inference offers relevant alternatives but under different guarantees and assumptions. ([Project Euclid][6])

**Required revision or decisive test.**

* State the one-step claim explicitly as a marginal guarantee.
* Define the next revised vector as (d_{n+1}=\widehat d+E_{n+1}) and impose or verify its admissibility relative to (\ell).
* State that no simultaneous or long-run guarantee follows from repeated application without additional control.
* For repeated deployment, either provide a sequential procedure with an appropriate theorem, use a prespecified finite-horizon error allocation, or limit the claim to per-decision marginal validity.
* Report calibration sample size, grouping rule, treatment of ties, missingness, vintage alignment and any model-selection step.
* Present exchangeability and drift diagnostics as model checks, not as proof that exchangeability holds.

### 6. The practical scalability of exact escalation is unresolved

**Issue.**
The exact formulations are mathematically finite, but the manuscript does not establish that the recommended escalation step is usable beyond toy instances.

**Manuscript evidence.**
The exact mixed-integer and disjunctive models are cross-checked only for (T=3,\ldots,6) in Section 10. The scaling results to (T=160) concern the polynomial lower certificate, not the exact radius. Table 1 reports that pruned enumeration solved a median 6.25% of outside paths, but does not provide absolute path counts, runtime distributions, timeouts or worst cases. Section 11 nevertheless recommends exact escalation near operationally important boundaries.

**Why it matters.**
The number of McCormick products is polynomial, but mixed-integer solution time need not be. The finite disjunction remains exponentially large in the worst case. Median pruning percentages can conceal highly difficult instances, and percentages alone can decline while the absolute number of paths grows rapidly.

The lower certificate’s usefulness also depends on the cost of resolving non-certification. A cheap conservative test is operationally valuable only if unresolved cases can be handled transparently rather than implicitly treated as safe or unsafe.

**Required revision or decisive test.**

Provide an exact-solver benchmark that reports:

* horizon and number of nominal cycles;
* total and processed outside paths;
* runtime quantiles, not only medians;
* optimality gaps, node counts and solver statuses;
* counts of timeouts and unresolved cases;
* distance between certified lower and feasible upper bounds at termination;
* separate results for the MILP, pruned disjunction and exhaustive enumeration where possible;
* performance near degenerate or nearly tied instances;
* sensitivity to floors, weights and numbers of distinct slopes.

If only very small cases are tractable, retain the formulations as exact theoretical baselines and narrow the operational escalation claim accordingly.

### 7. Dependence on an arbitrarily selected nominal optimum is not resolved

**Issue.**
The certificate is conditional on one selected nominal path, while operational conclusions can change under nominal degeneracy.

**Manuscript evidence.**
Definition 1.1 protects the prefix of a selected (P^\star). Proposition 1.3(d) correctly notes that a nominal outside tie implies radius zero. Step 2 of the operational protocol instructs the user to select and record one tie-broken optimal path but does not prescribe a stability-aware or reproducible tie-breaking rule.

**Why it matters.**
Two nominally optimal paths can have different early setup epochs. The resulting certificate may therefore depend on solver-specific tie-breaking rather than economic information. A radius of zero can mean that the nominal problem already permits a different prefix, not that an infinitesimal forecast movement has caused a meaningful instability. Conversely, selecting one path from a degenerate optimal face can make the apparent commitment horizon arbitrary.

This does not invalidate the conditional mathematical definition, but it weakens its interpretation as an objective decision fence.

**Required revision or decisive test.**

At minimum:

1. State prominently that the reported radius is conditional on (P^\star).
2. Prescribe a deterministic and auditable tie-break.
3. Detect and report whether alternative nominal optima have different protected prefixes.
4. Consider one of the following robustness outputs:

   * the longest prefix common to all nominal optimisers;
   * the minimum and maximum certificate over nominal optimal paths;
   * a secondary optimisation selecting a nominal optimum for stability under a disclosed criterion.
5. Include degenerate and near-degenerate instances in the computational audit.

### 8. The rolling theorem needs explicit admissible-domain, information and quantity semantics

**Issue.**
Theorem 9.3 appears mathematically sound under the structural path interpretation, but its present wording invites a stronger operational reading than the proof supports.

**Manuscript evidence.**
The manuscript states on p. 3 that the radius freezes setup epochs and cycle boundaries, not literal quantities. The rolling theorem then prices an implemented block by (C_\pi(d)), replans at its endpoint, and states the bound “for every realised (d)”. The proof uses a radial projection onto the radius ball. No separate case is given for (\rho=\infty).

**Why it matters.**

* The theorem should apply to (d) in the floor-constrained admissible domain, not literally every vector.
* If (\rho=\infty), the projection
  [
  f+\frac{\rho}{|d-f|}(d-f)
  ]
  is undefined. The infinite-radius case is simple but must be stated separately.
* (C_\pi(d)) assumes that the setup structure chosen from the forecast can serve the realised cycle demand. Operationally, this entails quantity recourse or retrospective assignment of actual demand to the chosen setup block.
* Replanning at a cycle endpoint as a zero-inventory state similarly presumes that realised cycle demand has been exactly covered.
* A literal supplier order often commits quantity, capacity or delivery slots as well as timing. The theorem does not presently cover those consequences.

**Required revision or decisive test.**

Restate Theorem 9.3 with:

1. (d\ge\ell) as an explicit domain condition;
2. separate finite-(\rho), zero-(\rho) and infinite-(\rho) cases;
3. a proof that an inside optimum remains globally optimal on the closed radius ball, including boundary ties;
4. an explicit information structure describing what is fixed at the beginning of a block and what remains adjustable;
5. a statement that the regret is for structural setup decisions with quantity recourse, unless a fuller inventory-dynamics model is supplied;
6. a precise relationship between forecast revision dates, realised demand revelation and cycle-boundary replanning.

The conclusion and operational protocol should use the same semantics.

## 5. Rigour, results and inference

### 5.1 Theoretical audit

I found the following parts convincing on direct inspection:

* Proposition 3.1’s decomposition into a path-independent holding-cost term and reduced ordered-slope arc costs.
* Proposition 3.2’s Monge inequality.
* The affine path representation in Equation (6).
* The coordinatewise floor-aware fixed-path radius in Theorem 4.1.
* The validity of the frozen-comparator lower bound and its full-path exactness in Theorem 5.1.
* The suffix-potential representation in Theorem 7.1.
* The binary-product construction underlying Theorem 7.2.
* The conformal rank calculation in Theorem 8.1.
* The telescoping identity in Lemma 9.1.
* The ordered-slope diameter in Lemma 9.2.

The main theoretical weakness is not an observed false result but the incomplete proof and specification of Theorem 5.2. The exact-complexity claim is appropriately limited: the manuscript proves only membership in NP and explicitly leaves hardness versus polynomial solvability open.

Proposition 3.3 should nevertheless specify whether nominal optimality of (P^\star) is a promise or part of the language. Because shortest-path optimality is polynomially checkable, this is readily repaired.

### 5.2 Independent recalculations

The following are **reviewer calculations from the manuscript’s equations**, not reproductions of the absent release.

| Check                                               |                                                                                               Recalculated result | Interpretation                                                                                                                                                        |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| All four paths in the (T=3) example                 |                                            (C_{(1,4)}=14); (C_{(1,2,4)}=11); (C_{(1,3,4)}=14); (C_{(1,2,3,4)}=12) | Confirms the selected nominal path and nominal gaps.                                                                                                                  |
| Frozen pairwise radii for the two outside paths     |                                                                                                   (2.5) and (1.5) | Confirms the polynomial lower certificate (\underline\rho=1.5).                                                                                                       |
| Exact fixed-competitor disjuncts                    |                                                                            (2.5) for ((1,4)); (2.0) for ((1,3,4)) | Confirms exact strong radius (\rho=2).                                                                                                                                |
| Continuous path relaxation at proposed radius (R=1) |                          A feasible half-integral flow exists; one reconstruction uses (z_{13}=z_{14}=z_{34}=0.5) | Supports the manuscript’s claim that the natural continuous relaxation is not exact.                                                                                  |
| Table 1 tight-count percentage                      |                                                                                                 (36/129=27.9069%) | Consistent with the reported 27.9%. The integer numerator should be reported.                                                                                         |
| Equal-scale conformal row                           |                                        (0.8964) is about (1.30) reported Monte Carlo standard errors below (0.90) | Consistent with the stated nominal level. Under a binomial-SE calculation, the rounded numbers imply approximately 12,000 trials; the actual number should be stated. |
| Ordered-slope diameter                              |                          Independent enumeration on random ordered-slope cases with (T\le6) matched Equation (34) | Supports Lemma 9.2; not a proof.                                                                                                                                      |
| Rolling bound                                       | No violation in 4,000 independent small numerical checks: 200 random instances with 20 realised-demand draws each | Increases confidence in implementation of the displayed theorem, but does not replace its proof or reproduce the authors’ 220 cases.                                  |

### 5.3 Agreement among text, tables and figures

The principal reported numbers are internally aligned:

* the abstract’s 569 lower-certificate checks and 220 rolling cases match Table 1;
* the 1.5-versus-2 example matches Figure 1 and Proposition 6.1;
* Figure 2’s equal-scale coverage is consistent with Table 1’s 0.8964;
* the 27.9% tightness figure is arithmetically consistent with 36 out of 129 cases.

However, internal agreement is not reproducibility. The reported summaries do not reveal:

* the total number of exact instances generated before restricting to 129 finite instances;
* the incidence of solver failures or unresolved statuses;
* exact sample sizes in the calibration experiment;
* the full distribution of exact runtimes;
* realised regret relative to the reported bound on the original scale;
* whether all analysis choices were fixed before viewing results.

These are transparency gaps. They indicate possible analytic flexibility but do not support an allegation of p-hacking or selective reporting. A complete manifest and raw outputs would substantially reduce the concern.

### 5.4 Practical versus mathematical importance

The polynomial certificate is mathematically meaningful even when conservative. The reported median lower-to-exact ratio of 0.778 suggests potential usefulness, while the tenth percentile of 0.396 shows that conservatism can be material. Yet a ratio alone does not establish business value: committing one additional cycle may be either negligible or critical depending on lead times, setup costs and supplier constraints.

Likewise, reducing a median generic rolling bound from 719.2 to 298.2 demonstrates a mathematical dead-zone effect, but the manuscript does not report enough about the corresponding realised regret distribution to assess whether either bound is operationally informative. The practical interpretation should therefore remain provisional.

## 6. External literature check

### 6.1 Search record

**Review date:** 4 August 2026.

**Sources searched:** ACM Digital Library, publisher and DOI records, SpringerLink, ScienceDirect-indexed records, Erasmus RePub, the Tinbergen Institute repository, Project Euclid, INFORMS Winter Simulation Conference proceedings, arXiv/OpenReview records, general scholarly web search and official REF 2029/REF 2021 sources.

**Representative search strings:**

* `"Certified Commitment Horizons in Dynamic Lot Sizing"`
* `"WW-Prefix-Radius"`
* `"prefix stability" "dynamic lot sizing"`
* `dynamic lot sizing demand perturbation stability region`
* `parametric dynamic lot sizing demand vector Wagner Whitin`
* `economic lot sizing sensitivity simultaneous parameter changes`
* `stability radius combinatorial optimisation shortest path`
* `forecast evolution rolling horizon lot sizing`
* `plan stability semiconductor rolling horizon`
* `conformal prediction exchangeability distribution shift online`
* `REF 2029 Unit of Assessment 17 panel criteria`

**Inclusion logic:** direct deterministic lot-sizing stability papers; generic stability-radius work bearing on the claimed mathematics; recent rolling-horizon or forecast-evolution work bearing on significance; conformal work bearing on exchangeability and sequential use; and official REF guidance.

**Access limits:** Full text was inspected for van Hoesel and Wagelmans, the Chakravarti and Wagelmans working-paper version, Weijers and co-authors, and the REF panel document. Richter and Vörös and Richter and Weber were assessed through indexed metadata and available abstracts. Forel and Grunow was assessed through its publisher-supplied abstract and bibliographic record. This was a targeted, non-exhaustive search, not a systematic review.

### 6.2 Pivotal literature

**Richter and Vörös (1989).**
This is the most consequential omission. Its available abstract describes parametric dynamic lot sizing with setup/holding costs, the demand vector, and combined cost-demand parameterisation, with stability regions preserving a Wagner–Whitin solution. Because full text was not obtained, I cannot determine whether it covers weighted norm radii, floors or a prefix class rather than one full solution. The paper must nevertheless be treated as a direct antecedent, not a peripheral citation. ([ACM Digital Library][1])

**van Hoesel and Wagelmans (1993).**
The manuscript cites this paper, but the comparison is too brief. It studies maximal individual parameter ranges preserving an economic lot-sizing solution and explicitly positions earlier papers as analysing simultaneous changes and maximal stability regions. This historical account contradicts the implication that the 1993 paper is the sole or necessarily closest deterministic precedent. ([RePub][2])

**Chakravarti and Wagelmans (1998).**
This paper develops stability-radius algorithms for optimal or approximate min-sum and min-max binary solutions and reports polynomial solvability when the underlying optimisation problem is polynomially solvable. The current manuscript’s moving inside envelope and correlated demand-to-arc map may take it outside that fixed-solution result, but the relationship needs a formal reduction or non-reduction argument. ([Tinbergen Papers][4])

**Richter and Weber (1994).**
This paper studies sequential stability and conditions under which stability regions behave monotonically as the horizon grows. Its object is not obviously the same as prefix depth, but it bears directly on the manuscript’s horizon language and monotonicity narrative and should be discussed. ([Springer][7])

**Forel and Grunow (2023) and Weijers et al. (2025).**
These are important comparators for significance rather than mathematical priority. Forel and Grunow model forecast evolution in rolling-horizon lot sizing and report evaluations on both synthetic and real-world data. Weijers et al. study plan stability with real semiconductor data and multiple operational key performance indicators. The manuscript cites the former but does not use either body of evidence to benchmark what “operational” validation would require. ([IDEAS/RePEc][3])

**Barber et al. (2023) and Gibbs and Candès (2021).**
These sources clarify that useful conformal procedures under non-exchangeability or online distribution shift require modified methods and provide guarantees different from ordinary one-step exchangeable calibration. They support the manuscript’s caution about drift, but also show that repeated operational deployment should not be left at a general suggestion to use “weighted or rolling conformal” methods. ([Project Euclid][6])

### 6.3 Implications for originality, significance and credibility

The search did not locate an exact duplicate of the complete layered construction. That negative result is bounded by terminology, indexing and access limitations and is not evidence of absolute priority.

The literature supports the following revised positioning:

* **Established background:** fixed-solution lot-sizing sensitivity; demand-vector parametric stability; generic stability radii; rolling-horizon forecast evolution; conformal order-statistic guarantees.
* **Potentially original core:** strong stability of a selected **prefix class** with a moving best continuation, together with the particular floor-aware polynomial lower certificate.
* **Potentially original synthesis:** integration of that deterministic geometry with exact inverse formulations and a dead-zone structural rolling bound.
* **Not yet established:** whether the full-path special case or parts of the frozen certificate are already implicit in earlier parametric formulations.
* **Significance gap:** no real-data or field comparison demonstrates that the certificate improves a commitment decision relative to standard fences or rolling policies.

## 7. Minor comments

1. **NP formulation.** In Proposition 3.3, specify whether nominal optimality of (P^\star) is a promise. Alternatively, include a polynomial shortest-path optimality check in the verifier.

2. **Asymmetric scaling.** A weighted (L_\infty) norm is directionally symmetric. The statement on p. 3 that it can encode “asymmetric operational scaling after an appropriate coordinate transformation” needs the transformation to be defined or the word “asymmetric” removed.

3. **Graph definition.** Give explicit vertex and arc sets for (G_k), not only a prose description. This will reduce ambiguity about the omitted expected (k)th arc and the transition to the deviated layer.

4. **Indexing.** Add one small worked example linking physical periods, cumulative-demand vertices and arc endpoints. This would prevent off-by-one confusion in (D_j-D_i).

5. **Breakpoint conventions.** State how duplicate values of (w_t(\widehat d_t-\ell_t)), zero downward slack and an empty denominator-positive path set are handled algorithmically.

6. **Notation.** The lower certificate (\underline\rho) and exact radius (\rho) are visually difficult to distinguish in several displayed statements and in Table 2. Consider a different symbol, such as (\rho^{\mathrm{fr}}).

7. **Formal versus numerical certificate.** Reserve “formal certificate” for a rational or outward-rounded result. A floating-point optimum with a tolerance should be described as a numerically computed lower bound unless accompanied by a verified primal–dual enclosure.

8. **Zero demand.** The discussion of vacuous setups is appropriate, but the paper should adopt one convention throughout: positive floors, preprocessing, or explicit allowance of zero-demand arcs.

9. **Computational denominators.** Report both the numerator and denominator behind every percentage, including 27.9%, and the total number of generated cases behind “129 finite instances”.

10. **Simulation sample size.** Report the number of calibration histories, calibration-set size, number of next-revision draws and confidence interval construction for Figure 2(c).

11. **Runtime reporting.** Include interquartile ranges numerically in a table or supplement, not only graphically, and state whether compilation, data generation and model construction are included.

12. **Figure 2(d).** The (\log_{10}(1+x)) display is reasonable, but add a raw-scale summary of realised regret, bound slack and bound-to-regret ratios.

13. **Weight selection.** Give at least one concrete operational example of (w_t), including units, and show how rescaling demand units affects the certificate.

14. **Step 3 witness language.** Clarify exactly what “retain the primal path, adversarial revision and solver record” means for the frozen certificate, especially when an LP optimum is non-unique.

15. **Release citation.** Add an archival identifier, licence, versioned citation and software availability statement.

16. **References.** Add Richter and Vörös (1989), Richter and Weber (1994), and a specific sequential conformal reference if sequential deployment remains part of the discussion.

17. **Conclusion wording.** Replace “each layer exposes its own assumptions and failure modes” with a short explicit enumeration; several assumptions currently remain implicit in the theorem statements.

## 8. Prioritised revision plan

### Must fix before the claims are publishable

1. Complete the direct-antecedent literature review and provide a theorem-level novelty comparison.
2. Repair and fully specify the proof and algorithm for Theorem 5.2.
3. Supply the code, raw outputs, environment and complete computational manifest, or remove/recast unreproducible numerical claims.
4. Restate the conformal result with its admissible-domain, marginal and repeated-use limitations.
5. Restate the rolling theorem with explicit information, quantity-recourse, domain and infinite-radius semantics.
6. Address nominal degeneracy and dependence on the selected (P^\star).
7. Remove or substantiate “operationally complete”.
8. Document exact-solver scalability or narrow the exact-escalation protocol.

### Should fix to strengthen the paper

1. Add a real or realistically reconstructed forecast-vintage case and compare against fixed-fence and unrestricted-replanning baselines.
2. Benchmark exact enumeration and the MILP over a wider and more adversarial instance set.
3. Report sensitivity to floors, weights, cost separation and nominal near-ties.
4. Separate mathematical, numerical and operational notions of “certification” throughout.
5. Report all computational denominators, exclusions, uncertainty intervals and solver statuses.
6. Expand the prefix-deviation construction with pseudocode and a worked example.

### Could improve presentation or future work

1. Provide rational primal–dual verification or proof-assistant formalisation of the central certificate.
2. Develop a common-prefix or optimiser-selection version that is robust to nominal degeneracy.
3. Investigate time-uniform revision control and capacitated or multi-item extensions.
4. Report both lower and feasible upper radius bounds when exact solution times out.
5. Explore fixed-parameter algorithms in the number of protected cycles, distinct slopes or active floor breakpoints, as already suggested in Section 12.

## 9. Editorial recommendation

**Recommendation: Major revisions.**

The paper contains a coherent and potentially important theoretical contribution. The fixed-competitor geometry, strict lower-bound example, exact formulations and dead-zone idea form a credible research programme. The current submission is not ready for acceptance because the novelty review misses a direct antecedent, the central polynomial proof is not fully complete, the computational release is unavailable for review, and the statistical and operational conclusions exceed the demonstrated scope.

My confidence is **0.86**. The recommendation would move towards rejection if full-text comparison showed that earlier parametric lot-sizing work substantially subsumes the prefix result, if the central LP argument could not be completed, or if the released computations failed material checks. It would move towards minor revision or acceptance after a convincing novelty comparison, a complete proof, reproducible artefacts, explicit statistical and rolling semantics, and appropriately bounded operational claims.

## 10. Provisional REF calibration

### 10.1 Applicable framework

The most relevant unit is **Unit of Assessment 17: Business and Management Studies**, because the output is framed around management science, operations management and supply-chain planning. REF 2029 retains the 34-unit structure and UoA 17. ([REF 2029][8]) The REF 2021 UoA 17 descriptor expressly includes management science, operations management and supply-chain management; the UoA 10 descriptor notes that operational research focused on business and management should not normally be submitted there. ([REF 2021][9])

As of 4 August 2026, final REF 2029 Panel Criteria and Working Methods are scheduled for publication in autumn 2026. ([REF 2029][10]) I therefore use the current UoA structure, the supplied 12-point rubric, and the REF 2021 Main Panel C output definitions: 4* world-leading, 3* internationally excellent, 2* internationally recognised and 1* nationally recognised, assessed in terms of originality, significance and rigour. ([REF 2021][9])

### 10.2 Indicative ratings

| Dimension                  | Provisional rating | Supplied rubric | Rationale                                                                                                                                                                                                                                                                                   | Confidence |
| -------------------------- | -----------------: | --------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------: |
| **Originality**            |      **3* Medium** |        **8/12** | The prefix-face object, moving inside continuation and floor-aware polynomial lower certificate appear novel and potentially internationally important. The direct 1989 antecedent and generic stability-radius results prevent a higher rating until the novelty boundary is demonstrated. |       0.70 |
| **Significance**           |         **3* Low** |        **7/12** | The problem of forecast-induced plan nervousness is internationally relevant, and the method could influence commitment-fence design. Significance is presently prospective because the model is narrow, exact escalation is untested at realistic scales and there is no field evidence.   |       0.75 |
| **Rigour**                 |      **3* Medium** |        **8/12** | The paper contains substantial formal development, internally coherent examples and multiple cross-checks. The central proof gap, incomplete edge-case specification and absent computational release rule out 4*.                                                                          |       0.80 |
| **Overall output quality** |         **3* Low** |        **7/12** | Holistically, the work is potentially internationally excellent but not yet an authoritative point of reference. The unresolved novelty comparison and reproducibility limitations are decisive.                                                                                            |       0.74 |

The overall grade is **holistic rather than the arithmetic average** of the three dimensions. A successful major revision could plausibly move the output to **3* Medium or High**. A finding that the core stability construction is substantially anticipated could move originality and overall quality down to **2***.

This calibration is **indicative only and is not an official REF panel decision**.

## 11. References

### Lot-sizing sensitivity and stability

Chakravarti, N., & Wagelmans, A. P. M. (1998). Calculation of stability radii for combinatorial optimization problems. *Operations Research Letters, 23*(1–2), 1–7. [https://doi.org/10.1016/S0167-6377(98)00031-5](https://doi.org/10.1016/S0167-6377%2898%2900031-5) ([Tinbergen Papers][4])

Richter, K., & Vörös, J. (1989). A parametric analysis of the dynamic lot-sizing problem. *Journal of Information Processing and Cybernetics, 25*(3), 67–73. Stable record: [https://dl.acm.org/doi/10.5555/70375.70376](https://dl.acm.org/doi/10.5555/70375.70376) ([ACM Digital Library][1])

Richter, K., & Weber, J. (1994). Sequential stability of the constant cost dynamic lot size model—Searching for monotonicity. *OR Spektrum, 15*(4), 197–203. [https://doi.org/10.1007/BF01719450](https://doi.org/10.1007/BF01719450) ([Springer][7])

van Hoesel, C. P. M., & Wagelmans, A. P. M. (1993). Sensitivity analysis of the economic lot-sizing problem. *Discrete Applied Mathematics, 45*(3), 291–312. [https://doi.org/10.1016/0166-218X(93)90016-H](https://doi.org/10.1016/0166-218X%2893%2990016-H) ([RePub][2])

### Forecast evolution and operational plan stability

Forel, A., & Grunow, M. (2023). Dynamic stochastic lot sizing with forecast evolution in rolling-horizon planning. *Production and Operations Management, 32*(2), 449–468. [https://doi.org/10.1111/poms.13881](https://doi.org/10.1111/poms.13881) ([IDEAS/RePEc][3])

Weijers, E., Sluijter, N., Hogers, G., Schelthoff, K., Adan, I., & van Jaarsveld, W. (2025). Improving plan stability in semiconductor manufacturing through stochastic optimization: A case study. In *Proceedings of the 2025 Winter Simulation Conference* (pp. 1815–1826). [https://www.informs-sim.org/wsc25papers/con235.pdf](https://www.informs-sim.org/wsc25papers/con235.pdf) ([informs-sim.org][5])

### Conformal calibration and distribution shift

Barber, R. F., Candès, E. J., Ramdas, A., & Tibshirani, R. J. (2023). Conformal prediction beyond exchangeability. *The Annals of Statistics, 51*(2), 816–845. [https://doi.org/10.1214/23-AOS2276](https://doi.org/10.1214/23-AOS2276) ([Project Euclid][6])

Gibbs, I., & Candès, E. (2021). Adaptive conformal inference under distribution shift. *Advances in Neural Information Processing Systems, 34*, 1660–1672. [https://arxiv.org/abs/2106.00170](https://arxiv.org/abs/2106.00170) ([arXiv][11])

### REF guidance

Research Excellence Framework. (2025). *Contributions to Knowledge and Understanding guidance*. [https://2029.ref.ac.uk/guidance/section-4-contributions-to-knowledge-and-understanding-cku-guidance/](https://2029.ref.ac.uk/guidance/section-4-contributions-to-knowledge-and-understanding-cku-guidance/) ([REF 2029][12])

Research Excellence Framework. (2026). *Units of assessment*. [https://2029.ref.ac.uk/panels/units-of-assessment/](https://2029.ref.ac.uk/panels/units-of-assessment/) ([REF 2029][8])

Research Excellence Framework. (2025). *REF 2029 timetable*. [https://2029.ref.ac.uk/about/timetable/](https://2029.ref.ac.uk/about/timetable/) ([REF 2029][10])

Research England, Scottish Funding Council, Higher Education Funding Council for Wales, & Department for the Economy, Northern Ireland. (2019). *Panel criteria and working methods* (REF 2019/02). [https://2021.ref.ac.uk/media/1450/ref-2019_02-panel-criteria-and-working-methods.pdf](https://2021.ref.ac.uk/media/1450/ref-2019_02-panel-criteria-and-working-methods.pdf) ([REF 2021][9])

[END]

[1]: https://dl.acm.org/doi/10.5555/70375.70376 "https://dl.acm.org/doi/10.5555/70375.70376"
[2]: https://repub.eur.nl/pub/2309/eur_wagelmans_21.pdf "PII: 0166-218X(93)90016-H"
[3]: https://ideas.repec.org/a/bla/popmgt/v32y2023i2p449-468.html "Dynamic stochastic lot sizing with forecast evolution in rolling‐horizon planning"
[4]: https://papers.tinbergen.nl/97106.pdf "https://papers.tinbergen.nl/97106.pdf"
[5]: https://www.informs-sim.org/wsc25papers/con235.pdf "https://www.informs-sim.org/wsc25papers/con235.pdf"
[6]: https://projecteuclid.org/journals/annals-of-statistics/volume-51/issue-2/Conformal-prediction-beyond-exchangeability/10.1214/23-AOS2276.short "https://projecteuclid.org/journals/annals-of-statistics/volume-51/issue-2/Conformal-prediction-beyond-exchangeability/10.1214/23-AOS2276.short"
[7]: https://link.springer.com/content/pdf/10.1007/BF01719450.pdf "https://link.springer.com/content/pdf/10.1007/BF01719450.pdf"
[8]: https://2029.ref.ac.uk/panels/units-of-assessment/ "https://2029.ref.ac.uk/panels/units-of-assessment/"
[9]: https://2021.ref.ac.uk/media/1450/ref-2019_02-panel-criteria-and-working-methods.pdf "https://2021.ref.ac.uk/media/1450/ref-2019_02-panel-criteria-and-working-methods.pdf"
[10]: https://2029.ref.ac.uk/about/timetable/ "https://2029.ref.ac.uk/about/timetable/"
[11]: https://arxiv.org/abs/2106.00170 "https://arxiv.org/abs/2106.00170"
[12]: https://2029.ref.ac.uk/guidance/section-4-contributions-to-knowledge-and-understanding-cku-guidance/ "https://2029.ref.ac.uk/guidance/section-4-contributions-to-knowledge-and-understanding-cku-guidance/"
