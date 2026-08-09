class ImpactAnalyzer:

    def __init__(self, graph):
        self.graph = graph

    def analyze(self, symbol):

        affected_nodes = self.graph.impact(symbol)

        return {
            "changed_symbol": symbol,
            "affected_nodes": affected_nodes
        }