"""TF-IDF retriever (scikit-learn). Swap in embeddings later without touching the agent."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .chunking import Chunk


class TfidfRetriever:
    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self._vectorizer = TfidfVectorizer(stop_words="english", sublinear_tf=True)
        self._matrix = None

    def fit(self, chunks: list[Chunk]) -> None:
        self.chunks = list(chunks)
        if self.chunks:
            self._matrix = self._vectorizer.fit_transform(c.text for c in self.chunks)
        else:
            self._matrix = None

    def search(self, query: str, k: int = 3) -> list[tuple[Chunk, float]]:
        if self._matrix is None or not query.strip():
            return []
        scores = cosine_similarity(self._vectorizer.transform([query]), self._matrix).ravel()
        top = scores.argsort()[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in top if scores[i] > 0]
