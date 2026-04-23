from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_PATH = ROOT / "packages" / "schemas"
for path in (str(ROOT), str(SCHEMAS_PATH)):
    if path not in sys.path:
        sys.path.append(path)

from brainopt.models import WorkerScoreBatchRequest, WorkerScoreBatchResponse, WorkerScoreRequest, WorkerScoreResponse

from .config import WorkerSettings
from .tribe_runtime import TribeRuntime

settings = WorkerSettings()
runtime = TribeRuntime(settings)
app = FastAPI(title=settings.app_name)
logger = logging.getLogger(__name__)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.post("/score-candidate", response_model=WorkerScoreResponse)
def score_candidate(payload: WorkerScoreRequest) -> WorkerScoreResponse:
    try:
        return runtime.score_candidate(payload)
    except Exception as exc:
        logger.exception("Candidate scoring failed for %s", payload.candidate_id)
        raise HTTPException(status_code=500, detail=f"Failed to score candidate: {exc}") from exc


@app.post("/score-batch", response_model=WorkerScoreBatchResponse)
def score_batch(payload: WorkerScoreBatchRequest) -> WorkerScoreBatchResponse:
    if len(payload.candidates) > settings.worker_max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size {len(payload.candidates)} exceeds worker_max_batch_size={settings.worker_max_batch_size}",
        )
    items: list[WorkerScoreResponse] = []
    for candidate in payload.candidates:
        items.append(score_candidate(candidate))
    return WorkerScoreBatchResponse(items=items)
