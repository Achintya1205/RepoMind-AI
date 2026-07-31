import json
GRAPH_KEYWORDS = [
    "depends",
    "dependency",
    "depend",
    "calls",
    "called",
    "caller",
    "callee",
    "imports",
    "imported",
    "uses",
    "used by",
    "inherits",
    "extends",
    "references",
    "referenced",
    "what breaks",
    "impact",
    "affected"
]


HYBRID_KEYWORDS = [
    "how",
    "what",
    "where",
    "why",
    "authentication",
    "login",
    "comment",
    "api",
    "database",
    "flow",
    "implement",
    "implementation",
    "logic",
    "function",
    "explain"
]


class QueryRouter:

    def __init__(self):

        self.symbols = set()

        with open(
            "ingestion/chunker/chunks.json",
            "r",
            encoding="utf-8"
        ) as f:

            chunks = json.load(f)

        for chunk in chunks:

            self.symbols.add(
                chunk["metadata"]["name"].lower()
            )

    def route(self, query):

        query = query.lower()

        symbol_found = any(
            symbol in query
            for symbol in self.symbols
        )

        graph = any(
            word in query
            for word in GRAPH_KEYWORDS
        )

        hybrid = any(
            word in query
            for word in HYBRID_KEYWORDS
        )

        if symbol_found:
            return "GRAPH_AND_HYBRID"

        if graph and hybrid:
            return "GRAPH_AND_HYBRID"

        if graph:
            return "GRAPH"
 
        return "HYBRID"