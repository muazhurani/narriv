from __future__ import annotations

import re
from typing import Any

import pandas as pd
from brainopt.models import SentenceFeature


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks = [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]
    return chunks if chunks else [text]


def _char_fallback(text: str, temporal_energy: list[float]) -> list[SentenceFeature]:
    sentences = split_sentences(text)
    if not sentences:
        return []
    if not temporal_energy:
        return [
            SentenceFeature(
                sentence_index=idx,
                text=sentence,
                start_t=0,
                end_t=0,
                mean_energy=0.0,
                peak_energy=0.0,
                relative_contribution=0.0,
            )
            for idx, sentence in enumerate(sentences)
        ]

    total_chars = sum(len(sentence) for sentence in sentences)
    if total_chars <= 0:
        total_chars = len(text)
    n_timesteps = len(temporal_energy)
    total_energy = sum(temporal_energy) or 1e-8

    features: list[SentenceFeature] = []
    char_cursor = 0
    for idx, sentence in enumerate(sentences):
        start_ratio = char_cursor / total_chars
        char_cursor += len(sentence)
        end_ratio = char_cursor / total_chars

        start_t = min(n_timesteps - 1, int(round(start_ratio * max(0, n_timesteps - 1))))
        end_t = min(n_timesteps - 1, int(round(end_ratio * max(0, n_timesteps - 1))))
        if end_t < start_t:
            end_t = start_t

        segment = temporal_energy[start_t : end_t + 1]
        if not segment:
            segment = [temporal_energy[min(start_t, n_timesteps - 1)]]

        segment_sum = sum(segment)
        features.append(
            SentenceFeature(
                sentence_index=idx,
                text=sentence,
                start_t=start_t,
                end_t=end_t,
                mean_energy=segment_sum / len(segment),
                peak_energy=max(segment),
                relative_contribution=segment_sum / total_energy,
            )
        )

    return features


def _segment_overlap_indices(
    sentence_start: float,
    sentence_stop: float,
    segments: list[Any],
    n_timesteps: int,
) -> tuple[int, int]:
    overlaps: list[int] = []
    sentence_mid = (sentence_start + sentence_stop) / 2.0
    for idx, segment in enumerate(segments[:n_timesteps]):
        seg_start = float(getattr(segment, "start", idx))
        seg_duration = float(getattr(segment, "duration", 1.0))
        seg_stop = seg_start + seg_duration
        if seg_stop > sentence_start and seg_start < sentence_stop:
            overlaps.append(idx)

    if overlaps:
        return overlaps[0], overlaps[-1]

    nearest_idx = 0
    nearest_distance = float("inf")
    for idx, segment in enumerate(segments[:n_timesteps]):
        seg_start = float(getattr(segment, "start", idx))
        seg_duration = float(getattr(segment, "duration", 1.0))
        seg_mid = seg_start + seg_duration / 2.0
        distance = abs(seg_mid - sentence_mid)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_idx = idx
    return nearest_idx, nearest_idx


def map_sentence_features(
    text: str,
    temporal_energy: list[float],
    events: pd.DataFrame | None = None,
    segments: list[Any] | None = None,
) -> list[SentenceFeature]:
    sentences = split_sentences(text)
    if not sentences or not temporal_energy:
        return _char_fallback(text, temporal_energy)

    if events is None or segments is None or events.empty:
        return _char_fallback(text, temporal_energy)

    word_events = events.loc[events["type"] == "Word"].copy() if "type" in events.columns else pd.DataFrame()
    if word_events.empty or "text" not in word_events.columns or "start" not in word_events.columns:
        return _char_fallback(text, temporal_energy)

    word_events = word_events.sort_values("start").reset_index(drop=True)
    total_energy = sum(temporal_energy) or 1e-8
    n_timesteps = len(temporal_energy)

    token_cursor = 0
    sentence_features: list[SentenceFeature] = []
    for idx, sentence in enumerate(sentences):
        sentence_tokens = re.findall(r"\S+", sentence)
        if not sentence_tokens:
            continue

        next_cursor = min(len(word_events), token_cursor + len(sentence_tokens))
        sentence_words = word_events.iloc[token_cursor:next_cursor]
        token_cursor = next_cursor
        if sentence_words.empty:
            return _char_fallback(text, temporal_energy)

        start_time = float(sentence_words["start"].min())
        durations = sentence_words["duration"] if "duration" in sentence_words.columns else 0.4
        stop_time = float((sentence_words["start"] + durations).max())
        start_t, end_t = _segment_overlap_indices(start_time, stop_time, segments, n_timesteps)

        window = temporal_energy[start_t : end_t + 1]
        if not window:
            window = [temporal_energy[min(start_t, n_timesteps - 1)]]
        window_sum = sum(window)
        sentence_features.append(
            SentenceFeature(
                sentence_index=idx,
                text=sentence,
                start_t=start_t,
                end_t=end_t,
                mean_energy=window_sum / len(window),
                peak_energy=max(window),
                relative_contribution=window_sum / total_energy,
            )
        )

    if not sentence_features:
        return _char_fallback(text, temporal_energy)
    return sentence_features
