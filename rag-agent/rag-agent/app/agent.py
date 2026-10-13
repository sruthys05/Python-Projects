"""A small agentic RAG loop: retrieve -> grade -> (rewrite & retry) -> answer or abstain."""
from dataclasses import dataclass, field

from . import llm
from .chunking import Chunk
from .retriever import TfidfRetriever

NOT_FOUND = "I couldn't find this in the indexed documents."


@dataclass
class AgentResult:
    answer: str
    sources: list[dict] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
    grounded: bool = True


class RagAgent:
    def __init__(self, retriever: TfidfRetriever, threshold: float = 0.1, k: int = 3) -> None:
        self.retriever = retriever
        self.threshold = threshold
        self.k = k

    def _retrieve(self, query: str, trace: list[str]) -> list[tuple[Chunk, float]]:
        hits = self.retriever.search(query, self.k)
        best = hits[0][1] if hits else 0.0
        trace.append(f"retrieve(query={query!r}) -> {len(hits)} hits, best_score={best:.3f}")
        return hits

    def ask(self, question: str) -> AgentResult:
        trace: list[str] = []
        hits = self._retrieve(question, trace)

        # Grade: is the best hit relevant enough? If not, rewrite the query and retry once.
        if not hits or hits[0][1] < self.threshold:
            new_query = llm.rewrite_query(question)
            trace.append(f"grade: low relevance, rewrote query -> {new_query!r}")
            hits = self._retrieve(new_query, trace) if new_query else []

        if not hits or hits[0][1] < self.threshold:
            trace.append("grade: still low relevance, abstaining")
            return AgentResult(answer=NOT_FOUND, trace=trace, grounded=False)

        chunks = [c for c, _ in hits]
        answer = llm.generate_answer(question, chunks)
        trace.append(f"answer generated with {'Claude' if llm.llm_available() else 'extractive fallback'}")
        sources = [{"source": c.source, "chunk": c.index, "score": round(s, 3), "text": c.text} for c, s in hits]
        return AgentResult(answer=answer, sources=sources, trace=trace)
