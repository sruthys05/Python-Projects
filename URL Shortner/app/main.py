from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.database import create_schema
from app.routes import router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_schema()
    yield


def create_app(initialize_schema: bool = True) -> FastAPI:
    app = FastAPI(title="URL Shortener", version="1.0.0")
    if initialize_schema:
        app.router.lifespan_context = lifespan
    app.include_router(router)
    return app


app = create_app()
