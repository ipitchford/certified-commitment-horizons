"""Expanded prefix-deviation DAG.

A source-to-sink path follows the selected nominal prefix until its first
divergence and then enters the ordinary physical lot-sizing DAG. The expected
k-th protected arc is omitted, so expanded paths are exactly the physical paths
that fail to retain the protected prefix.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .model import Path, WWInstance, enumerate_paths, follows_prefix, validate_complete_path

Node = tuple[str, int]


@dataclass(frozen=True)
class ExpandedArc:
    idx: int
    tail: Node
    head: Node
    physical_i: int
    physical_j: int
    kind: str


@dataclass(frozen=True)
class PrefixDeviationGraph:
    T: int
    prefix: Path
    nodes: tuple[Node, ...]
    arcs: tuple[ExpandedArc, ...]
    source: Node
    sink: Node

    @property
    def outgoing(self) -> dict[Node, tuple[ExpandedArc, ...]]:
        out: dict[Node, list[ExpandedArc]] = {node: [] for node in self.nodes}
        for arc in self.arcs:
            out[arc.tail].append(arc)
        return {node: tuple(arcs) for node, arcs in out.items()}

    @property
    def incoming(self) -> dict[Node, tuple[ExpandedArc, ...]]:
        inc: dict[Node, list[ExpandedArc]] = {node: [] for node in self.nodes}
        for arc in self.arcs:
            inc[arc.head].append(arc)
        return {node: tuple(arcs) for node, arcs in inc.items()}

    def topological_nodes(self) -> tuple[Node, ...]:
        matching = tuple(node for node in self.nodes if node[0] == "M")
        deviated = tuple(sorted((node for node in self.nodes if node[0] == "D"), key=lambda x: x[1]))
        return (*matching, *deviated)

    def has_source_sink_path(self) -> bool:
        reachable = {self.source}
        out = self.outgoing
        for node in self.topological_nodes():
            if node not in reachable:
                continue
            reachable.update(arc.head for arc in out[node])
        return self.sink in reachable

    def incidence_without_sink(self) -> tuple[np.ndarray, np.ndarray, tuple[Node, ...]]:
        """Return ``N,h`` for outflow-minus-inflow equations ``N x = h``."""
        rows = tuple(node for node in self.nodes if node != self.sink)
        row_index = {node: r for r, node in enumerate(rows)}
        N = np.zeros((len(rows), len(self.arcs)), dtype=float)
        for arc in self.arcs:
            if arc.tail in row_index:
                N[row_index[arc.tail], arc.idx] += 1.0
            if arc.head in row_index:
                N[row_index[arc.head], arc.idx] -= 1.0
        h = np.zeros(len(rows), dtype=float)
        h[row_index[self.source]] = 1.0
        return N, h, rows

    def shortest_path(
        self,
        arc_weights: Sequence[float],
        *,
        tol: float = 1e-10,
    ) -> tuple[float, tuple[int, ...]]:
        weights = np.asarray(arc_weights, dtype=float)
        if weights.shape != (len(self.arcs),):
            raise ValueError("arc_weights has the wrong length")
        if not self.has_source_sink_path():
            raise ValueError("the prefix-deviation graph contains no outside path")
        out = self.outgoing
        dist = {node: np.inf for node in self.nodes}
        chosen: dict[Node, tuple[int, ...] | None] = {node: None for node in self.nodes}
        dist[self.source] = 0.0
        chosen[self.source] = ()
        for node in self.topological_nodes():
            current = chosen[node]
            if current is None:
                continue
            for arc in out[node]:
                candidate = float(dist[node] + weights[arc.idx])
                candidate_ids = (*current, arc.idx)
                incumbent = chosen[arc.head]
                if (
                    incumbent is None
                    or candidate < dist[arc.head] - tol
                    or (abs(candidate - dist[arc.head]) <= tol and candidate_ids < incumbent)
                ):
                    dist[arc.head] = candidate
                    chosen[arc.head] = candidate_ids
        arc_ids = chosen[self.sink]
        if arc_ids is None:
            raise RuntimeError("topological shortest-path pass failed to reach the sink")
        return float(dist[self.sink]), arc_ids

    def physical_path(self, arc_indices: Sequence[int]) -> Path:
        path = [0]
        for idx in arc_indices:
            arc = self.arcs[int(idx)]
            if path[-1] != arc.physical_i:
                raise ValueError("expanded arcs do not form a coherent physical path")
            path.append(arc.physical_j)
        if path[-1] != self.T:
            raise ValueError("expanded path does not reach the terminal node")
        return tuple(path)

    def enumerate_physical_paths(self) -> set[Path]:
        if not self.has_source_sink_path():
            return set()
        result: set[Path] = set()
        out = self.outgoing

        def walk(node: Node, ids: tuple[int, ...]) -> None:
            if node == self.sink:
                result.add(self.physical_path(ids))
                return
            for arc in out[node]:
                walk(arc.head, (*ids, arc.idx))

        walk(self.source, ())
        return result


def build_prefix_deviation_graph(
    instance: WWInstance,
    nominal_path: Sequence[int],
    k: int,
) -> PrefixDeviationGraph:
    p = validate_complete_path(nominal_path, instance.T)
    m = len(p) - 1
    if not (1 <= k <= m):
        raise ValueError("k must protect between one and all nominal arcs")
    prefix = p[: k + 1]
    matching_nodes: list[Node] = [("M", r) for r in range(k)]
    deviated_nodes: list[Node] = [("D", j) for j in range(1, instance.T + 1)]
    nodes = (*matching_nodes, *deviated_nodes)
    source: Node = ("M", 0)
    sink: Node = ("D", instance.T)
    arcs: list[ExpandedArc] = []

    def add(tail: Node, head: Node, i: int, j: int, kind: str) -> None:
        arcs.append(ExpandedArc(len(arcs), tail, head, i, j, kind))

    # Match protected arcs until the first divergence. At state k-1, the
    # expected k-th arc is omitted because taking it would complete the prefix.
    for r in range(k):
        i = p[r]
        expected = p[r + 1]
        if r < k - 1:
            add(("M", r), ("M", r + 1), i, expected, "match")
        for j in range(i + 1, instance.T + 1):
            if j != expected:
                add(("M", r), ("D", j), i, j, "diverge")

    # After first divergence, use the ordinary physical DAG.
    for i in range(1, instance.T):
        for j in range(i + 1, instance.T + 1):
            add(("D", i), ("D", j), i, j, "deviated")

    return PrefixDeviationGraph(
        instance.T,
        prefix,
        tuple(nodes),
        tuple(arcs),
        source,
        sink,
    )


def verify_graph_bijection(
    instance: WWInstance,
    nominal_path: Sequence[int],
    k: int,
) -> tuple[int, int]:
    graph = build_prefix_deviation_graph(instance, nominal_path, k)
    expanded = graph.enumerate_physical_paths()
    outside = {
        path
        for path in enumerate_paths(instance.T)
        if not follows_prefix(path, graph.prefix)
    }
    if expanded != outside:
        missing = sorted(outside - expanded)[:5]
        extra = sorted(expanded - outside)[:5]
        raise AssertionError(f"graph/path bijection failed; missing={missing}, extra={extra}")
    return len(expanded), len(outside)


def verify_acyclic_nonnegative_circulation_property(graph: PrefixDeviationGraph, *, tol: float = 1e-10) -> bool:
    """Numerically verify the structural lemma used by Charnes--Cooper.

    In a finite DAG, ``N y = 0`` and ``y >= 0`` imply ``y = 0``. This helper
    checks the graph is topologically ordered and is used only as a release
    assertion; the manuscript gives the direct source-removal proof.
    """
    order = {node: r for r, node in enumerate(graph.topological_nodes())}
    return all(order[arc.tail] < order[arc.head] for arc in graph.arcs)


def outside_shortest_path(
    instance: WWInstance,
    demand: Sequence[float],
    nominal_path: Sequence[int],
    k: int,
    *,
    tol: float = 1e-10,
) -> tuple[float, Path | None]:
    """Return the best path that leaves the protected prefix.

    The computation is a shortest path on the expanded prefix-deviation DAG.
    If no outside path exists, ``(inf, None)`` is returned.
    """
    graph = build_prefix_deviation_graph(instance, nominal_path, k)
    if not graph.has_source_sink_path():
        return float("inf"), None
    d = np.asarray(demand, dtype=float)
    if d.shape != instance.demand.shape:
        raise ValueError("demand has the wrong shape")
    D = np.concatenate(([0.0], np.cumsum(d)))
    weights = np.asarray(
        [
            instance.K[arc.physical_i]
            + instance.q[arc.physical_i]
            * (D[arc.physical_j] - D[arc.physical_i])
            for arc in graph.arcs
        ],
        dtype=float,
    )
    value, ids = graph.shortest_path(weights, tol=tol)
    return value, graph.physical_path(ids)
