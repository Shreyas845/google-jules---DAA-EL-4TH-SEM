"""Generate a real, step-by-step ISL execution trace for the interactive Graph Viewer.

This drives the actual :class:`isl.isl_algorithm.ISLAlgorithm` on a small graph and records,
for each batch, the true state the frontend animates:

* fixed node layout (computed once, so nodes don't jump between frames)
* community membership per node (before and after the batch)
* the inserted/deleted edges of the batch
* the affected region ISL selected
* which nodes actually moved communities, and the resulting metrics

Everything returned is produced by the real algorithm — no positions, communities, or metrics
are invented. The graph is intentionally small (default ~60 nodes) so the trace is legible and
fast to compute on request.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger("isl.backend")

# Small, legible defaults for an on-screen demonstration.
DEFAULT_N = 60
DEFAULT_BATCHES = 8
DEFAULT_BATCH_SIZE = 3
DEFAULT_MU = 0.15
DEFAULT_SEED = 42


def _layout_positions(graph) -> List[Dict[str, float]]:
    """Compute a stable 2D layout once, normalized to [0, 1] x [0, 1]."""
    layout = graph.layout_fruchterman_reingold()
    coords = layout.coords
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = (max_x - min_x) or 1.0
    span_y = (max_y - min_y) or 1.0
    return [
        {"x": (c[0] - min_x) / span_x, "y": (c[1] - min_y) / span_y} for c in coords
    ]


def _affected_layers(
    graph, updated_edges, variant, state, tau, r_max
) -> List[List[int]]:
    """Reconstruct the affected set as ordered hop-layers, mirroring how ISL builds it.

    Returns a list of node-id lists, one per expansion layer:

    * layer 0 — the *seed* endpoints of the changed edges (S0),
    * layer 1 — the 1-hop neighborhood added around the seeds (S1 \\ S0),
    * layers 2.. — for the adaptive variant, each additional hop the algorithm chose to
      expand because a boundary node still showed a Significance gain above ``tau``.

    The union of all layers equals the affected set the algorithm actually optimizes over, so
    this is a faithful decomposition — it re-uses the exact ``affected_set`` primitives rather
    than inventing a separate notion of "radius".
    """
    from isl.affected_set import get_boundary_nodes, expand_one_hop
    from isl.delta_s import scan_node_gains

    if not updated_edges:
        return []

    seeds = set()
    for u, v in updated_edges:
        seeds.add(u)
        seeds.add(v)

    layers: List[List[int]] = [sorted(int(x) for x in seeds)]

    # Layer 1: the immediate 1-hop ring (matches build_affected_set_1hop).
    one_hop = set(seeds)
    for u in seeds:
        one_hop.update(graph.neighbors(u))
    layers.append(sorted(int(x) for x in (one_hop - seeds)))
    current = one_hop

    # Layers 2..: only the adaptive variant expands further, and only while a boundary node
    # still improves Significance — exactly the loop in build_affected_set_adaptive.
    if variant == "isl_adaptive":
        for _hop in range(1, r_max):
            boundary = get_boundary_nodes(current, graph)
            if not boundary:
                break
            max_boundary_gain = -float("inf")
            for v in boundary:
                gains = scan_node_gains(v, state, graph, current)
                if gains:
                    max_boundary_gain = max(max_boundary_gain, max(gains.values()))
            if max_boundary_gain > tau:
                expanded = expand_one_hop(current, graph)
                layers.append(sorted(int(x) for x in (expanded - current)))
                current = expanded
            else:
                break

    return layers


def generate_trace(
    n: int = DEFAULT_N,
    num_batches: int = DEFAULT_BATCHES,
    batch_size: int = DEFAULT_BATCH_SIZE,
    mu: float = DEFAULT_MU,
    seed: int = DEFAULT_SEED,
    variant: str = "isl_1hop",
) -> Dict[str, Any]:
    """Run ISL step by step and return a JSON-serializable trace.

    Returns a dict with ``meta``, ``nodes`` (id + fixed position), and ``frames`` — one frame
    per batch describing the update, the affected set, moved nodes, communities, and metrics.
    """
    import numpy as np

    from isl.benchmark import BenchmarkFramework
    from isl.isl_algorithm import ISLAlgorithm
    from isl.affected_set import build_affected_set_1hop, build_affected_set_adaptive

    # Clamp to safe, legible bounds.
    n = int(max(20, min(n, 150)))
    num_batches = int(max(1, min(num_batches, 25)))
    batch_size = int(max(1, min(batch_size, 10)))

    bench = BenchmarkFramework()
    dataset = {
        "type": "lfr",
        "n": n,
        "mu": mu,
        "min_community": max(5, n // 12),
        "max_community": max(10, n // 5),
        "average_degree": 6,
    }
    graph, ground_truth = bench.generate_lfr(dataset, seed)
    n = graph.vcount()

    initial_sigma = bench.generate_initial_partition(graph, seed)
    stream = bench.generate_update_stream(
        graph, initial_sigma, "random_uniform", batch_size, num_batches, seed
    )

    positions = _layout_positions(graph)
    nodes = [{"id": i, "x": positions[i]["x"], "y": positions[i]["y"]} for i in range(n)]

    config = {"params": {"K": 50, "delta_dwell": 2, "tau_min": 1e-6,
                         "max_iter": 50, "num_orderings": 3, "R_max": 3}}
    algo = ISLAlgorithm(config, variant)
    algo.initialize(graph.copy(), initial_sigma)

    def edges_of(g) -> List[List[int]]:
        return [[e.source, e.target] for e in g.es]

    frames: List[Dict[str, Any]] = []

    # Frame 0: the initial state, before any update.
    frames.append(
        {
            "batch_idx": 0,
            "stage": "initial",
            "edges": edges_of(algo.graph),
            "communities": algo.get_current_partition().tolist(),
            "added": [],
            "deleted": [],
            "affected": [],
            "affected_layers": [],
            "seeds": [],
            "moved": [],
            "metrics": {
                "significance": float(algo.get_current_surprise()),
                "community_count": int(len(set(algo.get_current_partition().tolist()))),
                "nodes_moved": 0,
                "affected_size": 0,
                "time_ms": 0.0,
            },
        }
    )

    tau = config["params"]["tau_min"]
    r_max = config["params"]["R_max"]

    for batch in stream:
        add = [tuple(e) for e in batch["add"]]
        dele = [tuple(e) for e in batch["del"]]
        sigma_before = algo.get_current_partition().copy()

        # Recompute the affected set the same way ISL will, so the frame highlights the
        # region the algorithm actually optimizes over.
        updated_edges = add + dele
        # ISL applies the batch edges and selects its affected region inside process_batch.
        # We run it, then reconstruct the same affected set (and its hop-layers) on the now
        # post-update graph, using the very same affected_set primitives the algorithm uses —
        # so the region we highlight is the region ISL optimized over, not an invented one.
        metrics = algo.process_batch(add, dele, batch["batch_idx"], ground_truth)
        sigma_after = algo.get_current_partition()

        if not updated_edges:
            affected = set()
        elif variant == "isl_adaptive":
            affected = build_affected_set_adaptive(
                algo.graph, updated_edges, algo.state, tau, r_max
            )
        else:
            affected = build_affected_set_1hop(algo.graph, updated_edges)

        # Ordered hop-layers (seed / 1-hop / adaptive expansions) for the radius visualization.
        layers = _affected_layers(
            algo.graph, updated_edges, variant, algo.state, tau, r_max
        )
        seeds = layers[0] if layers else []

        moved = [i for i in range(len(sigma_after)) if sigma_before[i] != sigma_after[i]]

        frames.append(
            {
                "batch_idx": int(batch["batch_idx"]),
                "stage": "updated",
                "edges": edges_of(algo.graph),
                "communities": sigma_after.tolist(),
                "communities_before": sigma_before.tolist(),
                "added": [list(e) for e in add],
                "deleted": [list(e) for e in dele],
                "affected": sorted(int(x) for x in affected),
                "affected_layers": layers,
                "seeds": seeds,
                "moved": [int(x) for x in moved],
                "metrics": {
                    "significance": float(metrics.get("S", 0.0)),
                    "community_count": int(metrics.get("community_count", 0)),
                    "nodes_moved": int(len(moved)),
                    "affected_size": int(metrics.get("affected_set_size", len(affected))),
                    "time_ms": float(metrics.get("time_ms", 0.0)),
                    "modularity": float(metrics.get("Q", 0.0)),
                    "churn_rate": float(metrics.get("churn_rate", 0.0)),
                    "periodic_fired": bool(metrics.get("periodic_trigger_fired", False)),
                },
            }
        )

    return {
        "meta": {
            "n": n,
            "num_batches": num_batches,
            "batch_size": batch_size,
            "mu": mu,
            "seed": seed,
            "variant": variant,
        },
        "nodes": nodes,
        "frames": frames,
    }
