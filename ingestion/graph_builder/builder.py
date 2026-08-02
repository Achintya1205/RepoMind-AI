import json
from pathlib import Path
from ingestion.graph_builder.resolver import ImportResolver
import pickle
from pathlib import Path

import networkx as nx


class DependencyGraphBuilder:

    def __init__(self, repo_root):

        self.graph = nx.DiGraph()

        self.resolver = ImportResolver(repo_root)

        self.function_nodes = {}

    def load_ast(self, json_file):

        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def add_file_node(self, file_path):

        self.graph.add_node(
            file_path,
            node_type="file"
        )

    def add_function_node(self, file_path, function):

        node_id = f"{file_path}::{function['name']}"

        self.graph.add_node(
            node_id,
            node_type="function",
            name=function["name"]
        )

        self.graph.add_edge(
            file_path,
            node_id,
            edge_type="DEFINES"
        )

        self.function_nodes[
            (file_path, function["name"])
        ] = node_id

    def add_class_node(self, file_path, cls):

        node_id = f"{file_path}::{cls['name']}"

        self.graph.add_node(
            node_id,
            node_type="class",
            name=cls["name"]
        )

        self.graph.add_edge(
            file_path,
            node_id,
            edge_type="DEFINES"
        )

    def add_call_edges(self, file_data):

        current_file = file_data["file"]

        for call in file_data.get("calls", []):

            caller_name = call.get("caller")

            callee_name = call.get("name")

            if caller_name is None:
                continue


            caller_id = self.function_nodes.get(
                (
                    current_file,
                    caller_name
                )
            )

            callee_id = self.function_nodes.get(
                (
                    current_file,
                    callee_name
                )
            )


            if (caller_id and callee_id and caller_id != callee_id):

                self.graph.add_edge(
                    caller_id,
                    callee_id,
                    edge_type="CALLS"
                )

    def add_import_edges(self, file_data):

        current_file = file_data["file"]

        for import_data in file_data.get("imports", []):

            statement = import_data.get("statement")

            if not statement:
                continue


            imported_file = None


            # JavaScript / TypeScript imports
            if statement.startswith("import"):

                if " from " in statement:

                    import_path = (
                        statement
                        .split(" from ")[1]
                        .strip()
                        .replace("'", "")
                        .replace('"', "")
                        .replace(";", "")
                    )

                    imported_file = self.resolver.resolve_javascript_import(
                        current_file,
                        import_path
                    )


            elif statement.startswith("from"):

                module = (
                    statement
                    .split("from")[1]
                    .strip()
                    .split(" import")[0]
                )

                imported_file = self.resolver.resolve_python_import(
                    current_file,
                    module
                )


            elif statement.startswith("import"):

                module = (
                    statement
                    .replace("import", "")
                    .strip()
                    .split()[0]
                )

                imported_file = self.resolver.resolve_python_import(
                    current_file,
                    module
                )


            if imported_file:

                self.graph.add_edge(
                    current_file,
                    imported_file,
                    edge_type="IMPORTS"
                )

    def build_graph(self, ast_data):

        for file_data in ast_data:

            file_path = file_data["file"]

            self.add_file_node(file_path)

            self.add_import_edges(file_data)

            for function in file_data.get("functions", []):
                self.add_function_node(file_path, function)

            for function in file_data.get("arrow_functions", []):
                self.add_function_node(file_path, function)

            for cls in file_data.get("classes", []):
                self.add_class_node(file_path, cls)

            self.add_call_edges(file_data)

        Path("graph_output").mkdir(exist_ok=True)

        with open("graph_output/dependency_graph.pkl", "wb") as f:
            pickle.dump(self.graph, f)

        return self.graph
    