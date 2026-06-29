import igraph as ig
from isl.community_state import CommunityState
from isl.delta_s import scan_node_gains

def build_affected_set_1hop(graph: ig.Graph, updated_edges: list) -> set:
    """
    S0 = all endpoints of inserted/deleted edges
    S1 = S0 U N(S0)
    """
    s0 = set()
    for u, v in updated_edges:
        s0.add(u)
        s0.add(v)

    s1 = set(s0)
    for u in s0:
        s1.update(graph.neighbors(u))

    return s1

def get_boundary_nodes(affected_set: set, graph: ig.Graph) -> set:
    """
    Return nodes in affected_set that have at least one neighbor outside affected_set.
    """
    boundary = set()
    for u in affected_set:
        for n in graph.neighbors(u):
            if n not in affected_set:
                boundary.add(u)
                break
    return boundary

def expand_one_hop(affected_set: set, graph: ig.Graph) -> set:
    """
    Add all neighbors of boundary nodes to affected_set.
    """
    boundary = get_boundary_nodes(affected_set, graph)
    new_set = set(affected_set)
    for u in boundary:
        new_set.update(graph.neighbors(u))
    return new_set

def build_affected_set_adaptive(
    graph: ig.Graph,
    updated_edges: list,
    state: CommunityState,
    tau: float,
    R_max: int = 3
) -> set:
    """
    Start with S1 (from build_affected_set_1hop).
    Expand boundary if max ΔSignificance gain for boundary nodes > tau.
    Expand up to R_max hops total.
    """
    current_set = build_affected_set_1hop(graph, updated_edges)

    for hop in range(1, R_max):
        boundary = get_boundary_nodes(current_set, graph)
        if not boundary:
            break

        max_boundary_gain = -float('inf')
        for v in boundary:
            gains = scan_node_gains(v, state, graph, current_set)
            if gains:
                v_max = max(gains.values())
                if v_max > max_boundary_gain:
                    max_boundary_gain = v_max

        if max_boundary_gain > tau:
            current_set = expand_one_hop(current_set, graph)
        else:
            break

    return current_set
