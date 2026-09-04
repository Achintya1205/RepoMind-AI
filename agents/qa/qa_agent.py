from retrieval.hybrid_retriever import HybridRetriever
from agents.llm.client import generate
from agents.utils.sources import format_sources

SYSTEM_PROMPT = """You are a code Q&A agent for a codebase called RepoMind-AI.

You will be given a user question and a list of numbered SOURCE snippets
retrieved from the repository. Each source shows its file path and line range.

Rules:

1. Answer the question using ONLY information contained in the provided sources.
Do not use outside knowledge unless the source explicitly shows it.

2. Every factual claim about the code MUST end with a citation in the exact
format (file:start_line-end_line), taken from the matching source's header.

Example:
"The retriever calls the reranker after merging candidates
(retrieval/hybrid_retriever.py:70-79)."

3. If a source is not relevant to the question, ignore it. Do not force a
citation to unrelated sources.

4. Only say:
"The retrieved code does not show this."
when NONE of the provided sources contain useful information related to the
question.

If partial information exists, explain what can be determined from the sources
and clearly mention what is missing.

5. Be concise. Prefer direct, specific answers over general summaries.

6. If the question asks you to diagnose a cause, identify why something might
go wrong, or determine what's "likely" responsible for some behavior (a
root-cause / diagnostic-style question, even without a formal error or stack
trace) - distinguish what the sources actually PROVE from what you're
inferring. Don't state a specific root cause with confident language unless
the sources directly demonstrate it; use "likely", "one possibility is", or
similar when the evidence is suggestive but not conclusive, and say plainly
if the sources don't show enough to identify a cause at all.
"""
class QAAgent:

    def __init__(self, retriever=None, llm_client=None):

        self.retriever = retriever or HybridRetriever()
        self.llm_client = llm_client

    def answer(self, query, k=5):

        retrieved = self.retriever.hybrid_retrieve(query, k=3)

        if not retrieved:

            return {
                "query": query,
                "answer": "No relevant code was retrieved for this question.",
                "sources": []
            }

        sources_block = format_sources(retrieved)

        user_message = (
            f"QUESTION:\n{query}\n\n"
            f"SOURCES:\n{sources_block}\n\n"
            "Answer the question using only the sources above, with "
            "(file:start_line-end_line) citations on every factual claim."
        )

        answer_text = generate(
            SYSTEM_PROMPT,
            user_message,
            max_output_tokens=1500,
            client=self.llm_client
        )

        sources_out = [
            {
                "file": item["metadata"].get("file"),
                "start_line": item["metadata"].get("start_line"),
                "end_line": item["metadata"].get("end_line"),
                "name": item["metadata"].get("name"),
                "type": item["metadata"].get("type"),
                "rerank_score": item.get("rerank_score")
            }
            for item in retrieved
        ]

        return {
            "query": query,
            "answer": answer_text,
            "retrieved_chunks": retrieved,
            "sources": sources_out
        }


if __name__ == "__main__":

    agent = QAAgent()

    result = agent.answer(
        "Where is authentication implemented?"
    )

    print(result["answer"])
    print("\nSources used for retrieval:")

    for src in result["sources"]:
        print(f"  {src['file']}:{src['start_line']}-{src['end_line']}")