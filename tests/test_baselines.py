import pytest
import igraph as ig
import numpy as np
import networkx as nx
from isl.baselines import (
    run_static_significance, run_static_leiden, run_bfs_leiden, run_no_update,
    partition_to_sigma, sigma_to_membership
)

@pytest.fixture
def lfr_graph():
    G_nx = nx.LFR_benchmark_graph(
        n=100, tau1=3, tau2=1.5, mu=0.1, average_degree=5, max_degree=15,
        min_community=10, max_community=20, seed=42
    )
    return ig.Graph(100, list(G_nx.edges()))

def test_static_significance_nontrivial_partition(lfr_graph):
    sigma, time_ms = run_static_significance(lfr_graph, seed=42)
    num_communities = len(set(sigma))
    assert 2 < num_communities < 100
    assert time_ms > 0

def test_static_leiden_nontrivial_partition(lfr_graph):
    sigma, time_ms = run_static_leiden(lfr_graph, seed=42)
    num_communities = len(set(sigma))
    assert 2 < num_communities < 100
    assert time_ms > 0

def test_bfs_leiden_outside_radius_unchanged(lfr_graph):
    # Initial partition
    sigma_in = np.zeros(100, dtype=int)

    # Run BFS on a single node
    affected = [0]
    sigma_out, time_ms = run_bfs_leiden(lfr_graph, sigma_in, affected, radius=1, seed=42)

    # Nodes outside radius 1 of node 0 should still be in the same relative community
    # Note: BFS leiden renumbers ALL communities at the end!
    # So we can't check absolute label equality, but we can check if they are all in the SAME community
    neighborhood = set(lfr_graph.neighborhood(0, order=1))
    outside_nodes = [v for v in range(100) if v not in neighborhood]

    # They started all in C0. After renumbering, they should all share some label C_x
    if outside_nodes:
        first_outside_label = sigma_out[outside_nodes[0]]
        for v in outside_nodes:
            assert sigma_out[v] == first_outside_label

    assert time_ms > 0

def test_no_update_returns_identical():
    sigma_in = np.array([0, 1, 2, 0])
    sigma_out = run_no_update(sigma_in)
    assert sigma_in is sigma_out

def test_partition_to_sigma_consecutive_labels():
    membership = [10, 5, 5, 20, 10]
    sigma = partition_to_sigma(membership, 5)
    # unique labels: 10->0, 5->1, 20->2
    # expected: [0, 1, 1, 2, 0]
    assert np.array_equal(sigma, [0, 1, 1, 2, 0])

def test_sigma_to_membership_roundtrip():
    sigma = np.array([0, 1, 1, 2, 0])
    membership = sigma_to_membership(sigma)
    assert membership == [0, 1, 1, 2, 0]

def test_static_significance_seed_reproducible(lfr_graph):
    sigma1, _ = run_static_significance(lfr_graph, seed=123)
    sigma2, _ = run_static_significance(lfr_graph, seed=123)
    assert np.array_equal(sigma1, sigma2)

def test_timing_measurement_positive(lfr_graph):
    _, t1 = run_static_significance(lfr_graph, seed=42)
    _, t2 = run_static_leiden(lfr_graph, seed=42)
    sigma_in = np.zeros(100, dtype=int)
    _, t3 = run_bfs_leiden(lfr_graph, sigma_in, [0], radius=1, seed=42)

    assert t1 > 0
    assert t2 > 0
    assert t3 > 0
