# Literature and novelty audit

**Search frozen:** 5 August 2026 (extended for v2.1.0 with partial inverse / partial anti-inverse optimisation)  
**Purpose:** delimit the contribution; this is a targeted audit, not a systematic review.

## Corpus boundary

### Full text inspected

- van Hoesel, C. P. M., & Wagelmans, A. P. M. (1993). Sensitivity analysis of the economic lot-sizing problem. *Discrete Applied Mathematics, 45*(3), 291-312. https://doi.org/10.1016/0166-218X(93)90016-H
- Chakravarti, N., & Wagelmans, A. P. M. (1998). Calculation of stability radii for combinatorial optimization problems. *Operations Research Letters, 23*(1-2), 1-7. Working-paper full text inspected; published DOI: https://doi.org/10.1016/S0167-6377(98)00031-5
- Weijers, E., Sluijter, N., Hogers, G., Schelthoff, K., Adan, I., & van Jaarsveld, W. (2025). Improving plan stability in semiconductor manufacturing through stochastic optimization: A case study. *Proceedings of the 2025 Winter Simulation Conference*, 1815-1826. https://www.informs-sim.org/wsc25papers/con235.pdf

The inspected-copy hashes are retained in `THIRD_PARTY_NOTICES.md`. Article PDFs and extracted article text are excluded from the public package because redistribution permission was not established.

### Added for v2.1.0 (partial inverse / anti-inverse; verified 5 August 2026)

- Gassner, E. (2009). Selected partial inverse combinatorial optimization problems with forbidden elements. Technical Report 2009-15, Graz University of Technology. https://www.math.tugraz.at/fosp/pdfs/tugraz_0149.pdf — partial anti-inverse shortest paths strongly NP-hard under L1 and L-infinity.
- Ley, E., & Merkert, M. (2025). Solution methods for partial inverse combinatorial optimization problems in which weights can only be increased. *Journal of Global Optimization, 93*, 263-298. https://doi.org/10.1007/s10898-025-01529-x — partial inverse shortest path on a DAG NP-complete even with one required arc.
- Cheung, K. K. H., Gleixner, A., & Steffy, D. E. (2017). Verifying integer programming results. *IPCO 2017*, LNCS 10328, 148-160. https://doi.org/10.1007/978-3-319-59250-3_13 — certificate-checking paradigm adopted by the v2.1.0 exact layer.
- Eifler, L., & Gleixner, A. (2021). A computational status update for exact rational mixed integer programming. *IPCO 2021*, LNCS 12707, 163-177. https://doi.org/10.1007/978-3-030-73879-2_12

Representative added search strings: "partial inverse shortest path DAG NP-complete"; "partial anti-inverse shortest path forbidden elements L-infinity"; "verifying integer programming results exact rational certificate".

### Richter--Vörös (1989) acquisition dossier (added 5 August 2026, manual search by the project owner)

**Verified citation.** Richter, K., & Vörös, J. (1989). A parametric analysis of the dynamic lot-sizing problem. *Journal of Information Processing and Cybernetics: EIK, 25*(3), 67–73. Akademie-Verlag, Berlin; ISSN 0863-0593; Zbl 0672.90033; MSC 90B05, 90C31. Triangulated across zbMATH, dblp and later OR-Spektrum reference lists.

**Why no lawful digital full text was located.** The 10.5555 identifier on the ACM page is the DOI system's reserved *test prefix* used for ACM Guide index stubs; https://doi.org/10.5555/70375.70376 returns 404 and Crossref has no record. EIK (the GDR cybernetics journal, English title from vol. 23, 1987) ceased with vol. 30 (1994); the 1987–94 English-title run is not known to have been digitised (De Gruyter's archive e-books cover the pre-1987 German-title volumes). OpenAlex (W3191933066) records the article as closed access with a single location (the ACM stub) and no repository copy; the other routes documented in this bounded search produced no lawful full text.

**Content per zbMATH review.** Parametrises Wagner–Whitin in (i) setup and holding costs, (ii) the demand vector, (iii) both jointly; derives stability regions within which a Wagner–Whitin solution remains optimal; computes the joint case numerically as a two-parameter region. Consistent with a fixed-solution, scalar-parametrisation object; no indication of a prefix-class event, simultaneous weighted norms, or floors. A review summary cannot exclude theorem-level overlap.

