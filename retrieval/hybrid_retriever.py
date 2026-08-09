from sentence_transformers import CrossEncoder

from retrieval.vector_store import VectorStore
from retrieval.keyword_search import KeywordSearch


class HybridRetriever:

    def __init__(self):

        self.vector_store = VectorStore()
        self.keyword_search = KeywordSearch()

        self.reranker = CrossEncoder("BAAI/bge-reranker-base")

    def hybrid_retrieve(self, query, k=5):

        vector_results = self.vector_store.search(
            query,
            k=10
        )

        keyword_results = self.keyword_search.search(
            query,
            k=10
        )

        candidates = []

        candidates.extend(vector_results)
        candidates.extend(keyword_results)

        # Remove duplicate chunks.
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

        # Rerank only the unique candidate set.
        pairs = [
            [query, chunk["content"]]
            for chunk in candidates
        ]

        scores = self.reranker.predict(
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