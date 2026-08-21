from agents.debug.trace_parser import TraceParser
from agents.tools.graph_tool import GraphTool
from agents.utils.chunk_lookup import ChunkStore
from agents.utils.sources import format_sources
from agents.llm.client import generate


SYSTEM_PROMPT = """You are a debugging assistant.

You are given:
1. A parsed stack trace location (function, file, line) - exact, from the
   error itself.
2. A GROUND-TRUTH list of functions that call the failing function,
   computed from the repository's real dependency graph. Do not add
   callers to this list or assume others exist.
3. Source code for the failing function and, where available, its real
   callers.

Using ONLY this evidence, explain the likely root cause and where to look
next. Reference what the code actually does, not generic debugging advice.
Be honest about uncertainty - if the evidence doesn't clearly point to a
single cause, say what you can determine and what would need to be checked
next, rather than asserting a confident conclusion the evidence doesn't
support.

Be concise: 3-5 sentences.
"""
class DebugAgent:

    def __init__(self, graph_tool=None, chunk_store=None, llm_client=None):

        self.parser = TraceParser()
        self.graph = graph_tool or GraphTool()
        self.chunk_store = (
            chunk_store if chunk_store is not None else self._default_chunk_store()
        )
        self.llm_client = llm_client

    def _default_chunk_store(self):

        try:
            return ChunkStore()
        except (FileNotFoundError, OSError):
            return None

    def analyze(self, trace):

        parsed = self.parser.parse(trace)

        if not parsed["function"]:
            return {
                "error": "Could not parse stack trace"
            }

        callers = self.graph.callers(
            parsed["function"]
        )

        explanation = self._reason_about_bug(parsed, callers)

        return {
            "location": parsed,
            "callers": callers,
            "explanation": explanation
        }

    def _reason_about_bug(self, location, callers):

        if not self.chunk_store:
            return self._fallback_explanation(location, callers)

        function_chunks = self.chunk_store.get_by_name(
            location["function"], limit=1
        )
        caller_chunks = self.chunk_store.get_for_names(
            callers, total_limit=3
        )

        sources_block = format_sources(function_chunks + caller_chunks)

        callers_text = "\n".join(f"- {c}" for c in callers) or "None found."

        user_message = (
            f"STACK TRACE LOCATION:\n"
            f"Function: {location['function']}\n"
            f"File: {location['file']}\n"
            f"Line: {location['line']}\n\n"
            f"GROUND-TRUTH CALLERS ({len(callers)} total):\n{callers_text}\n\n"
            f"SOURCE CODE:\n{sources_block}"
        )

        try:
            return generate(
                SYSTEM_PROMPT,
                user_message,
                max_output_tokens=500,
                client=self.llm_client
            )

        except Exception:
            return self._fallback_explanation(location, callers)

    def _fallback_explanation(self, location, callers):

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

(LLM reasoning unavailable - showing deterministic trace/graph facts only.)
"""