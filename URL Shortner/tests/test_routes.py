from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import create_app
from app.models.url_mapping import URLMapping, utc_now
from app.routes.urls import url_service


@pytest.fixture
def client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with test_session() as session:
            yield session

    app = create_app(initialize_schema=False)
    app.dependency_overrides[get_db] = override_get_db
    url_service.cache.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_shorten_redirect_and_stats(client: TestClient) -> None:
    created = client.post("/shorten", json={"url": "https://example.com/article"})
    assert created.status_code == 201
    body = created.json()
    assert body["short_code"]
    assert body["short_url"].endswith("/" + body["short_code"])
    assert body["long_url"] == "https://example.com/article"

    redirected = client.get(f"/{body['short_code']}", follow_redirects=False)
    assert redirected.status_code == 307
    assert redirected.headers["location"] == "https://example.com/article"

    stats = client.get(f"/stats/{body['short_code']}")
    assert stats.status_code == 200
    assert stats.json()["clicks"] == 1


def test_missing_code_returns_404(client: TestClient) -> None:
    assert client.get("/notfound").status_code == 404
    assert client.get("/stats/notfound").status_code == 404


def test_expired_code_returns_410(client: TestClient) -> None:
    created = client.post("/shorten", json={"url": "https://example.com/old"})
    short_code = created.json()["short_code"]

    override = next(iter(client.app.dependency_overrides.values()))
    session_generator = override()
    session = next(session_generator)
    try:
        mapping = session.query(URLMapping).filter_by(short_code=short_code).one()
        mapping.expires_at = utc_now() - timedelta(seconds=1)
        session.commit()
    finally:
        session_generator.close()
    url_service.cache.invalidate(short_code)

    assert client.get(f"/{short_code}").status_code == 410
    assert client.get(f"/stats/{short_code}").status_code == 410


def test_invalid_url_is_rejected(client: TestClient) -> None:
    assert client.post("/shorten", json={"url": "not-a-url"}).status_code == 422
