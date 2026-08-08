# Full & final review: *Certified Commitment Horizons in Dynamic Lot Sizing* v2.1.1

**Recommendation:** Major revisions before Evidence Press release
**Confidence:** 0.94
**Fatal concerns identified:** None
**Review date:** 5 August 2026

## 1. Executive assessment

This manuscript develops a mathematically explicit “commit or escalate” rule for deterministic, single-item, uncapacitated Wagner–Whitin lot sizing under forecast revision. Its strongest contribution is the strong prefix-stability object: the weighted distance to the nearest admissible demand vector at which an optimal replenishment path can leave a protected prefix, together with an exact-rational frozen-comparator lower certificate, a witness-backed upper bound, and finite exact escalation. The manuscript is unusually candid about scope, ties, unresolved cases, exchangeability, quantity recourse and the absence of field validation.

I recommend **major revisions before release through Evidence Press**, with high confidence. I found no fatal mathematical defect: the principal proofs survived detailed checking, the three-period strict-gap example recalculates correctly, and a reviewer-built small-instance linear-programming oracle supported all 53 checked brackets. The decisive weakness is release assurance. The advertised quick replay returns 65 passed and one failed test, so the producer verification receipt is not reproducible as submitted. The failed assertion incorrectly imposes monotonicity on unresolved upper witness bounds; this looks like a test-design defect rather than a refutation of the theorem, but it blocks an “internally replayed” release. The shipped parametric algorithm is also described as polynomial although that claim is proved for a different linear-programming procedure, and its arbitrary iteration cap is not theoretically justified. Finally, licensing, third-party redistribution, data provenance and version metadata require correction. Novelty remains credible but conditional pending full-text comparison with Richter and Vörös (1989).

## 2. Scope and evidence limits

### Manuscript type and intended contribution

This is a **theoretical and computational operations-research manuscript with an executable research package**. It addresses deterministic dynamic lot sizing, inverse optimisation, exact certification, forecast calibration and rolling-horizon decision support. Its likely audience comprises researchers and advanced practitioners in operations research, production planning, combinatorial optimisation and reproducible computational research.

I have assessed it as an **Evidence Press candidate release**, not as a conventional journal submission. Evidence Press distinguishes an unrefereed candidate from stronger verification levels; its “internally replayed” level requires a functioning author-side replay, including negative and mutation controls, while independent reproduction is a separate higher level. ([Evidence Press][1])

### Materials inspected

**Manuscript evidence inspected**

* The 29-page PDF and LaTeX source.
* Python source code, tests, scripts, lock files and package metadata.
* Figures, processed outputs and tabulated audit results.
* `README`, `CITATION.cff`, `pyproject.toml`, provenance and claims records.
* `release/SHA256SUMS` and `release/verification_receipt.json`.
* Bundled literature files and UCI-derived data materials.
* The supplied REF scoring image.

The PDF is professionally typeset, uses embedded fonts, and showed no evident clipping or Type 3-font problems. Its tables and four-panel audit graphic are dense but usable.

### Recalculations and replay performed

I:

1. Verified the supplied manifest for all 116 files covered by its exclusion rules.
2. Confirmed the recorded dependency environment: Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, pandas 2.2.3 and Matplotlib 3.10.8.
3. Ran `bash run_all.sh --quick`, obtaining **65 passed and one failed test**.
4. Recalculated the strict three-period example.
5. Built a separate floating-point linear-programming oracle for small instances and checked 53 protected-prefix cases from 20 randomly generated instances with (T=3,\ldots,6).
6. Recalculated reported proportions and Wilson confidence intervals.
7. Checked the processed UCI illustration summaries against the manuscript table.

### Limitations

The full benchmark suite was **not run after the advertised quick replay had failed**. I did not have an external replication, proof-assistant formalisation, author response, preregistration, operational field logs or access to a final public repository and archival DOI. The small-instance oracle used SciPy/HiGHS floating-point linear programming; it is an independent numerical cross-check, not a formal certificate. I therefore distinguish “not externally reproduced” from “not reproducible”: the former remains true by design, while the latter currently applies to the submitted quick replay in the reviewer environment.

## 3. Contribution and positioning

### Strongest defensible thesis

The manuscript’s strongest thesis is:

> For deterministic, single-item, uncapacitated Wagner–Whitin lot sizing with weighted (L_\infty) demand revisions and coordinate floors, the nearest revision at which an optimal replenishment path can leave a protected prefix can be bounded or certified through reduced affine arcs, a prefix-deviation directed acyclic graph, fixed-path geometry, a polynomial frozen-comparator lower certificate, a witness upper bound and finite exact escalation.

The work then attaches two deliberately narrower layers:

* a **one-step split-conformal calibration** for the next revision under exchangeability; and
* a **deterministic rolling-horizon structural-loss bound** under the stated quantity-recourse assumptions.

This is properly understood as a bounded and auditable **decision protocol**, not as evidence that the protocol improves realised industrial performance.

### Claim-to-evidence map

