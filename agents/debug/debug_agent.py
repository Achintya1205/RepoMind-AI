from agents.debug.trace_parser import TraceParser
from agents.tools.graph_tool import GraphTool


class DebugAgent:


    def __init__(self):

        self.parser = TraceParser()
        self.graph = GraphTool()


    def analyze(self, trace):

        parsed = self.parser.parse(trace)


        if not parsed["function"]:
            return {
                "error": "Could not parse stack trace"
            }


        callers = self.graph.callers(
            parsed["function"]
        )


        return {

            "location": parsed,

            "callers": callers,

            "explanation": self.explain(
                parsed,
                callers
            )
        }



    def explain(self, location, callers):

        return f"""
Possible root cause:

Error occurred in:

Function:
{location['function']}

File:
{location['file']}

Line:
{location['line']}


Functions calling this code:

{callers}


Debugging should start from this function because
the stack trace points here and these callers depend on it.
"""