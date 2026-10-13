"""Environment-backed application settings."""

import os
from dataclasses import dataclass
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value < 1:
        raise ValueError(f"{name} must be greater than zero")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/urls.db")
    cache_size: int = _positive_int("CACHE_SIZE", 256)
    default_expiry_days: int = _positive_int("DEFAULT_EXPIRY_DAYS", 30)
    short_code_length: int = _positive_int("SHORT_CODE_LENGTH", 7)
    max_url_length: int = _positive_int("MAX_URL_LENGTH", 2048)

    @property
    def default_expiry(self) -> timedelta:
        return timedelta(days=self.default_expiry_days)


settings = Settings()
