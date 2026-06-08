import pytest
import igraph as ig
import numpy as np
from isl.affected_set import (
    build_affected_set_1hop,
    build_affected_set_adaptive,
    get_boundary_nodes,
    expand_one_hop
)
from isl.community_state import CommunityState

def test_1hop_path_graph():
    # 0-1-2-3-4-5-6-7-8-9
    edges = [(i, i+1) for i in range(9)]
    g = ig.Graph(10, edges)
    # update (4,5) implies 4 and 5 are endpoints.
    # N(4) = {3,5}, N(5) = {4,6}
    # S1 = {4,5} U {3,5} U {4,6} = {3,4,5,6}
    updated = [(4,5)]
    s1 = build_affected_set_1hop(g, updated)
    assert s1 == {3,4,5,6}

def test_1hop_clique_graph():
    g = ig.Graph.Full(5)
    updated = [(0,1)]
    s1 = build_affected_set_1hop(g, updated)
    assert s1 == {0,1,2,3,4}

def test_1hop_disconnected_graph():
    g = ig.Graph(10)
    # Comp 1: 0-1-2. Comp 2: 3-4-5
    g.add_edges([(0,1), (1,2), (3,4), (4,5)])
    s1 = build_affected_set_1hop(g, [(0,1)])
    assert s1 == {0,1,2}

def test_1hop_multiple_updates():
    edges = [(i, i+1) for i in range(9)]
    g = ig.Graph(10, edges)
    # updates at ends
    s1 = build_affected_set_1hop(g, [(0,1), (8,9)])
    assert s1 == {0,1,2, 7,8,9}

def test_boundary_nodes_correct():
    edges = [(i, i+1) for i in range(9)]
    g = ig.Graph(10, edges)
    # S = {4,5}
    b = get_boundary_nodes({4,5}, g)
    assert b == {4,5} # 4 connects to 3, 5 connects to 6

    # S = {0,1,2,3,4,5,6,7,8,9}
    b2 = get_boundary_nodes(set(range(10)), g)
    assert b2 == set()

def test_adaptive_no_expansion_needed():
    g = ig.Graph.Tree(10, 2)
    state = CommunityState(10, np.zeros(10, dtype=int), g)
    state.recompute_from_scratch(g)

    # Very high tau, should not expand
    updated = [(0,1)]
    s_adapt = build_affected_set_adaptive(g, updated, state, tau=1000.0, R_max=3)
    s_1hop = build_affected_set_1hop(g, updated)
    assert s_adapt == s_1hop

def test_adaptive_expands_correctly():
    # To force expansion, we need a negative tau
    g = ig.Graph.Tree(10, 2)
    state = CommunityState(10, np.zeros(10, dtype=int), g)
    state.recompute_from_scratch(g)

    updated = [(0,1)]
    s_1hop = build_affected_set_1hop(g, updated)

    # -inf tau guarantees expansion if boundary has neighbors
    s_adapt = build_affected_set_adaptive(g, updated, state, tau=-float('inf'), R_max=2)
    assert len(s_adapt) > len(s_1hop)
    assert s_adapt == expand_one_hop(s_1hop, g)

def test_adaptive_respects_R_max():
    # Line graph of 20 nodes
    g = ig.Graph(20, [(i, i+1) for i in range(19)])
    state = CommunityState(20, np.zeros(20, dtype=int), g)
    state.recompute_from_scratch(g)

    updated = [(9,10)]
    s_1hop = build_affected_set_1hop(g, updated) # {8,9,10,11}
    s_adapt = build_affected_set_adaptive(g, updated, state, tau=-float('inf'), R_max=3)
    # Hop 1 (from s_1hop which is the baseline): {8,9,10,11}
    # Hop 2 (loop iter 1): expand to {7,8,9,10,11,12}
    # Hop 3 (loop iter 2): expand to {6,7,8,9,10,11,12,13}
    assert s_adapt == {6,7,8,9,10,11,12,13}
