# Adversarial review brief for the v2.2.0 addendum

**Status:** review is with the project owner (machine reviewer unavailable on 18 August 2026; no machine review of v2.2.0 has been performed).

The brief below is refute-framed: it lists the specific attack surfaces for each of the four new results, followed by the definitions and the full section text as sent. Treat any reviewer reply as hypotheses and verify each claim against the implementation before acting.

---

You are an adversarial mathematical reviewer. Your ONLY goal is to REFUTE. Below are definitions and four new results (with proofs) added to a paper on the strong prefix-stability radius of Wagner-Whitin lot sizing. Model: periods 1..T, nodes 1..T+1, complete paths v0=1<...<vm=T+1, reduced arc cost c_ij(d)=K_i+q_i*(D_j-D_i) with K>=0, q non-increasing, demand box d>=floor>=0, weighted L-infinity radius. Attack each claim in turn. Hunt specifically for: (a) counting errors at the boundary s=T, s=T+1, T=1; (b) failure of the local-tie equivalence under ties, zero setup costs, zero demands, O_r over an empty set, and the distinction between unconstrained suffix value V and the protected-continuation value W; (c) an instance where min over arcs of the one-arc radius differs from the prefix radius; (d) holes in the NP witness-size argument (does the extended polyhedron really capture the event? bit-length claim); (e) failure of the production-balance conversion lemma: unused setups, zero demand, y_1=1 requirement, late-vs-early divergence in the deviation row, big-M validity, and whether min plan cost really equals B_k(d) including when some K_i=0. For each of the four results output: VERDICT: REFUTED (with explicit counterexample data) / GAP (exact location and why the step fails) / NO REFUTATION FOUND (after stating the strongest attack you tried and why it fails). Be concrete and numerical where possible; do not pad.

=== DEFINITIONS ===
\section{The decision problem}\label{sec:decision}

A fixed calendar fence answers a scheduling convention, not a robustness question. The relevant decision is instance-specific:

\begin{quote}
How far must the current demand forecast move before an optimal schedule may change any protected setup epoch or replenishment-cycle boundary?
\end{quote}

Periods are $1,\ldots,T$. A complete path
\[
P=(v_0=1<v_1<\cdots<v_m=T+1)
\]
encodes replenishment cycles: arc $(v_r,v_{r+1})$ sets up in period $v_r$ and covers demand through period $v_{r+1}-1$. Fix a nominal forecast $\dhat\in\R_+^T$, a selected nominal optimal path $P^\star$, and its first $k$ arcs
\[
\pi_k=(v_0,\ldots,v_k).
\]
Let
\[
\cI_k=\{P:P\text{ starts with }\pi_k\},
\qquad
\cO_k=\cP\setminus\cI_k,
\]
and define the best prefix-retaining and prefix-leaving costs at revised demand $d$ by
\[
A_k(d)=\min_{P\in\cI_k}C_P(d),
\qquad
B_k(d)=\min_{Q\in\cO_k}C_Q(d).
\]
A tie already permits a rational schedule change. Thus the prefix is compulsory for every optimum exactly when $B_k(d)>A_k(d)$.

Let $w\in\R_{++}^T$, let $\ellv\in\R_+^T$ satisfy $\ellv\le\dhat$, and put
\[
\norm{x}_{\infty,w}=\max_t w_t|x_t|.
\]
Weights set the coordinate scale; they are directionally symmetric. Direction-specific revision penalties would require a genuinely asymmetric gauge and are outside the present results.

\begin{definition}[Strong prefix-stability radius]\label{def:radius}
The weighted strong radius of the first $k$ cycles is
\begin{equation}\label{eq:rho}
\rho_{k,w}(\dhat)=
\inf\left\{
\winf{d-\dhat}: d\ge\ellv,\ B_k(d)\le A_k(d)
\right\},
\end{equation}
with the convention $\inf\varnothing=+\infty$. For $w=\one$ we write $\rho_{k,\infty}$.
\end{definition}

The radius freezes structural setup epochs and cycle boundaries. It does not freeze quantities. Under the uncapacitated model, a retained cycle can adjust its order quantity to revised or realised demand.

\begin{problem}[\WWR]\label{prob:decision}
\textbf{Input:} rational $K,q,\dhat,\ellv,w,R$, a rational Wagner--Whitin instance, a nominally optimal path $P^\star$, and $k\in\{1,\ldots,m\}$. Nominal optimality may be treated as a promise or checked by one shortest-path calculation.\\
\textbf{Question:} does some $d\ge\ellv$ satisfy
\[
\winf{d-\dhat}\le R
\quad\text{and}\quad
B_k(d)\le A_k(d)?
\]
Equivalently, is $\rho_{k,w}(\dhat)\le R$?
\end{problem}

