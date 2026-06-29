import numpy as np
import igraph as ig
from isl.community_state import CommunityState
from isl.delta_s import scan_node_gains

def run_local_moves(
    graph: ig.Graph,
    state: CommunityState,
    affected_set: set,
    params: dict
) -> dict:
    delta_dwell = params.get('delta_dwell', 2)
    tau_min = params.get('tau_min', 1e-6)
    max_iter = params.get('max_iter', 100)
    num_orderings = params.get('num_orderings', 3)

    best_signif = -float('inf')
    best_sigma = None
    best_comm_size = None
    best_comm_internal = None
    best_p = None
    best_M = None
    best_dwell = None

    affected_list = list(affected_set)

    # Store original sigma to compute communities_modified at the end
    original_sigma = state.sigma.copy()

    total_nodes_moved = 0
    total_passes = 0
    all_orderings_signif = []

    for ordering_idx in range(num_orderings):
        state_copy = CommunityState(graph.vcount(), state.sigma.copy(), graph)
        state_copy.comm_size = state.comm_size.copy()
        state_copy.comm_internal_edges = state.comm_internal_edges.copy()
        state_copy.m = state.m
        state_copy.p = state.p
        state_copy.M = state.M
        state_copy.N = state.N
        state_copy.dwell_counter = state.dwell_counter.copy()

        passes_this_ordering = 0
        nodes_moved_this_ordering = 0

        while passes_this_ordering < max_iter:
            np.random.shuffle(affected_list)
            moves_in_pass = 0

            for v in affected_list:
                if state_copy.dwell_counter[v] < delta_dwell:
                    continue

                gains = scan_node_gains(v, state_copy, graph, affected_set)
                if not gains:
                    continue

                best_c = max(gains, key=gains.get)
                best_gain = gains[best_c]

                if best_gain > tau_min:
                    c_old = state_copy.sigma[v]
                    n_old = state_copy.comm_size[c_old]
                    n_new = state_copy.comm_size.get(best_c, 0)

                    e_old = 0
                    e_new = 0
                    for neighbor in graph.neighbors(v):
                        nc = state_copy.sigma[neighbor]
                        if nc == c_old:
                            e_old += 1
                        elif nc == best_c:
                            e_new += 1

                    state_copy.move_node(v, best_c, e_old, e_new, n_old, n_new)
                    moves_in_pass += 1
                    nodes_moved_this_ordering += 1

            passes_this_ordering += 1
            if moves_in_pass == 0:
                break

        final_signif = state_copy.get_significance()
        all_orderings_signif.append(final_signif)
        total_nodes_moved += nodes_moved_this_ordering
        total_passes += passes_this_ordering

        if final_signif > best_signif:
            best_signif = final_signif
            best_sigma = state_copy.sigma.copy()
            best_comm_size = state_copy.comm_size.copy()
            best_comm_internal = state_copy.comm_internal_edges.copy()
            best_p = state_copy.p
            best_M = state_copy.M
            best_dwell = state_copy.dwell_counter.copy()

    # Restore best state
    state.sigma = best_sigma
    state.comm_size = best_comm_size
    state.comm_internal_edges = best_comm_internal
    state.p = best_p
    state.M = best_M
    state.dwell_counter = best_dwell

    # Identify modified communities
    communities_modified = set()
    for v in affected_list:
        if state.sigma[v] != original_sigma[v]:
            communities_modified.add(state.sigma[v])
            communities_modified.add(original_sigma[v])

    # Ensure partition_obj stays in sync
    state.get_significance()

    return {
        'nodes_moved': total_nodes_moved // num_orderings, # avg
        'passes_completed': total_passes // num_orderings,
        'best_ordering_surprise': best_signif, # Blueprint expects 'surprise' key name technically, but logging can adapt
        'all_orderings_surprise': all_orderings_signif,
        'communities_modified': communities_modified
    }
