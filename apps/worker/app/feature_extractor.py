from __future__ import annotations

import numpy as np

from brainopt.models import RawFeatures


def _safe_mean(values: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    return float(np.mean(values))


def extract_temporal_features(predictions: np.ndarray) -> tuple[RawFeatures, list[float]]:
    if predictions.ndim != 2:
        raise ValueError(f"Expected 2D predictions array, got shape {predictions.shape}")

    n_timesteps, n_vertices = predictions.shape
    abs_predictions = np.abs(predictions)
    temporal_energy = np.mean(abs_predictions, axis=1)

    one_third = max(1, n_timesteps // 3)
    early = temporal_energy[:one_third]
    mid = temporal_energy[one_third : min(n_timesteps, 2 * one_third)]
    late = temporal_energy[min(n_timesteps, 2 * one_third) :]

    mean_energy = _safe_mean(temporal_energy)
    peak_energy = float(np.max(temporal_energy)) if n_timesteps else 0.0
    spikiness = peak_energy / mean_energy if mean_energy > 1e-8 else 0.0

    features = RawFeatures(
        raw_shape_t=n_timesteps,
        raw_shape_v=n_vertices,
        global_mean=float(np.mean(abs_predictions)) if abs_predictions.size else 0.0,
        global_peak=float(np.max(abs_predictions)) if abs_predictions.size else 0.0,
        global_std=float(np.std(predictions)) if predictions.size else 0.0,
        early_mean=_safe_mean(early),
        mid_mean=_safe_mean(mid),
        late_mean=_safe_mean(late),
        dropoff=float(_safe_mean(early) - _safe_mean(late)),
        sustainability=(mean_energy / peak_energy) if peak_energy > 1e-8 else 0.0,
        spikiness=spikiness,
        variance_over_time=float(np.var(temporal_energy)) if temporal_energy.size else 0.0,
        peak_time=int(np.argmax(temporal_energy)) if temporal_energy.size else 0,
    )
    return features, temporal_energy.astype(float).tolist()