\begin{proposition}[Basic geometry]\label{prop:geometry}
Assume $P^\star$ is nominally optimal.
\begin{enumerate}[label=(\alph*)]
\item For every $r<\rho_{k,w}(\dhat)$, every optimum at every admissible $d$ with $\winf{d-\dhat}\le r$ retains $\pi_k$.
\item If the radius is finite, a nearest destabilising point exists. At a nearest point, $A_k(d)=B_k(d)$, except that $\rho_{k,w}=0$ may already be a nominal tie; even then $A_k(\dhat)=B_k(\dhat)$.
\item $\rho_{k+1,w}(\dhat)\le\rho_{k,w}(\dhat)$ whenever both prefixes exist.
\item The value depends only on the node prefix $\pi_k$, not on which nominal optimum containing that prefix supplied it.
\end{enumerate}
\end{proposition}

\begin{proof}
Part (a) is the complement of the event in \eqref{eq:rho}. For (b), intersect the admissible domain with a closed ball whose radius exceeds the infimum. This set is compact. Both $A_k$ and $B_k$ are minima of finitely many affine functions and hence continuous, so a convergent destabilising sequence attains the infimum. If $B_k<A_k$ at a nearest point, continuity along the segment from $\dhat$ gives an earlier equality. For (c), $\cI_{k+1}\subseteq\cI_k$ and $\cO_{k+1}\supseteq\cO_k$. Part (d) follows because these two path classes are determined by $\pi_k$ alone.
\end{proof}


=== NP PROPOSITION ===
\begin{proposition}[Membership in NP]\label{prop:np}
The rational decision problem \WWR{} belongs to NP: a yes-instance with
input encoding length $L$ has a certificate of length
$\operatorname{poly}(L)$ verifiable in $\operatorname{poly}(L)$ exact
rational arithmetic.
\end{proposition}

\begin{proof}
A yes-certificate is a pair $(Q,d)$: an outside path (at most $T+1$ node
labels) and a rational revised demand vector. The verifier checks, in
exact rational arithmetic, that $Q$ is a complete path not retaining
$\pi_k$; that $d\ge\ellv$ and $w_t\lvert d_t-\dhat_t\rvert\le R$ for
every $t$; and that $C_Q(d)\le C_{\pi_k}(d)+V_{s}(d)=A_k(d)$, computing
$V_s(d)$ by the $O(T^2)$ suffix recursion. Every intermediate value is a
sum of at most $T+1$ products of input rationals with $d$-coordinates, so
all numerators and denominators stay within $\operatorname{poly}(L)$ bits
and the verification runs in polynomial time; no potentials need be
supplied, since the verifier recomputes the inside envelope itself.

For the certificate-size bound, fix any $Q\in\cO_k$ witnessing the event.
The feasible set
$\{(d,u):d\ge\ellv,\ \winf{d-\dhat}\le R,\ u_s=0,\
u_j-u_i\le\bar c_{ij}(d)\ (s\le i<j\le T+1),\
C_Q(d)\le C_{\pi_k}(d)+u_{T+1}\}$
is a rational polyhedron with $O(T^2)$ rows whose coefficients are input
data, and it is non-empty exactly when $d$ can be chosen destabilising
for $Q$ (\cref{thm:fixedlp}): the potentials can always be raised to
$u_{T+1}=V_s(d)$. A non-empty rational polyhedron contains a point of
encoding length polynomial in the facet encoding length --- a basic
feasible solution whose entries are quotients of subdeterminants of the
constraint data \parencite[Cor.~10.2]{Schrijver1986} --- and projecting
it to $d$ gives the required $\operatorname{poly}(L)$-bit witness. If
nominal optimality of $P^\star$ is not promised, the verifier first
checks it by one exact shortest path. The release ships this verifier as
an executable function, exercised against certified witnesses and
corrupted certificates in the test suite.
\end{proof}


=== NEW SECTION ===
\section{Enumeration complexity, arc decomposition and a compact exact model}\label{sec:addendum}

