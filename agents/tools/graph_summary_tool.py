import pickle
from pathlib import Path
from collections import Counter


GRAPH_PATH = Path("graph_output/dependency_graph.pkl")


class GraphSummaryTool:

    def __init__(self):
        with open(GRAPH_PATH, "rb") as f:
            self.graph = pickle.load(f)

    def file_count(self):
        return sum(
            1
            for _, data in self.graph.nodes(data=True)
            if data.get("node_type") == "file"
        )

    def function_count(self):
        return sum(
            1
            for _, data in self.graph.nodes(data=True)
            if data.get("node_type") == "function"
        )

    def class_count(self):
        return sum(
            1
            for _, data in self.graph.nodes(data=True)
            if data.get("node_type") == "class"
        )

    def language_breakdown(self):
        """
        Counts file nodes by extension so the architecture summary can
        describe what the repository actually is, instead of assuming
        it. A repo indexed via the dynamic pipeline could be pure
        Python, pure JS/TS, or a mix of both.
        """

        counts = Counter()

        for node, data in self.graph.nodes(data=True):

            if data.get("node_type") != "file":
                continue

            ext = Path(node).suffix.lower()

            if ext:
                counts[ext] += 1

        return dict(counts)

    def edge_counts(self):
        counter = Counter()

        for _, _, data in self.graph.edges(data=True):
            counter[data.get("edge_type")] += 1

        return dict(counter)

    def top_modules(self, k=10):

        imports = Counter()

        ignore = [
            "test",
            "tests",
            "__tests__",
            "mock",
            "mocks",
            "storybook",
            ".config"
        ]

        for src, dst, data in self.graph.edges(data=True):

            if data.get("edge_type") != "IMPORTS":
                continue

            path = dst.lower()

            if any(x in path for x in ignore):
                continue

            imports[dst] += 1

        return imports.most_common(k)

    def entry_points(self):

        entries = []

        include = [
            # JavaScript / TypeScript
            "main.ts",
            "main.tsx",
            "index.tsx",
            "server.ts",
            "server.js",
            "app.ts",
            "app.js",
            "next.config",
            "vite.config",
            # Python
            "main.py",
            "__main__.py",
            "cli.py",
            "manage.py",
            "app.py",
            "wsgi.py",
            "asgi.py",
        ]

        ignore = [
            "__tests__",
            "test",
            "mock",
            "components",
            "features",
            "pages",
            "layout",
            "page.tsx",
            "seo",
            "ui"
        ]

        for node, data in self.graph.nodes(data=True):

            if data.get("node_type") != "file":
                continue

            path = node.lower()

            if any(x in path for x in ignore):
                continue

            filename = Path(path).name

            if any(x in filename for x in include):
                entries.append(node)

        return entries

    def summary(self):

        return {
            "files": self.file_count(),
            "functions": self.function_count(),
            "classes": self.class_count(),
            "edges": self.edge_counts(),
            "top_modules": self.top_modules(),
            "entry_points": self.entry_points(),
            "languages": self.language_breakdown()
        }