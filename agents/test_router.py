from router import RouterNode


router = RouterNode()


queries = [

    "How does authentication work?",

    "What breaks if I remove LoginForm?",

    "Explain the architecture of this repo",

    "Why is login failing?",

    "Refactor this API client",

    "Create documentation for auth flow"

]


for q in queries:

    state = {
        "query": q,
        "conversation_history": [],
        "retrieved_chunks": [],
        "graph_results": [],
        "retry_count": 0,
        "current_agent": "",
        "answer": ""
    }


    result = router.route(state)


    print(q)
    print(
        "=>",
        result["current_agent"]
    )
    print("----------------")