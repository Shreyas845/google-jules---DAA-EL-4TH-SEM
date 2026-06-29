import pytest
import os
import igraph as ig
import numpy as np
from isl.benchmark import BenchmarkFramework

def test_lfr_node_count():
    bench = BenchmarkFramework()
    params = {'n': 100, 'mu': 0.3, 'min_community': 10, 'max_community': 20}
    g, sigma = bench.generate_lfr(params, seed=42)
    assert g.vcount() == 100

def test_lfr_ground_truth_nontrivial():
    bench = BenchmarkFramework()
    params = {'n': 100, 'mu': 0.3, 'min_community': 10, 'max_community': 20}
    g, sigma = bench.generate_lfr(params, seed=42)
    assert 1 < len(set(sigma)) < 100

def test_sbm_block_sizes_correct():
    bench = BenchmarkFramework()
    params = {'block_sizes': [50, 50], 'p_in': 0.5, 'p_out': 0.05}
    g, sigma = bench.generate_sbm(params, seed=42)
    assert g.vcount() == 100
    assert len(set(sigma)) == 2

def test_stream_roundtrip_serialization(tmpdir):
    bench = BenchmarkFramework()
    stream = [{'batch_idx': 1, 'add': [(0,1), (2,3)], 'del': []}]
    path = os.path.join(tmpdir, "stream.json")
    bench.serialize_stream(stream, path)

    loaded = bench.load_stream(path)
    assert loaded == stream

def test_random_uniform_batch_size():
    bench = BenchmarkFramework()
    g = ig.Graph(100)
    sigma = np.zeros(100)
    stream = bench.generate_update_stream(g, sigma, 'random_uniform', batch_size=5, num_batches=1, seed=42)
    assert len(stream[0]['add']) == 5

def test_stream_num_batches():
    bench = BenchmarkFramework()
    g = ig.Graph(100)
    sigma = np.zeros(100)
    stream = bench.generate_update_stream(g, sigma, 'random_uniform', batch_size=5, num_batches=10, seed=42)
    assert len(stream) == 10

def test_initial_partition_reproducible():
    bench = BenchmarkFramework()
    g = ig.Graph.Famous("Petersen")
    p1 = bench.generate_initial_partition(g, seed=42)
    p2 = bench.generate_initial_partition(g, seed=42)
    assert np.array_equal(p1, p2)

def test_small_community_formation_target_size():
    bench = BenchmarkFramework()
    # n=1000, m ~ 1000. target size should be < sqrt(2000) ~ 44
    g = ig.Graph.Tree(1000, 2)
    m = g.ecount()
    sigma = np.zeros(1000)
    stream = bench.generate_update_stream(g, sigma, 'small_community_formation', batch_size=10, num_batches=1, seed=42)

    # Check that added edges involve only nodes < sqrt(2m)
    target_size_approx = int(np.sqrt(2 * m))
    for u, v in stream[0]['add']:
        assert u < target_size_approx
        assert v < target_size_approx

def test_snap_loading_insertion_only():
    bench = BenchmarkFramework()
    # Point to nonexistent file will return empty graph
    g = bench.load_snap_dataset('CollegeMsg', 'nonexistent.txt')
    assert g.vcount() == 100
