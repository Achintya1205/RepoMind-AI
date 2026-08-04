from agents.debug.debug_agent import DebugAgent


agent = DebugAgent()


trace = """
Error: Cannot read property 'token'

at login (src/auth.js:20:5)
at handleSubmit (src/form.js:10:3)
"""

result = agent.analyze(trace)


print(result)