This section, added in version 2.2.0, settles four questions raised by a
machine complexity-and-prior-art audit of the released escalation layer:
the exact size of the released disjunction, a decomposition of the strong
radius into single-arc events, the encoding-level content of
\cref{prop:np}, and a mixed-integer reformulation whose size is
polynomial without arc--demand products. Every theorem here is
machine-checked against the release's exact rational layer; the
producer-side evidence is described in \cref{sec:audit}.

\subsection{Exact size and cost of the released disjunction}\label{sec:enumsize}

For a node $i\in\{1,\ldots,T+1\}$, let $N(i)$ denote the number of paths
from $i$ to the terminal node $T+1$ in the complete lot-sizing graph, so
$N(i)=2^{\max\{T-i,0\}}$: a path from $i$ chooses an arbitrary subset of
the internal nodes $\{i+1,\ldots,T\}$, and $N(T+1)=1$.

\begin{theorem}[Outside-path count]\label{thm:outsidecount}
Let $\pi_k$ end at $s=v_k$. Then
\[
\lvert\cO_k\rvert
=N(1)-N(s)
=2^{T-1}-2^{\max\{T-s,0\}},
\]
and, partitioning by the first protected arc left, paths whose first
divergence occurs at $(v_r,v_{r+1})$ number $N(v_r)-N(v_{r+1})$, which
telescopes over $r<k$ to the same total. Every non-empty prefix has
$s\ge2$, hence
\[
2^{T-2}\le\lvert\cO_k\rvert<2^{T-1}.
\]
\end{theorem}

\begin{proof}
A complete path is determined by the subset of internal nodes
$\{2,\ldots,T\}$ it visits, giving $\lvert\cP\rvert=N(1)=2^{T-1}$.
Retaining $\pi_k$ fixes the inclusion of every protected node and the
exclusion of every internal node below $s$ that $\pi_k$ skips, and leaves
the subset of $\{s+1,\ldots,T\}$ free, giving $N(s)$ inside paths (one
when $s\in\{T,T+1\}$, where the free set is empty). Subtraction and the
first-divergence partition are immediate; the bound uses $s\ge2$ for any
prefix with at least one arc.
\end{proof}

\begin{corollary}[The released escalation is worst-case exponential]\label{cor:enumexp}
Both released escalation routines --- the floating disjunction and its
exact certified counterpart --- materialise the full candidate family
$\cO_k$, compute a pairwise lower bound per candidate and sort, before the
first fixed-competitor programme is solved. Their candidate-generation
stage therefore performs $\Theta(\lvert\cO_k\rvert)$ work and stores
$\Theta(\lvert\cO_k\rvert)$ records, which by \cref{thm:outsidecount} is
$\Omega(2^{T-2})$ for every non-empty prefix; ordering adds
$O(\lvert\cO_k\rvert\log\lvert\cO_k\rvert)$ comparisons, and the complete
escalation runs in $2^{O(T)}\operatorname{poly}(L)$ time on rational input
of encoding length $L$. Lower-bound pruning acts only after generation and
cannot reduce this stage. The count is available in closed form before
any generation; version 2.2.0 discloses it and refuses escalations whose
disjunction exceeds a caller-set cap.
\end{corollary}

\begin{remark}[The bound diagnoses the algorithm, not the problem]\label{rem:algnotproblem}
A full protected path has $\lvert\cO_m\rvert=2^{T-1}-1$, yet its exact
radius is polynomial because the frozen certificate is exact there
(\cref{thm:lower}); the fixed-competitor programme \eqref{eq:fixedlp} is
polynomial for any single outside path. Exponential enumeration therefore
says nothing about the complexity class of \WWR{}; by
\cref{cor:arcreduction} below, the unresolved classification is confined
to the one-protected-arc core.
\end{remark}

\subsection{Local-tie decomposition of the strong radius}\label{sec:decomposition}

Fix the protected prefix $\pi_k=(v_0,\ldots,v_k)$ of the nominal path.
For revised demand $d$, let $V_i(d)$ be the optimal suffix value from
node $i$ (so $V_{T+1}=0$), let
\[
P_r(d)=\sum_{t<r}\bar c_{v_tv_{t+1}}(d)
\]
be the cost of the prefix through $v_r$, and define at each protected arc
\[
E_r(d)=\bar c_{v_rv_{r+1}}(d)+V_{v_{r+1}}(d),
\qquad
O_r(d)=\min_{\substack{j>v_r,\ j\ne v_{r+1}}}
\bigl\{\bar c_{v_rj}(d)+V_j(d)\bigr\},
\]
with $\min\varnothing=+\infty$ (the case $v_r=T$, $v_{r+1}=T+1$).
$E_r$ is the value of continuing along the protected Bellman arc and then
optimally; $O_r$ is the best value of leaving through any alternative
arc. The protected arc at $v_r$ is \emph{compulsory} when $O_r>E_r$;
the local tie $O_r\le E_r$ says it has ceased to be so. Write also
$W_r(d)$ for the best value from $v_r$ among continuations that follow
the remaining protected arcs $v_r\to\cdots\to v_k$ and then anything, so
$W_k=V_{v_k}$, $W_r=\bar c_{v_rv_{r+1}}+W_{r+1}$, and
$A_k(d)=P_r(d)+W_r(d)$ for every $r\le k$.

