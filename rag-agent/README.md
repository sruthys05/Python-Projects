# RAG Agent: Ask Questions Over Your Own Documents

A small, fully tested **Retrieval-Augmented Generation (RAG) agent** built with Python and FastAPI.
It indexes a folder of documents, retrieves the most relevant passages for a question, and answers
**only from those passages**, citing sources. If the documents don't contain the answer, it says so
instead of guessing.

## How it works

```
question ──► retrieve (TF-IDF) ──► grade relevance ──┬─ good ──► generate answer ──► answer + sources + trace
                  ▲                                  │
                  └──── rewrite query & retry once ◄─┘ low
                                                     └─ still low ──► abstain ("not found")
```

The "agentic" part is the **retrieve → grade → rewrite/retry → answer-or-abstain loop** in
[`app/agent.py`](app/agent.py). Every response includes a `trace` showing the decisions the agent made.

| Module | Responsibility |
|---|---|
| `app/chunking.py` | Splits documents into overlapping word chunks |
| `app/retriever.py` | TF-IDF + cosine similarity retrieval (scikit-learn) |
| `app/agent.py` | The control loop: grade, retry, abstain |
| `app/llm.py` | Answer generation: Claude if an API key is set, otherwise an offline extractive fallback |
| `app/main.py` | FastAPI service |

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API docs. Sample DSA notes in `data/docs/` are indexed on startup.

```bash
curl -X POST localhost:8000/ask -H "Content-Type: application/json" \
     -d '{"question": "What is the time complexity of BFS?"}'
```

### Optional: LLM-generated answers

Without a key the agent runs fully offline and returns the best-matching sentences from the top document.
For natural-language answers with citations, set an Anthropic API key:

```bash
export ANTHROPIC_API_KEY=your_key_here
export ANTHROPIC_MODEL=claude-sonnet-5-5   # optional override
```

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Index status (documents, chunks) |
| `GET` | `/documents` | List indexed documents |
| `POST` | `/ingest` | Add a document: `{"name": "x.md", "text": "..."}` |
| `POST` | `/ask` | Ask a question: `{"question": "..."}` → `answer`, `grounded`, `sources`, `trace` |

## Tests

```bash
pytest -q
```

Covers chunking (overlap, edge cases), retrieval ranking, abstaining on off-topic questions,
the query-retry path, overlap de-duplication, and the API endpoints.

## Design decisions & limitations

- **TF-IDF instead of embeddings.** Zero downloads and easy to reason about. In testing, adding bigrams made
  generic phrases like "time complexity" outrank the rare, meaningful term "BFS", so the retriever uses unigrams.
  TF-IDF matches words, not meaning (it won't link "car" to "automobile"). The `TfidfRetriever` interface
  (`fit`, `search`) is small so a sentence-transformer + FAISS/Chroma retriever can be swapped in.
- **Relevance threshold (0.1)** was chosen from observed scores on the sample documents; retune it for your own corpus.
- **In-memory index.** Documents are re-indexed on startup and on `/ingest`; nothing is persisted.
- **Extractive fallback is a demo mode.** Answer quality is much better with an LLM configured.

## Ideas for next steps

- Embedding-based retrieval with a vector store
- PDF ingestion and persistent storage
- Retrieval evaluation (hit-rate / MRR on a labeled question set)
- Streaming responses and a small web UI
