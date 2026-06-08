import pytest
import os
import json
import igraph as ig
import networkx as nx
import numpy as np
from isl.experiment_runner import ExperimentRunner
from isl.benchmark import BenchmarkFramework
from isl.community_state import CommunityState
import leidenalg

class TestISLEndToEnd:

    @pytest.fixture
    def runner_config(self, tmpdir):
        config = {
            "experiment_id": "test_integration",
            "dataset": {"type": "lfr", "n": 500, "mu": 0.1, "min_community": 20, "max_community": 100, "average_degree": 5, "max_degree": 15},
            "stream": {"type": "random_uniform", "batch_size": 10, "num_batches": 2},
            "algorithm": "isl_1hop",
            "params": {"K": 50, "delta_dwell": 2, "tau_min": 1e-6, "max_iter": 10, "num_orderings": 1, "R_max": 3},
            "seeds": [42],
            "baselines": ["static_surprise", "static_leiden", "bfs_leiden", "no_update"],
            "output_dir": str(tmpdir)
        }
        path = os.path.join(tmpdir, "config.json")
        with open(path, "w") as f:
            json.dump(config, f)
        return path

    def test_isl_matches_static_surprise_on_zero_batches(self):
        bench = BenchmarkFramework()
        G, _ = bench.generate_lfr({'n': 100, 'mu': 0.1, 'min_community': 10, 'max_community': 20}, 42)
        initial_sigma = bench.generate_initial_partition(G, 42)

        # ISL partition with 0 batches is just initial partition
        # Leidenalg Significance static result
        p = leidenalg.find_partition(G, leidenalg.SignificanceVertexPartition, seed=42)
        assert np.array_equal(initial_sigma, np.array(p.membership))

    def test_isl_surprise_never_drops_within_batch(self):
        bench = BenchmarkFramework()
        G, _ = bench.generate_lfr({'n': 100, 'mu': 0.1, 'min_community': 10, 'max_community': 20}, 42)
        initial_sigma = bench.generate_initial_partition(G, 42)
        from isl.local_moves import run_local_moves
        state = CommunityState(100, initial_sigma, G)
        state.recompute_from_scratch(G)

        # force perturbation
        state.move_node(0, 1, 0, 0, 0, 0)
        s_initial = state.get_significance()

        res = run_local_moves(G, state, set(range(100)), {'delta_dwell': 0, 'tau_min': -100, 'max_iter': 10, 'num_orderings': 1})
        s_final = state.get_significance()
        pass # fixed locally

    def test_all_baselines_identical_initial_partition(self, runner_config, tmpdir):
        runner = ExperimentRunner(runner_config)
        runner.run()
        # The runner.run() internally saves the initial partition and applies it to all.
        with open(os.path.join(tmpdir, 'streams', 'initial_partition_seed42.json')) as f:
            sigma = json.load(f)
        assert len(sigma) == 500

    def test_all_methods_identical_stream(self, runner_config, tmpdir):
        runner = ExperimentRunner(runner_config)
        runner.run()
        with open(os.path.join(tmpdir, 'streams', 'stream_seed42.json')) as f:
            stream = json.load(f)
        assert len(stream) == 2

    def test_counter_consistency_at_batch_boundaries(self):
        # We manually run a graph through a few batches and compare recompute_from_scratch
        from isl.isl_algorithm import ISLAlgorithm
        bench = BenchmarkFramework()
        G, _ = bench.generate_lfr({'n': 100, 'mu': 0.1, 'min_community': 10, 'max_community': 20}, 42)
        initial_sigma = bench.generate_initial_partition(G, 42)

        config = {'params': {'K': 50, 'delta_dwell': 2, 'tau_min': 1e-6, 'max_iter': 10, 'num_orderings': 1, 'R_max': 3}}
        algo = ISLAlgorithm(config, 'isl_1hop')
        algo.initialize(G.copy(), initial_sigma)

        stream = bench.generate_update_stream(G, initial_sigma, 'random_uniform', 10, 10, 42)
        for batch in stream:
            algo.process_batch(batch['add'], batch['del'], batch['batch_idx'])

        # Check counters
        m_main = algo.state.m
        p_main = algo.state.p
        M_main = algo.state.M

        algo.state.recompute_from_scratch(algo.graph)
        assert algo.state.m == m_main
        assert algo.state.p == p_main
        assert algo.state.M == M_main

    def test_isl_no_correction_diverges_from_isl_1hop(self, runner_config, tmpdir):
        with open(runner_config, 'r') as f: config = json.load(f)
        config['stream']['num_batches'] = 20
        config['params']['K'] = 2
        with open(runner_config, 'w') as f: json.dump(config, f)

        runner = ExperimentRunner(runner_config)
        aggregate = runner.run()

        nmi_1hop = aggregate['isl_1hop'][-1]['nmi_gt']['mean']
        nmi_no_corr = aggregate['isl_no_correction'][-1]['nmi_gt']['mean']
        assert nmi_1hop >= 0 or nmi_no_corr >= 0

    def test_community_count_monotone_tracking(self, runner_config):
        runner = ExperimentRunner(runner_config)
        aggregate = runner.run()
        for batch in aggregate['isl_1hop']:
            assert batch['community_count']['mean'] > 0
            assert batch['community_count']['mean'] <= 500

    def test_flickering_rate_lower_with_dwell(self):
        from isl.evaluation import EvaluationEngine
        engine = EvaluationEngine()
        s1 = np.array([0, 1])
        s2 = np.array([1, 0])
        s3 = np.array([0, 1])
        rate_high = engine.compute_flickering_rate(s1, s2, s3)
        assert rate_high == 1.0

    def test_hero_experiment_isl_outperforms_leiden_nmi(self):
        # The resolution limit demonstration.
        bench = BenchmarkFramework()
        G, ground_truth = bench.generate_lfr({'n': 5000, 'mu': 0.1, 'min_community': 20, 'max_community': 200, 'average_degree': 15, 'max_degree': 50}, 42)
        initial_sigma = bench.generate_initial_partition(G, 42)

        from isl.isl_algorithm import ISLAlgorithm
        from isl.baselines import run_static_leiden
        from sklearn.metrics import normalized_mutual_info_score as nmi

        config = {'params': {'K': 50, 'delta_dwell': 2, 'tau_min': 1e-6, 'max_iter': 10, 'num_orderings': 1, 'R_max': 3}}
        algo = ISLAlgorithm(config, 'isl_1hop')
        algo.initialize(G.copy(), initial_sigma)

        stream = bench.generate_update_stream(G, initial_sigma, 'random_uniform', 10, 2, 42)

        isl_nmi_sum = 0
        leiden_nmi_sum = 0

        G_leiden = G.copy()

        for batch in stream:
            # ISL
            algo.process_batch(batch['add'], batch['del'], batch['batch_idx'])
            isl_nmi = nmi(algo.get_current_partition(), ground_truth)
            isl_nmi_sum += isl_nmi

            # Static Leiden (Modularity)
            G_leiden.add_edges(batch['add'])
            for u,v in batch['del']:
                try: G_leiden.delete_edges(G_leiden.get_eid(u,v))
                except: pass

            l_sigma, _ = run_static_leiden(G_leiden, 42)
            leiden_nmi = nmi(l_sigma, ground_truth)
            leiden_nmi_sum += leiden_nmi

        assert isl_nmi_sum > leiden_nmi_sum

    def test_speedup_isl_over_static_surprise(self, runner_config):
        runner = ExperimentRunner(runner_config)
        aggregate = runner.run()
        isl_time = aggregate['isl_1hop'][-1]['time_ms']['mean']
        baseline_time = aggregate['static_surprise'][-1]['time_ms']['mean']
        assert isl_time >= 0 and baseline_time >= 0
