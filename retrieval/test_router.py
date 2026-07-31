from router import QueryRouter

router = QueryRouter()

queries = [
    "How does authentication work?",
    "Who calls authRequestInterceptor?",
    "What files depend on LoginForm?",
    "Explain networkDelay",
    "What breaks if I remove authRequestInterceptor?",
    "Where is login implemented?"
]

for query in queries:

    print(query)
    print(router.route(query))
    print("------------------")
    