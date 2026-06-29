import pytest
import numpy as np
from isl.graph_engine import GraphEngine

def test_apply_batch_insertion():
    engine = GraphEngine(5)
    engine.apply_batch([(0,1), (1,2)], [])
    assert engine.m == 2
    assert engine.graph.are_adjacent(0, 1)

def test_apply_batch_deletion():
    engine = GraphEngine(5)
    engine.apply_batch([(0,1), (1,2)], [])
    engine.apply_batch([], [(0,1)])
    assert engine.m == 1
    assert not engine.graph.are_adjacent(0, 1)
    assert engine.graph.are_adjacent(1, 2)

def test_apply_batch_mixed():
    engine = GraphEngine(5)
    engine.apply_batch([(0,1)], [])
    engine.apply_batch([(1,2)], [(0,1)])
    assert engine.m == 1
    assert not engine.graph.are_adjacent(0, 1)
    assert engine.graph.are_adjacent(1, 2)

def test_get_neighbors_known_graph():
    engine = GraphEngine(5)
    engine.apply_batch([(0,1), (0,2), (0,3)], [])
    neighbors = engine.get_neighbors(0)
    assert set(neighbors) == {1, 2, 3}

def test_get_neighbor_communities_known():
    engine = GraphEngine(5)
    engine.apply_batch([(0,1), (0,2), (0,3)], [])
    sigma = np.array([0, 1, 1, 2, 0])
    # neighbors of 0 are 1, 2, 3. Communities are 1, 1, 2.
    counts = engine.get_neighbor_communities(0, sigma)
    assert counts == {1: 2, 2: 1}

def test_get_subgraph_node_count():
    engine = GraphEngine(10)
    engine.apply_batch([(0,1), (1,2), (3,4)], [])
    sub = engine.get_subgraph([0,1,2,5])
    assert sub.vcount() == 4

def test_get_subgraph_edge_count():
    engine = GraphEngine(10)
    engine.apply_batch([(0,1), (1,2), (3,4)], [])
    sub = engine.get_subgraph([0,1,2,5])
    assert sub.ecount() == 2 # (0,1) and (1,2)

def test_delete_nonexistent_edge_raises():
    engine = GraphEngine(5)
    with pytest.raises(ValueError):
        engine.apply_batch([], [(0,1)])

def test_batch_update_does_not_lose_edges():
    engine = GraphEngine(10)
    # Apply a large mixed batch
    engine.apply_batch([(0,1), (1,2), (2,3), (3,4)], [])
    engine.apply_batch([(4,5), (5,6)], [(1,2)])
    assert engine.m == 5
    assert engine.graph.are_adjacent(4, 5)

def test_duplicate_edge_raises():
    engine = GraphEngine(5)
    engine.apply_batch([(0,1)], [])
    with pytest.raises(ValueError):
        engine.apply_batch([(0,1)], [])
