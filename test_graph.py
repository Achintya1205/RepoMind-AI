import pickle

with open("graph_output/dependency_graph.pkl", "rb") as f:
    graph = pickle.load(f)

print("Nodes:", graph.number_of_nodes())
print("Edges:", graph.number_of_edges())

for edge in list(graph.edges(data=True))[:10]:
    print(edge)