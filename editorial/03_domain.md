# Dynamic-lot-sizing domain report

**Reviewed object:** initial sealed-review SHA-256 `d34945f2282dd9f0c4c9a999059549ae2dd3fceaae6e8a9dd615af8f3cbb7ef1`.

The source-model issue is repaired. `forced_source_graph` and `classical_active_horizon` are distinct contracts; the classical interpretation requires a positive period-one demand floor and positive later setup costs. The 101-versus-1 leading-zero case is retained as a negative control. Setup epochs, productive setups, empty nodes and cycle boundaries are distinguished, and the operational ceiling correctly protects structure under quantity recourse rather than fixed order quantities.

**Decision:** ACCEPT. Critical 0; Major 0; Minor 0. Independent operations-research specialist review remains a later assurance gate.
