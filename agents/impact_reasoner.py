from agents.impact_explainer import ImpactExplainer
from agents.utils.chunk_lookup import ChunkStore
from agents.utils.sources import format_sources
from agents.llm.client import generate


SYSTEM_PROMPT = """You are a code-impact analysis assistant.

You are given:
1. A GROUND-TRUTH list of functions that call the changed symbol, computed
   by traversing the repository's real dependency graph. This list is
   exact - it is not something you need to infer or guess, and you must
   not add functions to it that aren't listed.
2. Source code for the changed symbol and, where available, a sample of
   its real callers.

Using ONLY this evidence, explain what changing this symbol could affect
and why - referencing what the callers actually do with it where the code
shows that. Do not claim a function is affected unless it appears in the
ground-truth caller list. Do not invent callers, files, or behavior not
shown in the evidence.

Be concise: 2-4 sentences, then a short bullet list of the affected
functions if there are more than a couple.
"""


class ImpactReasoner:

    def __init__(self, chunk_store=None, llm_client=None):

        self.chunk_store = (
            chunk_store if chunk_store is not None else self._default_chunk_store()
        )
        self.llm_client = llm_client
        self.fallback = ImpactExplainer()

    def _default_chunk_store(self):

        try:
            return ChunkStore()
        except (FileNotFoundError, OSError):
            return None

    def explain(self, impact_result):

        symbol = impact_result["changed_symbol"]
        affected = impact_result["affected_nodes"]

        if not affected:
            return f"No callers found for `{symbol}` - changing it should not affect other functions in the indexed code."

        if not self.chunk_store:
            return self.fallback.explain(impact_result)

        symbol_chunks = self.chunk_store.get_by_name(symbol, limit=1)
        caller_chunks = self.chunk_store.get_for_names(affected, total_limit=4)

        sources_block = format_sources(symbol_chunks + caller_chunks)

        affected_list = "\n".join(f"- {node}" for node in affected)

        user_message = (
            f"CHANGED SYMBOL: {symbol}\n\n"
            f"GROUND-TRUTH AFFECTED FUNCTIONS (from graph traversal, "
            f"{len(affected)} total):\n{affected_list}\n\n"
            f"SOURCE CODE:\n{sources_block}"
        )

        try:
            return generate(
                SYSTEM_PROMPT,
                user_message,
                max_output_tokens=600,
                client=self.llm_client
            )

        except Exception:
            return self.fallback.explain(impact_result)