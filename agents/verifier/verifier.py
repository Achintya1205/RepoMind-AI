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

        words = answer.replace(".", "").split()


        # Symbol verification
        for word in words:

            if word.startswith(("validate", "authenticate")):

                if word not in available_symbols:
                    grounded = False
                    reasons.append(
                        f"Unsupported symbol: {word}"
                    )


        # "X calls Y" claims - only match tight, identifier-shaped tokens
        # immediately around the word "calls" (not whole sentences), and
        # only treat it as a real code-structure claim to verify if BOTH
        # sides resolve to an actual known symbol in the graph. Ordinary
        # prose ("one calls .sign() to sign a string") will fail that
        # symbol check and gets silently skipped rather than misreported
        # as an ungrounded code claim - it isn't hallucination, it's just
        # not a code-structure sentence at all.
        pattern = re.compile(
            r"`?([A-Za-z_][\w.]*(?:\(\))?)`?\s+calls\s+`?([A-Za-z_][\w.]*(?:\(\))?)`?"
        )

        for match in pattern.finditer(answer):

            caller = match.group(1).rstrip(".").rstrip("()")
            callee = match.group(2).rstrip(".").rstrip("()")

            caller_known = self.graph_tool.get_node(caller) is not None
            callee_known = self.graph_tool.get_node(callee) is not None

            if not (caller_known and callee_known):
                # Not a real code-symbol claim - e.g. ordinary prose
                # that happens to contain the word "calls" - so there
                # is nothing meaningful to verify here.
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