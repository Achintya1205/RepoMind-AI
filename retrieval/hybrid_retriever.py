from sentence_transformers import CrossEncoder

from vector_store import VectorStore
from keyword_search import KeywordSearch


class HybridRetriever:

    def __init__(self):

        self.vector_store = VectorStore()

        self.keyword_search = KeywordSearch()

        self.reranker = CrossEncoder(
            "BAAI/bge-reranker-base"
        )

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

        seen = set()
        unique_candidates = []

        for chunk in candidates:

            key = (
                chunk["metadata"]["file"],
                chunk["metadata"]["name"],
                chunk["metadata"]["type"]
            )

            if key not in seen:
                seen.add(key)
                unique_candidates.append(chunk)

                candidates = unique_candidates


        # remove duplicate chunks later


        pairs = []

        for chunk in candidates:

            pairs.append(
                [
                    query,
                    chunk["content"]
                ]
            )


        scores = self.reranker.predict(
            pairs
        )


        ranked = sorted(
            zip(candidates, scores),
            key=lambda x:x[1],
            reverse=True
        )


        return [
            {
                "chunk": item[0],
                "rerank_score": float(item[1])
            }
            for item in ranked[:k]
        ]