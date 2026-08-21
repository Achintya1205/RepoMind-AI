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

    def analyze(self, symbol):

        impact = self.impact_analyzer.analyze(symbol)

        affected = impact["affected_nodes"]

        plan = self._reason_about_refactor(symbol, affected)

        return {
            "symbol": symbol,
            "affected_files": affected,
            "plan": plan
        }

    def _reason_about_refactor(self, symbol, affected):

        if not self.chunk_store:
            return self._fallback_plan(symbol, affected)

        symbol_chunks = self.chunk_store.get_by_name(symbol, limit=1)
        caller_chunks = self.chunk_store.get_for_names(affected, total_limit=4)

        sources_block = format_sources(symbol_chunks + caller_chunks)

        affected_text = "\n".join(f"- {node}" for node in affected) or "None found."

        user_message = (
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