# Project Status — v1.0

_Single source of truth for what exists today._

## Project identity

**ISL — Incremental Significance-Leiden.** ISL incrementally maintains a
**Significance**-optimal community partition on dynamic graphs, processing only the nodes
affected by each batch of edge updates instead of recomputing from scratch.

> The project's early research used the **Surprise** objective under the working name
> "Incremental Surprise-Leiden". It settled on **Significance**. Any remaining "surprise" token
> in code is an internal variable/label alias, not a second objective.

## Component status — complete

| Component | Location | Status |
|-----------|----------|--------|
| Algorithm library | `isl/` | **Complete** |
| Experiment runner | `isl/experiment_runner.py` | **Complete** |
| Benchmark framework | `isl/benchmark.py` | **Working** (see limitations) |
| Evaluation engine | `isl/evaluation.py` | **Complete** |
| Validation scripts + artifacts | `validations/` | **Complete** |
| Tests | `tests/` | **Present** (pytest) |
| Backend API | `backend/` | **Complete** — all endpoints call real code |
| Frontend dashboard | `frontend/` | **Complete** — full narrative + interactive + data views |

## Backend endpoints (all real)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | Liveness check |
| `GET /api/validations` | Committed A/B/C validation JSON |
| `GET /api/images/{name}` | Committed validation plots (path-traversal safe) |
| `GET /api/configs` | Available experiment configs |
| `GET /api/results` · `GET /api/results/{name}` | Stored experiment aggregates |
| `POST /api/experiment/run` · `GET /api/experiment/status/{id}` | Run the real `ExperimentRunner` as a background job; poll for progress |
| `GET /api/graph/trace` | Real step-by-step `ISLAlgorithm` execution trace for the Graph Viewer / Demo Mode |

The backend imports the `isl/` library directly — it never reimplements the science. Experiment
execution runs on a background thread with an in-memory job registry; progress is polled
(WebSockets were deliberately avoided as unnecessary complexity). The graph trace runs the actual
algorithm on a small graph, so every node position, community, affected set and metric it returns
is genuine.

## Frontend (React + TypeScript)

A guided research-presentation platform. Pages, grouped as a narrative:

- **The Story** — Home, Problem, Motivation, ISL Overview, Algorithm Workflow
- **See It Work** — Graph Viewer (interactive, zoom/pan/tooltips/playback), Demo Mode (auto-presented)
- **Evidence** — Experiments (run real jobs), Validation (A/B/C with honest outcomes), Results (charts from real aggregates)
- **Engineering** — Architecture, Future Scope

Light/dark themed, responsive, with **Presenter Notes** and **What/Why/Takeaway** explanation
panels on every major page for faculty demonstration.

## Known algorithm-library limitations (intentional, documented)

- `benchmark.generate_update_stream` emits **insertions only** (no edge deletions).
- `benchmark.load_snap_dataset` is simplistic (ignores timestamps; dummy graph if file missing).
- `visualization.figure_6_parameter_sensitivity` is a placeholder; figures 1 and 7 plot
  single-experiment (not multi-µ) data.

These are surfaced on the dashboard's **Future Scope** page rather than hidden.

## Reference results

From a completed run of the pipeline (default LFR configuration):

| Method | NMI (mean) | Time (ms) |
|--------|------------|-----------|
| ISL-1hop | 0.7710 | 7.26 |
| Static Leiden | 0.9835 | 5.80 |

`results/smoke_test/` ships as a small, real precomputed result set the Results page reads.

## Reproducibility

Runs are seed-driven; streams and initial partitions are cached under `output_dir/streams/` and
reused per seed, so repeated runs replicate structurally.