| Main claim                                                          | Primary manuscript support                    | Assessment                                                                       |
| ------------------------------------------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------- |
| Positive strong prefix-stability radius under the stated conditions | Common-prefix results, pp. 7–9                | Mathematically credible and appropriately tie-aware                              |
| Prefix-deviation representation                                     | Directed acyclic graph construction, pp. 9–10 | Clear bijective construction; no defect found                                    |
| Exact-rational frozen lower certificate                             | Section 7, especially Theorem 7.2, pp. 10–12  | Proof is plausible; implementation does not fully match the proved algorithm     |
| Witness-backed upper bound and bracket                              | pp. 12–14                                     | Sound as a bracket; an unresolved upper witness is not itself an exact radius    |
| Finite exact escalation                                             | pp. 14–15                                     | Conceptually supported; coded iteration cap weakens the implementation guarantee |
| One-step conformal calibration                                      | p. 15 onward                                  | Standard finite-sample result correctly restricted to exchangeability            |
| Rolling structural-loss bound                                       | p. 17                                         | Valid only under the stated Bellman and quantity-recourse framework              |
| Computational usefulness                                            | Synthetic audit, p. 18 onward                 | Supports feasibility and internal behaviour, not external effectiveness          |
| Practical relevance                                                 | Small UCI illustration, p. 21                 | A useful pipeline illustration, but too stylised to establish field value        |

### Originality and significance

**Reviewer inference:** the most plausible original component is not generic lot-sizing sensitivity, inverse shortest paths or split conformal prediction individually. It is the combination of:

* a **strong**, tie-sensitive prefix-face radius;
* comparison against the **best moving continuation inside the protected prefix**, rather than only the nominal path;
* the frozen lower-certificate/exact-escalation hierarchy;
* exact-rational, machine-checkable output;
* and an explicit commitment-versus-escalation protocol.

That combination appears non-trivial and potentially useful. However, the manuscript’s novelty account remains conditional because Richter and Vörös (1989) explicitly considered demand-vector parametrisation and stability of a Wagner–Whitin solution. I located metadata and an abstract but not a lawful full text during this targeted review. Earlier work also directly addresses economic lot-sizing sensitivity and combinatorial stability radii. ([Academia.edu][2])

The significance is currently **methodological rather than demonstrated operational impact**. Recent rolling-horizon and semiconductor-planning studies confirm that forecast evolution and plan stability are genuine planning concerns, but they do not validate this particular certificate or commitment policy. ([Sage Journals][3])

## 4. Major comments

### 1. The advertised internally replayed release does not replay successfully

**Classification:** Major

**Issue**

The supplied verification receipt records a successful 66-test producer run, whereas the submitted one-command quick replay produces 65 passing tests and one failure in the reviewer environment.

**Manuscript evidence**

The failing test is:

```text
tests/test_exactcert.py::test_certified_enumeration_brackets_and_monotonicity
```

At approximately line 335 it asserts that, as the protected prefix is enlarged, each returned **upper witness bound** must be non-increasing. The observed values were approximately:

[
u_1=0.35869824692536467,\qquad
u_2=0.35869824692536495,
]

an exact-rational difference of approximately (2.80\times10^{-16}). Both cases were marked `exact_certified=False`, had the same lower bound and corresponding witness paths, and retained an unresolved disjunct.

The exact strong radius is monotone under prefix enlargement, and the frozen lower certificate is likewise constructed monotonically. An independently selected feasible upper witness, however, need not be monotone unless it is exact or generated by a proven nested construction.

**Why it matters**

This is not merely a cosmetic floating-point tolerance problem. Increasing a tolerance would conceal the logical error in the test. Nor does the failure refute the main theorem: it instead shows that the test assigns a theorem-level property to an unresolved auxiliary bound.

For an Evidence Press candidate, being unrefereed is acceptable; claiming internal replay while the advertised replay fails is not. Evidence Press treats author replay, negative controls and mutation controls as evidence distinct from peer review or independent reproduction. ([Evidence Press][1])

**Required revision or decisive test**

1. Replace the assertion with one of the following:

   * test monotonicity only for cases with `exact_certified=True`;
   * compare against a complete enumerative oracle for small (T);
   * or construct and prove a canonical nested sequence of upper bounds.
2. Do **not** repair this by introducing a numerical tolerance around the present assertion.
3. Add end-to-end mutations of:

   * certificate numerator or denominator;
   * protected prefix;
   * witness path;
   * admissibility floor;
   * status flag;
   * hash and manifest entry;
   * infinity/unresolved representation.
4. Run the clean package from a fresh archive in at least the primary supported environment and one second supported environment.
5. Regenerate the receipt, processed outputs and manifest only after those runs pass.
6. Retain the failed review transcript or document the correction transparently in the release history.

### 2. Polynomial-time theory is conflated with the released parametric implementation

**Classification:** Major

**Issue**

The manuscript proves polynomial-time computability for an exact-rational linear-programming route, but the released source describes a different parametric shortest-path procedure as polynomial and imposes an iteration cap without a theorem showing that the cap suffices.

**Manuscript evidence**

Theorem 7.2, pp. 10–12, obtains the frozen radius using at most (T+1) shortest-path computations together with polynomial-size Charnes–Cooper linear programmes and polynomial bit-complexity reasoning.

By contrast, `src/wwprefix/exactcert.py`, around lines 499–506, describes the implemented parametric shortest-path procedure as computing the certificate “in polynomial time”. Around lines 607–612 it sets:

```python
max_iterations = 4 * len(graph.arcs) + 64
```

and raises `CertificationError` when the cap is exceeded. The paper reports no more than six steps in the tested cases, which is useful empirical information but not a worst-case proof.

**Why it matters**

Finite termination after traversing all relevant affine pieces does not itself establish a polynomial bound on the number of pieces. General parametric shortest-path instances are known to admit superpolynomially many breakpoints; recent work gives closely related quasipolynomial lower and upper behaviour. Those results do not show that the manuscript’s specially structured Wagner–Whitin graph has the same complexity, but they do show why the missing structure-specific proof cannot be silently assumed. ([arXiv][4])

