from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "tribe-worker"
    tribe_repo_path: str = Field(..., validation_alias="TRIBE_REPO_PATH")
    tribe_model_id: str = "facebook/tribev2"
    tribe_cache_folder: str = "/tmp/tribe_cache"
    tribe_device: str = "cpu"
    worker_max_batch_size: int = Field(default=16, ge=1, le=64)

    @property
    def use_cuda(self) -> bool:
        return self.tribe_device.lower().startswith("cuda")