\begin{lemma}[First-arc split]\label{lem:firstarc}
$V_{v_r}(d)=\min\{E_r(d),O_r(d)\}$ for every $r<k$, and
$E_r\le W_r$ pointwise.
\end{lemma}

\begin{proof}
The Bellman recursion at $v_r$ splits its outgoing arcs into the
protected arc and the rest, giving the first identity. The second holds
because $V_{v_{r+1}}\le W_{r+1}$: the protected continuation is one
feasible suffix.
\end{proof}

\begin{theorem}[Local-tie decomposition]\label{thm:localtie}
For every admissible demand $d\ge\ellv$,
\[
B_k(d)\le A_k(d)
\quad\Longleftrightarrow\quad
\exists\,r\in\{0,\ldots,k-1\}:\ O_r(d)\le E_r(d).
\]
All statements hold with weak inequalities, for zero demands, zero setup
costs, and a prefix ending at the terminal node; no strictness or
nondegeneracy is used.
\end{theorem}

\begin{proof}
($\Leftarrow$) Suppose $O_r\le E_r$ at some $r<k$ and $O_r<\infty$. The
path that follows the prefix to $v_r$, takes a minimising alternative arc
$(v_r,j)$, $j\ne v_{r+1}$, and continues with an optimal suffix from $j$
is a complete path; its position $r+1$ differs from $v_{r+1}$, so it lies
in $\cO_k$. Hence
\[
B_k(d)\le P_r(d)+O_r(d)\le P_r(d)+E_r(d)\le P_r(d)+W_r(d)=A_k(d),
\]
using \cref{lem:firstarc} for the middle inequality. If $O_r=+\infty$ the
hypothesis forces $E_r=+\infty$, impossible in a finite graph.

($\Rightarrow$) By contraposition assume $O_r>E_r$ for every $r<k$. Then
$V_{v_r}=E_r$ by \cref{lem:firstarc}, and backward induction from
$V_{v_k}=W_k$ gives $V_{v_r}=W_r$ for all $r\le k$: indeed if
$V_{v_{r+1}}=W_{r+1}$ then
$V_{v_r}=E_r=\bar c_{v_rv_{r+1}}+V_{v_{r+1}}=W_r$. Every outside path $Q$
has a first divergence at some protected node $v_r$ with $r<k$: it
follows $v_0,\ldots,v_r$ and then takes an arc $(v_r,j)$ with
$j\ne v_{r+1}$. Its cost obeys
\[
C_Q(d)\ \ge\ P_r(d)+\bar c_{v_rj}(d)+V_j(d)\ \ge\ P_r(d)+O_r(d)
\ >\ P_r(d)+E_r(d)=P_r(d)+V_{v_r}(d)=P_r(d)+W_r(d)=A_k(d).
\]
Minimising over $Q\in\cO_k$ gives $B_k(d)>A_k(d)$.
\end{proof}

\begin{corollary}[Prefix-to-arc radius decomposition]\label{cor:arcreduction}
Define the one-arc radius
\[
\rho_r
=\inf\bigl\{\winf{d-\dhat}:d\ge\ellv,\ O_r(d)\le E_r(d)\bigr\}.
\]
Then
\[
\rho_{k,w}(\dhat)=\min_{r<k}\rho_r,
\]
every finite value is attained, and $\rho_r$ depends only on the data of
periods $v_r,\ldots,T$: it equals the strong radius, with one protected
arc, of the suffix sub-instance whose nominal path starts with
$(v_r,v_{r+1})$, with weights, floors and box coordinates restricted
accordingly. Consequently \WWR{} with an arbitrary prefix reduces in
polynomial time to at most $k$ instances with a single protected arc, and
since one arc is itself a special case, the two formulations are
polynomially equivalent. The monotonicity
$\rho_{k+1,w}\le\rho_{k,w}$ of \cref{prop:geometry} is recovered as
minimisation over a larger arc set.
\end{corollary}

