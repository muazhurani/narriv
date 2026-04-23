from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Narriv API"
    worker_url: str = "http://127.0.0.1:8001"
    request_timeout_seconds: float = Field(default=180.0, gt=0.0)
    optimize_logs_dir: str = "data/run_logs"

    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4"
    openai_fallback_model: str = "gpt-5.1"
    openai_api_base: str = "https://api.openai.com/v1"
    openai_reasoning_effort: str = "none"
    openai_max_retries: int = Field(default=2, ge=0, le=5)
    use_mock_llm: bool = False
    cors_allowed_origins: str = (
        "http://127.0.0.1:3000,"
        "http://localhost:3000,"
        "http://127.0.0.1:3001,"
        "http://localhost:3001"
    )

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]
