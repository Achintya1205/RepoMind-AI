class ImpactAnalyzer:


    def __init__(self, graph):
        self.graph = graph


    def analyze(self, symbol):

        callers = self.graph.impact(symbol)


        return {
            "symbol": symbol,
            "affected_files": callers,
            "impact": f"""
Changing {symbol} may affect:

{callers}

Review these callers before modifying.
"""
        }