The present code fails loudly rather than emitting a false certificate, which is an important safeguard. Nevertheless, a valid problem instance could in principle reach the arbitrary cap before the theoretically finite search is complete. For (T>12), the supplied checker also depends partly on the producer computation for lower-bound minimality, so “independently written checker” overstates the assurance obtained.

**Required revision or decisive test**

* Distinguish explicitly among:

  1. the polynomial linear-programming algorithm proved in Theorem 7.2;
  2. the finite-piece parametric algorithm used in the package;
  3. the empirical observation that tested instances needed at most six iterations.
* Remove the polynomial-time claim from the implementation docstring unless a structure-specific proof is supplied.
* Either:

  * implement the proved LP method as a fallback;
  * prove a sufficient bound for this graph family;
  * or document the cap as an incomplete engineering limit and report how capped cases are represented.
* State prominently that the large-(T) checker is separately implemented but is **not an independent external reproduction** and is not fully independent of the producer’s optimisation route.

### 3. The public-release bundle has unresolved licensing and provenance boundaries

**Classification:** Major for release; not a fatal scientific defect

**Issue**

The package does not yet establish a coherent licence for the manuscript, code, metadata, third-party papers and UCI-derived materials.

**Manuscript evidence**

* The repository, `CITATION.cff` and `pyproject.toml` indicate MIT licensing.
* The manuscript’s own licence is not clearly reported.
* The Evidence Press schema and site materials refer to CC0 for their original content or records.
* The archive includes third-party PDFs:

  * an Elsevier article carrying conventional publisher rights;
  * an IEEE conference paper;
  * a Chakravarti/Wagelmans paper for which redistribution permission is not reported.
* `docs/data_provenance.md` states that the exact mirror URL for the downloaded UCI data was not retained.
* The source archive contains generated `.pytest_cache` and Python 3.11 `.pyc` material.

The official UCI record licenses *Daily Demand Forecasting Orders* under CC BY 4.0, identifies 60 instances, 12 features and no missing values, and provides DOI `10.24432/C5BC8T`. CC BY material must retain its attribution and licence; it cannot simply be subsumed under an undifferentiated CC0 assertion. ([UCI Machine Learning Repository][5])

**Why it matters**

A scientific claim may be sound while its release package remains legally unsuitable for public redistribution. Depositing copyrighted papers without permission could obstruct publication of the complete archive. Ambiguous licence inheritance also weakens reuse and machine-readable provenance.

**Required revision or decisive test**

1. Define separate licences for:

   * manuscript text and original figures;
   * source code;
   * Evidence Press metadata;
   * UCI-derived data;
   * third-party materials.
2. Remove bundled publisher PDFs from the public archive unless redistribution permission is documented. Preserve citations, stable links, acquisition dates and hashes instead.
3. Reacquire or verify the UCI bytes from the official record, retaining the exact retrieval URL, date, licence, source hash and any transformation script.
4. Add a machine-readable third-party notice and exclusions from any broad CC0 declaration.
5. Remove caches, bytecode and generated local artefacts before producing the archival ZIP.
6. Reserve the final release claim until the repository, archived deposit and DOI are present. Their absence is reasonable at the present candidate stage, but not in the public release record.

### 4. The originality claim requires a direct comparison with the 1989 demand-parameter stability paper

**Classification:** Major

**Issue**

The manuscript acknowledges earlier sensitivity work, but the nearest identifiable antecedent is not compared closely enough to establish what is new.

**Manuscript evidence**

The literature boundary on approximately pp. 6–7 distinguishes the paper from classical lot-sizing sensitivity and inverse optimisation. It does not provide a theorem-by-theorem comparison with Richter and Vörös (1989).

**External evidence**

Richter and Vörös describe parametric analyses with respect to setup and holding costs, the demand vector, and joint cost-demand variation, with the purpose of finding stability regions that retain a Wagner–Whitin solution. Van Hoesel and Wagelmans study sensitivity of economic lot sizing; Chakravarti and Wagelmans develop stability-radius calculations for combinatorial optimisation; and Richter and Weber analyse sequential stability. ([Academia.edu][2])

Only abstract-level and bibliographic information was available to me for Richter and Vörös. It would therefore be improper to allege duplication. It is equally premature to state an unqualified first-result claim without checking the full paper.

**Why it matters**

The likely novelty is narrower and more interesting than “demand stability for Wagner–Whitin”:

* strong prefix rather than complete-path retention;
* ties treated as destabilisation;
* the best continuation within the protected prefix allowed to change;
* coordinate floors and weighted (L_\infty) revisions;
* a lower/upper certification hierarchy;
* exact-rational evidence artefacts;
* and integration into a calibrated commitment protocol.

The paper should claim that combination, not the already-established broad territory.

**Required revision or decisive test**

* Obtain the full Richter and Vörös article through a library or author archive.
* Add a comparison table covering:

  * object preserved;
  * perturbation set and norm;
  * tie convention;
  * whether the incumbent path or an optimal face is preserved;
  * exactness and complexity;
  * certificate or witness output;
  * implementation availability.
* Replace categorical priority claims with conditional wording until the comparison is complete.
* If material overlap is found, reframe the paper around the strong-prefix, moving-continuation and verifiable-certificate contributions.

### 5. Assurance language and release metadata are not internally coherent

