from pathlib import Path
from collections import Counter

from ingestion.graph_builder.builder import DependencyGraphBuilder
from ingestion.graph_builder.graph_io import save_graph


# repo_root passed here is only a fallback default for files that don't
# live under sample_repos/<name>/ - real per-file resolution now infers
# the correct root from each file's own path (see resolver.py).
builder = DependencyGraphBuilder(
    "sample_repos/bulletproof-react"
)


javascript_ast = builder.load_ast(
    Path("ingestion/parsers/output/javascript_ast_output.json")
)

python_ast = builder.load_ast(
    Path("ingestion/parsers/output/python_ast_output.json")
)

combined_ast = javascript_ast + python_ast


graph = builder.build_graph(combined_ast)


print()

print("Nodes:", graph.number_of_nodes())
print("Edges:", graph.number_of_edges())


print("\nCALL EDGES")

for u, v, data in graph.edges(data=True):

    if data.get("edge_type") == "CALLS":
        print(
            u,
            "----CALLS---->",
            v
        )


print("\nEdge types:")

print(
    Counter(
        data["edge_type"]
        for _, _, data in graph.edges(data=True)
    )
)


save_graph(
    graph,
    "dependency_graph.pkl"
)


print("Graph saved")