from graph_io import load_graph

graph = load_graph("dependency_graph.pkl")

def find_importers(graph, target_file):

    importers = []

    for u, v, data in graph.edges(data=True):

        if data.get("edge_type") == "IMPORTS" and target_file in v:
            importers.append(u)

    return importers

print(find_importers(graph, "discussions.ts"))