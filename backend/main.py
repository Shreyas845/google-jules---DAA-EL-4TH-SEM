from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExperimentConfig(BaseModel):
    n: int
    mu: float
    min_community: int
    max_community: int
    algorithm: str

@app.get("/api/validations")
def get_validations():
    validations = {}

    # Validation A
    try:
        with open("../validations/validation_a_results.json") as f:
            validations['A'] = json.load(f)
    except:
        validations['A'] = None

    # Validation B
    try:
        with open("../validations/validation_b_significance_results.json") as f:
            validations['B'] = json.load(f)
    except:
        validations['B'] = None

    # Validation C
    try:
        with open("../validations/validation_c_significance_results.json") as f:
            validations['C'] = json.load(f)
    except:
        validations['C'] = None

    return validations

@app.get("/api/images/{image_name}")
def get_image(image_name: str):
    image_path = os.path.join("../validations", image_name)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    return {"error": "Image not found"}

@app.post("/api/experiment/run")
def run_experiment(config: ExperimentConfig):
    # Mocking endpoint for experiment
    return {"status": "success", "message": "Experiment started", "job_id": "job_12345"}

@app.get("/api/experiment/status/{job_id}")
def get_experiment_status(job_id: str):
    # Mocking status endpoint
    return {
        "job_id": job_id,
        "status": "completed",
        "progress": 100,
        "results": {
            "nmi": 0.95,
            "time_ms": 350
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
