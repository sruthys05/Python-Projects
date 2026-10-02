import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_create_and_get_ticket(client):
    response = client.post(
        "/tickets",
        json={"title": "Payment refund", "description": "I need a refund for my invoice"},
    )

    assert response.status_code == 201
    created = response.json()
    assert created["category"] == "billing"
    assert created["priority"] == "normal"

    detail = client.get(f"/tickets/{created['id']}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Payment refund"


def test_list_tickets_and_missing_ticket(client):
    assert client.get("/tickets").json() == []
    assert client.get("/tickets/999").status_code == 404
