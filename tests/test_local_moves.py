import pytest
import igraph as ig
import numpy as np
from isl.community_state import CommunityState
from isl.local_moves import run_local_moves

@pytest.fixture
def test_graph():
    # 2 components of 4 nodes each, loosely connected
    g = ig.Graph(8)
    edges = [(i,j) for i in range(4) for j in range(i+1,4)] + \
            [(i,j) for i in range(4,8) for j in range(i+1,8)] + \
            [(0,4)]
    g.add_edges(edges)
    return g

def test_local_moves_improves_surprise(test_graph):
    sigma = np.arange(8, dtype=int) # all singletons
    state = CommunityState(8, sigma, test_graph)
    state.recompute_from_scratch(test_graph)

    initial_signif = state.get_significance()

    affected_set = set(range(8))
    params = {'delta_dwell': 0, 'tau_min': 1e-6, 'max_iter': 100, 'num_orderings': 1}

    res = run_local_moves(test_graph, state, affected_set, params)

    final_signif = state.get_significance()
    assert final_signif > initial_signif
    assert res['nodes_moved'] > 0

def test_local_moves_never_worsens_monotone(test_graph):
    # Start with optimal partition
    sigma = np.zeros(8, dtype=int)
    sigma[4:] = 1
    state = CommunityState(8, sigma, test_graph)
    state.recompute_from_scratch(test_graph)

    initial_signif = state.get_significance()

    affected_set = set(range(8))
    params = {'delta_dwell': 0, 'tau_min': 1e-6, 'max_iter': 100, 'num_orderings': 1}

    run_local_moves(test_graph, state, affected_set, params)

    final_signif = state.get_significance()
    assert final_signif >= initial_signif

def test_dwell_counter_respected(test_graph):
    sigma = np.zeros(8, dtype=int)
    state = CommunityState(8, sigma, test_graph)
    state.recompute_from_scratch(test_graph)

    # Force dwell to be 0 (just moved)
    state.dwell_counter[:] = 0

    affected_set = set(range(8))
    params = {'delta_dwell': 2, 'tau_min': 1e-6, 'max_iter': 10, 'num_orderings': 1}

    res = run_local_moves(test_graph, state, affected_set, params)

    # Should not move anything because dwell counter prevents it
    assert res['nodes_moved'] == 0

def test_tau_min_threshold():
    g = ig.Graph(4, [(0,1), (2,3), (1,2)])
    sigma = np.array([0, 0, 1, 1])
    state = CommunityState(4, sigma, g)
    state.recompute_from_scratch(g)

    affected_set = set(range(4))
    # Enormous tau threshold
    params = {'delta_dwell': 0, 'tau_min': 100.0, 'max_iter': 10, 'num_orderings': 1}
    res = run_local_moves(g, state, affected_set, params)

    assert res['nodes_moved'] == 0

def test_num_orderings_result_geq_single(test_graph):
    sigma = np.zeros(8, dtype=int)
    state1 = CommunityState(8, sigma.copy(), test_graph)
    state1.recompute_from_scratch(test_graph)

    params1 = {'delta_dwell': 0, 'tau_min': 1e-6, 'max_iter': 10, 'num_orderings': 1}
    res1 = run_local_moves(test_graph, state1, set(range(8)), params1)

    state3 = CommunityState(8, sigma.copy(), test_graph)
    state3.recompute_from_scratch(test_graph)
    params3 = {'delta_dwell': 0, 'tau_min': 1e-6, 'max_iter': 10, 'num_orderings': 3}
    res3 = run_local_moves(test_graph, state3, set(range(8)), params3)

    # best of 3 should be >= result of 1 ordering
    assert res3['best_ordering_surprise'] >= res1['best_ordering_surprise']

def test_communities_modified_correct(test_graph):
    sigma = np.arange(8, dtype=int)
    state = CommunityState(8, sigma, test_graph)
    state.recompute_from_scratch(test_graph)

    params = {'delta_dwell': 0, 'tau_min': 1e-6, 'max_iter': 10, 'num_orderings': 1}
    res = run_local_moves(test_graph, state, set(range(8)), params)

    assert len(res['communities_modified']) > 0

def test_max_iter_respected(test_graph):
    sigma = np.zeros(8, dtype=int)
    state = CommunityState(8, sigma, test_graph)
    state.recompute_from_scratch(test_graph)

    # 0 max iter means no passes
    params = {'delta_dwell': 0, 'tau_min': 1e-6, 'max_iter': 0, 'num_orderings': 1}
    res = run_local_moves(test_graph, state, set(range(8)), params)
    assert res['passes_completed'] == 0
    assert res['nodes_moved'] == 0

def test_immediate_counter_update(test_graph):
    sigma = np.zeros(8, dtype=int)
    state = CommunityState(8, sigma, test_graph)
    state.recompute_from_scratch(test_graph)

    initial_p = state.p
    initial_M = state.M

    # We execute a single move directly using state_copy logic to verify counters update immediately
    from copy import deepcopy
    state_copy = CommunityState(8, state.sigma.copy(), test_graph)
    state_copy.comm_size = state.comm_size.copy()
    state_copy.comm_internal_edges = state.comm_internal_edges.copy()
    state_copy.m = state.m
    state_copy.p = state.p
    state_copy.M = state.M
    state_copy.N = state.N

    state_copy.move_node(v=0, c_target=1, e_to_old=1, e_to_new=0, n_old_before_move=8, n_new_before_move=0)

    # The immediate counter update rule specifies state.p and state.M update inside move_node before next step.
    assert state_copy.p != initial_p
    assert state_copy.M != initial_M
