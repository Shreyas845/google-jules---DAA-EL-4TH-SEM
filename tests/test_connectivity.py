import pytest
import igraph as ig
import numpy as np
from isl.community_state import CommunityState
from isl.connectivity import check_and_fix_connectivity, split_community

def test_connected_community_unchanged():
    g = ig.Graph(3, [(0,1), (1,2), (0,2)])
    state = CommunityState(3, np.zeros(3, dtype=int), g)
    state.recompute_from_scratch(g)

    splits = check_and_fix_connectivity(g, state, {0})
    assert splits == []
    assert state.comm_size == {0: 3}

def test_disconnected_community_splits():
    # 0-1-2 and 3-4-5, no edges between them
    edges = [(0,1), (1,2), (0,2), (3,4), (4,5), (3,5)]
    g = ig.Graph(6, edges)
    # Put them all in community 0
    state = CommunityState(6, np.zeros(6, dtype=int), g)
    state.recompute_from_scratch(g)

    splits = check_and_fix_connectivity(g, state, {0})
    assert splits == [0]
    assert len(state.comm_size) == 2
    # One stays 0, the other gets 1
    assert set(state.sigma) == {0, 1}

def test_split_community_sizes_correct():
    edges = [(0,1), (1,2), (0,2), (3,4), (4,5), (3,5)]
    g = ig.Graph(6, edges)
    state = CommunityState(6, np.zeros(6, dtype=int), g)
    state.recompute_from_scratch(g)

    check_and_fix_connectivity(g, state, {0})
    assert sum(state.comm_size.values()) == 6
    assert state.comm_size[0] == 3
    assert state.comm_size[1] == 3

def test_split_community_M_correct():
    edges = [(0,1), (1,2), (0,2), (3,4), (4,5), (3,5)]
    g = ig.Graph(6, edges)
    state = CommunityState(6, np.zeros(6, dtype=int), g)
    state.recompute_from_scratch(g)

    assert state.M == 6 * 5 // 2 # 15
    check_and_fix_connectivity(g, state, {0})
    # After split, two comms of size 3. M should be 3 + 3 = 6
    assert state.M == 6

def test_only_affected_communities_checked():
    edges = [(0,1), (1,2), (0,2), (3,4), (4,5), (3,5)]
    g = ig.Graph(6, edges)
    state = CommunityState(6, np.zeros(6, dtype=int), g)
    state.recompute_from_scratch(g)

    # Do not include 0 in affected
    splits = check_and_fix_connectivity(g, state, {99}) # 99 doesn't exist
    assert splits == []
    assert len(state.comm_size) == 1

def test_new_labels_unique():
    edges = [(0,1), (2,3)]
    g = ig.Graph(4, edges)
    # sigma: C0={0,1}, C2={2,3}. So max label is 2.
    sigma = np.array([0, 0, 2, 2])
    state = CommunityState(4, sigma, g)
    state.recompute_from_scratch(g)

    # Now force C0 to be disconnected
    g.delete_edges([(0,1)])
    # We must manually trigger split by including 0 in affected
    check_and_fix_connectivity(g, state, {0})

    # C0 should split into C0 and C3 (since max was 2)
    assert 3 in state.comm_size
    assert len(state.comm_size) == 3
