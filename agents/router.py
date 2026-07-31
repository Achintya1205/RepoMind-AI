class RouterNode:


    def route(self, state):

        query = state["query"].lower()


        if any(
            word in query
            for word in [
                "break",
                "impact",
                "depend",
                "call",
                "caller",
                "dependency"
            ]
        ):
            state["current_agent"] = "impact_analysis"


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


        elif any(
            word in query
            for word in [
                "bug",
                "error",
                "issue",
                "fix"
            ]
        ):
            state["current_agent"] = "debug"


        elif any(
            word in query
            for word in [
                "refactor",
                "clean",
                "improve"
            ]
        ):
            state["current_agent"] = "refactor"


        elif any(
            word in query
            for word in [
                "documentation",
                "docs",
                "explain"
            ]
        ):
            state["current_agent"] = "docs"


        else:

            state["current_agent"] = "qa"


        return state