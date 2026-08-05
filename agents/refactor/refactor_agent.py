from agents.impact_analyzer import ImpactAnalyzer


class RefactorAgent:


    def __init__(self):

        self.impact_analyzer = ImpactAnalyzer()


    def analyze(self, symbol):

        impact = self.impact_analyzer.analyze(symbol)


        affected = impact["affected_nodes"]


        plan = self.generate_plan(
            symbol,
            affected
        )


        return {
            "symbol": symbol,
            "affected_files": affected,
            "plan": plan
        }



    def generate_plan(self, symbol, affected):

        return f"""
Refactor Plan for {symbol}


1. Analyze current implementation of {symbol}

2. Update function logic while preserving existing behavior

3. Review affected callers:

{affected}


4. Update related tests

5. Run regression testing on impacted modules
"""
    