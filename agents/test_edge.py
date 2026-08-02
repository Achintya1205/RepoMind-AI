from agents.tools.graph_tool import GraphTool

tool = GraphTool()

result = tool.has_call_edge(
    "useUsers",
    "getUsersQueryOptions"
)

print(result)