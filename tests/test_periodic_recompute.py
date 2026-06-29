import pytest
import numpy as np
import igraph as ig
import leidenalg
from isl.community_state import CommunityState
from isl.periodic_recompute import PeriodicRecomputeEngine

def test_trigger_fires_at_K_multiples():
    engine = PeriodicRecomputeEngine(K=10)
    triggered_at = []
    for i in range(1, 31):
        engine.increment_batch()
        if engine.should_trigger():
            triggered_at.append(i)
    assert triggered_at == [10, 20, 30]

def test_trigger_not_at_non_multiples():
    engine = PeriodicRecomputeEngine(K=10)
    for i in [1, 5, 9, 11]:
        engine.batch_counter = i
        assert not engine.should_trigger()

def test_adoption_when_nmi_below_threshold():
    g = ig.Graph.Famous("Petersen") # 10 nodes
    # Suboptimal partition
    sigma = np.zeros(10, dtype=int)
    state = CommunityState(10, sigma, g)
    state.recompute_from_scratch(g)

    engine = PeriodicRecomputeEngine(K=1, nmi_threshold=0.99)
    engine.increment_batch()

    res = engine.run_if_triggered(g, state, current_batch_idx=1)
    assert res['triggered']
    assert res['adopted_full']
    assert len(set(state.sigma)) > 1 # Petersen graph shouldn't just be 1 community optimally

def test_no_adoption_when_nmi_above_threshold():
    g = ig.Graph.Famous("Petersen")
    p = leidenalg.find_partition(g, leidenalg.SignificanceVertexPartition, seed=43) # seed 43 inside run_if_triggered

    # We set state to exactly the optimal partition, so NMI will be 1.0
    from isl.baselines import partition_to_sigma
    sigma = partition_to_sigma(p.membership, 10)

    state = CommunityState(10, sigma.copy(), g)
    state.recompute_from_scratch(g)

    engine = PeriodicRecomputeEngine(K=1, nmi_threshold=0.5, seed=42) # batch_idx=1 so seed=43
    engine.increment_batch()
    res = engine.run_if_triggered(g, state, current_batch_idx=1)

    assert res['triggered']
    assert not res['adopted_full']
    assert np.array_equal(state.sigma, sigma)

def test_state_consistent_after_adoption():
    g = ig.Graph.Famous("Petersen")
    sigma = np.zeros(10, dtype=int)
    state = CommunityState(10, sigma, g)
    state.recompute_from_scratch(g)

    engine = PeriodicRecomputeEngine(K=1, nmi_threshold=0.99)
    engine.increment_batch()
    res = engine.run_if_triggered(g, state, current_batch_idx=1)

    # Check consistency
    assert state.get_significance() == res['S_full']

def test_trigger_rate_correct():
    engine = PeriodicRecomputeEngine(K=10)
    g = ig.Graph.Famous("Petersen")
    sigma = np.zeros(10, dtype=int)
    state = CommunityState(10, sigma, g)
    state.recompute_from_scratch(g)

    for i in range(1, 101):
        engine.increment_batch()
        engine.run_if_triggered(g, state, i)

    assert engine.get_trigger_rate() == 10 / 100

def test_trigger_batches_recorded():
    engine = PeriodicRecomputeEngine(K=10)
    g = ig.Graph.Famous("Petersen")
    sigma = np.zeros(10, dtype=int)
    state = CommunityState(10, sigma, g)
    state.recompute_from_scratch(g)

    for i in range(1, 25):
        engine.increment_batch()
        engine.run_if_triggered(g, state, i)

    assert engine.trigger_batches == [10, 20]
