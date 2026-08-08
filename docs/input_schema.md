# Input and output schema

## Input document

```json
{
  "instance": {
    "K": [0.0, 3.0, 2.0],
    "q": [2.0, 1.0, 0.0],
    "demand": [1.0, 5.0, 1.0],
    "floor": [0.5, 0.5, 0.5],
    "weights": [1.0, 1.0, 1.0]
  },
  "nominal_path": [1, 2, 4]
}
```

`instance` may also be the top-level object. `nominal_path` is optional; when omitted, the software computes a nominal optimum with a deterministic tie-break: fewer setup arcs first, then lexicographic node order; when supplied, it must be *exactly* optimal for the supplied instance or the command refuses.

**Exact numeric strings.** Every numeric entry may instead be a string, parsed as an exact decimal (`"0.999999999"`) or exact rational (`"1/3"`). Plain JSON numbers are decided at their exact IEEE-754 binary values. Users whose data are decimal and who care about ulp-scale effects should use strings; the certified layer then decides the decimal instance exactly. The radius options `--proposed-radius` and `--radius` are strings parsed the same way.

## Field contracts

| Field | Contract | Interpretation |
|---|---|---|
| `K[t]` | finite, non-negative | setup or order cost for an arc beginning in period `t+1` |
| `q[t]` | finite and non-increasing | reduced cumulative-demand slope |
| `demand[t]` | finite, at least `floor[t]` | current nominal demand forecast |
| `floor[t]` | finite, non-negative | lower admissibility bound for revised demand |
| `weights[t]` | finite, strictly positive | coordinate scale in `max_t weights[t] * abs(d[t]-demand[t])` |
| `nominal_path` | strictly increasing, starts at 1, ends at `T+1` | replenishment path in public one-based node labels |

All arrays must have the same positive length `T`. The ordered-slope condition is the implementation-level Wagner-Whitin assumption used by the polynomial certificate and rolling diameter theorem.

## Public versus internal indices

The Python algorithms use zero-based nodes `0,...,T`; JSON uses one-based nodes `1,...,T+1`. Period-array positions remain ordinary JSON positions `0,...,T-1`.

## Commands

```bash
wwprefix certify INPUT.json --k K [--exact] [--proposed-radius R]
wwprefix decide INPUT.json --k K --radius R [--time-limit SECONDS]
```

`k` counts protected path arcs, not calendar periods. A single protected arc may span several periods.

## Decision semantics

The certified triage has three states:

- `certified_no_destabilisation`: the proposed radius is strictly below the certified exact lower radius;
- `certified_destabilising_witness_exists`: an exactly verified witness destabilises within the proposed radius;
- `unresolved_requires_exact_escalation`: the certified bounds do not decide the event.

Exact routines may also return `path_limit` or another unresolved status, and the MILP escalation is labelled `solver_level_only_not_exactly_certified`. Such outputs are evidence gaps, not negative decisions.

## Certified values, infinity and numerical safety

Certified values are serialized as `{"float": ..., "exact": "p/q"}` pairs; the exact string is authoritative. Proven infinity appears as the string `"inf"` in the exact slot together with an `infinity_status` of `proven_infinite_no_outside_path` or `proven_infinite_saturation` (the latter carries a certified positive `residual_gap`). Floating-point search results appear only under `float_search` and are diagnostic. There is no tolerance-based `safe_radius` any more: the certified lower radius *is* the operational lower certificate, computed in exact rational arithmetic. Any record can be re-verified with `python scripts/check_certificate.py RECORD.json INSTANCE.json`.
