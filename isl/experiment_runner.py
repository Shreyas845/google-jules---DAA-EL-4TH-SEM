import json
import igraph as ig
import os
import time
import numpy as np
from isl.benchmark import BenchmarkFramework
from isl.evaluation import EvaluationEngine
from isl.isl_algorithm import ISLAlgorithm
from isl.baselines import run_static_significance, run_static_leiden, run_bfs_leiden, run_no_update
import subprocess

class ExperimentRunner:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.output_dir = self.config['output_dir']
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'streams'), exist_ok=True)

        try:
            self.git_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
        except:
            self.git_hash = "unknown"

        self.bench = BenchmarkFramework()
        self.eval_engine = EvaluationEngine()

    def run(self) -> dict:
        t_start_total = time.perf_counter()

        all_results = {method: [] for method in self.config['baselines']}
        for variant in ['isl_1hop', 'isl_adaptive', 'isl_no_correction', 'isl_no_dwell']:
            all_results[variant] = []

        # For each seed
        for seed in self.config['seeds']:
            # 1. Generate/Load Graph
            ds = self.config['dataset']
            if ds['type'] == 'lfr':
                G, ground_truth = self.bench.generate_lfr(ds, seed)
            elif ds['type'] == 'sbm':
                G, ground_truth = self.bench.generate_sbm(ds, seed)
            else: # SNAP
                # Assuming path is stored in ds['path']
                G = self.bench.load_snap_dataset(ds['name'], ds['path'])
                ground_truth = np.zeros(G.vcount(), dtype=int) # No ground truth for real graphs

            n = G.vcount()

            # 2. Generate/Load Stream
            stream_config = self.config['stream']
            stream_path = os.path.join(self.output_dir, 'streams', f'stream_seed{seed}.json')
            if not os.path.exists(stream_path):
                stream = self.bench.generate_update_stream(
                    G, np.zeros(n), stream_config['type'],
                    stream_config['batch_size'], stream_config['num_batches'], seed
                )
                self.bench.serialize_stream(stream, stream_path)
            else:
                stream = self.bench.load_stream(stream_path)

            # 3. Initial Partition
            init_part_path = os.path.join(self.output_dir, 'streams', f'initial_partition_seed{seed}.json')
            if not os.path.exists(init_part_path):
                initial_sigma = self.bench.generate_initial_partition(G, seed)
                with open(init_part_path, 'w') as f:
                    json.dump(initial_sigma.tolist(), f)
            else:
                with open(init_part_path, 'r') as f:
                    initial_sigma = np.array(json.load(f))

            # 4. Run baselines
            for bline in self.config['baselines']:
                res = self._run_method_for_seed(bline, seed, stream, initial_sigma, G.copy(), ground_truth)
                all_results[bline].append(res)

            # 5. Run ISL variants
            for variant in ['isl_1hop', 'isl_adaptive', 'isl_no_correction', 'isl_no_dwell']:
                res = self._run_method_for_seed(variant, seed, stream, initial_sigma, G.copy(), ground_truth)
                all_results[variant].append(res)

        # Aggregate
        aggregate = {}
        for method, seed_results in all_results.items():
            aggregate[method] = self.eval_engine.aggregate_across_seeds(seed_results)

        # Wilcoxon
        wilcoxon_tests = {}
        # Only do if isl_1hop is available
        if 'isl_1hop' in all_results and 'static_leiden' in all_results:
            for bline in self.config['baselines']:
                # compare NMI of isl_1hop against baseline across all seeds for final batch
                n_batches = len(all_results['isl_1hop'][0])
                if n_batches > 0:
                    isl_vals = [s[-1]['nmi_gt'] for s in all_results['isl_1hop'] if 'nmi_gt' in s[-1]]
                    bl_vals = [s[-1]['nmi_gt'] for s in all_results[bline] if 'nmi_gt' in s[-1]]
                    if isl_vals and bl_vals:
                        wilcoxon_tests[f'isl_1hop_vs_{bline}'] = self.eval_engine.run_wilcoxon_test(isl_vals, bl_vals)

        # Save
        self.save_results(all_results, 'results.json')
        self.save_results(aggregate, 'aggregate.json')
        self.save_results(wilcoxon_tests, 'wilcoxon_tests.json')

        metadata = {
            'config': self.config,
            'git_commit_hash': self.git_hash,
            'total_runtime_s': time.perf_counter() - t_start_total
        }
        self.save_results(metadata, 'metadata.json')

        return aggregate

    def _run_method_for_seed(self, method_name: str, seed: int, stream: list, initial_sigma: np.ndarray, G: ig.Graph, ground_truth: np.ndarray) -> list:
        results = []
        current_sigma = initial_sigma.copy()

        if method_name.startswith('isl_'):
            algo = ISLAlgorithm(self.config, method_name)
            algo.initialize(G, current_sigma)
            for batch in stream:
                res = algo.process_batch(batch['add'], batch['del'], batch['batch_idx'], ground_truth)
                # Compute nmi_gt
                gt_padded = np.pad(ground_truth, (0, max(0, len(algo.get_current_partition()) - len(ground_truth))), constant_values=0)
                res['nmi_gt'] = self.eval_engine.compute_nmi(algo.get_current_partition(), gt_padded[:len(algo.get_current_partition())])
                results.append(res)
        else:
            for batch in stream:
                # expand graph if needed
                max_v = max(max(u, v) for u, v in batch['add'] + batch['del']) if (batch['add'] or batch['del']) else -1
                if max_v >= G.vcount():
                    G.add_vertices(max_v - G.vcount() + 1)
                # apply graph edges
                G.add_edges(batch['add'])
                eids = []
                for u,v in batch['del']:
                    try: eids.append(G.get_eid(u,v))
                    except: pass
                if eids: G.delete_edges(eids)

                t0 = time.perf_counter()

                if method_name in ('static_surprise', 'static_significance'):
                    current_sigma, t_ms = run_static_significance(G, seed + batch['batch_idx'])
                elif method_name == 'static_leiden':
                    current_sigma, t_ms = run_static_leiden(G, seed + batch['batch_idx'])
                elif method_name == 'bfs_leiden':
                    affected = list(set([u for u,v in batch['add']+batch['del']] + [v for u,v in batch['add']+batch['del']]))
                    current_sigma, t_ms = run_bfs_leiden(G, current_sigma, affected, radius=1, seed=seed + batch['batch_idx'])
                elif method_name == 'no_update':
                    current_sigma = run_no_update(current_sigma)
                    t_ms = 0.0

                # Compute nmi_gt
                gt_padded = np.pad(ground_truth, (0, max(0, len(current_sigma) - len(ground_truth))), constant_values=0)
                nmi_gt = self.eval_engine.compute_nmi(current_sigma, gt_padded[:len(current_sigma)])

                # We need Q, S, community_count
                import leidenalg
                q = self.eval_engine.compute_modularity(G, current_sigma)
                part = leidenalg.SignificanceVertexPartition(G, initial_membership=current_sigma.tolist())
                s = part.quality()
                k = self.eval_engine.compute_community_count(current_sigma)

                results.append({
                    'batch_idx': batch['batch_idx'],
                    'algorithm': method_name,
                    'S': s,
                    'Q': q,
                    'time_ms': t_ms,
                    'community_count': k,
                    'nmi_gt': nmi_gt
                })

        return results

    def save_results(self, data: dict, filename: str):
        with open(os.path.join(self.output_dir, filename), 'w') as f:
            json.dump(data, f, indent=2)
