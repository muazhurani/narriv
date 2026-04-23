from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_PATH = ROOT / "packages" / "schemas"
SCORING_PATH = ROOT / "packages" / "scoring"
for path in (str(ROOT), str(SCHEMAS_PATH), str(SCORING_PATH)):
    if path not in sys.path:
        sys.path.append(path)

from brainopt.models import (
    CandidateBatch,
    OptimizeRequest,
    OptimizeResponse,
    RefineRequest,
    RefineResponse,
    ScoreOnlyRequest,
    ScoreOnlyResponse,
    WorkerScoreRequest,
)
from brainopt_scoring import rank_candidates

from .config import ApiSettings
from .llm_provider import LLMProvider, LLMRateLimitError, MockProvider, OpenAIProvider
from .log_exporter import write_optimize_log, write_refine_log, write_score_log
from .worker_client import WorkerClient

settings = ApiSettings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
worker_client = WorkerClient(base_url=settings.worker_url, timeout_seconds=settings.request_timeout_seconds)


def build_provider() -> LLMProvider:
    if settings.use_mock_llm or not settings.openai_api_key:
        return MockProvider()
    return OpenAIProvider(
        api_key=settings.openai_api_key,
        model_name=settings.openai_model,
        fallback_model=settings.openai_fallback_model,
        api_base=settings.openai_api_base,
        reasoning_effort=settings.openai_reasoning_effort,
        max_retries=settings.openai_max_retries,
        timeout_seconds=settings.request_timeout_seconds,
    )


llm_provider = build_provider()


def _generation_error(exc: Exception) -> HTTPException:
    if isinstance(exc, LLMRateLimitError):
        return HTTPException(status_code=429, detail=f"Generation rate-limited: {exc}")
    return HTTPException(status_code=500, detail=f"Generation failed: {exc}")


def _refinement_error(exc: Exception) -> HTTPException:
    if isinstance(exc, LLMRateLimitError):
        return HTTPException(status_code=429, detail=f"Refinement rate-limited: {exc}")
    return HTTPException(status_code=500, detail=f"Refinement failed: {exc}")


async def _rank_score_request(
    payload: ScoreOnlyRequest,
) -> tuple[str, list]:
    run_id = f"run_{uuid4().hex[:10]}"
    requests = [
        WorkerScoreRequest(
            candidate_id=item.id,
            platform=payload.platform,
            text=item.text,
            strategy=item.strategy,
            tone=item.tone,
        )
        for item in payload.candidates
    ]
    try:
        batch_result = await worker_client.score_batch(requests)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Worker scoring failed: {exc}") from exc

    ranked = rank_candidates(
        candidates=payload.candidates,
        scores=batch_result.items,
        platform=payload.platform,
        constraints=payload.constraints,
    )
    if not ranked:
        raise HTTPException(status_code=500, detail="No candidates were ranked.")
    return run_id, ranked


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.post("/optimize/generate", response_model=CandidateBatch)
async def generate_only(payload: OptimizeRequest) -> CandidateBatch:
    try:
        return await llm_provider.generate_variants(payload)
    except Exception as exc:
        raise _generation_error(exc) from exc


@app.post("/optimize/score", response_model=ScoreOnlyResponse)
async def score_only(payload: ScoreOnlyRequest) -> ScoreOnlyResponse:
    run_id, ranked = await _rank_score_request(payload)
    winner = ranked[0]
    try:
        explanation = await llm_provider.explain_score_only(
            platform=payload.platform,
            tone=payload.tone,
            ranked_candidates=ranked,
        )
    except Exception:
        explanation = winner.reason

    log_file_path = None
    try:
        log_file_path = str(
            write_score_log(
                logs_dir=settings.optimize_logs_dir,
                run_id=run_id,
                request=payload,
                llm_model=llm_provider.model_name,
                candidates=ranked,
                recommended_candidate_id=winner.id,
                winner_text=winner.text,
                explanation=explanation,
            )
        )
    except Exception:
        log_file_path = None

    return ScoreOnlyResponse(
        run_id=run_id,
        platform=payload.platform,
        candidates=ranked,
        recommended_candidate_id=ranked[0].id,
        winner_text=winner.text,
        explanation=explanation,
        llm_model=llm_provider.model_name,
        log_file_path=log_file_path,
        experimental_score=True,
    )


@app.post("/optimize", response_model=OptimizeResponse)
async def optimize(payload: OptimizeRequest) -> OptimizeResponse:
    run_id = f"run_{uuid4().hex[:10]}"
    try:
        generated = await llm_provider.generate_variants(payload)
    except Exception as exc:
        raise _generation_error(exc) from exc

    score_request = ScoreOnlyRequest(
        platform=payload.platform,
        tone=payload.tone,
        constraints=payload.constraints,
        candidates=generated.variants,
    )
    _, ranked_candidates = await _rank_score_request(score_request)
    winner = ranked_candidates[0]

    try:
        explanation = await llm_provider.explain_ranking(payload, ranked_candidates)
    except Exception:
        explanation = winner.reason

    winner_text = winner.text
    if payload.refine_winner:
        try:
            winner_text = await llm_provider.refine_winner(payload, winner)
        except Exception:
            winner_text = winner.text

    log_file_path = None
    try:
        log_file_path = str(
            write_optimize_log(
                logs_dir=settings.optimize_logs_dir,
                run_id=run_id,
                request=payload,
                llm_model=llm_provider.model_name,
                candidates=ranked_candidates,
                recommended_candidate_id=winner.id,
                winner_text=winner_text,
                explanation=explanation,
                generated_variants=generated.variants,
            )
        )
    except Exception:
        log_file_path = None

    return OptimizeResponse(
        run_id=run_id,
        platform=payload.platform,
        candidates=ranked_candidates,
        recommended_candidate_id=winner.id,
        winner_text=winner_text,
        explanation=explanation,
        llm_model=llm_provider.model_name,
        log_file_path=log_file_path,
        experimental_score=True,
    )


@app.post("/refine", response_model=RefineResponse)
async def refine(payload: RefineRequest) -> RefineResponse:
    run_id = f"run_{uuid4().hex[:10]}"
    try:
        final_text = await llm_provider.refine_text(payload)
    except Exception as exc:
        raise _refinement_error(exc) from exc

    explanation = (
        f"Refined for goal: {payload.refinement_goal}."
        if payload.refinement_goal
        else "Refined to improve clarity and flow while preserving the original claim."
    )
    log_file_path = None
    try:
        log_file_path = str(
            write_refine_log(
                logs_dir=settings.optimize_logs_dir,
                run_id=run_id,
                request=payload,
                llm_model=llm_provider.model_name,
                final_text=final_text,
                explanation=explanation,
            )
        )
    except Exception:
        log_file_path = None

    return RefineResponse(
        final_text=final_text,
        explanation=explanation,
        llm_model=llm_provider.model_name,
        log_file_path=log_file_path,
    )