**Classification:** Major for an evidence-focused venue

**Issue**

Several labels imply a higher or different assurance state than the package demonstrates, while version and title metadata disagree across files.

**Manuscript evidence**

* `paper/main.tex`, around line 47, retains the running header **“Preprint v2.0.0”**, while the title page identifies v2.1.1.
* The assurance box states **“two rounds of adversarial peer review”** and an **“independently written checker”**.
* `README.md`, around line 160, says numerical lower radii still subtract a safety margin and that exact-rational certification is future work, contradicting v2.1.1.
* `release/provenance.json` sets `"formal_numerical_certification": false`, which is ambiguous given the exact-rational certificate claim.
* Claim-search record C11 is frozen on 4 August 2026 while the paper is dated 5 August 2026.
* C12 refers to release 2.1.0.
* `CITATION.cff` uses “Calibrated Forecast Revisions” rather than the title-page phrase “One-Step Calibration of Forecast Revisions”.
* The verification receipt reports the producer’s 66-test pass, while the submitted replay does not.

**Why it matters**

Evidence Press expressly separates author replay, independent reproduction and peer review. Internal or model-assisted adversarial inspection should not be presented in language likely to be understood as external scholarly peer review. A separately implemented checker can be valuable without being organisationally independent. ([Evidence Press][1])

Metadata conflicts are especially consequential here because versioned claims, hashes, receipts and citations form part of the scholarly argument rather than peripheral administration.

**Required revision or decisive test**

* Use one source of truth for version, date, title, licence and verification status, with generated checks that fail on divergence.
* Replace “adversarial peer review” with “internal adversarial review” or another accurate description unless external reviewers actually participated.
* Replace “independently written checker” with “separately implemented producer-side checker”, adding its (T>12) limitation.
* Divide the ambiguous provenance flag into, for example:

  * exact-rational computational certification;
  * proof-assistant formalisation;
  * external independent reproduction.
* Refresh all claim-search dates, scope records, receipts and hashes after the scientific and code corrections.

## 5. Rigour, results and inference

### 5.1 Mathematical audit

I found no fatal proof defect in the material inspected.

| Component                 | What the argument directly establishes                                                                     | Important qualification                                                      | Reviewer judgement                                              |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Strong prefix radius      | Distance to the nearest admissible demand vector at which at least one optimum leaves the protected prefix | Ties count as destabilisation; deterministic single-item uncapacitated model | Clear and defensible                                            |
| Common-prefix result      | Conditions for a positive neighbourhood in which every optimum retains the protected prefix                | Depends on the stated nominal optimal-face condition                         | Proof appears sound                                             |
| Fixed-path tie formula    | Floor-truncated weighted-(L_\infty) distance to equality with a fixed competitor                           | Does not by itself account for a better continuation within the prefix       | Correctly used as an intermediate result                        |
| Prefix-deviation DAG      | Represents paths that first depart from the protected prefix                                               | Requires the acyclic lot-sizing network                                      | Bijection and no-circulation reasoning appear sound             |
| Frozen lower certificate  | Certifies a lower bound against a frozen inside comparator                                                 | Can be strict relative to the true strong radius                             | Properly recognised                                             |
| Full-path special case    | Frozen and exact objects coincide when the protected prefix fixes the complete path                        | Narrow special case                                                          | Correct                                                         |
| Witness upper bound       | Supplies a feasible destabilising revision and hence an upper bound                                        | Need not be exact or monotone while unresolved                               | Correct in theory; test suite mishandles this distinction       |
| Exact escalation          | Finite resolution by considering competing affine pieces                                                   | Released cap is not covered by the proof                                     | Theoretical idea credible; implementation contract needs repair |
| One-step conformal result | Marginal finite-sample rank guarantee for the next revision under exchangeability                          | Not a general sequential, conditional or distribution-shift guarantee        | Appropriately scoped                                            |
| Rolling theorem           | Deterministic structural-loss bound through Bellman residuals                                              | Requires quantity recourse and the specified modelling assumptions           | A bound, not a performance-estimation result                    |

The reductions from lot sizing to affine shortest paths and from first-prefix departure to a directed acyclic deviation graph are well motivated. I specifically checked the use of acyclicity in excluding non-zero non-negative circulation and the positivity needed for the Charnes–Cooper normalisation; I found the argument coherent. This remains reviewer verification, not a machine-checked proof.

### 5.2 Recalculation of the strict-gap example

For the three-period example with

[
q=(2,1,0),\quad K=(0,3,2),\quad d^0=(1,5,1),
]

the four path costs given by the manuscript reduce to:

[
\begin{aligned}
C_{(1,2,4)}(d)&=2d_1+d_2+d_3+3,\
C_{(1,2,3,4)}(d)&=2d_1+d_2+5,\
C_{(1,3,4)}(d)&=2d_1+2d_2+2,\
C_{(1,4)}(d)&=2d_1+2d_2+2d_3.
\end{aligned}
]

At the nominal vector:

[
C_{(1,2,4)}(1,5,1)=11,
]

while the other costs are 12, 14 and 14. Thus the stated nominal optimum is correct.

At (d=(1,3.5,2.5)), distance 1.5 under the example’s norm:

[
C_{(1,2,4)}=11,\qquad
C_{(1,3,4)}=11,
]

but the protected-prefix continuation ((1,2,3,4)) has cost 10.5. The frozen comparator therefore ties an outside path without producing a true strong-prefix destabilisation.

