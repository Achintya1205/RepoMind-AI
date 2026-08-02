from agents.tools.graph_tool import GraphTool
from agents.impact_explainer import ImpactExplainer


class ImpactAnalyzer:

    def __init__(self):
        self.graph_tool = GraphTool()
        self.explainer = ImpactExplainer()


    def analyze(self, symbol):

        impacted = self.graph_tool.impact(symbol)

        result = {
            "changed_symbol": symbol,
            "impact_count": len(impacted),
            "affected_nodes": impacted
        }

        result["explanation"] = (
            self.explainer.explain(result)
        )

        return result