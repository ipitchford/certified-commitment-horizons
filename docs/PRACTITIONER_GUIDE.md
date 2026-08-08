# Practitioner guide: certified commitment horizons for replenishment planning

**Audience:** supply and production planners, S&OP leads, and the engineers who
maintain their planning systems.
**Version:** 2.1.2 (8 August 2026).

## The problem this tool addresses

Every planning cycle, the forecast moves and the optimiser reshuffles the
near-term schedule. The standard defence is a **frozen fence**: commit the next
N periods regardless. Fences are calendar conventions — they answer "how far
ahead do we freeze?" with the same N for a stable item and a volatile one.
The result is the familiar pair of failure modes: nervousness when the fence is
too short, and stale commitments (dead stock, expediting, supplier churn) when
it is too long.

This tool replaces the calendar convention with an **instance-specific,
certified question**:

> How far would the demand forecast have to move — in a weighted worst-case
> sense you configure — before re-optimising could change any of the first
> *k* replenishment cycles you are about to commit?

The answer is a **radius** in forecast space, with a machine-checked
certificate. If your plausible next forecast revision is strictly smaller than
the certified radius, committing the first *k* cycles is provably safe *within
the stated model*: no admissible revision inside that radius can make any
alternative schedule optimal that changes those cycles.

## What "certified" means here — and what it does not

- **Certified means exact arithmetic plus a checkable witness.** Every
  certified number is computed in exact rational arithmetic (no tolerances) and
  every decision record carries evidence — an explicit destabilising forecast
  when one exists — that `scripts/check_certificate.py` re-verifies without
  trusting the main package.
- **Certified-safe protects schedule *structure*, not quantities.** The claim
  is that the *setup epochs and cycle boundaries* of the first *k* cycles stay
  optimal. Order quantities within retained cycles are assumed adjustable
  (uncapacitated recourse). If your contracts fix quantities, the guarantee is
  weaker than your commitment.
- **The model is single-item, uncapacitated Wagner–Whitin.** Capacity limits,
  minimum order quantities, joint setups across items, perishability and
  service-level constraints are outside the certificate. Treat the radius as a
  lower-bound sanity gate for such items, not a proof.
- **Probability enters only through your forecast-revision history**, via an
  optional calibration layer, and only as a one-step marginal statement. The
  tool never claims coverage for realised demand or for repeated use of the
  same threshold across many decisions without explicit error budgeting.

## Mapping your data

The input is a JSON file (see `docs/input_schema.md`):

| Field | Planning meaning | How to set it |
|---|---|---|
| `demand` | Current forecast per period (day/week/month buckets) | Straight from your demand plan. Use numeric strings (`"41.7"`) if you care about exact decimal semantics. |
| `K` | Setup / ordering cost per period | Changeover cost, PO processing cost, or fixed freight per order. |
| `q` | Reduced unit cost: unit cost minus cumulative holding | Computed as `p_i − H_i` (the paper, Section 2). For stationary unit cost and holding rate h, `q_i = p − (i−1)h`. Must be non-increasing — this is exactly the Wagner–Whitin "no speculative motive" condition. |
| `floor` | Lowest credible demand per period | Contracted baseline demand, or zero. The certificate knows demand cannot fall below it. |
| `weights` | How much a unit of forecast movement in period t "counts" | Set `w_t = 1/σ_t` where σ_t is your typical revision size for that horizon — then the radius is measured in "typical revisions". Near-term periods usually get larger weights (they move less). |

**Choosing k.** Run `certify` for each k you might commit (the radius is
non-increasing in k). Typical use: k = 1 or 2 — the cycles you must release to
purchasing or the shop floor this cycle.

## The decision workflow

```bash
wwprefix certify plan.json --k 2 --proposed-radius "0.8"
```

`--proposed-radius` is the revision magnitude you want protection against —
e.g. your calibrated 80th-percentile revision, or a managerially chosen
stress size. The record returns one of three certified classifications:

1. **`certified_no_destabilisation`** — commit the k cycles. No admissible
   forecast within the proposed radius can change them.
2. **`certified_destabilising_witness_exists`** — do not treat the commitment
   as robust: the record contains an explicit forecast, within your proposed
   radius, under which a different schedule is optimal. Look at the witness —
   it tells you *which* alternative structure wins and *which periods* move.
3. **`unresolved_requires_exact_escalation`** — the polynomial certificate
   could not close the gap. Either escalate (`--exact`, small horizons; or
   `decide --radius R` for a solver-level MILP probe), shorten k, or commit
   on managerial judgement with the gap documented.

Never recode unresolved as safe. That rule is the whole point of the tool.

### Suggested cadence integration

- **Weekly/monthly S&OP or MRP run:** after the optimiser produces the new
  plan, run `certify` on the cycles due for release. Attach the decision
  record (JSON) to the release documentation. Run the producer-side checker in
  CI: `python scripts/check_certificate.py decision.json plan.json`.
- **Certified runtimes** (pure Python, one core): seconds up to ~100 periods;
  about 2–4 minutes at 365 daily buckets. This fits batch planning windows.
  Weekly buckets (T ≤ 52) are effectively instant.
- **Calibration (optional):** maintain a history of forecast revisions at the
  same alignment (same product class, same horizon, same information lag).
  The split-conformal threshold from that history is a defensible way to set
  `--proposed-radius`, with a stated one-step, marginal guarantee — see the
  paper, Section 11, for exactly what that does and does not promise.

### Reading the record

- `certified_bracket.lower_radius` — the certified safe radius (exact rational
  and float rendering).
- `certified_bracket.upper_witness` — when present, a concrete destabilising
  forecast and the alternative schedule it activates. This is operationally
  valuable even when you commit: it names the scenario that would have changed
  your plan.
- `infinity_status` — some prefixes can *never* be destabilised (e.g. no
  admissible demand path makes an alternative structure competitive); the
  record proves it rather than asserting it.
- `float_search` — diagnostics only. Nothing in it is certified; it exists so
  engineers can compare the fast estimates against the certified values.

## What impact to expect — honestly

In the paper's illustrative reconstruction (real demand, reconstructed
forecasts, stylised costs), certificate-gated commitment achieved zero
structural regret while fixed 2–4 period fences accrued regret through forced
stale structure. That is an interface demonstration, not a field trial: the
honest expected benefits in practice are

1. **fewer arbitrary frozen-fence arguments** — the fence length becomes an
   auditable, item-specific computation instead of a policy constant;
2. **an evidence trail** — every commitment ships with a certificate or an
   explicit unresolved flag, which procurement and audit can replay;
3. **targeted stability** — nervous items get short certified horizons,
   stable items get long ones, from the same rule;
4. **a named risk scenario** — the destabilising witness, when it exists, is
   a concrete forecast to discuss in S&OP rather than an abstract worry.

A field validation — live vintages, real costs, capacity, service outcomes —
has not been done. If you run one, the authors' request is simple: preserve
the decision records and the checker outputs, and compare against your
incumbent fence policy on cost *and* on plan-change counts.

## Failure modes to respect

- **Disordered slopes** (`q` increasing somewhere): the model's condition is
  violated; the tool refuses rather than guessing. Usually means speculative
  cost structure (buying early is genuinely worse) — the WW model does not fit.
- **Wrong weights** make the radius meaningless in either direction. Calibrate
  them from revision history; revisit when the forecast process changes.
- **Capacity-constrained items:** a certified-safe structure can still be
  infeasible against capacity. Gate on the certificate *and* your capacity
  check.
- **Multi-item joint setups:** the certificate is per item; joint-setup
  interactions can destabilise a prefix the single-item model certifies.