\begin{proof}
By \cref{thm:localtie} the destabilising set
$\{d\ge\ellv:B_k\le A_k\}$ is the union over $r<k$ of the local tie sets
$\{d\ge\ellv:O_r\le E_r\}$, and the distance to a finite union is the
minimum of the distances. Each local set is a finite union of polyhedra
(one polyhedron per minimising alternative arc and suffix path, or the
compact extended description with potentials as in \eqref{eq:fixedlp}),
hence closed, so finite distances are attained. $E_r$ and $O_r$ involve
only arcs with tails at or after $v_r$, whose costs depend on
$d_{v_r},\ldots,d_T$ alone; coordinates before $v_r$ are free and best
left nominal. Interpreting the sub-problem on periods $v_r,\ldots,T$ with
the shifted nominal path makes $O_r\le E_r$ exactly the event
$B_1\le A_1$ of that sub-instance.
\end{proof}

\begin{example}[An interior link can fail first]\label{ex:interiorarc}
Exact decimal data, $T=5$: $K=(15.0,\,44.3,\,18.5,\,31.3,\,29.5)$,
$q=(0,\,-1.6,\,-3.4,\,-5.5,\,-7.2)$,
$\dhat=(86.8,\,67.7,\,43.1,\,23.4,\,97.9)$,
$\ellv=(15.6,\,10.9,\,12.9,\,3.5,\,22.6)$,
$w=(1.2,\,1.8,\,1.8,\,1.1,\,1.0)$. The unique nominal optimum sets up in
every period, $P^\star=(1,2,3,4,5,6)$; protect $k=4$ arcs. The exact
one-arc radii are
\[
\rho_0=\tfrac{28809}{400}=72.0225,
\qquad
\rho_1=\infty,
\qquad
\rho_2=\tfrac{4906}{525}\approx9.3448,
\qquad
\rho_3=\infty,
\]
so $\rho_{4,w}=\tfrac{4906}{525}$, attained at the \emph{third} protected
arc: the certified enumeration over all $2^{4}-1$ outside paths returns
the same rational. Local action stability is thus genuinely
non-monotone along the prefix --- protecting fewer arcs here changes
nothing until the third link is included, and the first link is over
seven times more robust than the prefix it heads.
\end{example}

\begin{remark}[The open core, restated]\label{rem:opencore}
By \cref{cor:arcreduction}, the unresolved complexity classification of
\cref{sec:scope} is exactly this: can a rational demand vector in the
weighted floor-truncated box make one specified Wagner--Whitin outgoing
arc cease to be uniquely optimal, under correlated costs
$K_i+q_i(D_j-D_i)$, ordered slopes and the induced Monge structure?
Generic partial inverse and anti-inverse hardness
\parencite{Gassner2009,LeyMerkert2025} modifies arc weights
independently and does not settle this restriction in either direction.
\end{remark}

\subsection{A compact production-balance exact model}\label{sec:compact}

The fixed-radius model of \cref{thm:milp} pays $O(T^3)$ arc--period
products because path indicators multiply demand. Reformulating over the
original reduced lot-sizing quantities removes every product. Take
variables $y_i\in\{0,1\}$ (setup), $x_i\ge0$ (production),
$I_i\ge0$ (end-of-period inventory) for $i=1,\ldots,T$, demand $d$, and
suffix potentials $u_j$ for $j=s,\ldots,T+1$ as in
\eqref{eq:dualpotential}, and impose
\begin{align}
I_i&=I_{i-1}+x_i-d_i,\qquad I_0=I_T=0,\label{eq:balance}\\
x_i&\le M y_i,\qquad M=\textstyle\sum_t U_t,\label{eq:vub}\\
y_1&=1,\label{eq:sourcesetup}\\
\sum_{\substack{i<s,\ i\notin\pi_k}} y_i
\;+\;
\sum_{\substack{v\in\pi_k\setminus\{1\},\ v\le T}}(1-y_v)
&\;\ge\;1,\label{eq:deviation}
\end{align}
with the demand box and floors of the mode in use. The plan cost is
$\sum_iK_iy_i+\sum_iq_ix_i$; the fixed-radius decision minimises plan
cost minus $C_{\pi_k}(d)+u_{T+1}$, and the minimum-radius variant instead
couples plan cost $\le C_{\pi_k}(d)+u_{T+1}$, adds
$w_t\lvert d_t-\dhat_t\rvert\le r$ row pairs, and minimises $r$ under an
explicit cap. Constraint \eqref{eq:sourcesetup} reflects that every
complete path pays the period-1 setup; \eqref{eq:deviation} states that
the open-setup pattern differs from the protected one at or before $s$.

