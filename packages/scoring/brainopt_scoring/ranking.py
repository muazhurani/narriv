from __future__ import annotations

import math
import re
from typing import Iterable

import numpy as np

from brainopt.models import (
    CandidateDiagnostics,
    CandidateVariant,
    Constraints,
    RankedCandidate,
    RankedScores,
    WorkerScoreResponse,
)


def _minmax(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values
    span = float(values.max() - values.min())
    if span <= 1e-12:
        return np.full_like(values, 0.5, dtype=np.float64)
    return (values - values.min()) / span


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _unit_scale(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return _clip01((value - lo) / (hi - lo))


def _count_hashtags(text: str) -> int:
    return len(re.findall(r"#\w+", text))


def _sentence_lengths(text: str) -> list[int]:
    chunks = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    if not chunks:
        return [len(text.split())]
    return [len(chunk.split()) for chunk in chunks]


def _readability_score(text: str) -> float:
    lengths = _sentence_lengths(text)
    avg_words = float(np.mean(lengths))
    target = 14.0
    # Best near target sentence length, softer penalty further away.
    score = math.exp(-abs(avg_words - target) / 12.0)
    return _clip01(score)


def _platform_fit_score(text: str, platform: str) -> float:
    platform_norm = platform.lower()
    char_count = len(text)
    if platform_norm in {"twitter", "x"}:
        return _clip01(1.0 - max(0, char_count - 280) / 280.0)
    if platform_norm == "linkedin":
        if char_count < 150:
            return 0.6
        if char_count > 3000:
            return _clip01(1.0 - (char_count - 3000) / 3000.0)
        return 0.95
    if platform_norm in {"threads", "instagram"}:
        if char_count <= 500:
            return 0.95
        return _clip01(1.0 - (char_count - 500) / 2000.0)
    return 0.85


def _constraint_compliance_score(text: str, constraints: Constraints) -> float:
    penalties = 0.0
    if constraints.max_chars is not None and len(text) > constraints.max_chars:
        penalties += min(0.8, (len(text) - constraints.max_chars) / max(constraints.max_chars, 1))
    if constraints.hard_max_length is not None and len(text) > constraints.hard_max_length:
        penalties += min(1.0, (len(text) - constraints.hard_max_length) / max(constraints.hard_max_length, 1))
    if constraints.hashtag_limit is not None:
        hashtags = _count_hashtags(text)
        if hashtags > constraints.hashtag_limit:
            penalties += min(0.5, (hashtags - constraints.hashtag_limit) / max(constraints.hashtag_limit + 1, 1))
    if constraints.include_cta and not re.search(r"\b(comment|reply|share|follow|dm|book|join|read|learn)\b", text.lower()):
        penalties += 0.12
    return _clip01(1.0 - penalties)


def _dropoff_after_sentence(score: WorkerScoreResponse) -> int | None:
    means = [item.mean_energy for item in score.sentence_features]
    if len(means) < 2:
        return None
    for idx in range(1, len(means)):
        if means[idx] < 0.85 * means[idx - 1]:
            return idx - 1
    return None


def _compose_reason(
    hook: float,
    sustained: float,
    end: float,
    platform_fit: float,
    readability: float,
    weakest_flags: Iterable[str],
) -> str:
    strengths: list[str] = []
    if hook >= 0.7:
        strengths.append("strong opening energy")
    if sustained >= 0.7:
        strengths.append("good mid/late momentum")
    if end >= 0.7:
        strengths.append("solid closing strength")
    if platform_fit >= 0.8:
        strengths.append("fits platform length norms")
    if readability >= 0.8:
        strengths.append("clean sentence pacing")
    if not strengths:
        strengths.append("balanced signal profile")
    issues = [flag for flag in weakest_flags if flag]
    if not issues:
        return f"Best signals: {', '.join(strengths)}."
    return f"Best signals: {', '.join(strengths)}. Watch: {', '.join(issues)}."


def rank_candidates(
    candidates: list[CandidateVariant],
    scores: list[WorkerScoreResponse],
    platform: str,
    constraints: Constraints,
) -> list[RankedCandidate]:
    score_by_id = {item.candidate_id: item for item in scores}
    aligned: list[tuple[CandidateVariant, WorkerScoreResponse]] = [
        (candidate, score_by_id[candidate.id]) for candidate in candidates if candidate.id in score_by_id
    ]
    if not aligned:
        return []

    hook_raw = np.array([item.raw_features.early_mean for _, item in aligned], dtype=np.float64)
    sustained_raw = np.array(
        [0.6 * item.raw_features.mid_mean + 0.4 * item.raw_features.late_mean - max(item.raw_features.dropoff, 0.0) for _, item in aligned],
        dtype=np.float64,
    )
    clarity_raw = np.array([1.0 / (1.0 + item.raw_features.variance_over_time) for _, item in aligned], dtype=np.float64)
    end_raw = np.array([item.raw_features.late_mean for _, item in aligned], dtype=np.float64)
    novelty_raw = np.array(
        [max(0.0, 1.0 - abs(item.raw_features.spikiness - 1.35) / 1.35) for _, item in aligned], dtype=np.float64
    )

    hook_norm = _minmax(hook_raw)
    sustained_norm = _minmax(sustained_raw)
    clarity_norm = _minmax(clarity_raw)
    end_norm = _minmax(end_raw)
    novelty_norm = _minmax(novelty_raw)

    ranked: list[RankedCandidate] = []
    for idx, (candidate, score) in enumerate(aligned):
        hook_abs = _unit_scale(score.raw_features.early_mean, 0.08, 0.18)
        sustained_value = 0.6 * score.raw_features.mid_mean + 0.4 * score.raw_features.late_mean - max(
            score.raw_features.dropoff, 0.0
        )
        sustained_abs = _unit_scale(sustained_value, 0.06, 0.16)
        clarity_abs = _unit_scale(1.0 / (1.0 + 2000.0 * score.raw_features.variance_over_time), 0.55, 0.98)
        end_abs = _unit_scale(score.raw_features.late_mean, 0.06, 0.16)
        novelty_abs = _clip01(1.0 - abs(score.raw_features.spikiness - 1.30) / 0.55)

        # Blend absolute calibration with batch-local normalization so weak batches
        # do not automatically produce a "perfect" winner.
        hook_score = 0.6 * hook_abs + 0.4 * float(hook_norm[idx])
        sustained_score = 0.6 * sustained_abs + 0.4 * float(sustained_norm[idx])
        clarity_score = 0.6 * clarity_abs + 0.4 * float(clarity_norm[idx])
        end_score = 0.6 * end_abs + 0.4 * float(end_norm[idx])
        novelty_score = 0.6 * novelty_abs + 0.4 * float(novelty_norm[idx])

        brainscore = (
            0.30 * hook_score
            + 0.25 * sustained_score
            + 0.20 * clarity_score
            + 0.15 * end_score
            + 0.10 * novelty_score
        )

        platform_fit = _platform_fit_score(candidate.text, platform)
        readability = _readability_score(candidate.text)
        compliance = _constraint_compliance_score(candidate.text, constraints)
        final_score = (
            0.45 * brainscore
            + 0.20 * platform_fit
            + 0.15 * readability
            + 0.10 * novelty_score
            + 0.10 * compliance
        )

        strongest_sentence = None
        weakest_sentence = None
        if score.sentence_features:
            strongest_sentence = max(score.sentence_features, key=lambda s: s.mean_energy).sentence_index
            weakest_sentence = min(score.sentence_features, key=lambda s: s.mean_energy).sentence_index

        warnings: list[str] = []
        if compliance < 0.75:
            warnings.append("constraint pressure")
        if readability < 0.65:
            warnings.append("readability drift")
        if score.raw_features.dropoff > 0.15:
            warnings.append("late-stage dropoff")

        ranked.append(
            RankedCandidate(
                id=candidate.id,
                strategy=candidate.strategy,
                tone=candidate.tone,
                text=candidate.text,
                scores=RankedScores(
                    brainscore=round(brainscore, 4),
                    hook_score=round(hook_score, 4),
                    sustained_response_score=round(sustained_score, 4),
                    clarity_stability_score=round(clarity_score, 4),
                    end_strength_score=round(end_score, 4),
                    novelty_spike_score=round(novelty_score, 4),
                    platform_fit_score=round(platform_fit, 4),
                    readability_score=round(readability, 4),
                    constraint_compliance_score=round(compliance, 4),
                    final_score=round(final_score, 4),
                ),
                diagnostics=CandidateDiagnostics(
                    strongest_sentence=strongest_sentence,
                    weakest_sentence=weakest_sentence,
                    dropoff_after_sentence=_dropoff_after_sentence(score),
                ),
                reason=_compose_reason(
                    hook=hook_score,
                    sustained=sustained_score,
                    end=end_score,
                    platform_fit=platform_fit,
                    readability=readability,
                    weakest_flags=warnings,
                ),
                raw_features=score.raw_features,
                sentence_features=score.sentence_features,
                temporal_energy=score.temporal_energy,
            )
        )

    ranked.sort(key=lambda item: item.scores.final_score, reverse=True)
    return ranked
