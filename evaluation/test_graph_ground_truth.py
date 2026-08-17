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


def ground_truth_callers(graph, nodes):
    """
    Independently recomputes the real upstream caller set via BFS over
    CALLS edges, without using GraphTool.impact() at all - this is what
    makes the comparison a genuine ground-truth check rather than the
    function testing itself.
    """

    actual = []
    visited = set(nodes)
    queue = list(nodes)

    while queue:
        current = queue.pop(0)

        for caller in graph.predecessors(current):

            if caller in visited:
                continue

            edge = graph.get_edge_data(caller, current)

            if edge.get("edge_type") == "CALLS":
                visited.add(caller)
                actual.append(caller)
                queue.append(caller)

    return actual


def main():
    graph = GraphTool()

    # Sample drawn from both test repos, reusing the same unambiguous
    # symbols already used in the debug/refactor/impact golden questions -
    # this ties the graph eval directly to what the agents are actually
    # exercised against elsewhere, rather than an arbitrary pick.
    symbols = [
        # bulletproof-react (JS/TS)
        "useAuthorization",
        "useUser",
        "Layout",
        # full-stack-fastapi-template (Python)
        "authenticate",
        "get_current_user",
        "verify_password",
        "get_password_hash",
        "get_current_active_superuser",
        "read_item",
    ]

    print("=" * 70)
    print("RepoMind AI - Graph Ground-Truth Evaluation")
    print("=" * 70)

    precisions = []
    recalls = []
    not_found = []

    for symbol in symbols:
        nodes = graph.get_nodes(symbol)

        if not nodes:
            print(f"\n{symbol}: symbol not found")
            not_found.append(symbol)
            continue

        actual = ground_truth_callers(graph.graph, nodes)

        predicted = graph.impact(symbol)

        precision, recall = precision_recall(
            predicted,
            actual
        )

        precisions.append(precision)
        recalls.append(recall)

        print(f"\nSYMBOL: {symbol}")
        print(f"Ground truth nodes: {len(actual)}")
        print(f"Predicted nodes:    {len(predicted)}")
        print(f"Precision:          {precision:.2f}")
        print(f"Recall:             {recall:.2f}")

        print("Status:", "PASS" if set(predicted) == set(actual) else "CHECK")

        if set(predicted) != set(actual):
            print("\nMissing:")
            for item in sorted(set(actual) - set(predicted)):
                print(f"  {item}")

            print("\nExtra:")
            for item in sorted(set(predicted) - set(actual)):
                print(f"  {item}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Symbols sampled:     {len(symbols)}")
    print(f"Symbols not found:   {len(not_found)}")

    if precisions:
        avg_precision = sum(precisions) / len(precisions)
        avg_recall = sum(recalls) / len(recalls)
        print(f"Average precision:   {avg_precision:.2f}")
        print(f"Average recall:      {avg_recall:.2f}")


if __name__ == "__main__":
    main()