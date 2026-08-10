import json
import sys
from pathlib import Path

from retrieval.hybrid_retriever import HybridRetriever


GOLDEN_DIR = "evaluation/golden"

DEFAULT_REPO = "bulletproof-react"


def is_hit(result_metadata, item):
    """
    A retrieved chunk counts as a real hit only if it's the actual
    labeled answer - not because a name happens to appear in the query.

    Golden entries can label the expected answer two ways:
      - "expected_symbol": exact function/class name (preferred, precise)
      - "expected_file": just the file (looser, use when the question
        is about a file/module rather than one symbol)
    """

    if item.get("expected_symbol"):
        return (
            result_metadata.get("name") == item["expected_symbol"]
        )

    if item.get("expected_file"):
        return (
            result_metadata.get("file") == item["expected_file"]
        )

    return False


def run_eval(repo_name):
    dataset_path = f"{GOLDEN_DIR}/{repo_name}.jsonl"

    retriever = HybridRetriever()

    with open(dataset_path, "r", encoding="utf-8") as f:
        questions = [
            json.loads(line)
            for line in f
            if line.strip()
        ]

    total = len(questions)
    recall_hits = 0
    reciprocal_rank_sum = 0.0
    unlabeled = 0

    for item in questions:

        if not item.get("expected_symbol") and not item.get("expected_file"):
            unlabeled += 1
            continue

        results = retriever.hybrid_retrieve(
            item["question"],
            k=5
        )

        hit_rank = None

        for rank, result in enumerate(results, start=1):
            if is_hit(result["metadata"], item):
                hit_rank = rank
                break

        if hit_rank is not None:
            recall_hits += 1
            reciprocal_rank_sum += 1.0 / hit_rank

    scored = total - unlabeled

    recall_at_5 = recall_hits / scored if scored else 0.0
    mrr = reciprocal_rank_sum / scored if scored else 0.0

    print(f"\nRepoMind AI - Retrieval Evaluation ({repo_name})")
    print("=" * 50)
    print(f"Questions in dataset:  {total}")

    if unlabeled:
        print(f"Skipped (no ground truth label): {unlabeled}")

    print(f"Questions scored:      {scored}")
    print(f"Recall@5:              {recall_at_5:.2f}")
    print(f"MRR:                   {mrr:.2f}")


def main():
    """
    Usage:
      python -m evaluation.test_retrieval
          -> runs default repo

      python -m evaluation.test_retrieval bulletproof-react
          -> runs one repo

      python -m evaluation.test_retrieval --all
          -> runs every golden file
    """

    args = sys.argv[1:]

    if args and args[0] == "--all":

        for path in sorted(Path(GOLDEN_DIR).glob("*.jsonl")):
            repo_name = path.stem
            run_eval(repo_name)

        return

    repo_name = args[0] if args else DEFAULT_REPO

    run_eval(repo_name)


if __name__ == "__main__":
    main()