At (d=(1,3,3)), distance 2:

[
C_{(1,2,3,4)}=C_{(1,3,4)}=10,
]

so an inside and an outside optimal path coexist. This is a true strong-prefix event. My separate LP oracle also returned radius 2; another optimum was attained at (d=(0.5,3,3)). The example therefore correctly demonstrates that the frozen certificate can be strictly below the exact strong radius.

### 5.3 Independent small-instance numerical cross-check

For each small generated instance I:

1. Enumerated complete replenishment paths.
2. Identified paths inside and outside the protected prefix.
3. For each outside path (Q), solved a linear programme minimising (r) subject to:

   * the coordinate floors;
   * the weighted (L_\infty) revision box;
   * (C_Q(d)\leq C_P(d)) for every inside path (P).
4. Minimized over outside paths.

Across **53 protected-prefix cases from 20 instances**, every package interval contained the oracle value. Where the package reported an exact radius, its result agreed with the oracle to numerical precision. Exact/oracle radii also had the expected prefix monotonicity in all 53 cases.

This is positive evidence, but it has two limits: the instances are small, and HiGHS uses floating-point arithmetic. It cannot replace exact package tests or a proof of the implementation’s iteration bound.

### 5.4 Audit proportions and uncertainty

I recalculated the reported proportions:

| Reported result | Count reconstruction | Wilson 95% interval |
| --------------- | -------------------: | ------------------: |
| 0.9038          |      18,076 / 20,000 |       0.8996–0.9078 |
| 0.8409          |      16,818 / 20,000 |       0.8358–0.8459 |
| 0.77905         |      15,581 / 20,000 |       0.7732–0.7847 |
| 0.8984          |        4,492 / 5,000 |       0.8897–0.9065 |

The point calculations are internally consistent. Adding binomial or Monte Carlo uncertainty intervals would prevent readers from treating simulation frequencies as exact properties of the method. The distinction matters particularly for the 5,000-run result.

### 5.5 Conformal and rolling inference

The conformal component is correctly presented as a one-step split-conformal rank result under exchangeability. Recent conformal work develops methods for distribution shift and non-exchangeable sequences, but those extensions require additional assumptions or modified algorithms. The manuscript should continue to resist any suggestion that the ordinary calibration theorem automatically supplies a rolling multi-period coverage guarantee. ([NeurIPS Proceedings][6])

The rolling theorem is a deterministic decomposition or upper bound under the stated recourse framework. It does not show that committing according to the certificate minimises realised operational regret, nor that the bound is tight in representative industries. The manuscript generally respects that boundary.

### 5.6 UCI illustration

The processed summaries agree with the reported table:

| Rule             | Mean commitment | Reported regret |
| ---------------- | --------------: | --------------: |
| Certificate only |            0.17 |               0 |
| Exact escalation |            0.33 |               0 |
| Fixed 2          |            2.08 |         £114.80 |
| Fixed 3          |            3.92 |         £308.22 |
| Fixed 4          |            4.17 |         £308.22 |
| Updated cycle    |            2.25 |          £73.33 |

This confirms the table calculation, not the real-world economic validity of the policy. The dataset is not a lot-sizing field trial, and the costs and transformation are stylised. The pound sign can suggest actual monetary calibration that the evidence does not provide. “Cost units” would be safer unless a genuine sterling interpretation is documented.

## 6. External literature check

### Search record

**Review date:** 5 August 2026.

**Sources searched:** supplied bibliography and PDFs; Evidence Press; DBLP/ACM records; ScienceDirect; Springer; Winter Simulation Conference proceedings; NeurIPS proceedings; Project Euclid; arXiv; UCI Machine Learning Repository; and official REF 2029 materials.

**Representative search strings**

* `"dynamic lot sizing" stability radius demand vector prefix`
* `"A Parametric Analysis of the Dynamic Lot-Sizing Problem" abstract full text`
* `"partial inverse shortest path" L infinity DAG`
* `"parametric shortest path" breakpoints superpolynomial`
* `"rolling horizon" lot sizing forecast evolution plan stability`
* `"conformal prediction beyond exchangeability"`
* `site:2029.ref.ac.uk originality significance rigour`

**Inclusion logic:** original papers, official proceedings, datasets and standards were prioritised. Older papers were retained where they are direct antecedents; recent work from 2021–2026 was used for contemporary positioning. The search was targeted rather than exhaustive.

**Access limits:** full text was inspected for the supplied van Hoesel/Wagelmans and Chakravarti/Wagelmans materials, the official Weijers et al. conference paper, Gassner’s report and Ley and Merkert. Richter and Vörös was assessed from abstract and metadata only.

### Pivotal comparisons

**Lot-sizing stability.** Richter and Vörös (1989) is the closest apparent antecedent because it includes demand-vector parametrisation and stability of a Wagner–Whitin solution. Van Hoesel and Wagelmans (1993) give direct economic lot-sizing sensitivity analysis, while Chakravarti and Wagelmans (1998) place stability radii in a broader combinatorial-optimisation framework. Richter and Weber (1994) address sequential stability and monotonicity. These papers narrow any claim of being the first demand-stability analysis, but do not, on the material available, eliminate the manuscript’s stronger prefix-face contribution. ([Academia.edu][2])

