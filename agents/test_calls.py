from agents.tools.graph_tool import GraphTool

tool = GraphTool()

for src, dst, data in tool.graph.edges(data=True):

    if data.get("edge_type") == "CALLS":
        print("CALLER:", src)
        print("CALLEE:", dst)
        print("----------------")