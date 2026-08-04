class RouterNode:


    def route(self, state):

        query = state["query"].lower()

        if any(
            word in query
            for word in [
                "traceback",
                "stack trace",
                "exception",
                "error:",
                "bug",
                "error",
                "issue",
                "fix"
            ]
        ):
            state["current_agent"] = "debug"


        # Impact analysis
        elif any(
            word in query
            for word in [
                "break",
                "impact",
                "depend",
                "caller",
                "dependency",
                "calls"
            ]
        ):
            state["current_agent"] = "impact_analysis"


        # Architecture
        elif any(
            word in query
            for word in [
                "architecture",
                "design",
                "structure",
                "overview"
            ]
        ):
            state["current_agent"] = "architecture"


        # Refactoring
        elif any(
            word in query
            for word in [
                "refactor",
                "clean",
                "improve"
            ]
        ):
            state["current_agent"] = "refactor"


        # Documentation
        elif any(
            word in query
            for word in [
                "documentation",
                "docs"
            ]
        ):
            state["current_agent"] = "docs"


        # General questions
        else:
            state["current_agent"] = "qa"


        return state



router = RouterNode()


def route_query(state):
    return router.route(state)