**Inverse shortest paths.** Gassner establishes strong hardness results for several partial inverse combinatorial problems, including weighted (L_1) and (L_\infty) settings with forbidden elements. Ley and Merkert give a recent NP-completeness result for a restricted directed-acyclic-graph partial inverse shortest-path problem with one required arc and increase-only weights. These sources support the manuscript’s decision to exploit specialised Wagner–Whitin structure rather than imply that generic inverse shortest paths are straightforward. 

**Parametric complexity.** Gajjar and Radhakrishnan construct planar parametric shortest-path instances with (n^{\Omega(\log n)}) complexity. Chillara, Gajjar and Raja provide recent matching-style quasipolynomial analysis for linear edge weights in the general setting. These results challenge the unqualified polynomial description of the package’s piece-traversal algorithm, although they do not settle the special lot-sizing graph family. ([arXiv][4])

**Rolling planning and plan stability.** Forel and Grunow study dynamic stochastic lot sizing under forecast evolution and rolling-horizon planning. Weijers et al. report a semiconductor case study in which stochastic optimisation improves plan stability while preserving relevant operational performance. This literature supports the practical problem motivation but also shows that operational validation normally requires richer uncertainty and implementation evidence than the present UCI illustration supplies. ([Sage Journals][3])

**Conformal calibration.** Gibbs and Candès and Barber et al. demonstrate that sequential distribution shift and non-exchangeability require methods beyond ordinary split conformal prediction. The manuscript’s one-step result is credible because it remains within the conventional exchangeable setting; its novelty is the use of this calibration in the commitment protocol, not the rank theorem itself. ([NeurIPS Proceedings][6])

### Literature-based conclusion

**Reviewer inference:** the manuscript is likely original in its exact formulation and integration, but the originality is presently **credible rather than conclusively established**. The literature supports four revisions to the positioning:

1. Treat general lot-sizing sensitivity and stability radii as established background.
2. Make the strong optimal-prefix face, moving inside continuation and exact evidence artefact the principal novelty.
3. Present conformal prediction and Bellman-residual reasoning as enabling components rather than new foundational theories.
4. Make any polynomial implementation claim specific to the algorithm actually proved.

## 7. Minor comments

1. Define “strong” stability in plain language at first use: a tie with any path outside the prefix is already a loss of strong stability, even if an inside optimum remains.

2. Use “upper witness bound” consistently whenever the bracket has not closed. “Radius” by itself can imply exactness.

3. Clarify the manuscript’s “no LP” language. The released heuristic implementation may avoid LPs, but Theorem 7.2’s polynomial construction explicitly uses them.

4. Report uncertainty for all Monte Carlo frequencies, including the 4,492/5,000 result.

5. Distinguish clearly between the reported **330 exact agreements** and **512 bracket checks**; readers should not infer 512 independently exact comparisons.

6. Add processor, memory, operating system and concurrency information to runtime tables. Replace broad “commodity hardware” or batch-readiness claims with measured conditions.

7. Use neutral “cost units” rather than pounds in the UCI illustration, or repeat beside the table that the monetary mapping is synthetic.

8. Increase the font and legend size of the multi-panel audit figure. Use redundant line styles or markers so the figure remains interpretable in greyscale and for readers with colour-vision deficiencies.

9. Reduce excess blank space around the contents and opening sections.

10. Explain early that exact decimal strings in JSON are rational encodings and should not be parsed through binary floating point when verifying equality.

11. Correct the Winter Simulation Conference authors to **Nino Sluijter** and **Kai Schelthoff**.

12. Verify the UCI recommended creator list against the official record; the package’s final-author attribution appears inconsistent with that record. ([UCI Machine Learning Repository][5])

13. Do not present the ACM `10.5555` index record as a resolvable DOI. Prefer the stable DBLP bibliographic record for Richter and Vörös.

14. Replace “no lawful digital copy exists” with the evidence-supported statement: “No lawful full text was located in the targeted search conducted on 5 August 2026.”

15. Correct the title in `CITATION.cff` to match the title page exactly.

16. Clean `.pytest_cache`, `.pyc` and other generated files from the source archive. The original ZIP contained 19 such cache or bytecode entries outside the 116-file manifest set.

17. Preserve the present explicit caveats about one-step exchangeability, quantity recourse, synthetic validation and the absence of field evidence; these are strengths rather than weaknesses.

## 8. Prioritised revision plan

### Must fix before the claims are publishable

1. Correct the invalid upper-bound monotonicity test and produce a clean replay with a new receipt and manifest.
2. Add meaningful mutation controls and adversarial negative cases.
3. Separate the proved polynomial LP method from the released parametric routine; supply a fallback, a valid bound, or a candid incompleteness contract.
4. Resolve manuscript, code, data and third-party licensing; remove unauthorised publisher PDFs from the public archive.
5. Restore official UCI provenance, attribution and licence information.
6. Obtain and compare the full Richter and Vörös paper before finalising priority claims.
7. Synchronise version, title, date, claims records, assurance language and citation metadata.
8. Recast internal review and checker claims so they cannot be mistaken for external peer review or independent reproduction.

### Should fix to strengthen the paper

1. Add a theorem-and-assumption comparison table against the closest stability literature.
2. Foreground the (T>12) checker dependency and the status of unresolved disjuncts.
3. Add Monte Carlo confidence intervals and fuller benchmark-environment details.
4. Preserve separate counts for exact validation, bracket containment and mere execution.
5. Add one integration test that regenerates the release from a clean checkout and rejects metadata drift.
6. Make all practical claims explicitly conditional on the stylised cost transformation and lack of field validation.

### Could improve presentation or future work

