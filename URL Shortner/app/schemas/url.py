from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from app.config import settings


class URLCreate(BaseModel):
    url: AnyHttpUrl = Field(max_length=settings.max_url_length)
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class URLResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    short_code: str
    short_url: str
    long_url: str
    created_at: datetime
    expires_at: datetime


class Stats(BaseModel):
    short_code: str
    long_url: str
    created_at: datetime
    expires_at: datetime
    clicks: int
