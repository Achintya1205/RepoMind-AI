def rerank(results, query):

    query_words = query.lower().split()

    scored = []


    for item in results:

        content = item["content"].lower()
        metadata = item["metadata"]

        name = metadata.get("name", "").lower()


        # Start with semantic similarity
        score = 1 - item["distance"]


        # Keyword matching
        for word in query_words:

            if word in content:
                score += 0.2


        # Entity importance

        auth_terms = [
            "auth",
            "login",
            "token",
            "session",
            "credential",
            "permission"
        ]


        for term in auth_terms:

            if term in name:
                score += 0.5


        # Exact function purpose boosts

        if "check" in name:
            score += 0.3


        if "cookie" in name:
            score += 0.3


        scored.append(
            (
                score,
                item
            )
        )


    scored.sort(
        key=lambda x:x[0],
        reverse=True
    )


    return [
        item
        for score,item in scored
    ]