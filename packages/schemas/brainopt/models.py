from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Constraints(BaseModel):
    max_chars: int | None = Field(default=None, ge=1)
    include_cta: bool = True
    hashtag_limit: int | None = Field(default=None, ge=0)
    hard_max_length: int | None = Field(default=None, ge=1)


class CandidateNotes(BaseModel):
    hook: str = ""
    cta: str = ""
    audience_angle: str = ""


class CandidateVariant(BaseModel):
    id: str
    strategy: str
    tone: str
    text: str
    notes: CandidateNotes = Field(default_factory=CandidateNotes)


class CandidateBatch(BaseModel):
    platform: str
    variants: list[CandidateVariant]


class WorkerScoreRequest(BaseModel):
    candidate_id: str
    platform: str
    text: str
    strategy: str = ""
    tone: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class RawFeatures(BaseModel):
    raw_shape_t: int
    raw_shape_v: int
    global_mean: float
    global_peak: float
    global_std: float
    early_mean: float
    mid_mean: float
    late_mean: float
    dropoff: float
    sustainability: float
    spikiness: float
    variance_over_time: float
    peak_time: int


class SentenceFeature(BaseModel):
    sentence_index: int
    text: str
    start_t: int
    end_t: int
    mean_energy: float
    peak_energy: float
    relative_contribution: float


class WorkerScoreResponse(BaseModel):
    candidate_id: str
    platform: str
    text: str
    raw_features: RawFeatures
    temporal_energy: list[float]
    sentence_features: list[SentenceFeature] = Field(default_factory=list)
    segments: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkerScoreBatchRequest(BaseModel):
    candidates: list[WorkerScoreRequest]


class WorkerScoreBatchResponse(BaseModel):
    items: list[WorkerScoreResponse]


class RankedScores(BaseModel):
    brainscore: float
    hook_score: float
    sustained_response_score: float
    clarity_stability_score: float
    end_strength_score: float
    novelty_spike_score: float
    platform_fit_score: float
    readability_score: float
    constraint_compliance_score: float
    final_score: float


class CandidateDiagnostics(BaseModel):
    strongest_sentence: int | None = None
    weakest_sentence: int | None = None
    dropoff_after_sentence: int | None = None


class RankedCandidate(BaseModel):
    id: str
    strategy: str
    tone: str
    text: str
    scores: RankedScores
    diagnostics: CandidateDiagnostics
    reason: str
    raw_features: RawFeatures
    sentence_features: list[SentenceFeature] = Field(default_factory=list)
    temporal_energy: list[float] = Field(default_factory=list)


class OptimizeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    topic: str
    source_material: str = ""
    platform: Literal["twitter", "x", "linkedin", "instagram", "threads", "general"] = "general"
    audience: str
    goal: str
    tone: str
    constraints: Constraints = Field(default_factory=Constraints)
    candidate_count: int = Field(default=8, ge=2, le=20)
    refine_winner: bool = True


class ScoreOnlyRequest(BaseModel):
    platform: str
    tone: str = ""
    constraints: Constraints = Field(default_factory=Constraints)
    candidates: list[CandidateVariant]


class ScoreOnlyResponse(BaseModel):
    run_id: str
    platform: str
    candidates: list[RankedCandidate]
    recommended_candidate_id: str
    winner_text: str
    explanation: str
    llm_model: str
    log_file_path: str | None = None
    experimental_score: bool = True


class RefineRequest(BaseModel):
    platform: Literal["twitter", "x", "linkedin", "instagram", "threads", "general"] = "general"
    tone: str = ""
    constraints: Constraints = Field(default_factory=Constraints)
    text: str
    refinement_goal: str = ""


class RefineResponse(BaseModel):
    final_text: str
    explanation: str
    llm_model: str
    log_file_path: str | None = None


class OptimizeResponse(BaseModel):
    run_id: str
    platform: str
    candidates: list[RankedCandidate]
    recommended_candidate_id: str
    winner_text: str
    explanation: str
    llm_model: str
    log_file_path: str | None = None
    experimental_score: bool = True
