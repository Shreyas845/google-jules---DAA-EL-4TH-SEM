"""Service layer for the ISL dashboard backend.

This module is the bridge between the FastAPI routes (``main.py``) and the ISL research
library (``isl/``). It contains three responsibilities:

* **Experiments** — run the real :class:`isl.experiment_runner.ExperimentRunner` in a
  background thread with a small in-memory job registry (``JobStore``).
* **Graph trace** — drive the real :class:`isl.isl_algorithm.ISLAlgorithm` step by step on a
  small graph and capture a per-batch trace (positions, communities, affected set, moves) for
  the interactive Graph Viewer / Demo Mode. Nothing here is fabricated — every frame is produced
  by the actual algorithm.
* **Results & validations** — load stored experiment aggregates and committed validation JSON.

The research modules are imported lazily inside functions so the read-only parts of the API
(validations, stored results) still work even if the heavy scientific stack is not installed.
"""
from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import CONFIGS_DIR, RESULTS_DIR, VALIDATIONS_DIR, VALIDATION_RESULT_FILES

logger = logging.getLogger("isl.backend")


# ======================================================================================
# Job store (experiment execution)
# ======================================================================================
class JobStore:
    """Thread-safe in-memory registry of experiment jobs.

    A job dict looks like::

        {"status": "queued|running|completed|failed",
         "progress": 0..100, "message": str,
         "config_name": str, "results": dict | None, "error": str | None,
         "started_at": float, "finished_at": float | None}
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(self, config_name: str) -> str:
        job_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._jobs[job_id] = {
                "status": "queued",
                "progress": 0,
                "message": "Queued",
                "config_name": config_name,
                "results": None,
                "error": None,
                "started_at": time.time(),
                "finished_at": None,
            }
        return job_id

    def update(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(fields)

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def list(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [{"job_id": jid, **j} for jid, j in self._jobs.items()]


JOBS = JobStore()


def _config_path(config_name: str) -> Path:
    """Resolve a config name to a file under configs/, guarding against traversal."""
    candidate = (CONFIGS_DIR / config_name).resolve()
    if CONFIGS_DIR.resolve() not in candidate.parents:
        raise ValueError("Invalid config path")
    if not candidate.is_file():
        raise FileNotFoundError(f"Config not found: {config_name}")
    return candidate


def run_experiment_job(job_id: str, config_name: str) -> None:
    """Execute a real ExperimentRunner run in this (background) thread.

    Progress is coarse (queued -> running -> completed/failed) because the underlying runner
    is a single ``run()`` call; the live per-batch progress story is told by the graph-trace
    service instead. On success, the runner's ``aggregate.json`` is loaded into the job.
    """
    try:
        JOBS.update(job_id, status="running", progress=5, message="Loading configuration")
        cfg_path = _config_path(config_name)

        from isl.experiment_runner import ExperimentRunner  # lazy import (heavy deps)

        JOBS.update(job_id, progress=15, message="Running experiment (this may take a while)")
        logger.info("Job %s: starting ExperimentRunner on %s", job_id, config_name)

        runner = ExperimentRunner(str(cfg_path))
        aggregate = runner.run()

        # Prefer the aggregate the runner wrote to disk; fall back to the return value.
        out_dir = Path(runner.output_dir)
        agg_file = out_dir / "aggregate.json"
        results = aggregate
        if agg_file.is_file():
            with open(agg_file, "r", encoding="utf-8") as f:
                results = json.load(f)

        JOBS.update(
            job_id,
            status="completed",
            progress=100,
            message="Completed",
            results={"aggregate": results, "output_dir": str(out_dir)},
            finished_at=time.time(),
        )
        logger.info("Job %s: completed", job_id)
    except Exception as exc:  # noqa: BLE001 - surface any failure to the client
        logger.exception("Job %s failed", job_id)
        JOBS.update(
            job_id,
            status="failed",
            message="Failed",
            error=str(exc),
            finished_at=time.time(),
        )


def start_experiment(config_name: str) -> str:
    """Register a job and launch it on a daemon thread. Returns the job id."""
    job_id = JOBS.create(config_name)
    thread = threading.Thread(
        target=run_experiment_job, args=(job_id, config_name), daemon=True
    )
    thread.start()
    return job_id


# ======================================================================================
# Results & validations (read-only)
# ======================================================================================
def list_configs() -> List[Dict[str, Any]]:
    """List available experiment configs with a short summary."""
    configs = []
    for path in sorted(CONFIGS_DIR.glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        ds = data.get("dataset", {})
        configs.append(
            {
                "name": path.name,
                "experiment_id": data.get("experiment_id", path.stem),
                "dataset_type": ds.get("type", "?"),
                "n": ds.get("n"),
                "mu": ds.get("mu"),
                "num_batches": data.get("stream", {}).get("num_batches"),
                "seeds": len(data.get("seeds", [])),
                "baselines": data.get("baselines", []),
            }
        )
    return configs


def list_stored_results() -> List[str]:
    """Names of result sets already computed under results/."""
    if not RESULTS_DIR.is_dir():
        return []
    return sorted(
        p.name for p in RESULTS_DIR.iterdir() if p.is_dir() and (p / "aggregate.json").is_file()
    )


def load_stored_result(name: str) -> Optional[Dict[str, Any]]:
    """Load a stored aggregate.json (+ metadata) by result-set name."""
    base = (RESULTS_DIR / name).resolve()
    if RESULTS_DIR.resolve() not in base.parents:
        raise ValueError("Invalid result path")
    agg = base / "aggregate.json"
    if not agg.is_file():
        return None
    with open(agg, "r", encoding="utf-8") as f:
        aggregate = json.load(f)
    metadata = None
    meta_file = base / "metadata.json"
    if meta_file.is_file():
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    return {"name": name, "aggregate": aggregate, "metadata": metadata, "precomputed": True}


def load_validations() -> Dict[str, Any]:
    """Load the committed A/B/C validation result JSON."""
    out: Dict[str, Any] = {}
    for label, filename in VALIDATION_RESULT_FILES.items():
        path = VALIDATIONS_DIR / filename
        try:
            with open(path, "r", encoding="utf-8") as f:
                out[label] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            out[label] = None
    return out