\begin{lemma}[Conversion]\label{lem:conversion}
Let $(y,x,I,d)$ satisfy \eqref{eq:balance}--\eqref{eq:sourcesetup} with
$d\ge0$. Reassign every unit of period-$t$ demand to the \emph{latest}
open setup at or before $t$. The result is the zero-inventory plan of the
complete path whose nodes are exactly $\{i:y_i=1\}\cup\{T+1\}$, its cost
is at most $\sum_iK_iy_i+\sum_iq_ix_i$, and $y$ is unchanged.
\end{lemma}

\begin{proof}
By \eqref{eq:balance} and $I\ge0$, demand in period $t$ is covered by
production in open periods $i\le t$; \eqref{eq:sourcesetup} guarantees an
open setup exists at or before every period. Moving one unit of
period-$t$ demand from an open setup $i$ to the latest open setup
$i'\in[i,t]$ changes its variable cost from $q_i$ to $q_{i'}\le q_i$ by
the ordered slopes \eqref{eq:orderedq}, so total variable cost does not
increase; setup cost is unchanged because $y$ is untouched. After
reassignment each period is served entirely by its latest open
predecessor, which is precisely the zero-inventory plan of the stated
path; an open setup serving nothing remains a node whose cycle carries
zero quantity at identical cost $K_i+q_i\cdot0$. Zero demands need no
treatment: their assignment is empty.
\end{proof}

\begin{theorem}[Exactness of the compact model]\label{thm:compact}
Fix admissible $d\ge\ellv$. The minimum of
$\sum_iK_iy_i+\sum_iq_ix_i$ over
\eqref{eq:balance}--\eqref{eq:deviation} equals $B_k(d)$. Consequently,
with the potentials of \eqref{eq:dualpotential}: the fixed-radius
decision model is an exact formulation of \WWR{} at radius $R$ with
$T$ binary and $O(T)$ continuous variables and $O(T^2)$ constraints and
no bilinear terms; and the minimum-radius model computes
$\min\{\rho_{k,w},\text{cap}\}$-feasibility exactly, its optimal value
equalling $\rho_{k,w}(\dhat)$ whenever $\rho_{k,w}\le\text{cap}$.
\end{theorem}

\begin{proof}
($\ge$) Given a feasible plan, \cref{lem:conversion} produces a complete
path of no greater cost with the same $y$-pattern. Retention of $\pi_k$
by that path would mean its node set contains every protected node up to
$s$ as consecutive initial nodes and no others below $s$; equivalently
$y_v=1$ for all $v\in\pi_k$, $v\le T$, and $y_i=0$ for every internal
$i<s$ off the prefix --- exactly the pattern excluded by
\eqref{eq:deviation}. Hence the induced path lies in $\cO_k$ and the plan
cost is at least $B_k(d)$.
($\le$) Any $Q\in\cO_k$ defines the feasible plan that produces each
cycle's demand at its setup node: its $y$-pattern violates prefix
retention at its first divergence, satisfying \eqref{eq:deviation} ---
an early divergence to $j<v_{r+1}$ opens a gap setup, a late one to
$j>v_{r+1}$ closes the protected setup $v_{r+1}$ (with
$v_{r+1}\le T$, since a divergence at $v_{r+1}=T+1$ is impossible) ---
and its cost is $C_Q(d)$. The potential rows make
$u_{T+1}\le V_s(d)$ with equality achievable, exactly as in
\cref{thm:fixedlp}, so comparing plan cost with $C_{\pi_k}(d)+u_{T+1}$
decides $B_k(d)\le A_k(d)$; the radius rows are linear in $(d,r)$.
Attainment transfers from \cref{prop:geometry}.
\end{proof}

Solver outputs remain floating point: as everywhere in this release, a
finite compact-model radius or witness enters the certified record only
after the exact layer re-verifies it (the binding-comparator tie of the
disjunct certifier), and an infeasibility below the cap is solver-level
evidence, never an infinity certificate. \Cref{sec:audit} reports a
corpus equivalence gate --- the compact model must reproduce every
resolved exact $T\le18$ radius, witness and infinite-radius result of the
existing audits before any scaling claim --- and a preregistered
benchmark against the released escalation.

