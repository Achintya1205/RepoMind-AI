from agents.graph import app


trace = """
Traceback (most recent call last):
 File "auth.py", line 20, in login
 ValueError: invalid token
"""


result = app.invoke(
    {
        "query": trace,
        "current_agent": ""
    }
)


print(result["final_answer"])