import pytest
import numpy as np
import igraph as ig
from isl.community_state import CommunityState

@pytest.fixture
def sample_graph():
    # 6-node graph, 2 communities: {0,1,2} and {3,4,5}
    # Edges: (0,1), (1,2), (0,2), (3,4), (4,5), (3,5), (2,3)
    edges = [(0,1), (1,2), (0,2), (3,4), (4,5), (3,5), (2,3)]
    g = ig.Graph(6, edges)
    return g

@pytest.fixture
def initial_labels():
    return np.array([0, 0, 0, 1, 1, 1])

def test_initial_state_from_known_partition(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    assert np.array_equal(state.sigma, initial_labels)
    assert state.comm_size == {0: 3, 1: 3}
    assert state.M == 3 * 2 // 2 + 3 * 2 // 2 # 3 + 3 = 6
    assert state.N == 6 * 5 // 2 # 15
    assert state.p == 6 # 3 intra-edges in C0 + 3 intra-edges in C1
    assert state.comm_internal_edges == {0: 3, 1: 3}
    assert state.m == 7

def test_move_node_updates_sigma(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    # Move node 0 from community 0 to community 1
    # Node 0 has 2 edges to C0 ({1, 2}) and 0 edges to C1
    state.move_node(v=0, c_target=1, e_to_old=2, e_to_new=0, n_old_before_move=3, n_new_before_move=3)

    assert state.sigma[0] == 1

def test_move_node_updates_comm_size(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    state.move_node(v=0, c_target=1, e_to_old=2, e_to_new=0, n_old_before_move=3, n_new_before_move=3)

    assert state.comm_size[0] == 2
    assert state.comm_size[1] == 4

def test_move_node_updates_comm_internal_edges(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    state.move_node(v=0, c_target=1, e_to_old=2, e_to_new=0, n_old_before_move=3, n_new_before_move=3)

    assert state.comm_internal_edges[0] == 1 # Original 3, minus 2 incident on node 0
    assert state.comm_internal_edges[1] == 3 # Original 3, plus 0 incident on node 0 from C1

def test_move_node_updates_p(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    original_p = state.p
    state.move_node(v=0, c_target=1, e_to_old=2, e_to_new=0, n_old_before_move=3, n_new_before_move=3)

    assert state.p == original_p - 2 # Net change: +0 - 2

def test_move_node_updates_M(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    original_M = state.M
    # M change: (n_B + 1 - 1) - n_A
    # n_A = 3, n_B = 3. delta_M = n_B - (n_A - 1) = 3 - 2 = 1?
    # Wait, new sizes are 2 and 4. New M = 2*1//2 + 4*3//2 = 1 + 6 = 7
    # Original M = 3 + 3 = 6. Delta M = +1.
    state.move_node(v=0, c_target=1, e_to_old=2, e_to_new=0, n_old_before_move=3, n_new_before_move=3)

    assert state.M == original_M + 1

def test_empty_community_cleanup(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    # Move nodes 0, 1, 2 to community 1
    state.move_node(v=0, c_target=1, e_to_old=2, e_to_new=0, n_old_before_move=3, n_new_before_move=3)
    state.move_node(v=1, c_target=1, e_to_old=1, e_to_new=0, n_old_before_move=2, n_new_before_move=4)
    state.move_node(v=2, c_target=1, e_to_old=0, e_to_new=1, n_old_before_move=1, n_new_before_move=5) # 2 is connected to 3 which is in C1

    assert 0 not in state.comm_size
    assert 0 not in state.comm_internal_edges

def test_singleton_community_move():
    edges = []
    g = ig.Graph(1, edges)
    state = CommunityState(1, np.array([0]), g)
    state.recompute_from_scratch(g)

    assert state.comm_size == {0: 1}
    state.move_node(v=0, c_target=1, e_to_old=0, e_to_new=0, n_old_before_move=1, n_new_before_move=0)

    assert 0 not in state.comm_size
    assert state.comm_size == {1: 1}

def test_apply_edge_update_insertion_same_community(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    original_m = state.m
    original_p = state.p
    original_internal = state.comm_internal_edges[0]

    state.apply_edge_update(0, 1, action=+1)

    assert state.m == original_m + 1
    assert state.p == original_p + 1
    assert state.comm_internal_edges[0] == original_internal + 1

def test_apply_edge_update_insertion_different_community(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    original_m = state.m
    original_p = state.p

    state.apply_edge_update(0, 4, action=+1) # 0 is in C0, 4 is in C1

    assert state.m == original_m + 1
    assert state.p == original_p # unchanged
    assert state.comm_internal_edges[0] == 3
    assert state.comm_internal_edges[1] == 3

def test_apply_edge_update_deletion(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    original_m = state.m
    original_p = state.p

    state.apply_edge_update(0, 1, action=-1)

    assert state.m == original_m - 1
    assert state.p == original_p - 1
    assert state.comm_internal_edges[0] == 2

def test_get_significance_known_value(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    import leidenalg
    p = leidenalg.SignificanceVertexPartition(sample_graph, initial_membership=initial_labels.tolist())
    expected = p.quality()

    assert abs(state.get_significance() - expected) < 1e-10

def test_get_significance_zero_protection():
    g = ig.Graph(6, []) # Empty graph
    state = CommunityState(6, np.array([0,0,0,1,1,1]), g)
    state.recompute_from_scratch(g)

    # Empty graph, shouldn't raise exception
    sig = state.get_significance()
    assert not np.isnan(sig)

def test_recompute_from_scratch_matches_maintained(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    state.move_node(v=0, c_target=1, e_to_old=2, e_to_new=0, n_old_before_move=3, n_new_before_move=3)
    state.apply_edge_update(1, 4, action=+1)

    m_main = state.m
    p_main = state.p
    M_main = state.M

    state.recompute_from_scratch(sample_graph) # wait, sample_graph itself wasn't mutated for the edge update, so recompute would use original graph
    # Let's mock graph mutation
    sample_graph.add_edge(1, 4)
    state.recompute_from_scratch(sample_graph)

    assert state.m == m_main
    assert state.p == p_main
    assert state.M == M_main

def test_dwell_counter_reset_on_move(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    state.increment_dwell_counters()
    assert state.dwell_counter[0] == 1

    state.move_node(v=0, c_target=1, e_to_old=2, e_to_new=0, n_old_before_move=3, n_new_before_move=3)

    assert state.dwell_counter[0] == 0
    assert state.dwell_counter[1] == 1

def test_dwell_counter_increment(sample_graph, initial_labels):
    state = CommunityState(6, initial_labels, sample_graph)
    state.recompute_from_scratch(sample_graph)

    state.increment_dwell_counters()
    state.increment_dwell_counters()
    state.increment_dwell_counters()

    assert np.all(state.dwell_counter == 3)
