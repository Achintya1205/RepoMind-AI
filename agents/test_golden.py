import json
from agents.graph import app

DATASET = "evaluation/golden/bulletproof-react.jsonl"

with open(DATASET, "r", encoding="utf-8") as f:
    questions = [json.loads(next(f))]

for item in questions:
    state = {
        "query": item["question"],
        "conversation_history": [],
        "retrieved_chunks": [],
        "graph_results": [],
        "retry_count": 0,
        "current_agent": "",
        "answer": "",
        "verified": {},
        "final_answer": {},
        "metadata": []
    }

    result = app.invoke(state)

    print("\n" + "=" * 70)
    print(item["id"])
    print("QUESTION:", item["question"])
    print("EXPECTED:", item["expected_agent"])
    print("ACTUAL:", result.get("current_agent"))
    print("ANSWER:", result.get("final_answer") or result.get("answer", ""))