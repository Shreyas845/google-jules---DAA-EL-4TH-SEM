import pytest
import igraph as ig
import numpy as np
from copy import deepcopy
import leidenalg
from isl.community_state import CommunityState
from isl.delta_s import compute_delta_s, scan_node_gains

def brute_force_delta_s(state_before, v, c_target, graph):
    # Full graph evaluation
    p_before = leidenalg.SignificanceVertexPartition(graph, initial_membership=state_before.sigma.tolist())
    sig_before = p_before.quality()

    state_copy = deepcopy(state_before)
    state_copy.move_node(v, c_target, 0, 0, 0, 0) # Just moves node in sigma

    p_after = leidenalg.SignificanceVertexPartition(graph, initial_membership=state_copy.sigma.tolist())
    sig_after = p_after.quality()

    return sig_after - sig_before

def test_delta_s_tiny_graph_move_improves():
    g = ig.Graph(4, [(0,1), (2,3), (1,2)])
    sigma = np.array([0, 1, 1, 2])
    state = CommunityState(4, sigma, g)
    state.recompute_from_scratch(g)

    # Move node 0 to community 1 (it is connected to 1)
    ds = compute_delta_s(g, state.sigma.copy(), 0, 1)
    bf = brute_force_delta_s(state, 0, 1, g)
    assert abs(ds - bf) < 1e-10

def test_delta_s_tiny_graph_move_worsens():
    g = ig.Graph(4, [(0,1), (2,3)])
    sigma = np.array([0, 0, 1, 1])
    state = CommunityState(4, sigma, g)
    state.recompute_from_scratch(g)

    # Move node 0 to community 1 (no connections)
    ds = compute_delta_s(g, state.sigma.copy(), 0, 1)
    bf = brute_force_delta_s(state, 0, 1, g)
    assert abs(ds - bf) < 1e-10

def test_delta_s_singleton_source():
    g = ig.Graph(3, [(0,1), (1,2)])
    sigma = np.array([0, 1, 1])
    state = CommunityState(3, sigma, g)
    state.recompute_from_scratch(g)

    gains = scan_node_gains(0, state, g, affected_set=set([0,1,2]))
    bf = brute_force_delta_s(state, 0, 1, g)
    assert abs(gains[1] - bf) < 1e-10

def test_delta_s_singleton_target():
    g = ig.Graph(3, [(0,1), (1,2)])
    sigma = np.array([0, 0, 0])
    state = CommunityState(3, sigma, g)
    state.recompute_from_scratch(g)

    gains = scan_node_gains(0, state, g, affected_set=set([0,1,2]))
    # Move to a new community
    new_c = max(state.comm_size.keys()) + 1
    assert new_c in gains
    bf = brute_force_delta_s(state, 0, new_c, g)
    assert abs(gains[new_c] - bf) < 1e-10

def test_delta_s_large_source_community():
    n = 100
    g = ig.Graph.Tree(n, 2)
    sigma = np.zeros(n, dtype=int)
    sigma[n-1] = 1
    state = CommunityState(n, sigma, g)
    state.recompute_from_scratch(g)

    ds = compute_delta_s(g, state.sigma.copy(), 0, 1)
    bf = brute_force_delta_s(state, 0, 1, g)
    assert abs(ds - bf) < 1e-10

def test_delta_s_large_community_move():
    n = 100
    g = ig.Graph.Tree(n, 2)
    sigma = np.zeros(n, dtype=int)
    sigma[80:] = 1
    state = CommunityState(n, sigma, g)
    state.recompute_from_scratch(g)

    ds = compute_delta_s(g, state.sigma.copy(), 79, 1)
    bf = brute_force_delta_s(state, 79, 1, g)
    assert abs(ds - bf) < 1e-10

def test_delta_s_large_community_internal_move():
    n = 100
    g = ig.Graph.Tree(n, 2)
    sigma = np.zeros(n, dtype=int)
    sigma[80:] = 1
    state = CommunityState(n, sigma, g)
    state.recompute_from_scratch(g)

    ds = compute_delta_s(g, state.sigma.copy(), 0, 1)
    bf = brute_force_delta_s(state, 0, 1, g)
    assert abs(ds - bf) < 1e-10

