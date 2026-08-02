class ImpactExplainer:

    def explain(self, impact_result):

        symbol = impact_result["changed_symbol"]
        affected = impact_result["affected_nodes"]

        if not affected:
            return f"No callers found for {symbol}."

        count = len(affected)

        return (
            f"Changing `{symbol}` may affect "
            f"{count} dependent function{'s' if count != 1 else ''}. "
            f"The affected functions are: "
            + ", ".join(affected)
        )