# ISL: Incremental Significance-Leiden

This repository contains the Python implementation of the Incremental Significance-Leiden (ISL) algorithm.
The algorithm maintains optimal community partitions on dynamic graphs using the Significance objective function.

## Environment Setup
Create the environment and install dependencies:
```bash
pip install -r requirements.txt
```
Or using conda:
```bash
conda env create -f environment.yml
conda activate isl
```

## Reproduction
To run the default experiment:
```bash
python -m isl.experiment_runner configs/default_experiment.json
```
