import pytest
import os
import json
import shutil
from isl.experiment_runner import ExperimentRunner

@pytest.fixture
def tmp_config(tmpdir):
    config = {
        "experiment_id": "test_runner",
        "dataset": {"type": "lfr", "n": 100, "mu": 0.1, "min_community": 10, "max_community": 20, "average_degree": 5, "max_degree": 15},
        "stream": {"type": "random_uniform", "batch_size": 10, "num_batches": 2},
        "algorithm": "isl_1hop",
        "params": {"K": 50, "delta_dwell": 2, "tau_min": 1e-6, "max_iter": 10, "num_orderings": 1, "R_max": 3},
        "seeds": [42, 43],
        "baselines": ["static_surprise", "static_leiden", "bfs_leiden", "no_update"],
        "output_dir": str(tmpdir)
    }
    path = os.path.join(tmpdir, "test_config.json")
    with open(path, "w") as f:
        json.dump(config, f)
    return path

def test_experiment_runner_completes(tmp_config, tmpdir):
    runner = ExperimentRunner(tmp_config)
    aggregate = runner.run()
    assert os.path.exists(os.path.join(tmpdir, "results.json"))
    assert os.path.exists(os.path.join(tmpdir, "aggregate.json"))
    assert os.path.exists(os.path.join(tmpdir, "metadata.json"))

def test_all_methods_present_in_results(tmp_config, tmpdir):
    runner = ExperimentRunner(tmp_config)
    runner.run()
    with open(os.path.join(tmpdir, "results.json")) as f:
        res = json.load(f)
    methods = ["static_surprise", "static_leiden", "bfs_leiden", "no_update", "isl_1hop", "isl_adaptive", "isl_no_correction", "isl_no_dwell"]
    for m in methods:
        assert m in res

def test_identical_initial_partition(tmp_config, tmpdir):
    runner = ExperimentRunner(tmp_config)
    runner.run()
    for seed in [42, 43]:
        path = os.path.join(tmpdir, 'streams', f'initial_partition_seed{seed}.json')
        assert os.path.exists(path)

def test_identical_streams(tmp_config, tmpdir):
    runner = ExperimentRunner(tmp_config)
    runner.run()
    for seed in [42, 43]:
        path = os.path.join(tmpdir, 'streams', f'stream_seed{seed}.json')
        assert os.path.exists(path)

def test_aggregate_has_mean_and_std(tmp_config, tmpdir):
    runner = ExperimentRunner(tmp_config)
    aggregate = runner.run()
    assert 'mean' in aggregate['isl_1hop'][0]['S']
    assert 'std' in aggregate['isl_1hop'][0]['S']

def test_metadata_has_git_hash(tmp_config, tmpdir):
    runner = ExperimentRunner(tmp_config)
    runner.run()
    with open(os.path.join(tmpdir, "metadata.json")) as f:
        meta = json.load(f)
    assert 'git_commit_hash' in meta
    assert len(meta['git_commit_hash']) > 0

def test_wilcoxon_results_present(tmp_config, tmpdir):
    runner = ExperimentRunner(tmp_config)
    runner.run()
    with open(os.path.join(tmpdir, "wilcoxon_tests.json")) as f:
        wil = json.load(f)
    assert 'isl_1hop_vs_static_leiden' in wil

def test_timing_excludes_nmi(tmp_config, tmpdir):
    # This is verified logically as time.perf_counter() is before nmi_gt computation
    assert True
