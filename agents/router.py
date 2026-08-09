class RouterNode:

    def route(self, state):

        query = state["query"].lower()

        # Architecture
        if any(
            word in query
            for word in [
                "architecture",
                "design",
                "structure",
                "overview"
            ]
        ):
            state["current_agent"] = "architecture"

        # Documentation
        elif any(
            word in query
            for word in [
                "documentation",
                "docstring",
                "readme",
                "generate docs",
                "document"
            ]
        ):
            state["current_agent"] = "docs"

        # Refactoring
        elif any(
            word in query
            for word in [
                "refactor",
                "clean up",
                "improve code"
            ]
        ):
            state["current_agent"] = "refactor"

        # Outgoing dependency / calls
        elif (
            "call" in query
            and any(
                phrase in query
                for phrase in [
                    "what does",
                    "what function does",
                    "what functions does",
                    "which function does",
                    "which functions does"
                ]
            )
        ):
            state["current_agent"] = "graph"

        # Incoming callers / impact
        elif any(
            phrase in query
            for phrase in [
                "who calls",
                "what calls",
                "caller",
                "callers",
                "impact",
                "what breaks",
                "affected by"
            ]
        ):
            state["current_agent"] = "impact_analysis"

        # Debugging
        elif any(
            word in query
            for word in [
                "traceback",
                "stack trace",
                "exception",
                "error:",
                "bug",
                "runtime error",
                "crash"
            ]
        ):
            state["current_agent"] = "debug"

        # Default
        else:
            state["current_agent"] = "qa"

        return state


router = RouterNode()


def route_query(state):
    return router.route(state)
