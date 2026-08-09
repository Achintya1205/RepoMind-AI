from agents.tools.graph_tool import GraphTool


def precision_recall(predicted, actual):
    predicted = set(predicted)
    actual = set(actual)

    if not predicted:
        precision = 1.0 if not actual else 0.0
    else:
        precision = len(predicted & actual) / len(predicted)

    recall = (
        len(predicted & actual) / len(actual)
        if actual
        else 1.0
    )

    return precision, recall


def main():
    graph = GraphTool()

    # Ground truth is obtained directly from the dependency graph.
    # The evaluation checks whether GraphTool's impact traversal
    # correctly returns the CALLS-based upstream dependency set.
    symbols = [
        "useAuthorization",
        "useUser",
        "Layout",
    ]

    print("=" * 70)
    print("RepoMind AI - Graph Ground-Truth Evaluation")
    print("=" * 70)

    for symbol in symbols:
        nodes = graph.get_nodes(symbol)

        if not nodes:
            print(f"\n{symbol}: symbol not found")
            continue

        actual = []

        visited = set()
        queue = list(nodes)

        while queue:
            current = queue.pop(0)

            if current in visited:
                continue

            visited.add(current)

            for caller in graph.graph.predecessors(current):
                edge = graph.graph.get_edge_data(
                    caller,
                    current
                )

                if edge.get("edge_type") == "CALLS":
                    actual.append(caller)
                    queue.append(caller)

        predicted = graph.impact(symbol)

        precision, recall = precision_recall(
            predicted,
            actual
        )

        print(f"\nSYMBOL: {symbol}")
        print(f"Ground truth nodes: {len(actual)}")
        print(f"Predicted nodes:    {len(predicted)}")
        print(f"Precision:          {precision:.2f}")
        print(f"Recall:             {recall:.2f}")

        print("Status:", "PASS" if predicted == actual else "CHECK")

        if predicted != actual:
            print("\nMissing:")
            for item in sorted(set(actual) - set(predicted)):
                print(f"  {item}")

            print("\nExtra:")
            for item in sorted(set(predicted) - set(actual)):
                print(f"  {item}")


if __name__ == "__main__":
    main()