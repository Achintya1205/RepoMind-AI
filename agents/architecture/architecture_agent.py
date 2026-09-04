from agents.tools.graph_summary_tool import GraphSummaryTool
from agents.utils.chunk_lookup import ChunkStore
from agents.utils.sources import format_sources
from agents.llm.client import generate


SYSTEM_PROMPT = """You are analyzing the architecture of a software repository.

You are given:
1. STRUCTURAL FACTS computed deterministically from the repository's real
   dependency graph (file/function/class counts, edge counts, detected
   languages, entry points, most-imported modules). These facts are exact
   and ground truth - never contradict them.
2. REPRESENTATIVE SOURCE CODE - real code snippets from the repository's
   detected entry points and most-imported modules, where available.
3. The user's actual question about this repository.

Using ONLY this evidence, answer the user's question with a genuine
component/data-flow explanation - not a restatement of the structural
facts. Specifically:

- Identify the main components/modules the evidence reveals (e.g. a CLI
  entry point, a core logic module, a set of utilities) and describe what
  each one is responsible for, based on what the code actually shows.
- Explain how these components relate: what calls what, what imports
  what, and where data/control flow moves between them - citing
  (file:start_line-end_line) when referencing specific code.
- Directly address what the user asked, not a generic architecture
  summary, if their question is specific (e.g. about a particular pattern
  or flow).

Rules:
- Do not invent frameworks, patterns, folder conventions, components, or
  relationships that aren't supported by the evidence shown.
- Do not construct a confident causal explanation for a NUMBER in the
  structural facts (e.g. "few imports means the code relies on decorator
  magic instead of imports") unless the shown source code actually
  demonstrates that mechanism. A low count often just means the code is
  small or simple - that is the more likely explanation and should be
  preferred unless the evidence specifically shows otherwise. If you're
  not sure why a number is what it is, don't guess a specific reason -
  just report the number, or say the evidence doesn't show why.
- Do not restate the raw numbers from STRUCTURAL FACTS (file/function
  counts, edge counts) - those are already shown to the user separately.
  Your job is the relationship/flow narrative, not a second copy of the
  statistics.
- If the evidence is sparse (e.g. no entry points detected, no source
  retrieved), say so plainly and explain what conclusions the graph facts
  alone can and cannot support, rather than padding with generic
  description.
- The dependency graph reflects static analysis of the parsed source - it
  will not capture dynamic imports, reflection-based dispatch, or code the
  parser couldn't resolve. Don't present it as a guaranteed-complete map
  of the repository's real structure.

Be substantive but concise: a few sentences per component/relationship,
not a wall of text.
"""


