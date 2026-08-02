from agents.tools.graph_tool import GraphTool

tool = GraphTool()

result = tool.impact("sendToClient")

print("IMPACT:")

for item in result:
    print(item)