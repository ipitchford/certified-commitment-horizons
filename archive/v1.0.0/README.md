# Certified Commitment Horizons in Dynamic Lot Sizing

This repository accompanies the research output:

> **Certified Commitment Horizons in Dynamic Lot Sizing: Prefix Stability, Inverse Shortest Paths and Calibrated Forecast Revisions**

It replaces an arbitrary frozen fence such as “commit the next 7 or 14 days” with a decision-specific certificate:

> How large must a revision to the current demand forecast become before a rationally optimal Wagner-Whitin schedule can change any of the first `k` replenishment cycles?

The canonical decision problem is `WW-Prefix-Radius-infinity`. For a selected nominal optimal path, a protected prefix and a weighted infinity-norm revision budget, it asks whether any admissible revised demand vector makes an outside path no more expensive than the best path that retains the prefix.

## What the release contains

- a manuscript PDF and LaTeX source;
- a polynomial frozen-comparator lower certificate;
- an exact fixed-competitor inverse linear programme;
- an exact disjunctive enumerator for small instances;
- an exact fixed-radius mixed-integer linear decision model;
- split-conformal calibration of historical forecast revisions;
- a deterministic rolling-horizon regret bound;
- tests, synthetic experiments, raw result tables and figures;
- a bounded literature/priority audit and a claim-evidence matrix.

## Decision semantics

The protected decisions are **setup epochs and replenishment-cycle boundaries**. They are not literal order quantities. Quantities change mechanically when demand changes, even when the same setup pattern remains optimal.

The graph model permits a non-negative coordinate-wise demand floor. A strictly positive floor is recommended when paths are interpreted literally as physical setup schedules, because zero-demand periods may otherwise require preprocessing or a convention about vacuous setups.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -r requirements-lock.txt
```

## Quick start

```bash
wwprefix certify examples/instance.json \
  --revisions examples/revisions.csv \
  --alpha 0.10 \
  --exact

wwprefix decide examples/instance.json --k 1 --radius 2.0
```

The first command returns the nominal path, one polynomial certificate for each protected prefix, optional exact small-instance radii, and a calibrated number of cycles to commit. The second solves `WW-Prefix-Radius-infinity` at one proposed radius by an exact mixed-integer formulation.

## Reproduction

```bash
make test
make figures
make paper
make verify
```

The full synthetic experiment suite is deterministic but more expensive:

```bash
make experiments
```

See `docs/reproduction.md` for the exact status of each check and `docs/data_schema.md` for input definitions.

## Verification status

- mathematical statements: producer-side proof audit plus executable tests;
- polynomial certificate: matched exhaustive path enumeration in 569 recorded cases;
- exact formulations: cross-checked on small random instances and an analytical strict-gap example;
- rolling theorem: no violation beyond `2.28e-13` in 220 recorded synthetic runs;
- external peer review: **not completed**;
- independent reproduction: **not completed**;
- formal proof assistant verification: **not completed**.

The paper states these boundaries explicitly. The unrestricted complexity classification of exact `WW-Prefix-Radius-infinity` remains open in this release.

## Licences

Code is released under the MIT Licence. The manuscript and documentation are released under Creative Commons Attribution 4.0 International (CC BY 4.0).
