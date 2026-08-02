from agents.tools.graph_tool import GraphTool

tool = GraphTool()

print(tool.callers("authRequestInterceptor"))
print(tool.callees("authRequestInterceptor"))