from __future__ import annotations

import httpx

from brainopt.models import WorkerScoreBatchRequest, WorkerScoreBatchResponse, WorkerScoreRequest


class WorkerClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def score_batch(self, candidates: list[WorkerScoreRequest]) -> WorkerScoreBatchResponse:
        payload = WorkerScoreBatchRequest(candidates=candidates)
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/score-batch", json=payload.model_dump())
            response.raise_for_status()
            data = response.json()
        return WorkerScoreBatchResponse.model_validate(data)
