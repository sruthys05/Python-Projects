from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Ticket Triage API"
    database_url: str = "sqlite:///./data/tickets.db"
    model_path: str = "app/ml/models/ticket_classifier.joblib"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