1. Improve figure accessibility and reduce front-matter whitespace.
2. Add a small worked example of the JSON certificate-verification process.
3. Explore structure-specific breakpoint bounds for the Wagner–Whitin deviation graph.
4. Evaluate the commitment protocol in a genuine rolling production setting.
5. Study calibration under temporal dependence or forecast-regime shift, clearly separated from the present one-step theorem.

## 9. Editorial recommendation

**Recommendation: Major revisions.**

**Confidence: 0.94.**

The central mathematical contribution appears valid and sufficiently distinctive to justify continued development. The strict example, proof architecture, explicit tie semantics, small-instance oracle results and exact-rational evidence design are substantial strengths. I would not reject the work for lack of conventional peer review or field validation because Evidence Press candidate releases are not represented as journal-vetted outputs.

The release should nevertheless **not be listed as internally replayed in its present form**. The failed quick replay, incorrect test property, implementation/theorem mismatch, ambiguous checker independence and unresolved rights are direct contradictions of the proposed evidence status.

A decision in favour of candidate release would become well supported after:

* a clean and reproducible one-command replay;
* corrected mutation and negative controls;
* regenerated receipts and hashes;
* accurate complexity and completion claims;
* a lawful, provenance-complete public bundle;
* synchronised metadata;
* and a satisfactory full-text comparison with Richter and Vörös.

Discovery that the 1989 paper already contains the same strong-prefix, moving-continuation radius would require substantial reframing and could change the scientific recommendation. Conversely, if the comparison confirms the present distinction and the release defects are repaired, the remaining concerns would be bounded enough for an unrefereed Evidence Press candidate.

## 10. Provisional REF calibration

The most relevant provisional classification is **Unit of Assessment 10: Mathematical Sciences**, within Main Panel B, because the output’s substantive field is operational research and mathematical optimisation. REF 2029 recognises diverse and multi-component research outputs, including software and datasets, and assesses contributions to knowledge and understanding through originality, significance and rigour. As of the review date, final panel-specific REF 2029 criteria were still developing, so I use the current generic guidance together with the detailed REF 2021 Main Panel B descriptors. ([REF 2029][7])

The numerical sub-band values below use the **supplied 12-point high/medium/low mapping** for convenience; they are not official REF scores.

| Dimension                  | Provisional rating | Rationale                                                                                                                                                                                                                                                        | Confidence |
| -------------------------- | -----------------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------: |
| **Originality**            |  **3* low — 7/12** | The strong prefix-face formulation, moving continuation, exact certification hierarchy and executable protocol constitute a creative synthesis. The unresolved comparison with Richter and Vörös prevents a firmer 3* or 4* assessment.                          |       0.65 |
| **Significance**           | **2* high — 6/12** | The work addresses a credible planning problem and could provide useful auditable decision support. Influence, uptake, generality and operational benefit have not yet been demonstrated beyond synthetic and stylised illustration.                             |       0.70 |
| **Rigour**                 | **2* high — 6/12** | The mathematical treatment is careful, scope-aware and largely supported by independent spot checks. The failed release replay and unproved implementation guarantee are material because executable certification is part of the output’s central contribution. |       0.82 |
| **Overall output quality** | **2* high — 6/12** | Holistically, this is a strong and potentially 3* contribution whose current evidence package does not yet achieve its claimed reproducibility standard. The overall score is not an arithmetic average.                                                         |       0.78 |

A clean release, resolved novelty comparison and corrected implementation contract could plausibly move the overall assessment to **3* low**. A 4* case would ordinarily require either a demonstrably broader theoretical advance, decisive methodological generalisation, or evidence of substantial disciplinary or operational influence.

This calibration is **indicative only and is not an official REF panel decision**.

## 11. References

### Lot sizing, stability and planning

Chakravarti, N., & Wagelmans, A. P. M. (1998). Calculation of stability radii for combinatorial optimization problems. *Operations Research Letters, 23*(1–2), 1–7. `https://doi.org/10.1016/S0167-6377(98)00031-5` ([IDEAS/RePEc][8])

Forel, A., & Grunow, M. (2023). Dynamic stochastic lot sizing with forecast evolution in rolling-horizon planning. *Production and Operations Management, 32*(2), 449–468. `https://doi.org/10.1111/poms.13881` ([Sage Journals][3])

Richter, K., & Vörös, J. (1989). A parametric analysis of the dynamic lot-sizing problem. *Journal of Information Processing and Cybernetics, 25*(3), 67–73. `https://dblp.org/rec/journals/eik/RichterV89` ([Academia.edu][2])

Richter, K., & Weber, J. (1994). Sequential stability of the constant cost dynamic lot size model—Searching for monotonicity. *OR Spektrum, 15*, 197–203. `https://doi.org/10.1007/BF01719450` ([Springer Nature Link][9])

van Hoesel, S. P. M., & Wagelmans, A. P. M. (1993). Sensitivity analysis of the economic lot-sizing problem. *Discrete Applied Mathematics, 45*(3), 291–312. `https://doi.org/10.1016/0166-218X(93)90016-H` ([ScienceDirect][10])

Weijers, E., Sluijter, N., Hogers, G., Schelthoff, K., Adan, I., & van Jaarsveld, W. (2025). Improving plan stability in semiconductor manufacturing through stochastic optimization: A case study. In *Proceedings of the 2025 Winter Simulation Conference* (pp. 1815–1826). `https://www.informs-sim.org/wsc25papers/con235.pdf` ([INFORMS Simulation Society][11])

