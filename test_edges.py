from agents.tools.graph_tool import GraphTool

graph = GraphTool().graph

for src, dst, data in list(graph.edges(data=True))[:50]:
    print(src)
    print(" ---> ")
    print(dst)
    print(data)
    print("----------------")