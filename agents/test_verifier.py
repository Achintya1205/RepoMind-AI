from agents.verifier.verifier import Verifier
from agents.tools.graph_tool import GraphTool


metadata = [
    {
        "type": "function",
        "name": "useUsers",
        "file": "get-users.ts"
    },
    {
        "type": "function",
        "name": "getUsersQueryOptions",
        "file": "get-users.ts"
    }
]


graph_tool = GraphTool()

verifier = Verifier(
    metadata,
    graph_tool
)


fake_answer = """
useUsers calls getUsersQueryOptions
"""

result = verifier.verify(fake_answer)

print(result)