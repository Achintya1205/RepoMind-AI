from agents.tools.graph_tool import GraphTool

tool = GraphTool()

count = 0

for src, dst, data in tool.graph.edges(data=True):
    if data.get("edge_type") == "CALLS":
        print("CALLER:")
        print(src)
        print("CALLEE:")
        print(dst)
        print("----------------")

        count += 1

        if count == 10:
            break