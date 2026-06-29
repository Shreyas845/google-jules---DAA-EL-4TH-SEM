import igraph as ig
import leidenalg
import numpy as np

def compute_delta_s(
    subgraph: ig.Graph,
    subgraph_sigma: np.ndarray,
    v_subgraph_idx: int,
    c_target: int
) -> float:
    c_old = subgraph_sigma[v_subgraph_idx]
    if c_old == c_target:
        return 0.0

    # Helper to remap to 0..K-1 for leidenalg
    def eval_signif(sigma_arr):
        unique_labels = np.unique(sigma_arr)
        label_map = {old: new for new, old in enumerate(unique_labels)}
        mapped = [label_map[c] for c in sigma_arr]
        part = leidenalg.SignificanceVertexPartition(subgraph, initial_membership=mapped)
        return part.quality()

    sig_before = eval_signif(subgraph_sigma)

    # Move node
    subgraph_sigma[v_subgraph_idx] = c_target

    sig_after = eval_signif(subgraph_sigma)

    # Revert move
    subgraph_sigma[v_subgraph_idx] = c_old

    return sig_after - sig_before

def scan_node_gains(
    v: int,
    state,
    graph: ig.Graph,
    affected_set: set = None
) -> dict:
    """
    For node v, compute ΔSignificance for moving v to each neighboring community,
    plus an option to move to a new singleton community.

    Returns {community_label: delta_signif_value} for all communities ≠ sigma[v].

    Performance note:
    Extracts the subgraph induced by `affected_set` (if provided, else full graph)
    and computes the gain exactly on that subgraph using leidenalg.
    """
    # Identify neighbor communities
    neighbors = graph.neighbors(v)
    neighbor_comms = set()
    for n in neighbors:
        neighbor_comms.add(state.sigma[n])

    c_old = state.sigma[v]
    if c_old in neighbor_comms:
        neighbor_comms.remove(c_old)

    # Generate new singleton label
    new_singleton = max(state.comm_size.keys()) + 1 if state.comm_size else 0
    neighbor_comms.add(new_singleton)

    gains = {}

    if affected_set is None:
        # Fallback to full graph (brute force testing)
        subgraph = graph
        sub_sigma = state.sigma.copy()
        v_idx = v
    else:
        # We need the affected subgraph. The blueprint instructs that the gain is evaluated on the affected subgraph.
        # But wait! Significance is a global metric (m * D_KL). Evaluating it on a subgraph might yield different gains
        # than evaluating it on the full graph, because the total edges and node sizes change.
        # Let's extract the subgraph safely.
        nodes_list = sorted(list(affected_set))
        node_to_sub = {global_id: sub_id for sub_id, global_id in enumerate(nodes_list)}

        if v not in node_to_sub:
            # v not in affected set? Should not happen if caller is well-behaved
            nodes_list.append(v)
            node_to_sub[v] = len(nodes_list) - 1

        subgraph = graph.subgraph(nodes_list)
        sub_sigma = np.array([state.sigma[n] for n in nodes_list])
        v_idx = node_to_sub[v]

    for c_target in neighbor_comms:
        gain = compute_delta_s(subgraph, sub_sigma, v_idx, c_target)
        gains[c_target] = gain

    return gains
