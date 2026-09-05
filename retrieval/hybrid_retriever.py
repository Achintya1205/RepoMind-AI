from sentence_transformers import CrossEncoder

from retrieval.vector_store import VectorStore
from retrieval.keyword_search import KeywordSearch

class HybridRetriever:

    def __init__(self):
        self._vector_store = None
        self._keyword_search = None
        self._reranker = None

    def _ensure_loaded(self):

        if self._vector_store is None:
            self._vector_store = VectorStore()

        if self._keyword_search is None:
            self._keyword_search = KeywordSearch()

        if self._reranker is None:
            self._reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def hybrid_retrieve(self, query, k=5):

        self._ensure_loaded()

        vector_results = self._vector_store.search(
            query,
            k=10
        )

        keyword_results = self._keyword_search.search(
            query,
            k=10
        )

        candidates = []

        candidates.extend(vector_results)
        candidates.extend(keyword_results)
        seen = set()
        unique_candidates = []

        for chunk in candidates:

            metadata = chunk["metadata"]

            key = (
                metadata["file"],
                metadata["name"],
                metadata["type"]
            )

            if key not in seen:

                seen.add(key)
                unique_candidates.append(chunk)

        candidates = unique_candidates

        if not candidates:
            return []

        pairs = [
            [query, chunk["content"]]
            for chunk in candidates
        ]

        scores = self._reranker.predict(
            pairs,
            batch_size=8,
            show_progress_bar=False
        )

        ranked = sorted(
            zip(candidates, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {
                "chunk": chunk["content"],
                "metadata": chunk["metadata"],
                "rerank_score": float(score)
            }
            for chunk, score in ranked[:k]
        ]