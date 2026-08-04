from agents.architecture.architecture_agent import ArchitectureAgent


agent = ArchitectureAgent()


result = agent.analyze()


print("SUMMARY")
print(result["summary"])

print("\nEXPLANATION")
print(result["explanation"])