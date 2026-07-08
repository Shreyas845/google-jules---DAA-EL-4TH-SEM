# ISL — Incremental Significance-Leiden

ISL incrementally maintains a **Significance**-optimal community partition on **dynamic
graphs**. Instead of re-running community detection from scratch after every change, ISL
reprocesses only the nodes *affected* by each batch of edge updates — giving fast, stable
partitions that (unlike modularity-based methods) are not blind to small communities.

The repository contains the ISL algorithm library, an experiment/benchmark/evaluation
pipeline, a validation suite, a FastAPI backend, and a React dashboard that presents the whole
research story interactively.

> **Status: v1.0 — complete.** The algorithm, pipeline, and validation suite are runnable, and
> the dashboard is a full research-presentation platform: a guided narrative (Problem →
> Motivation → ISL → Workflow), an **interactive Graph Viewer** and one-click **Demo Mode** that
> animate real ISL runs, live **Experiments**, and **Validation**/**Results** views driven by
> real data. Every dashboard number comes from the real `isl/` library. See
> [`docs/STATUS.md`](docs/STATUS.md) for the component-by-component breakdown.

## Repository layout

```
isl/            # ISL algorithm + experiment runner, benchmark, evaluation, visualization
tests/          # pytest suite
configs/        # experiment configs (default_experiment.json, smoke_test.json)
validations/    # validation scripts + committed results (JSON) and plots (PNG)
backend/        # FastAPI API (main.py, services.py, graph_trace.py, config.py)
frontend/       # React + TypeScript dashboard (src/api.ts, components/, pages/)
docs/           # blueprint + STATUS.md; docs/research/ = historical research notes
```

The dashboard is organized as a guided narrative: **Home → Problem → Motivation → ISL Overview
→ Workflow → Graph Viewer → Demo Mode → Experiments → Validation → Results → Architecture →
Future Scope**. Every value it displays comes from the real `isl/` library.

## 1. Install

Python (from the repo root):

```bash
pip install -r requirements.txt          # ISL library
pip install -r backend/requirements.txt  # backend (also pulls the ISL deps)
```

Or with conda: `conda env create -f environment.yml && conda activate isl`.

Frontend:

```bash
cd frontend && npm install
```

## 2. Run the dashboard

Both servers at once (Git Bash / Linux / macOS):

```bash
./run_dashboard.sh      # backend :8000, frontend :3000
```

Or run them separately:

```bash
# Backend  (serves artifacts, runs experiments, generates live ISL graph traces)
cd backend && uvicorn main:app --host 127.0.0.1 --port 8000

# Frontend (in another terminal)
cd frontend && npm start
```

Open http://localhost:3000. The API base URL can be overridden with `REACT_APP_API_URL`.

## 3. Run experiments

```bash
python -m isl.experiment_runner configs/smoke_test.json         # fast smoke run
python -m isl.experiment_runner configs/default_experiment.json # full 5000-node run
```

Results (JSON) and any figures are written to the config's `output_dir` (e.g.
`results/<experiment_id>/`).

## 4. Run validations

```bash
python validations/run_validation_a.py
python validations/run_validation_b.py
python validations/run_validation_c.py
```

Each writes its results JSON, a Markdown report, and plots into `validations/`. These committed
artifacts are what the dashboard's Validations view displays.

## 5. Run tests

```bash
pytest
```

## More detail

- [`docs/STATUS.md`](docs/STATUS.md) — component-by-component status and remaining backend work
- [`docs/final_master_blueprint.md`](docs/final_master_blueprint.md) — algorithm & experiment design
- [`docs/research/`](docs/research/) — historical research notes (preserved for provenance)
