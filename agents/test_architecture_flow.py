from agents.graph import app


result = app.invoke(
    {
        "query": "Explain the architecture of this repository",
        "current_agent": ""
    }
)


print(result["final_answer"])