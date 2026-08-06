from agents.graph import app


tests = [

    "Where is authentication implemented?",

    "Explain repository architecture",

    "What breaks if sendToClient changes?",

    """
    TypeError: Cannot read properties of undefined
    at login (src/auth.js:20)
    """,

    "Generate documentation for authRequestInterceptor",

    "How can I refactor sendToClient?"
]


for query in tests:

    print("\n==============================")
    print("QUERY:")
    print(query)

    result = app.invoke(
        {
            "query": query,
            "current_agent": ""
        }
    )

    print("\nRESULT:")
    print(result["final_answer"])