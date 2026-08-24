# Input and output schema

## Instance object

A JSON input may be either the instance object itself or an object with an `instance` field and an optional `nominal_path`.

Required arrays, all of equal length `T`:

| Field | Type | Constraint | Meaning |
|---|---|---|---|
| `K` | numbers or numeric strings | `K_i >= 0` | setup cost at period `i` |
| `q` | numbers or numeric strings | non-increasing | reduced unit-cost slope |
| `demand` | numbers or numeric strings | `demand_i >= floor_i` | nominal forecast |
| `floor` | numbers or numeric strings | `floor_i >= 0` | declared coordinate lower bound |
| `weights` | numbers or numeric strings | `weights_i > 0` | weighted `L∞` metric |

Optional fields:

| Field | Allowed values | Default | Effect |
|---|---|---|---|
| `semantic_mode` | `forced_source_graph`, `classical_active_horizon` | `forced_source_graph` | selects the graph-only or classical interpretation contract |
| `nominal_path` | strictly increasing one-based node list beginning at 1 and ending at `T+1` | exact shortest path selected deterministically | must be exactly optimal |

The algorithm does not infer `floor`. Its provenance must state whether each
lower bound represents empirical/physical support, a contractual or planning
minimum, or a deliberately conservative truncation used to protect the
calculation. Those interpretations have the same mathematical inequality but
are not operationally interchangeable. In particular, the strictly positive
period-1 floor required by `classical_active_horizon` must be warranted for
every revision to which the classical interpretation is applied.

## Semantic modes

### `forced_source_graph`

Every complete path begins at period 1. A period-1 setup is therefore part of the graph definition even when first-period demand is zero. Paths that differ only by an empty zero-cost setup node remain distinct graph decisions.

This is the broad mathematical domain of the graph theorems. It must not be silently presented as the unconstrained classical lot-sizing model.

### `classical_active_horizon`

The parser requires:

```text
floor[0] > 0
K[i] > 0 for every i = 1, ..., T-1
```

With zero initial inventory, no backlogging and ordered reduced slopes, these conditions make the forced source productive under every admissible revision and exclude empty later setups from every optimum. The manuscript’s semantic-bridge theorem then transfers graph setup-prefix conclusions to ordinary uncapacitated Wagner–Whitin setup schedules.

The excluded leading-zero example is retained as `examples/leading_zero_semantic_counterexample.json`:

```text
K=(100,1), q=(1,0), demand=(0,1), floor=(0,0)
graph optimum = 101
ordinary physical optimum = 1
```

## Exact numeric parsing

Numeric strings are parsed as exact rationals:

```json
{"K": ["0.1", "3/2"]}
```

Plain JSON numbers are first parsed by the JSON implementation and then converted losslessly from their binary values. Use strings where exact decimal semantics matter.

## Public paths

Public JSON paths use one-based nodes. For a three-period horizon, `[1, 2, 4]` means the internal zero-based tuple `(0, 1, 3)`.

## Certified output

Every `certified_*` value is represented as:

```json
{"float": 1.5, "exact": "3/2"}
```

The rational string is authoritative. Proven infinity uses `"exact": "inf"` together with a specific infinity status.

Each command output contains:

- `schema_version: "3.0"`;
- `model_semantics`, including whether the classical bridge is active;
- exact verification of nominal optimality and the common nominal prefix;
- a certified lower/upper bracket;
- exact witness records when available;
- optional diagnostic `float_search`; and
- optional exact escalation or fixed-radius triage.

## Status vocabulary

| Status | Meaning |
|---|---|
| `exact_certified` | one exact rational strong radius is proved by the implemented certificate logic |
| `enumeration_completed_with_certified_interval` | candidate processing completed but exact closure failed; lower and upper witnesses remain valid |
| `certified_interval` | a bounded exact interval is valid without point closure |
| `refused_by_candidate_guard` | predeclared candidate cap exceeded before generation |
| `enumeration_stopped_path_limit` | a caller-supplied path cap stopped the search |
| `exact_infinite_no_outside_path` | no path can leave the protected class |
| `exact_infinite_saturation` | a positive residual gap remains after all beneficial demand coordinates saturate |
| solver-level status | a floating mixed-integer result has not met the exact certification conditions |

Enumeration completion and point certification are separate concepts. An independently found feasible upper witness need not be monotone across prefix depths; only the true exactly certified radii obey the monotonicity theorem.
