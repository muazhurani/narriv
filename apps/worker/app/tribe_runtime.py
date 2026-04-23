from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Any

from brainopt.models import WorkerScoreRequest, WorkerScoreResponse

from .config import WorkerSettings
from .feature_extractor import extract_temporal_features
from .sentence_mapper import map_sentence_features


class TribeRuntime:
    def __init__(self, settings: WorkerSettings) -> None:
        self.settings = settings
        self._model: Any = None
        self._model_lock = Lock()

    def _import_tribe_model(self):
        try:
            from tribev2 import TribeModel  # type: ignore
        except ImportError:
            repo_path = Path(self.settings.tribe_repo_path).resolve()
            if not repo_path.exists():
                raise RuntimeError(f"Tribe repo path not found: {repo_path}")
            if str(repo_path) not in sys.path:
                sys.path.append(str(repo_path))
            from tribev2 import TribeModel  # type: ignore
        return TribeModel

    def _ensure_model(self):
        if self._model is not None:
            return self._model
        with self._model_lock:
            if self._model is not None:
                return self._model
            tribe_model = self._import_tribe_model()
            config_update = None
            if not self.settings.use_cuda:
                config_update = {
                    "accelerator": "cpu",
                    "infra.gpus_per_node": 0,
                }
            self._model = tribe_model.from_pretrained(
                self.settings.tribe_model_id,
                cache_folder=self.settings.tribe_cache_folder,
                device=self.settings.tribe_device,
                require_cuda=self.settings.use_cuda,
                config_update=config_update,
                dataloader_num_workers=0,
            )
        return self._model

    @staticmethod
    def _serialize_segment(segment: Any) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key in ("start", "duration", "timeline", "subject"):
            if hasattr(segment, key):
                value = getattr(segment, key)
                if isinstance(value, (str, int, float, bool)):
                    out[key] = value
        if hasattr(segment, "ns_events"):
            try:
                out["event_count"] = len(getattr(segment, "ns_events"))
            except Exception:
                out["event_count"] = 0
        return out

    def score_candidate(self, payload: WorkerScoreRequest) -> WorkerScoreResponse:
        model = self._ensure_model()
        start = perf_counter()
        temp_path: Path | None = None
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as tmp_file:
            tmp_file.write(payload.text)
            tmp_file.flush()
            temp_path = Path(tmp_file.name)

        try:
            try:
                events = model.get_events_dataframe(text_path=str(temp_path))
                predictions, segments = model.predict(events=events, verbose=False)
            except Exception as exc:
                raw = str(exc)
                lowered = raw.lower()
                if "401" in lowered or "gated" in lowered or "repository not found" in lowered:
                    raise RuntimeError(
                        "Tribe text encoder likely needs authenticated Hugging Face access. "
                        "Run `huggingface-cli login` in the worker environment and set HF_TOKEN."
                    ) from exc
                if "requires cuda" in lowered or "no cuda gpu is available" in lowered:
                    raise RuntimeError(
                        "GPU mode was requested, but the worker environment cannot initialize CUDA. "
                        "Install a CUDA-enabled PyTorch build in .venv-worker and restart the worker."
                    ) from exc
                if "torch not compiled with cuda enabled" in lowered:
                    raise RuntimeError(
                        "Worker is using CPU-only PyTorch while TRIBE_DEVICE requests CUDA. "
                        "Install a CUDA-enabled PyTorch build in .venv-worker and restart the worker."
                    ) from exc
                if "cuda out of memory" in lowered:
                    raise RuntimeError(
                        "CUDA out of memory during Tribe scoring. Retry on CPU or reduce concurrent worker load."
                    ) from exc
                raise
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass

        raw_features, temporal_energy = extract_temporal_features(predictions)
        sentence_features = map_sentence_features(
            payload.text,
            temporal_energy,
            events=events,
            segments=segments,
        )
        elapsed_ms = int((perf_counter() - start) * 1000)

        serialized_segments = [self._serialize_segment(segment) for segment in segments[:32]]
        metadata = {
            "inference_ms": elapsed_ms,
            "segment_count": len(segments),
            "timesteps": raw_features.raw_shape_t,
            "vertices": raw_features.raw_shape_v,
            "tribe_model_id": self.settings.tribe_model_id,
        }
        return WorkerScoreResponse(
            candidate_id=payload.candidate_id,
            platform=payload.platform,
            text=payload.text,
            raw_features=raw_features,
            temporal_energy=temporal_energy,
            sentence_features=sentence_features,
            segments=serialized_segments,
            metadata=metadata,
        )
