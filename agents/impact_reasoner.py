from agents.impact_explainer import ImpactExplainer
from agents.utils.chunk_lookup import ChunkStore
from agents.utils.sources import format_sources
from agents.llm.client import generate


SYSTEM_PROMPT = """You are a code-impact analysis assistant.

You are given:
1. The user's ACTUAL QUESTION.
2. A GROUND-TRUTH list of functions that call the changed/queried symbol,
   computed by traversing the repository's real dependency graph, each
   tagged with its hop distance: distance 1 means a DIRECT caller (calls
   the symbol itself); distance 2+ means an INDIRECT caller (calls
   something that eventually leads to the symbol, through one or more
   other functions). This list is exact - do not add functions to it, and
   do not reclassify a function's distance.
3. Source code for the symbol and, where available, a sample of its real
   callers.

FIRST, determine what kind of question this actually is:

- A CALLER-LOOKUP question ("who calls X?", "what calls X?", "show me the
  caller hierarchy for X") is asking for a FACT: which functions call this
  symbol, directly and/or transitively. Answer concisely with the caller
  list/hierarchy from the evidence (noting direct vs indirect where it
  adds clarity). Do NOT add hypothetical impact/risk framing or discuss
  "what would break" - that isn't what was asked.

- An IMPACT/CHANGE question ("what breaks if I change X?", "is it safe to
  modify X?", "what's the risk of changing X?") is asking you to reason
  about CONSEQUENCES of a hypothetical change. For this type only:
  - Distinguish DIRECT impact (distance 1, breaks/changes behavior
    immediately) from INDIRECT impact (distance 2+, only affected if the
    change propagates through the functions in between).
  - Explain the BEHAVIORAL consequence where the code shows it - e.g. does
    a caller rely on this symbol's return value, a side effect, an
    exception it raises?
  - Give a brief risk assessment grounded in what the code actually shows.

Rules for both question types:
- Cite evidence in the format (file:start_line-end_line) when referencing
  specific code.
- Do not claim a function is affected/calling unless it appears in the
  ground-truth list. Do not invent callers, files, or behavior not shown.
- The ground-truth list reflects static analysis of the parsed source -
  it will not capture calls made via dynamic dispatch, reflection, or
  code the parser couldn't resolve. Don't claim it is a guaranteed
  complete picture of every real-world call path; if the question hinges
  on that completeness, say so briefly rather than presenting it as
  absolute.
- Do not pad the answer with information the question didn't ask for.

Be concise: match the length and depth of your answer to what was
actually asked - a lookup question deserves a short factual answer, not
a full impact report.
"""


class ImpactReasoner:

    def __init__(self, chunk_store=None, graph_tool=None, llm_client=None):

        self.chunk_store = (
            chunk_store if chunk_store is not None else self._default_chunk_store()
        )
        self.graph_tool = graph_tool
        self.llm_client = llm_client
        self.fallback = ImpactExplainer()

    def _default_chunk_store(self):

        try:
            return ChunkStore()
        except (FileNotFoundError, OSError):
            return None

    def explain(self, impact_result, query=None):
        symbol = impact_result["changed_symbol"]
        affected = impact_result["affected_nodes"]

        if not affected:
            return f"No callers found for `{symbol}` - there are no known callers, direct or indirect, in the indexed code."

        if not self.chunk_store:
            return self.fallback.explain(impact_result)

        tagged = self._get_tagged_affected(symbol, affected)

        symbol_chunks = self.chunk_store.get_by_name(symbol, limit=1)
        caller_chunks = self.chunk_store.get_for_names(affected, total_limit=4)

        sources_block = format_sources(symbol_chunks + caller_chunks)

        evidence_lines = "\n".join(
            f"- {node} (distance {depth}, {'DIRECT' if depth == 1 else 'INDIRECT'})"
            for node, depth in tagged
        )

        question_text = query.strip() if query and query.strip() else (
            f"What breaks if I change {symbol}?"
        )

        user_message = (
            f"USER QUESTION: {question_text}\n\n"
            f"SYMBOL: {symbol}\n\n"
            f"GROUND-TRUTH CALLERS ({len(affected)} total):\n"
            f"{evidence_lines}\n\n"
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
            return self.fallback.explain(impact_result)

    def _get_tagged_affected(self, symbol, affected):
        
        if self.graph_tool:
            tagged = self.graph_tool.impact_with_depth(symbol)
            if tagged:
                return tagged

        return [(node, 1) for node in affected]