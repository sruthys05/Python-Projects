"""FastAPI service exposing the RAG agent."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .agent import RagAgent
from .chunking import Chunk, chunk_text
from .retriever import TfidfRetriever

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "docs"

_documents: dict[str, str] = {}
_retriever = TfidfRetriever()
_agent = RagAgent(_retriever)


def _rebuild_index() -> None:
    chunks: list[Chunk] = []
    for name, text in _documents.items():
        chunks.extend(chunk_text(name, text))
    _retriever.fit(chunks)


def load_directory(path: Path = DOCS_DIR) -> None:
    for f in sorted(path.glob("*.md")) + sorted(path.glob("*.txt")):
        _documents[f.name] = f.read_text(encoding="utf-8")
    _rebuild_index()


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_directory()
    yield


app = FastAPI(title="RAG Agent", description="Ask questions over your own documents.",
              version="1.0.0", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class IngestRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=10)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "documents": len(_documents), "chunks": len(_retriever.chunks)}


@app.get("/documents")
def documents() -> list[str]:
    return sorted(_documents)


@app.post("/ingest", status_code=201)
def ingest(req: IngestRequest) -> dict:
    _documents[req.name] = req.text
    _rebuild_index()
    return {"ingested": req.name, "chunks": len(_retriever.chunks)}


@app.post("/ask")
def ask(req: AskRequest) -> dict:
    if not _documents:
        raise HTTPException(status_code=409, detail="No documents indexed. POST /ingest first.")
    result = _agent.ask(req.question)
    return {"answer": result.answer, "grounded": result.grounded, "sources": result.sources, "trace": result.trace}
