from fastapi import FastAPI

from app.config import get_settings
from app.database import Base, engine
from app.models import Ticket  # noqa: F401
from app.routes.tickets import router as tickets_router

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(tickets_router)


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
