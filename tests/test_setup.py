import pytest
import os
import json

def test_imports():
    import igraph
    import leidenalg
    import numpy
    import sklearn
    import scipy
    import matplotlib

def test_versions():
    import igraph
    import leidenalg

    # Simple version check, ensure it's at least 0.10
    def version_tuple(v):
        return tuple(map(int, (v.split("."))))

    assert version_tuple(igraph.__version__) >= (0, 10)
    assert version_tuple(leidenalg.__version__) >= (0, 10)

def test_config_load():
    with open('configs/default_experiment.json', 'r') as f:
        config = json.load(f)
    assert config['experiment_id'] == 'default'
    assert 'seeds' in config
    assert len(config['seeds']) == 10

def test_directory_existence():
    required_dirs = [
        'isl', 'tests', 'configs', 'data/synthetic',
        'data/real', 'data/streams', 'results', 'figures'
    ]
    for d in required_dirs:
        assert os.path.isdir(d), f"Directory {d} does not exist"
