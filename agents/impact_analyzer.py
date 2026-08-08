class ImpactAnalyzer:

    def __init__(self, graph):
        self.graph = graph

    def analyze(self, symbol):

        callers = self.graph.impact(symbol)

        affected = []

        for node in callers:
            if "::" in node:
                file_path, name = node.rsplit("::", 1)
                affected.append(f"{file_path}::{name}")
            else:
                affected.append(node)

        return {
            "symbol": symbol,
            "affected_files": affected,
            "impact": (
                f"Changing {symbol} may affect:\n\n"
                + "\n".join(f"- {item}" for item in affected)
                + "\n\nReview these callers before modifying."
            )
        }
