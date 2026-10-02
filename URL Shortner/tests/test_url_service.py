from datetime import timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.url_mapping import URLMapping, utc_now
from app.services.cache_service import URLCache
from app.services.url_service import URLService


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db_session:
        yield db_session
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_base62_encoding() -> None:
    assert URLService.encode_base62(0) == "0"
    assert URLService.encode_base62(61) == "Z"
    assert URLService.encode_base62(62) == "10"
    with pytest.raises(ValueError):
        URLService.encode_base62(-1)


def test_create_and_resolve_increments_click_count(session: Session) -> None:
    service = URLService(URLCache(4))
    mapping = service.create_url(session, "https://example.com/path")

    assert mapping.short_code
    assert service.resolve(session, mapping.short_code) == "https://example.com/path"
    assert service.resolve(session, mapping.short_code) == "https://example.com/path"
    session.refresh(mapping)
    assert mapping.clicks == 2


def test_collision_retries_until_an_unused_code_is_found(session: Session) -> None:
    class CollisionService(URLService):
        candidates = iter(["taken", "fresh"])

        def _generate_candidate_code(self) -> str:
            return next(self.candidates)

    service = CollisionService(URLCache(2))
    session.add(
        URLMapping(
            short_code="taken",
            long_url="https://existing.example",
            created_at=utc_now(),
            expires_at=utc_now() + timedelta(days=1),
        )
    )
    session.commit()

    created = service.create_url(session, "https://new.example")
    assert created.short_code == "fresh"
    assert session.scalar(select(URLMapping.id).where(URLMapping.short_code == "taken")) is not None


def test_expired_mapping_cannot_be_resolved_or_counted(session: Session) -> None:
    service = URLService(URLCache(2))
    mapping = service.create_url(session, "https://expired.example")
    mapping.expires_at = utc_now() - timedelta(seconds=1)
    session.commit()
    service.cache.invalidate(mapping.short_code)

    from app.services.url_service import URLExpiredError

    with pytest.raises(URLExpiredError):
        service.resolve(session, mapping.short_code)
