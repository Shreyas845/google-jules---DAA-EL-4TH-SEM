import numpy as np
import igraph as ig
from isl.community_state import CommunityState

def get_community_members(state: CommunityState, community: int) -> list:
    # return list of nodes in the given community
    return np.where(state.sigma == community)[0].tolist()

def split_community(state: CommunityState, community: int, components: list) -> list:
    """
    Assign each component after index 0 a new unique community label.
    Component 0 keeps the original label.
    Update all state counters.
    Returns list of new community labels created.
    """
    if len(components) <= 1:
        return []

    new_labels_created = []

    # We must cleanly update M and internal edges.
    # To be extremely safe, we could just recompute them for the affected components,
    # or handle the deltas.
    # Original community size:
    n_old = state.comm_size[community]

    # We will just remove the old community's contribution to M and p completely,
    # then re-add the pieces.
    state.M -= n_old * (n_old - 1) // 2
    state.p -= state.comm_internal_edges[community]

    del state.comm_size[community]
    del state.comm_internal_edges[community]

    for i, comp in enumerate(components):
        if i == 0:
            c_label = community
        else:
            c_label = max(state.comm_size.keys()) + 1 if state.comm_size else 0
            new_labels_created.append(c_label)

        # Update sigma
        for v in comp:
            state.sigma[v] = c_label

        n_c = len(comp)
        state.comm_size[c_label] = n_c
        state.M += n_c * (n_c - 1) // 2

        # Count internal edges
        # We can extract subgraph or just count
        e_c = 0
        if n_c > 1:
            sub = state.graph.subgraph(comp)
            e_c = sub.ecount()

        state.comm_internal_edges[c_label] = e_c
        state.p += e_c

    return new_labels_created

def check_and_fix_connectivity(
    graph: ig.Graph,
    state: CommunityState,
    affected_communities: set
) -> list:
    """
    For each community in affected_communities:
        1. Extract subgraph of community members
        2. Check if subgraph is connected
        3. If disconnected: split
    Returns list of community labels that were split.
    """
    split_occurred = []
    # We must iterate over a copy of the list because we might modify state
    for c in list(affected_communities):
        if c not in state.comm_size:
            continue # community might have been emptied

        members = np.where(state.sigma == c)[0].tolist()
        if len(members) <= 1:
            continue

        sub = graph.subgraph(members)
        components_sub = sub.connected_components()

        if len(components_sub) > 1:
            split_occurred.append(c)
            # map sub indices back to global indices
            global_components = []
            for comp_sub in components_sub:
                global_comp = [members[i] for i in comp_sub]
                global_components.append(global_comp)

            split_community(state, c, global_components)

    return split_occurred
