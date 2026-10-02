import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.url_mapping import URLMapping, utc_now
from app.services.cache_service import URLCache

_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


class URLExpiredError(Exception):
    pass


class URLService:
    def __init__(self, cache: URLCache | None = None) -> None:
        self.cache = cache or URLCache()

    @staticmethod
    def encode_base62(value: int) -> str:
        if value < 0:
            raise ValueError("value must not be negative")
        if value == 0:
            return _ALPHABET[0]
        encoded = ""
        while value:
            value, remainder = divmod(value, len(_ALPHABET))
            encoded = _ALPHABET[remainder] + encoded
        return encoded

    def _generate_candidate_code(self) -> str:
        upper_bound = len(_ALPHABET) ** settings.short_code_length
        value = secrets.randbelow(upper_bound)
        return self.encode_base62(value).rjust(settings.short_code_length, "0")

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

    def create_url(
        self,
        session: Session,
        long_url: str,
        expires_in_days: int | None = None,
    ) -> URLMapping:
        created_at = utc_now()
        lifetime = timedelta(days=expires_in_days or settings.default_expiry_days)
        expires_at = created_at + lifetime

        for _ in range(10):
            short_code = self._generate_candidate_code()
            if session.scalar(select(URLMapping.id).where(URLMapping.short_code == short_code)) is not None:
                continue
            mapping = URLMapping(
                short_code=short_code,
                long_url=long_url,
                created_at=created_at,
                expires_at=expires_at,
            )
            session.add(mapping)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                continue
            self.cache.put(short_code, long_url, expires_at)
            return mapping

        raise RuntimeError("Could not allocate a unique short code after 10 attempts")

    def resolve(self, session: Session, short_code: str) -> str:
        now = utc_now()
        cached = self.cache.get(short_code)
        if cached is not None:
            if self._as_utc(cached.expires_at) <= now:
                self.cache.invalidate(short_code)
                raise URLExpiredError(short_code)
            session.execute(
                update(URLMapping)
                .where(URLMapping.short_code == short_code)
                .values(clicks=URLMapping.clicks + 1)
            )
            session.commit()
            return cached.long_url

        mapping = session.scalar(select(URLMapping).where(URLMapping.short_code == short_code))
        if mapping is None:
            raise KeyError(short_code)
        if self._as_utc(mapping.expires_at) <= now:
            self.cache.invalidate(short_code)
            raise URLExpiredError(short_code)

        long_url = mapping.long_url
        expires_at = mapping.expires_at
        session.execute(
            update(URLMapping)
            .where(URLMapping.id == mapping.id)
            .values(clicks=URLMapping.clicks + 1)
        )
        session.commit()
        self.cache.put(short_code, long_url, expires_at)
        return long_url

    def get_stats(self, session: Session, short_code: str) -> URLMapping:
        mapping = session.scalar(select(URLMapping).where(URLMapping.short_code == short_code))
        if mapping is None:
            raise KeyError(short_code)
        if self._as_utc(mapping.expires_at) <= utc_now():
            raise URLExpiredError(short_code)
        session.refresh(mapping)
        return mapping
