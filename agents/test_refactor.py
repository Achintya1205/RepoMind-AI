from agents.refactor.refactor_agent import RefactorAgent


agent = RefactorAgent()


result = agent.analyze(
    "sendToClient"
)


print(result)