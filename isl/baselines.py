import igraph as ig
import leidenalg
import numpy as np
import time

def partition_to_sigma(membership: list, n: int) -> np.ndarray:
    """
    Convert leidenalg membership list to numpy sigma array.
    Renumber communities to consecutive integers starting at 0.
    """
    unique_labels = list(dict.fromkeys(membership)) # preserve order or just unique
    label_map = {old: new for new, old in enumerate(unique_labels)}
    sigma = np.array([label_map[c] for c in membership], dtype=int)
    return sigma

def sigma_to_membership(sigma: np.ndarray) -> list:
    """
    Convert sigma array to leidenalg membership format.
    """
    return sigma.tolist()

def run_static_significance(graph: ig.Graph, seed: int) -> tuple:
    """
    Run leidenalg.find_partition(graph, SignificanceVertexPartition, seed=seed).
    Returns (sigma_array, wall_clock_time_ms).
    """
    t0 = time.perf_counter()
    np.random.seed(seed)
    p = leidenalg.find_partition(graph, leidenalg.SignificanceVertexPartition, seed=seed)
    t1 = time.perf_counter()
    return partition_to_sigma(p.membership, graph.vcount()), (t1 - t0) * 1000

def run_static_leiden(graph: ig.Graph, seed: int) -> tuple:
    """
    Run leidenalg.find_partition(graph, ModularityVertexPartition, seed=seed).
    Returns (sigma_array, wall_clock_time_ms).
    """
    t0 = time.perf_counter()
    np.random.seed(seed)
    p = leidenalg.find_partition(graph, leidenalg.ModularityVertexPartition, seed=seed)
    t1 = time.perf_counter()
    return partition_to_sigma(p.membership, graph.vcount()), (t1 - t0) * 1000

def run_bfs_leiden(graph: ig.Graph, sigma: np.ndarray, affected_nodes: list, radius: int = 1, seed: int = 42) -> tuple:
    """
    Fixed-radius BFS from affected_nodes to radius hops.
    Extract subgraph of BFS expansion.
    Run static Leiden (modularity) on subgraph.
    Merge result back into full partition.
    Returns (updated_sigma, wall_clock_time_ms).
    """
    t0 = time.perf_counter()

    # 1. BFS to find subgraph nodes
    # We can use neighborhood
    if not affected_nodes:
        return sigma.copy(), (time.perf_counter() - t0) * 1000

    bfs_nodes = set()
    for v in affected_nodes:
        # Get neighborhood of radius
        neighborhood = graph.neighborhood(v, order=radius)
        bfs_nodes.update(neighborhood)

    bfs_nodes_list = sorted(list(bfs_nodes))

    # 2. Extract subgraph
    subgraph = graph.subgraph(bfs_nodes_list)

    # 3. Run Static Leiden on subgraph
    np.random.seed(seed)
    p_sub = leidenalg.find_partition(subgraph, leidenalg.ModularityVertexPartition, seed=seed)

    # 4. Merge back
    new_sigma = sigma.copy()

    # Find max label in current sigma to avoid collisions
    max_label = np.max(sigma) if len(sigma) > 0 else -1

    # The new communities in subgraph need to be mapped to non-colliding labels
    sub_membership = p_sub.membership
    unique_sub_labels = list(dict.fromkeys(sub_membership))

    label_map = {old: max_label + 1 + new for new, old in enumerate(unique_sub_labels)}

    for sub_idx, global_v in enumerate(bfs_nodes_list):
        new_sigma[global_v] = label_map[sub_membership[sub_idx]]

    # Finally, renumber all communities consecutively
    final_sigma = partition_to_sigma(new_sigma.tolist(), graph.vcount())

    t1 = time.perf_counter()
    return final_sigma, (t1 - t0) * 1000

def run_no_update(sigma: np.ndarray) -> np.ndarray:
    """
    Return sigma unchanged. Timing = 0.
    """
    return sigma
