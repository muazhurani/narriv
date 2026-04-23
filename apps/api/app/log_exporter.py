from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from brainopt.models import (
    CandidateVariant,
    OptimizeRequest,
    RankedCandidate,
    RefineRequest,
    ScoreOnlyRequest,
)


def _format_section(title: str) -> str:
    return f"{title}\n{'=' * len(title)}\n"


def _format_key_values(values: dict[str, object]) -> str:
    lines = []
    for key, value in values.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n"


def _format_candidate(
    candidate: RankedCandidate,
    variant_lookup: dict[str, CandidateVariant],
    rank_index: int,
) -> str:
    source = variant_lookup.get(candidate.id)
    notes = source.notes if source is not None else None
    sentence_lines = []
    for sentence in candidate.sentence_features:
        sentence_lines.append(
            "  - "
            f"[{sentence.sentence_index}] mean={sentence.mean_energy:.4f} "
            f"peak={sentence.peak_energy:.4f} share={sentence.relative_contribution:.4f} "
            f"t={sentence.start_t}-{sentence.end_t} :: {sentence.text}"
        )
    if not sentence_lines:
        sentence_lines.append("  - none")

    temporal_preview = ", ".join(f"{value:.4f}" for value in candidate.temporal_energy[:20])
    if len(candidate.temporal_energy) > 20:
        temporal_preview += ", ..."

    candidate_text = [
        _format_section(f"Candidate #{rank_index}: {candidate.id}"),
        _format_key_values(
            {
                "strategy": candidate.strategy,
                "tone": candidate.tone,
                "final_score": f"{candidate.scores.final_score:.4f}",
                "brainscore": f"{candidate.scores.brainscore:.4f}",
                "hook_score": f"{candidate.scores.hook_score:.4f}",
                "sustained_response_score": f"{candidate.scores.sustained_response_score:.4f}",
                "clarity_stability_score": f"{candidate.scores.clarity_stability_score:.4f}",
                "end_strength_score": f"{candidate.scores.end_strength_score:.4f}",
                "novelty_spike_score": f"{candidate.scores.novelty_spike_score:.4f}",
                "platform_fit_score": f"{candidate.scores.platform_fit_score:.4f}",
                "readability_score": f"{candidate.scores.readability_score:.4f}",
                "constraint_compliance_score": f"{candidate.scores.constraint_compliance_score:.4f}",
                "strongest_sentence": candidate.diagnostics.strongest_sentence,
                "weakest_sentence": candidate.diagnostics.weakest_sentence,
                "dropoff_after_sentence": candidate.diagnostics.dropoff_after_sentence,
                "global_mean": f"{candidate.raw_features.global_mean:.4f}",
                "global_peak": f"{candidate.raw_features.global_peak:.4f}",
                "global_std": f"{candidate.raw_features.global_std:.4f}",
                "early_mean": f"{candidate.raw_features.early_mean:.4f}",
                "mid_mean": f"{candidate.raw_features.mid_mean:.4f}",
                "late_mean": f"{candidate.raw_features.late_mean:.4f}",
                "dropoff": f"{candidate.raw_features.dropoff:.4f}",
                "sustainability": f"{candidate.raw_features.sustainability:.4f}",
                "spikiness": f"{candidate.raw_features.spikiness:.4f}",
                "variance_over_time": f"{candidate.raw_features.variance_over_time:.4f}",
                "peak_time": candidate.raw_features.peak_time,
            }
        ),
        "reason:\n"
        f"{candidate.reason}\n",
        "text:\n"
        f"{candidate.text}\n",
    ]
    if notes is not None:
        candidate_text.append(
            "generation_notes:\n"
            f"hook: {notes.hook}\n"
            f"cta: {notes.cta}\n"
            f"audience_angle: {notes.audience_angle}\n"
        )
    candidate_text.append("sentence_features:\n" + "\n".join(sentence_lines) + "\n")
    candidate_text.append("temporal_energy_preview:\n" + temporal_preview + "\n")
    return "\n".join(candidate_text)


