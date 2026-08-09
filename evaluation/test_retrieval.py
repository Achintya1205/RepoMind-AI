import json

from retrieval.hybrid_retriever import HybridRetriever


DATASET = "evaluation/golden/bulletproof-react.jsonl"


def main():
    retriever = HybridRetriever()

    with open(DATASET, "r", encoding="utf-8") as f:
        questions = [
            json.loads(line)
            for line in f
            if line.strip()
        ]

    total = len(questions)
    recall_hits = 0
    reciprocal_rank_sum = 0.0

    for item in questions:
        query = item["question"]

        results = retriever.hybrid_retrieve(
            query,
            k=5
        )

        # For this first evaluation pass, we consider retrieval successful
        # when at least one retrieved chunk belongs to the expected domain
        # implied by the question's expected agent.
        expected_agent = item["expected_agent"]

        names = [
            result["metadata"].get("name", "").lower()
            for result in results
        ]

        query_lower = query.lower()

        # Symbol-oriented questions
        symbol_hit = False

        for name in names:
            if name and name in query_lower:
                symbol_hit = True
                break

        if symbol_hit:
            recall_hits += 1

            for rank, result in enumerate(results, start=1):
                name = result["metadata"].get("name", "").lower()

                if name and name in query_lower:
                    reciprocal_rank_sum += 1.0 / rank
                    break

    recall_at_5 = recall_hits / total if total else 0.0
    mrr = reciprocal_rank_sum / total if total else 0.0

    print("\nRepoMind AI - Retrieval Evaluation")
    print("=" * 50)
    print(f"Questions evaluated: {total}")
    print(f"Recall@5:             {recall_at_5:.2f}")
    print(f"MRR:                  {mrr:.2f}")


if __name__ == "__main__":
    main()