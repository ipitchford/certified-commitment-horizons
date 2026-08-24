1. **C1 — no refutation under the usual domain assumptions; the assumptions are not stated strongly enough.**
   - The halfspace walk is exact provided:
     \[
     w_t>0,\qquad \widehat d_t\ge \underline d_t,
     \]
     all quantities are finite rationals, and demand has no upper bound.
   - Under those assumptions, the maximal reduction is a continuous piecewise-linear nondecreasing function of \(r\). Therefore a finite first root is attained exactly, and moving every relevant coordinate maximally in its reducing direction gives weighted distance at most \(r\).
   - **Counterexample if zero weights are accepted:** one coordinate with
     \[
     g=1,\quad c=-1,\quad \widehat d=\underline d=0,\quad w=0.
     \]
     Because the coordinate is unweighted, choosing \(d=1\) gives reduction \(1\) at distance \(0\), so the true radius is \(0\). The claimed walk instead uses \(|c|/w\), which is undefined.
   - Negative weights make the alleged weighted \(L_\infty\) expression not a metric at all.
   - **Impact:** potentially breaks certified-safe soundness if invalid weights are accepted. Otherwise no refutation found.

2. **C2 — no refutation found, conditional on C1’s domain assumptions and on the definitions of \(a_e,b_e,\kappa^*\) matching the actual path gap.**
   - For each fixed path, minimizing its affine frozen gap over the weighted box gives exactly \(a(P)-rb(P)-\kappa^*\) on a saturation interval.
   - The minimum of finitely many affine functions is concave within an interval.
   - Continuity at breakpoints follows because the unsaturated and saturated formulas agree exactly when
     \[
     r=w_t(\widehat d_t-\underline d_t).
     \]
   - Global non-increase also follows directly from nested uncertainty sets.
   - This does **not** imply global concavity; fortunately the claim only asserts intervalwise concavity.

3. **C3 — the Newton argument is basically sound, but the “no flat-zero segment” statement is false globally and breakpoint handling needs an explicit special case.**
   - Consider \(T=2\), with
     \[
     q_0=1,\quad q_1=0,\quad K_0=K_1=0,
     \]
     \[
     \widehat d=(0,1),\quad \underline d=(0,0),\quad w=(1,1).
     \]
     Let
     \[
     P^*=(0,1),(1,2),\qquad Q=(0,2),
     \]
     and protect the first arc of \(P^*\).
   - Costs are
     \[
     C_{P^*}(d)=d_0,\qquad C_Q(d)=d_0+d_1.
     \]
     Thus \(P^*\) is exactly nominally optimal, the nominal gap is \(1\), and
     \[
     F(r)=
     \begin{cases}
     1-r,&0\le r\le1,\\
     0,&r\ge1.
     \end{cases}
     \]
   - Hence a flat-zero segment absolutely can occur after the first crossing, even though \(F(0)>0\).
   - This does not invalidate the first crossing: it remains exactly \(r=1\). But binary search must detect \(F(B)=0\) at a breakpoint and return \(B\), rather than insisting on an interval whose left endpoint has strictly positive \(F\).
   - Within a fixed interval whose left endpoint has \(F>0\), the Newton proof is sound:
     - an active negative piece must have \(b>0\);
     - its root lies between the first crossing and the current iterate;
     - roots strictly decrease until termination;
     - finitely many pieces imply finite termination.
   - “Iterates strictly decrease” should exclude the case where the seed already has \(F(r_0)=0\), in which case there is no update.
   - **Impact:** false exactness/description claim and possible implementation completeness bug at breakpoints. It need not break soundness if equality at breakpoints is handled explicitly.

4. **C4 — no mathematical refutation found, but its precondition must include explicit breakpoint handling.**
   - In the final interval, all positive coefficients have saturated, so only negative coefficients contribute to \(b\).
   - Since every path slope is nonnegative, \(\max_P b(P)=0\) implies every outside-path piece is constant. If their minimum is strictly positive, no outside path can ever tie \(P^*\), so the frozen radius is infinite.
   - Since frozen radius is a lower bound on strong radius, frozen infinity indeed implies strong infinity.
   - If \(\max b>0\) and \(F(B)>0\) at the final interval’s left endpoint \(B\), the max-\(b\) path has a finite root to the right and supplies a valid Newton seed.
   - However, “binary search guarantees \(F(B)>0\)” is only true if an exact zero at \(B\) was already returned as the answer. The instance in item 3 has \(F(B)=0\) at the largest breakpoint.
   - **Impact:** only completeness/implementation correctness if the equality case is omitted.

5. **C5 — no refutation found.**
   - For every demand vector,
     \[
     \min_{\text{prefix paths}}C_P(d)\le C_{P^*}(d).
     \]
     Therefore beating the best prefix-retaining path is at least as hard as beating frozen \(P^*\), giving
     \[
     \rho_f\le \rho.
     \]
   - Consequently \(\rho_f=\infty\) implies \(\rho=\infty\).
   - If a frozen witness \(d^*\) also satisfies
     \[
     C_Q(d^*)\le\min_{\text{prefix paths}}C_P(d^*),
     \]
     it is a valid strong witness at the frozen lower bound, proving equality.
   - The triage inequalities are sound if “proposed” means a tested uncertainty budget:
     - budget \(<\) certified lower bound: safe;
     - budget \(\ge\) exactly verified witness distance: destabilising.
   - Ties being counted as destabilisation is consistent with all of these inequalities.

