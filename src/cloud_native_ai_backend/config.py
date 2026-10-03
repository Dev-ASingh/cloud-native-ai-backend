from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cloud-Native AI Backend"
    app_env: str = "development"
    readiness_dependency: bool = True
    database_url: str = "sqlite:///./cloud_native_ai_backend.db"
    worker_id: str = "development-worker"
    worker_poll_interval_seconds: float = 1.0
    auto_create_database: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )

    def validate_runtime(self) -> None:
        if self.app_env == "production" and self.auto_create_database:
            raise ValueError("AUTO_CREATE_DATABASE must be false in production.")
        if self.worker_poll_interval_seconds <= 0:
            raise ValueError("WORKER_POLL_INTERVAL_SECONDS must be positive.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
