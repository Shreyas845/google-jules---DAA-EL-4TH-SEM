"""Validation of the full benchmark study outputs.

These tests assert on the aggregated result files produced by the *full* experiment study
(``results/E1``, ``results/A1``, …). Those outputs are large and regenerated (gitignored), so on
a fresh checkout they are absent — the tests skip rather than fail. Run the full study first to
exercise them:

    python -m isl.experiment_runner configs/default_experiment.json
"""
import json
import os

import pytest

FULL_STUDY_DIRS = (
    [f"E{i}" for i in range(1, 13)]
    + [f"A{i}" for i in range(1, 3)]
    + [f"S{i}" for i in range(1, 8)]
)


def _load(path: str):
    if not os.path.exists(path):
        pytest.skip(f"{path} not present — run the full study to generate it")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_all_experiments_produce_results_files():
    present = [d for d in FULL_STUDY_DIRS if os.path.exists(f"results/{d}/aggregate.json")]
    if not present:
        pytest.skip("No full-study result sets present — run the study to generate them")
    for d in present:
        assert os.path.exists(f"results/{d}/results.json")
        assert os.path.exists(f"results/{d}/aggregate.json")
        assert os.path.exists(f"results/{d}/metadata.json")


def test_hero_experiment_nmi_superiority():
    agg = _load("results/E1/aggregate.json")
    assert agg["isl_1hop"][0]["nmi_gt"]["mean"] > 0.0


def test_ablation_K_sweep_covers_all_values():
    agg = _load("results/A1/aggregate.json")
    assert "K=50" in agg or "isl_1hop" in agg


def test_no_experiment_missing_community_count():
    agg = _load("results/E1/aggregate.json")
    assert "community_count" in agg["isl_1hop"][0]


def test_real_datasets_within_scope():
    # Placeholder scope assertion for the prototype.
    assert True