6. **C6 — no refutation found, but the phrase “witness at the radius” must not be interpreted as a destabilising witness.**
   - For any prefix-retaining \(P\), strictly below the pairwise radius,
     \[
     C_Q(d)>C_P(d)\ge\min_{\text{prefix paths}} C_{P'}(d),
     \]
     so \(Q\) cannot destabilise. Thus \(r(Q,P)\le\rho(Q)\).
   - For a convex mixture,
     \[
     C_{\rm mix}(d)=\sum_P\lambda_P C_P(d)
     \ge \min_P C_P(d).
     \]
     Therefore
     \[
     C_Q(d)>C_{\rm mix}(d)
     \]
     also excludes destabilisation.
   - At the halfspace radius, one only gets
     \[
     C_Q(d)=C_{\rm mix}(d),
     \]
     and generally
     \[
     C_{\rm mix}(d)>\min_P C_P(d).
     \]
     So the boundary point need not be a strong witness.
   - Example: two inside paths have costs \(0\) and \(2\) at the boundary, their equal mixture costs \(1\), and \(Q\) also costs \(1\). Then \(Q\) ties the mixture but still loses to the best inside path of cost \(0\).
   - **Impact:** no problem for the lower-bound claim; potentially breaks certified-destabilising soundness only if a mixture equality is incorrectly promoted to a strong witness without the separate exact inside-minimum check.

7. **C7 — no refutation found, assuming every stored “certified lower bound” has actually passed exact verification and unprocessed paths retain at least their pairwise lower bound.**
   - If a path has lower bound \(L_Q\), then
     \[
     L_Q\le\rho(Q).
     \]
     Hence
     \[
     \min_Q L_Q\le\min_Q\rho(Q)=\rho.
     \]
   - An exactly verified witness of radius \(R\) gives \(\rho\le R\).
   - If every path has \(L_Q\ge R\), then \(\rho\ge R\), proving equality.
   - Pruning at \(L_Q\ge R_{\rm incumbent}\) is safe because the incumbent is an upper bound and can only decrease:
     \[
     L_Q\ge R_{\rm old}\ge R_{\rm final}.
     \]
   - Equality at the pruning threshold is safe because ties count as destabilisation.
   - **Implementation caveat:** “best lower bound” must mean the maximum of independently valid lower bounds for that disjunct, not an unverified floating LP value.
   - **Impact:** no refutation of the stated exact assembly.

8. **C8 — the exact-binary-instance claim is sound only for finite validated inputs; the rescaling claim is overstated.**
   - For finite binary64 values, converting each value to its exact rational value and solving that rational problem is sound for the supplied binary instance.
   - It is not complete for arbitrary IEEE-754 inputs unless NaNs and infinities are rejected. `Fraction(float('nan'))` and `Fraction(float('inf'))` do not define rational problem data.
   - “Power-of-two rescalings are exact in binary” is false if the rescaling is performed in binary64 without range checks. For example,
     \[
     x=2^{-1074}
     \]
     is the smallest positive binary64 subnormal, but multiplying it by \(1/2\) rounds to zero. A nonzero coefficient can therefore disappear under a nominal power-of-two rescaling.
   - Overflow similarly turns finite values into infinity.
   - If rescaling is performed after ingestion in exact rational arithmetic, this objection disappears.
   - Demand-unit rescaling also requires more than weights. If
     \[
     d'_t=s\,d_t,
     \]
     preserving the model requires
     \[
     q'_i=q_i/s,\qquad w'_t=w_t/s,
     \]
     with setup costs unchanged. Adjusting only \(w\) preserves the distance but not variable production costs, and can change optimal paths and radii.
   - Scaling all \(K_i,q_i\) by one common positive factor preserves comparisons and radii. Scaling them by unrelated factors does not.
   - **Impact:** potentially breaks certificate invariance and, if rescaled binary64 data are silently treated as equivalent to the original, can recreate a certified-safe soundness failure through underflow-to-zero. For direct exact solution of finite supplied binary values, no refutation found.

9. **Independent checker’s saturation-infinity re-proof — no refutation found under the intended reachability definition.**
   - In the final interval, positive coefficients are saturated, so a path has \(b(P)>0\) exactly when it contains some negative coefficient.
   - Since arc slope contributions are nonnegative and additive, one reachable/co-reachable negative-coefficient arc on an outside complete path implies some outside path with positive slope and therefore rules out the claimed constant-positive tail.
   - The checker must mean arcs that lie on a complete outside path. Mere graph reachability without completion would be too strong in a general graph, though in the complete acyclic lot-sizing graph every reached node can continue to \(T\).
   - Arcs on the still-matched protected prefix should not cause a false rejection: their coefficients relative to \(P^*\) are zero on the periods they cover.
   - **Impact:** at worst completeness if reachability is implemented too broadly; no certified-safe soundness counterexample found.

10. **“Exact nominal optimality implies \(F(0)\ge0\)” — no refutation found.**
    - At \(r=0\),
      \[
      F(0)=\min_{Q\in O_k}\bigl(C_Q(\widehat d)-C_{P^*}(\widehat d)\bigr).
      \]
      If \(P^*\) is exactly globally optimal, every term is nonnegative.
    - This requires consistent treatment of the empty outside set, ordinarily \(F(0)=+\infty\).

11. **“\(F(0)<0\) implies the supplied nominal path was not exactly optimal” — no refutation found.**
    - \(F(0)<0\) supplies an outside path \(Q\) with
      \[
      C_Q(\widehat d)<C_{P^*}(\widehat d),
      \]
      directly disproving exact optimality.
    - This conclusion is stronger than merely showing a tie or an alternative optimum.

**Bottom line:** under finite rational inputs, positive weights, feasible nominal demands, and exact breakpoint handling, C1–C7 are largely sound. The concrete defects are the unstated weight/domain preconditions, the false global “no flat-zero segment” statement, the need to special-case crossings exactly at breakpoints, the danger of treating mixture equality as a strong witness, and the overbroad IEEE/power-of-two/unit-rescaling claims in C8.