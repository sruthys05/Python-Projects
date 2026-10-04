import os

import pytest
from fastapi.testclient import TestClient

os.environ.pop("ANTHROPIC_API_KEY", None)  # tests run offline with the extractive fallback

from app.agent import NOT_FOUND, RagAgent  # noqa: E402
from app.chunking import chunk_text  # noqa: E402
from app.llm import _extractive_answer  # noqa: E402
from app.main import app  # noqa: E402
from app.retriever import TfidfRetriever  # noqa: E402


def test_chunking_overlap_and_coverage():
    text = " ".join(f"w{i}" for i in range(200))
    chunks = chunk_text("a.md", text, size=80, overlap=20)
    assert len(chunks) >= 3
    assert chunks[0].text.split()[-20:] == chunks[1].text.split()[:20]
    assert chunks[-1].text.split()[-1] == "w199"


def test_chunking_rejects_bad_params():
    with pytest.raises(ValueError):
        chunk_text("a.md", "x y z", size=10, overlap=10)


def test_chunking_empty_text():
    assert chunk_text("a.md", "   ") == []


def test_markdown_heading_becomes_own_sentence():
    chunks = chunk_text("a.md", "# LRU Cache\nAn LRU cache evicts old entries.")
    assert chunks[0].text.startswith("LRU Cache. An LRU")


def test_extractive_answer_dedupes_overlapping_chunks():
    text = " ".join(f"Sentence number {i} talks about caching." for i in range(40))
    chunks = chunk_text("a.md", text, size=30, overlap=10)
    answer = _extractive_answer("caching sentence 7", chunks)
    sentences = [x for x in answer.split(".") if x.strip()]
    assert len(sentences) == len(set(sentences))


def _agent():
    r = TfidfRetriever()
    r.fit(
        chunk_text("lru.md", "An LRU cache uses a hash map and a doubly linked list for O(1) get and put.")
        + chunk_text("bs.md", "Binary search halves a sorted array each step and runs in O(log n) time.")
    )
    return RagAgent(r)


def test_retrieval_picks_right_document():
    res = _agent().ask("How does binary search work on a sorted array?")
    assert res.grounded
    assert res.sources[0]["source"] == "bs.md"


def test_agent_abstains_on_unrelated_question():
    res = _agent().ask("What is the capital of France?")
    assert res.answer == NOT_FOUND
    assert not res.grounded
    assert any("abstaining" in step for step in res.trace)


def test_agent_retries_with_rewritten_query():
    res = _agent().ask("Could you please tell me, in detail, about the LRU cache?")
    assert res.grounded
    assert res.sources[0]["source"] == "lru.md"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # triggers lifespan -> loads data/docs
        yield c


def test_health_reports_documents(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["documents"] >= 4


def test_ask_endpoint_grounded_answer(client):
    r = client.post("/ask", json={"question": "What is the time complexity of BFS?"})
    assert r.status_code == 200
    body = r.json()
    assert body["grounded"] and body["sources"][0]["source"] == "graph_traversal.md"
    assert "BFS" in body["answer"]
    assert "binary search" not in body["answer"].lower()  # answer comes from the top document only


def test_ask_endpoint_validation(client):
    assert client.post("/ask", json={"question": "hi"}).status_code == 422


def test_ingest_then_ask(client):
    r = client.post("/ingest", json={"name": "heap.md", "text": "A binary heap is a complete tree where the parent is smaller than its children, giving O(1) access to the minimum element."})
    assert r.status_code == 201
    body = client.post("/ask", json={"question": "What does a binary heap give access to?"}).json()
    assert body["sources"][0]["source"] == "heap.md"
