"""Backend configuration and path resolution.

All filesystem paths are resolved relative to the repository root (the parent of this
``backend/`` package) so the server behaves identically no matter the current working
directory. This replaces the previous CWD-relative ``../validations`` paths.
"""
import sys
from pathlib import Path

# Repo root = parent of the backend/ directory.
REPO_ROOT = Path(__file__).resolve().parent.parent

# Ensure the repo root is importable so `import isl.*` works no matter where uvicorn is
# launched from (e.g. `cd backend && uvicorn main:app`).
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

VALIDATIONS_DIR = REPO_ROOT / "validations"
CONFIGS_DIR = REPO_ROOT / "configs"
RESULTS_DIR = REPO_ROOT / "results"

# CORS: permissive for local dev; tighten to explicit origins before any deployment.
ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# Validation result files exposed by the API, keyed by the label the frontend expects.
VALIDATION_RESULT_FILES = {
    "A": "validation_a_results.json",
    "B": "validation_b_significance_results.json",
    "C": "validation_c_significance_results.json",
}