**Acquisition routes (in priority order).**
1. Author offprint: József Vörös, Professor Emeritus, University of Pécs FBE (voros.jozsef [at] ktk.pte.hu, office B111; full member, Hungarian Academy of Sciences). Secondary: Knut Richter (emeritus, Europa-Universität Viadrina; current status unverified).
2. British Library On Demand (Boston Spa) — probable holding, not programmatically confirmed (catalogue blocks automated queries); check https://ondemand.bl.uk before ordering.
3. Subito (https://www.subito-doc.de) — German document delivery serving private individuals abroad; TIB Hannover and the Berlin state libraries hold EIK comprehensively; near-guaranteed for a DDR journal.

**Accessible same-programme instalments** (metadata verified; full text not inspected in this release): Richter (1987), *EJOR 31*, 61–65, doi:10.1016/0377-2217(87)90137-8; Richter & Vörös (1989), *EJOR 41*(2), 169–173.


### Metadata or abstract inspected, full text not obtained

- Richter, K., & Vörös, J. (1989). A parametric analysis of the dynamic lot-sizing problem. *Journal of Information Processing and Cybernetics, 25*(3), 67-73. https://dblp.org/rec/journals/eik/RichterV89
- Richter, K., & Weber, J. (1994). Sequential stability of the constant cost dynamic lot size model-searching for monotonicity. *OR Spektrum, 15*(4), 197-203. https://doi.org/10.1007/BF01719450
- Forel, A., & Grunow, M. (2023). Dynamic stochastic lot sizing with forecast evolution in rolling-horizon planning. *Production and Operations Management, 32*(2), 449-468. https://doi.org/10.1111/poms.13881
- Barber, R. F., Candès, E. J., Ramdas, A., & Tibshirani, R. J. (2023). Conformal prediction beyond exchangeability. *The Annals of Statistics, 51*(2), 816-845. https://doi.org/10.1214/23-AOS2276
- Gibbs, I., & Candès, E. (2021). Adaptive conformal inference under distribution shift. *Advances in Neural Information Processing Systems, 34*, 1660-1672. https://arxiv.org/abs/2106.00170

## Inspected claims

1. **Demand-vector stability predates this paper.** The available Richter-Vörös abstract says it studies setup/holding costs, the demand vector, and combined costs and demand, and finds parameter stability regions preserving a Wagner-Whitin solution.
2. **Simultaneous perturbations and maximal stability regions predate this paper.** van Hoesel and Wagelmans explicitly position earlier work in those terms and study sensitivity of one optimal economic lot-sizing solution.
3. **Fixed-solution combinatorial stability radii predate this paper.** Chakravarti and Wagelmans give general stability-radius results for fixed binary solutions under independently bounded objective-coefficient perturbations.
4. **Sequential/horizon stability predates this paper.** Richter and Weber address sequential stability and monotonicity under a different object.
5. **Real-data plan-stability evaluation exists.** Forel-Grunow and Weijers et al. set a higher external-validity benchmark than the synthetic and reconstructed case here.
6. **Generic partial inverse and anti-inverse shortest paths are hard.** Gassner (2009) and Ley-Merkert (2025) establish NP-hardness for the arc-weight analogues of the present decision event; the open complexity question is therefore confined to the demand-induced, ordered-slope restriction, and the paper's polynomial certificate is a bound, not a solution, of the exact anti-inverse quantity.
6. **Ordinary conformal coverage is exchangeability-dependent.** The beyond-exchangeability and adaptive conformal literature provides different procedures and guarantees under drift.

## Contribution boundary

The release does **not** claim priority for demand sensitivity, stability regions, fixed-solution radii or forecast-horizon analysis. Its candidate contribution is narrower:

- loss of compulsory optimality of a selected **prefix face**, where the best prefix-retaining continuation may switch;
- a floor-aware polynomial frozen-comparator lower certificate on a prefix-deviation directed acyclic graph;
- a polynomial lower-upper bracket with exact closure conditions;
- integration with exact inverse formulations, one-step calibrated revisions and a structural rolling dead-zone theorem.

The full-path endpoint belongs near the fixed-solution literature and is presented as a special case, not a priority claim.

## Missingness and uncertainty

The decisive missing item is the full 1989 Richter-Vörös article. Searches covered exact title/author queries, ACM metadata, DBLP/EIK issue records, author profiles, ResearchGate, SciSpace, scholarly web search and archive indexes. The indexed abstract is enough to narrow the claim but not to settle theorem-level overlap, weighted-norm geometry, floors or prefix faces. The manuscript therefore labels originality as conditional.

## Search strings

Representative queries included:

- `"A Parametric Analysis of the Dynamic Lot-Sizing Problem" Richter Vörös PDF`
- `dynamic lot sizing demand perturbation stability region`
- `parametric dynamic lot sizing demand vector Wagner Whitin`
- `stability radius combinatorial optimisation shortest path`
- `forecast evolution rolling horizon lot sizing`
- `plan stability semiconductor rolling horizon`
- `conformal prediction exchangeability distribution shift online`