class ArchitectureAgent:

    def __init__(self, graph_summary=None, chunk_store=None, llm_client=None):

        self.graph_summary = graph_summary or GraphSummaryTool()
        self.chunk_store = (
            chunk_store if chunk_store is not None else self._default_chunk_store()
        )
        self.llm_client = llm_client

    def _default_chunk_store(self):

        try:
            return ChunkStore()
        except (FileNotFoundError, OSError):
            return None

    def analyze(self, query=None):

        summary = self.graph_summary.summary()

        facts_block = self._render_facts(summary)
        narrative = self._reason_about_architecture(summary, query)

        explanation = f"{facts_block}\n\nArchitecture Summary:\n\n{narrative}\n"

        return {
            "summary": summary,
            "explanation": explanation
        }

    def _render_facts(self, summary):

        files = summary["files"]
        functions = summary["functions"]
        classes = summary["classes"]
        edges = summary["edges"]
        top_modules = summary["top_modules"]
        entry_points = summary["entry_points"]

        modules_text = "\n".join(
            f"- {module}" for module, count in top_modules
        ) or "None detected."

        entry_text = "\n".join(
            f"- {entry}" for entry in entry_points[:10]
        ) or "None confidently detected."

        return f"""Repository Architecture Overview

The repository contains:

- Files: {files}
- Functions: {functions}
- Classes: {classes}

The dependency graph contains:

{edges}


Important modules:

{modules_text}


Detected entry points:

{entry_text}"""

    def _reason_about_architecture(self, summary, query=None):

        entry_points = summary.get("entry_points", [])
        top_modules = [module for module, count in summary.get("top_modules", [])]
        entry_chunks = (
            self.chunk_store.get_for_files(entry_points, per_file_limit=1)
            if self.chunk_store
            else []
        )
        module_chunks = (
            self.chunk_store.get_for_files(top_modules, per_file_limit=1)
            if self.chunk_store
            else []
        )

        seen_files = set()
        combined_chunks = []

        for chunk in entry_chunks + module_chunks:
            file = chunk["metadata"].get("file")
            if file in seen_files:
                continue
            seen_files.add(file)
            combined_chunks.append(chunk)

        facts_text = self._render_facts(summary)
        sources_block = format_sources(combined_chunks[:8])

        question_text = (
            query.strip()
            if query and query.strip()
            else "Explain this repository's overall architecture."
        )

        user_message = (
            f"USER QUESTION: {question_text}\n\n"
            f"STRUCTURAL FACTS:\n{facts_text}\n\n"
            f"REPRESENTATIVE SOURCE CODE:\n{sources_block}"
        )

        try:
            return generate(
                SYSTEM_PROMPT,
                user_message,
                max_output_tokens=700,
                client=self.llm_client
            )

        except Exception:
            return self._fallback_narrative(summary)

    def _fallback_narrative(self, summary):

        languages = summary.get("languages", {})
        edges = summary["edges"]
        functions = summary["functions"]
        classes = summary["classes"]

        return (
            f"{self._describe_languages(languages)} "
            f"{self._describe_composition(edges, functions, classes)} "
            "(LLM reasoning unavailable - showing a deterministic summary "
            "of the graph facts above instead.)"
        )

    def _describe_languages(self, languages):

        if not languages:
            return "No source files with a recognized language were found."

        py_exts = {".py"}
        js_exts = {".js", ".jsx", ".ts", ".tsx"}

        py_count = sum(n for ext, n in languages.items() if ext in py_exts)
        js_count = sum(n for ext, n in languages.items() if ext in js_exts)
        total = sum(languages.values())

        if py_count and js_count:
            return (
                f"This repository is a mixed-language codebase with "
                f"{py_count} Python file{'s' if py_count != 1 else ''} and "
                f"{js_count} JavaScript/TypeScript file{'s' if js_count != 1 else ''}."
            )

        if py_count and not js_count:
            return f"This repository is a Python codebase ({py_count} of {total} files)."

        if js_count and not py_count:
            return f"This repository is a JavaScript/TypeScript codebase ({js_count} of {total} files)."

        top_ext = max(languages, key=languages.get)
        return f"This repository is primarily composed of {top_ext} files."

    def _describe_composition(self, edges, functions, classes):

        calls = edges.get("CALLS", 0)
        imports = edges.get("IMPORTS", 0)

        if functions == 0:
            return "No functions were extracted from the parsed files."

        call_ratio = calls / functions

        if call_ratio > 1.5:
            density = "The call graph is densely interconnected, with functions frequently calling one another."
        elif call_ratio > 0.3:
            density = "The call graph shows a moderate level of interconnection between functions."
        else:
            density = "Functions appear largely independent of one another, with relatively few direct calls between them."

        module_note = (
            f"Files are connected by {imports} import relationship{'s' if imports != 1 else ''}."
            if imports
            else "Few or no cross-file import relationships were detected between the parsed files."
        )

        class_note = (
            f" The codebase defines {classes} class{'es' if classes != 1 else ''}."
            if classes
            else " No classes were detected; the codebase is primarily function-based."
        )

        return f"{density} {module_note}{class_note}"