from agents.graph import app


result = app.invoke(
    {
        "query": "Where is authentication implemented?",
        "current_agent": ""
    }
)


print(result)