def write_optimize_log(
    logs_dir: str | Path,
    run_id: str,
    request: OptimizeRequest,
    llm_model: str,
    candidates: list[RankedCandidate],
    recommended_candidate_id: str,
    winner_text: str,
    explanation: str,
    generated_variants: list[CandidateVariant],
) -> Path:
    output_dir = Path(logs_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{run_id}.txt"
    variant_lookup = {variant.id: variant for variant in generated_variants}

    chunks = [
        _format_section("Run Summary"),
        _format_key_values(
            {
                "run_id": run_id,
                "created_at_utc": datetime.now(UTC).isoformat(),
                "platform": request.platform,
                "topic": request.topic,
                "source_material_present": bool(request.source_material.strip()),
                "source_material_chars": len(request.source_material),
                "audience": request.audience,
                "goal": request.goal,
                "tone": request.tone,
                "candidate_count": request.candidate_count,
                "refine_winner": request.refine_winner,
                "llm_model": llm_model,
                "recommended_candidate_id": recommended_candidate_id,
            }
        ),
        _format_section("Constraints"),
        _format_key_values(request.constraints.model_dump()),
        _format_section("Source Material"),
        f"{request.source_material or '[none]'}\n\n",
        _format_section("Winner"),
        f"winner_text:\n{winner_text}\n\n",
        "explanation:\n"
        f"{explanation}\n\n",
        _format_section("Candidates"),
    ]

    for rank_index, candidate in enumerate(candidates, start=1):
        chunks.append(_format_candidate(candidate, variant_lookup=variant_lookup, rank_index=rank_index))

    path.write_text("\n".join(chunks), encoding="utf-8")
    return path.resolve()


def write_score_log(
    logs_dir: str | Path,
    run_id: str,
    request: ScoreOnlyRequest,
    llm_model: str,
    candidates: list[RankedCandidate],
    recommended_candidate_id: str,
    winner_text: str,
    explanation: str,
) -> Path:
    output_dir = Path(logs_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{run_id}.txt"
    variant_lookup = {variant.id: variant for variant in request.candidates}

    chunks = [
        _format_section("Run Summary"),
        _format_key_values(
            {
                "run_id": run_id,
                "created_at_utc": datetime.now(UTC).isoformat(),
                "platform": request.platform,
                "tone": request.tone,
                "candidate_count": len(request.candidates),
                "llm_model": llm_model,
                "recommended_candidate_id": recommended_candidate_id,
                "run_mode": "score_only",
            }
        ),
        _format_section("Constraints"),
        _format_key_values(request.constraints.model_dump()),
        _format_section("Winner"),
        f"winner_text:\n{winner_text}\n\n",
        "explanation:\n"
        f"{explanation}\n\n",
        _format_section("Candidates"),
    ]

    for rank_index, candidate in enumerate(candidates, start=1):
        chunks.append(
            _format_candidate(candidate, variant_lookup=variant_lookup, rank_index=rank_index)
        )

    path.write_text("\n".join(chunks), encoding="utf-8")
    return path.resolve()


def write_refine_log(
    logs_dir: str | Path,
    run_id: str,
    request: RefineRequest,
    llm_model: str,
    final_text: str,
    explanation: str,
) -> Path:
    output_dir = Path(logs_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{run_id}.txt"

    chunks = [
        _format_section("Run Summary"),
        _format_key_values(
            {
                "run_id": run_id,
                "created_at_utc": datetime.now(UTC).isoformat(),
                "platform": request.platform,
                "tone": request.tone,
                "llm_model": llm_model,
                "run_mode": "refine",
                "refinement_goal": request.refinement_goal,
            }
        ),
        _format_section("Constraints"),
        _format_key_values(request.constraints.model_dump()),
        _format_section("Original Text"),
        f"{request.text}\n\n",
        _format_section("Refined Text"),
        f"{final_text}\n\n",
        _format_section("Explanation"),
        f"{explanation}\n",
    ]

    path.write_text("\n".join(chunks), encoding="utf-8")
    return path.resolve()
