from agents.tools.graph_summary_tool import GraphSummaryTool


class ArchitectureAgent:

    def __init__(self):
        self.graph_summary = GraphSummaryTool()


    def analyze(self):

        summary = self.graph_summary.summary()

        explanation = self.generate_explanation(
            summary
        )

        return {
            "summary": summary,
            "explanation": explanation
        }


    def generate_explanation(self, summary):

        files = summary["files"]
        functions = summary["functions"]
        classes = summary["classes"]

        top_modules = summary["top_modules"]
        entry_points = summary["entry_points"]


        modules_text = "\n".join(
            [
                f"- {module}"
                for module, count in top_modules
            ]
        )


        entry_text = "\n".join(
            [
                f"- {entry}"
                for entry in entry_points[:10]
            ]
        )


        return f"""
Repository Architecture Overview

The repository contains:

- Files: {files}
- Functions: {functions}
- Classes: {classes}

The dependency graph contains:

{summary["edges"]}


Important modules:

{modules_text}


Detected entry points:

{entry_text}


Architecture Summary:

This repository is a multi-application frontend codebase.
The structure is organized around reusable components,
features, utilities, and application-specific modules.

The dependency graph shows how modules interact through imports
and function relationships. The main architecture follows a
feature-based organization where business features are separated
from shared UI components and utilities.
"""