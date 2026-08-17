import re


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

        identifier_pattern = re.compile(
            r"\b(?:validate|authenticate)(?:[A-Z]\w*|_\w+)\b"
        )

        for match in identifier_pattern.finditer(answer):

            word = match.group(0)

            if word not in available_symbols:
                grounded = False
                reasons.append(
                    f"Unsupported symbol: {word}"
                )

        pattern = re.compile(
            r"`?([A-Za-z_][\w.]*(?:\(\))?)`?\s+calls\s+`?([A-Za-z_][\w.]*(?:\(\))?)`?"
        )

        for match in pattern.finditer(answer):

            caller = match.group(1).rstrip(".").rstrip("()")
            callee = match.group(2).rstrip(".").rstrip("()")

            caller_known = self.graph_tool.get_node(caller) is not None
            callee_known = self.graph_tool.get_node(callee) is not None

            if not (caller_known and callee_known):
                continue

            if not self.graph_tool.has_call_edge(caller, callee):

                grounded = False

                reasons.append(
                    f"No CALLS edge between {caller} and {callee}"
                )


        return {
            "passed": grounded,
            "reasons": reasons
        }