from agents.impact_analyzer import ImpactAnalyzer
from agents.utils.chunk_lookup import ChunkStore
from agents.utils.sources import format_sources
from agents.llm.client import generate


SYSTEM_PROMPT = """You are a refactoring assistant.

You are given:
1. A GROUND-TRUTH list of functions that call the symbol being refactored,
   computed from the repository's real dependency graph. This is exact -
   do not add or omit callers.
2. Source code for the symbol being refactored and, where available, its
   real callers.

Using ONLY this evidence, propose a concrete, specific refactor plan for
this symbol - referencing what the code actually does and which real
callers would need attention. Do not produce generic advice ("update
tests", "run regression") unless it is specifically justified by what the
code shows. If the code reveals a specific risk (e.g. a caller relies on a
particular return shape or side effect), call that out explicitly.

Where relevant, briefly note if there's a reasonable alternative approach
(e.g. extracting a helper vs. changing the signature directly) and why you
recommend one over the other - only if the code gives a real basis for
that judgment, not as a generic checklist item.

Directly address what the user actually asked, if their question is more
specific than "refactor this" (e.g. asking specifically about testability,
splitting responsibilities, or a particular concern) - don't produce a
generic plan that ignores the angle they asked about.

The caller list reflects static analysis of the parsed source - it will
not capture calls made via dynamic dispatch, reflection, or code the
parser couldn't resolve. Don't present it as a guaranteed-complete picture
of every real caller.

Cite specific code in the format (file:start_line-end_line) when
referencing it.

Be concise: a short paragraph plus a numbered list of concrete steps
(3-6 steps).
"""
class RefactorAgent:

    def __init__(self, graph, chunk_store=None, llm_client=None):

        self.impact_analyzer = ImpactAnalyzer(graph)
        self.chunk_store = (
            chunk_store if chunk_store is not None else self._default_chunk_store()
        )
        self.llm_client = llm_client

    def _default_chunk_store(self):

        try:
            return ChunkStore()
        except (FileNotFoundError, OSError):
            return None

    def analyze(self, symbol, query=None):

        impact = self.impact_analyzer.analyze(symbol)

        affected = impact["affected_nodes"]

        plan = self._reason_about_refactor(symbol, affected, query)

        return {
            "symbol": symbol,
            "affected_files": affected,
            "plan": plan
        }

    def _reason_about_refactor(self, symbol, affected, query=None):

        if not self.chunk_store:
            return self._fallback_plan(symbol, affected)

        symbol_chunks = self.chunk_store.get_by_name(symbol, limit=1)
        caller_chunks = self.chunk_store.get_for_names(affected, total_limit=4)

        sources_block = format_sources(symbol_chunks + caller_chunks)

        affected_text = "\n".join(f"- {node}" for node in affected) or "None found."

        question_text = query.strip() if query and query.strip() else (
            f"How can I refactor {symbol}?"
        )

        user_message = (
            f"USER QUESTION: {question_text}\n\n"
            f"SYMBOL TO REFACTOR: {symbol}\n\n"
            f"GROUND-TRUTH CALLERS ({len(affected)} total):\n{affected_text}\n\n"
            f"SOURCE CODE:\n{sources_block}"
        )

        try:
            return generate(
                SYSTEM_PROMPT,
                user_message,
                max_output_tokens=700,
                client=self.llm_client
            )

        except Exception:
            return self._fallback_plan(symbol, affected)

    def _fallback_plan(self, symbol, affected):

        return f"""
Refactor Plan for {symbol}


1. Review the current implementation of {symbol}.

2. Update its logic while preserving its existing external behavior.

3. Review affected callers (from the dependency graph, {len(affected)} total):

{affected}

4. Update or add tests covering {symbol} and the callers listed above.

5. Run the affected tests to confirm no regressions.


(LLM reasoning unavailable - showing a graph-grounded but generic plan.)
"""