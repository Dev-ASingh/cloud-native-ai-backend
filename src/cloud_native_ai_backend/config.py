from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cloud-Native AI Backend"
    app_env: str = "development"
    readiness_dependency: bool = True
    database_url: str = "sqlite:///./cloud_native_ai_backend.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
