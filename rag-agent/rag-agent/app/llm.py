"""Answer generation. Uses Claude if ANTHROPIC_API_KEY is set, else an extractive fallback."""
import os
import re

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from .chunking import Chunk

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")


def llm_available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _keywords(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in ENGLISH_STOP_WORDS and len(w) > 2]


def rewrite_query(question: str) -> str:
    """Reformulate the query for a second retrieval attempt."""
    if llm_available():
        try:
            return _call_claude(
                "Rewrite the user's question as a short keyword search query. Reply with the query only.",
                question, max_tokens=60,
            ).strip()
        except Exception:
            pass
    return " ".join(_keywords(question))


def generate_answer(question: str, contexts: list[Chunk]) -> str:
    """Grounded answer from retrieved chunks."""
    if llm_available():
        try:
            joined = "\n\n".join(f"[{c.source}#{c.index}] {c.text}" for c in contexts)
            return _call_claude(
                "Answer ONLY from the provided context. Cite sources like [file#chunk]. "
                "If the context does not contain the answer, say you don't know.",
                f"Context:\n{joined}\n\nQuestion: {question}", max_tokens=400,
            )
        except Exception:
            pass  # fall back to extractive mode
    return _extractive_answer(question, contexts)


def _extractive_answer(question: str, contexts: list[Chunk]) -> str:
    """Offline fallback: pick the best-matching sentences from the top-ranked document."""
    top_source = contexts[0].source
    q = set(_keywords(question))

    sentences: list[str] = []
    for c in sorted((c for c in contexts if c.source == top_source), key=lambda c: c.index):
        for s in re.split(r"(?<=[.!?])\s+", c.text):
            s = s.strip()
            if not s:
                continue
            # chunks overlap, so drop duplicates and keep the more complete version of a split sentence
            dup = next((i for i, t in enumerate(sentences) if s in t or t in s), None)
            if dup is None:
                sentences.append(s)
            elif len(s) > len(sentences[dup]):
                sentences[dup] = s

    best = sorted(range(len(sentences)), key=lambda i: (-len(q & set(_keywords(sentences[i]))), i))[:3]
    return " ".join(sentences[i] for i in sorted(best))


def _call_claude(system: str, user: str, max_tokens: int) -> str:
    import anthropic  # optional dependency

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")
