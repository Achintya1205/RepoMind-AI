from agents.graph import app


result = app.invoke(
    {
        "query": "How can I refactor sendToClient?",
        "current_agent": ""
    }
)


print(result["final_answer"])