### Inverse and parametric shortest paths

Chillara, S., Gajjar, K., & Raja, N. (2026). *Shortest paths with linear edge weights*. arXiv. `https://arxiv.org/abs/2607.21055` ([arXiv][12])

Gajjar, K., & Radhakrishnan, J. (2019). *Parametric shortest paths in planar graphs*. arXiv. `https://arxiv.org/abs/1811.05115` ([arXiv][4])

Gassner, E. (2009). *Selected partial inverse combinatorial optimization problems with forbidden elements* (Report 2009-15). Graz University of Technology. `https://www.math.tugraz.at/fosp/pdfs/tugraz_0149.pdf` 

Ley, E., & Merkert, M. (2025). Solution methods for partial inverse combinatorial optimization problems in which weights can only be increased. *Journal of Global Optimization, 93*, 263–298. `https://doi.org/10.1007/s10898-025-01529-x` ([Springer Nature Link][13])

### Conformal prediction

Barber, R. F., Candès, E. J., Ramdas, A., & Tibshirani, R. J. (2023). Conformal prediction beyond exchangeability. *The Annals of Statistics, 51*(2), 816–845. `https://doi.org/10.1214/23-AOS2276` ([Project Euclid][14])

Gibbs, I., & Candès, E. J. (2021). Adaptive conformal inference under distribution shift. *Advances in Neural Information Processing Systems, 34*, 1660–1672. `https://proceedings.neurips.cc/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html` ([NeurIPS Proceedings][6])

### Data

Ferreira, R., Martiniano, A., Ferreira, A., Ferreira, A., & Sassi, R. (2016). *Daily Demand Forecasting Orders* [Data set]. UCI Machine Learning Repository. `https://doi.org/10.24432/C5BC8T` ([UCI Machine Learning Repository][5])

### Release and assessment standards

Evidence Press. (2026). *About this site*. `https://evidence-press.pages.dev/about/` ([Evidence Press][1])

Evidence Press. (2026). *Evidence Press papers index JSON schema*. `https://evidence-press.pages.dev/api/schema.json` 

Research Excellence Framework. (2026). *Section 4—Contributions to Knowledge and Understanding guidance*. `https://2029.ref.ac.uk/guidance/section-4-contributions-to-knowledge-and-understanding-cku-guidance/` ([REF 2029][7])

Research Excellence Framework. (2026). *Units of assessment*. `https://2029.ref.ac.uk/panels/units-of-assessment/` ([REF 2029][15])

Research England, Scottish Funding Council, Higher Education Funding Council for Wales, & Department for the Economy, Northern Ireland. (2019). *Panel criteria and working methods*. `https://2021.ref.ac.uk/media/1450/ref-2019_02-panel-criteria-and-working-methods.pdf` ([REF 2021][16])

[END]

[1]: https://evidence-press.pages.dev/about/ "About this site · Evidence Press"
[2]: https://independent.academia.edu/JozsefVoros "Jozsef Voros - Independent Researcher"
[3]: https://journals.sagepub.com/doi/abs/10.1111/poms.13881 "https://journals.sagepub.com/doi/abs/10.1111/poms.13881"
[4]: https://arxiv.org/abs/1811.05115 "[1811.05115] Parametric Shortest Paths in Planar Graphs"
[5]: https://archive.ics.uci.edu/dataset/409/daily%2Bdemand%2Bforecasting%2Borders "https://archive.ics.uci.edu/dataset/409/daily%2Bdemand%2Bforecasting%2Borders"
[6]: https://proceedings.neurips.cc/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html "Adaptive Conformal Inference Under Distribution Shift"
[7]: https://2029.ref.ac.uk/guidance/section-4-contributions-to-knowledge-and-understanding-cku-guidance/ "https://2029.ref.ac.uk/guidance/section-4-contributions-to-knowledge-and-understanding-cku-guidance/"
[8]: https://ideas.repec.org/p/ems/eureir/1403.html "https://ideas.repec.org/p/ems/eureir/1403.html"
[9]: https://link.springer.com/article/10.1007/BF01719450 "https://link.springer.com/article/10.1007/BF01719450"
[10]: https://www.sciencedirect.com/science/article/pii/0166218X9390016H "https://www.sciencedirect.com/science/article/pii/0166218X9390016H"
[11]: https://www.informs-sim.org/wsc25papers/con235.pdf "https://www.informs-sim.org/wsc25papers/con235.pdf"
[12]: https://arxiv.org/abs/2607.21055 "https://arxiv.org/abs/2607.21055"
[13]: https://link.springer.com/article/10.1007/s10898-025-01529-x "Solution methods for partial inverse combinatorial optimization problems in which weights can only be increased | Journal of Global Optimization | Springer Nature Link"
[14]: https://projecteuclid.org/journals/annals-of-statistics/volume-51/issue-2/Conformal-prediction-beyond-exchangeability/10.1214/23-AOS2276.short "https://projecteuclid.org/journals/annals-of-statistics/volume-51/issue-2/Conformal-prediction-beyond-exchangeability/10.1214/23-AOS2276.short"
[15]: https://2029.ref.ac.uk/panels/units-of-assessment/ "https://2029.ref.ac.uk/panels/units-of-assessment/"
[16]: https://2021.ref.ac.uk/media/1450/ref-2019_02-panel-criteria-and-working-methods.pdf "https://2021.ref.ac.uk/media/1450/ref-2019_02-panel-criteria-and-working-methods.pdf"
