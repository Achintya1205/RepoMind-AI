from agents.verifier.verifier import Verifier
from agents.verifier.retry import VerificationRetry
from agents.tools.graph_tool import GraphTool


metadata = [
    {
        "name": "useUsers"
    },
    {
        "name": "getUsersQueryOptions"
    }
]


verifier = Verifier(
    metadata,
    GraphTool()
)


retry = VerificationRetry(verifier)


answer = """
useUsers calls authenticateUser
"""


result = retry.run(answer)

print(result)