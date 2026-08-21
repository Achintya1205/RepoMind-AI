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
2. ENTRY POINT SOURCE CODE - real code snippets from the repository's
   detected entry point files, where available.

Using ONLY this evidence, write a clear, accurate explanation of the
repository's architecture: what kind of project it is, how it is organized,
and how its main parts relate to one another.

Rules:
- Do not invent frameworks, patterns, folder conventions, or structure that
  isn't supported by the evidence shown.
- Do not simply restate the raw numbers - synthesize them into an
  explanation a developer would actually find useful.
- If entry point source code is unavailable or the evidence is sparse, say
  so plainly rather than guessing or padding with generic description.
- Be concise: 3-5 sentences.
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

    def analyze(self):

        summary = self.graph_summary.summary()

        facts_block = self._render_facts(summary)
        narrative = self._reason_about_architecture(summary)

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

    def _reason_about_architecture(self, summary):

        entry_points = summary.get("entry_points", [])

        entry_chunks = (
            self.chunk_store.get_for_files(entry_points)
            if self.chunk_store
            else []
        )

        facts_text = self._render_facts(summary)
        sources_block = format_sources(entry_chunks)

        user_message = (
            f"STRUCTURAL FACTS:\n{facts_text}\n\n"
            f"ENTRY POINT SOURCE CODE:\n{sources_block}"
        )

        try:
            return generate(
                SYSTEM_PROMPT,
                user_message,
                max_output_tokens=500,
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