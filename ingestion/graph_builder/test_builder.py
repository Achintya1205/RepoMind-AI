from pathlib import Path
from collections import Counter

from builder import DependencyGraphBuilder
from graph_io import save_graph


builder = DependencyGraphBuilder(
    "sample_repos/bulletproof-react"
)


javascript_ast = builder.load_ast(
    Path("ingestion/parsers/output/javascript_ast_output.json")
)


graph = builder.build_graph(javascript_ast)


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