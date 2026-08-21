from retrieval.hybrid_retriever import HybridRetriever
from agents.utils.symbol_extractor import extract_symbol
from agents.utils.sources import format_sources
from agents.llm.client import generate


SYSTEM_PROMPT = """You are a documentation generator for a codebase.

You will be given one or more numbered SOURCE snippets retrieved from the
repository, each with a file path and line range.

Write clear, accurate documentation for the code shown. For each source,
describe: what it does, its parameters/inputs and return value or effect
where visible in the code, and any notable behavior (error handling, side
effects, edge cases) that is actually shown.

Rules:
- Base every claim strictly on the code shown. Do not invent behavior,
  parameters, or return values that aren't visible in the source.
- Every section MUST end with a citation in the exact format
  (file:start_line-end_line), taken from the matching source's header.
- Use Markdown with a "## name" heading per documented item.
- If a source is too small or unclear to document meaningfully, say so
  briefly rather than padding with generic text.
"""


class DocumentationGenerator:

    def __init__(self, graph_tool, retriever=None, llm_client=None):

        self.retriever = retriever or HybridRetriever()
        self.graph_tool = graph_tool
        self.llm_client = llm_client

    def generate(self, query):

        chunks = self.retriever.hybrid_retrieve(query)

        symbol = extract_symbol(query, self.graph_tool)

        if symbol:

            filtered = [
                chunk
                for chunk in chunks
                if chunk["metadata"]["name"].lower() == symbol.lower()
            ]

            if filtered:
                chunks = filtered

        if not chunks:
            return {
                "documentation": "No relevant code was retrieved to document.",
                "citations": []
            }

        documentation = self._reason_about_docs(query, chunks)

        return {
            "documentation": documentation,
            "citations": [
                item["metadata"]
                for item in chunks
            ]
        }

    def _reason_about_docs(self, query, chunks):

        sources_block = format_sources(chunks)

        user_message = (
            f"REQUEST: {query}\n\n"
            f"SOURCES:\n{sources_block}\n\n"
            "Generate documentation for the code shown above, with "
            "(file:start_line-end_line) citations."
        )

        try:
            return generate(
                SYSTEM_PROMPT,
                user_message,
                max_output_tokens=1200,
                client=self.llm_client
            )

        except Exception:
            return self._fallback_docs(chunks)

    def _fallback_docs(self, chunks):

        sections = []

        for item in chunks:

            metadata = item["metadata"]
            content = item.get("chunk", item.get("content", ""))

            sections.append(
                f"""## {metadata.get('name')}

File: {metadata.get('file')}
Lines: {metadata.get('start_line')}-{metadata.get('end_line')}
Type: {metadata.get('type')}

```
{content}
```

(LLM reasoning unavailable - showing raw retrieved code only.)
"""
            )

        return "\n".join(sections)