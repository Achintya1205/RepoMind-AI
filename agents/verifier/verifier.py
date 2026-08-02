class Verifier:

    def __init__(self, metadata, graph_tool):
        self.metadata = metadata
        self.graph_tool = graph_tool


    def verify(self, answer):

        reasons = []
        grounded = True

        available_symbols = {
            item["name"]
            for item in self.metadata
            if item.get("name")
        }

        words = answer.replace(".", "").split()


        # Symbol verification
        for word in words:

            if word.startswith(("validate", "authenticate")):

                if word not in available_symbols:
                    grounded = False
                    reasons.append(
                        f"Unsupported symbol: {word}"
                    )


        if " calls " in answer:

            parts = answer.split(" calls ")

            caller = parts[0].strip()
            callee = parts[1].strip()

            if not self.graph_tool.has_call_edge(
                caller,
                callee
            ):
                grounded = False

                reasons.append(
                    f"No CALLS edge between {caller} and {callee}"
                )


        return {
            "passed": grounded,
            "reasons": reasons
        }