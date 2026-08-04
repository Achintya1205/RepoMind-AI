from agents.graph import app


queries = [
    "Where is authentication implemented?",
    "What breaks if sendToClient changes?",
    "How can I refactor this function?",
    "Explain repository architecture"
]


for q in queries:

    print("\nQUERY:", q)

    result = app.invoke(
        {
            "query": q,
            "current_agent": ""
        }
    )

    print(result["final_answer"])