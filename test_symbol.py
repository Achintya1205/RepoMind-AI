from agents.graph import dependency_graph


symbol = "useAuthorization"


node = dependency_graph.get_node(symbol)

print("NODE:")
print(node)

print("\nCALLERS:")
for caller in dependency_graph.graph.predecessors(node):
    print(caller)
    print(
        dependency_graph.graph.get_edge_data(
            caller,
            node
        )
    )


print("\nCALLEES:")
for callee in dependency_graph.graph.successors(node):
    print(callee)
    print(
        dependency_graph.graph.get_edge_data(
            node,
            callee
        )
    )