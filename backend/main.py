"""ISL Dashboard backend (FastAPI).

Bridges the React dashboard to the ISL research library. All endpoints call real code:

* ``/api/validations`` + ``/api/images/{name}`` — serve committed validation artifacts.
* ``/api/configs`` — list available experiment configs.
* ``/api/results`` + ``/api/results/{name}`` — expose stored experiment aggregates.
* ``/api/experiment/run`` + ``/api/experiment/status/{id}`` — run the real ExperimentRunner in
  a background thread with a job registry (progress via polling).
* ``/api/graph/trace`` — run the real ISLAlgorithm step-by-step and return an animation trace.

See ``docs/STATUS.md`` and ``backend/services.py`` / ``backend/graph_trace.py``.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import services
from config import ALLOWED_ORIGINS, VALIDATIONS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("isl.backend")

app = FastAPI(title="ISL Dashboard API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------------------
class ExperimentRequest(BaseModel):
    """Launch request: pick a stored config by name (the safe, reproducible surface)."""
    config_name: str = "smoke_test.json"


# --------------------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------------------
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "isl-dashboard", "version": "1.0"}


# --------------------------------------------------------------------------------------
# Validation artifacts
# --------------------------------------------------------------------------------------
@app.get("/api/validations")
def get_validations() -> dict:
    """Return committed validation result JSON for A/B/C (or ``None`` if absent)."""
    return services.load_validations()


@app.get("/api/images/{image_name}")
def get_image(image_name: str):
    """Serve a committed validation plot, safely confined to ``validations/``."""
    candidate = (VALIDATIONS_DIR / image_name).resolve()
    if VALIDATIONS_DIR.resolve() not in candidate.parents:
        raise HTTPException(status_code=400, detail="Invalid image path")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(candidate)


# --------------------------------------------------------------------------------------
# Configs & stored results
# --------------------------------------------------------------------------------------
@app.get("/api/configs")
def get_configs() -> dict:
    return {"configs": services.list_configs()}


@app.get("/api/results")
def get_results() -> dict:
    """List result sets already computed on disk."""
    return {"results": services.list_stored_results()}


@app.get("/api/results/{name}")
def get_result(name: str) -> dict:
    try:
        result = services.load_stored_result(name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid result name")
    if result is None:
        raise HTTPException(status_code=404, detail="Result set not found")
    return result


# --------------------------------------------------------------------------------------
# Experiment execution (real, background thread + polling)
# --------------------------------------------------------------------------------------
@app.post("/api/experiment/run")
def run_experiment(req: ExperimentRequest) -> dict:
    """Launch a real experiment run. Poll ``/api/experiment/status/{job_id}`` for progress."""
    try:
        services._config_path(req.config_name)  # validate up front for a clean 400
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    job_id = services.start_experiment(req.config_name)
    logger.info("Launched experiment job %s (%s)", job_id, req.config_name)
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/experiment/status/{job_id}")
def experiment_status(job_id: str) -> dict:
    job = services.JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return {"job_id": job_id, **job}


@app.get("/api/experiment/jobs")
def experiment_jobs() -> dict:
    return {"jobs": services.JOBS.list()}


# --------------------------------------------------------------------------------------
# Interactive graph trace (real ISL step-by-step execution)
# --------------------------------------------------------------------------------------
@app.get("/api/graph/trace")
def graph_trace(
    n: int = Query(60, ge=20, le=150),
    batches: int = Query(8, ge=1, le=25),
    batch_size: int = Query(3, ge=1, le=10),
    mu: float = Query(0.15, ge=0.0, le=0.6),
    seed: int = Query(42),
    variant: str = Query("isl_1hop"),
) -> dict:
    """Compute and return a real ISL execution trace for the Graph Viewer / Demo Mode."""
    from graph_trace import generate_trace

    try:
        return generate_trace(
            n=n, num_batches=batches, batch_size=batch_size,
            mu=mu, seed=seed, variant=variant,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("graph trace failed")
        raise HTTPException(status_code=500, detail=f"Trace generation failed: {exc}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