def test_delta_s_high_gain_move():
    g = ig.Graph(4, [(0,1), (0,2), (0,3)])
    sigma = np.array([1, 0, 0, 0])
    state = CommunityState(4, sigma, g)
    state.recompute_from_scratch(g)

    gains = scan_node_gains(0, state, g, affected_set=set(range(4)))
    assert gains[0] > 0
    bf = brute_force_delta_s(state, 0, 0, g)
    assert abs(gains[0] - bf) < 1e-10

def test_delta_s_zero_gain_move():
    g = ig.Graph(2, [])
    sigma = np.array([0, 1])
    state = CommunityState(2, sigma, g)
    state.recompute_from_scratch(g)

    ds = compute_delta_s(g, state.sigma.copy(), 0, 1)
    bf = brute_force_delta_s(state, 0, 1, g)
    assert abs(ds - bf) < 1e-10

def test_delta_s_negative_gain_rejected():
    g = ig.Graph()
    g.add_vertices(10)
    edges = [(i,j) for i in range(5) for j in range(i+1,5)] + [(i,j) for i in range(5,10) for j in range(i+1,10)] + [(0,5)]
    g.add_edges(edges)
    sigma = np.zeros(10, dtype=int)
    sigma[5:] = 1
    state = CommunityState(10, sigma, g)
    state.recompute_from_scratch(g)

    # Move node 0 to community 1 (it is connected to node 5 which is in C1)
    # But it breaks its own clique, so it should be negative
    ds = compute_delta_s(g, state.sigma.copy(), 0, 1)
    assert ds < 0

def test_delta_s_consistent_with_state_after_sequential_moves():
    g = ig.Graph.Tree(20, 2)
    sigma = np.zeros(20, dtype=int)
    sigma[10:] = 1
    state = CommunityState(20, sigma, g)
    state.recompute_from_scratch(g)

    affected_set = set(range(20))
    for i in range(5):
        ds = compute_delta_s(g, state.sigma.copy(), i, 1)
        bf = brute_force_delta_s(state, i, 1, g)
        assert abs(ds - bf) < 1e-10
        # apply move immediately
        state.move_node(i, 1, 0, 0, 0, 0)

def test_delta_s_zero_p():
    g = ig.Graph(4, [(0,2), (1,3)])
    sigma = np.array([0, 0, 1, 1])
    state = CommunityState(4, sigma, g)
    state.recompute_from_scratch(g)

    # p = 0
    assert state.p == 0
    ds = compute_delta_s(g, state.sigma.copy(), 0, 1)
    bf = brute_force_delta_s(state, 0, 1, g)
    assert abs(ds - bf) < 1e-10

def test_delta_s_all_intra():
    g = ig.Graph(4, [(0,1), (2,3)])
    sigma = np.array([0, 0, 1, 1])
    state = CommunityState(4, sigma, g)
    state.recompute_from_scratch(g)

    assert state.p == state.m
    ds = compute_delta_s(g, state.sigma.copy(), 0, 1)
    bf = brute_force_delta_s(state, 0, 1, g)
    assert abs(ds - bf) < 1e-10

def test_delta_s_no_neighbors_in_target():
    g = ig.Graph(4, [(0,1), (2,3)])
    sigma = np.array([0, 0, 1, 1])
    state = CommunityState(4, sigma, g)
    state.recompute_from_scratch(g)

    ds = compute_delta_s(g, state.sigma.copy(), 0, 1)
    bf = brute_force_delta_s(state, 0, 1, g)
    assert abs(ds - bf) < 1e-10

def test_delta_s_numerical_stability_large_graph():
    # Test large numbers
    n = 2000
    g = ig.Graph.Tree(n, 3)
    sigma = np.zeros(n, dtype=int)
    sigma[n//2:] = 1
    state = CommunityState(n, sigma, g)
    state.recompute_from_scratch(g)

    ds = compute_delta_s(g, state.sigma.copy(), 0, 1)
    bf = brute_force_delta_s(state, 0, 1, g)
    assert abs(ds - bf) < 1e-10


def test_delta_s_two_sequential_moves_order_independent_of_formula():
    g = ig.Graph.Tree(10, 2)
    sigma = np.zeros(10, dtype=int)
    state1 = CommunityState(10, sigma, g)
    state1.recompute_from_scratch(g)

    affected = set(range(10))
    gains_x = scan_node_gains(0, state1, g, affected)

    state1.move_node(0, 1, 0, 0, 0, 0)
    gains_y = scan_node_gains(1, state1, g, affected)
    bf_y = brute_force_delta_s(state1, 1, 1, g)

    assert abs(gains_y[1] - bf_y) < 1e-10
