from agents.graph import app

state = {
    "query": "What does this function do?",
    "conversation_history": [],
    "retrieved_chunks": [],
    "graph_results": [],
    "retry_count": 0,
    "current_agent": "",
    "answer": ""
}

result = app.invoke(state)

print("\nFinal State:")
print(result)