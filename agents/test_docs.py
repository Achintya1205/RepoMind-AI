from agents.graph import app

result = app.invoke(
    {
        "query": "Generate documentation for authRequestInterceptor",
        "current_agent": ""
    }
)

print(result["final_answer"])
