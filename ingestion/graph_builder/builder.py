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
        self.functions_by_name = {}
        self.external_names_by_file = {}

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

        self.functions_by_name.setdefault(
            function["name"], []
        ).append(node_id)

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

        external_names = self.external_names_by_file.get(current_file, set())

        for call in file_data.get("calls", []):

            caller_name = call.get("caller")
            raw_callee = call.get("name")

            if caller_name is None or raw_callee is None:
                continue
            if "." in raw_callee:

                receiver = raw_callee.split(".")[0]

                if receiver != "self" and receiver in external_names:
                    continue

            callee_name = raw_callee.split(".")[-1]
            caller_id = self.function_nodes.get(
                (current_file, caller_name)
            )

            if caller_id is None:
                continue

            callee_id = self._resolve_callee(
                current_file,
                callee_name
            )

            if callee_id and callee_id != caller_id:

                self.graph.add_edge(
                    caller_id,
                    callee_id,
                    edge_type="CALLS"
                )

    def _resolve_callee(self, current_file, callee_name):

        same_file = self.function_nodes.get(
            (current_file, callee_name)
        )

        if same_file:
            return same_file

        imported_files = [
            v for u, v, d in self.graph.out_edges(current_file, data=True)
            if d.get("edge_type") == "IMPORTS"
        ]

        for imported_file in imported_files:

            candidate = self.function_nodes.get(
                (imported_file, callee_name)
            )

            if candidate:
                return candidate

        candidates = self.functions_by_name.get(callee_name)

        if candidates and len(candidates) == 1:
            return candidates[0]

        return None

    def add_import_edges(self, file_data):

        current_file = file_data["file"]

        for import_data in file_data.get("imports", []):

            statement = import_data.get("statement")

            if not statement:
                continue


            imported_file = None

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

            self.external_names_by_file[file_path] = self._extract_external_names(
                file_data
            )

            for function in file_data.get("functions", []):
                self.add_function_node(file_path, function)

            for function in file_data.get("arrow_functions", []):
                self.add_function_node(file_path, function)

            for cls in file_data.get("classes", []):
                self.add_class_node(file_path, cls)

        for file_data in ast_data:
            self.add_call_edges(file_data)

        Path("graph_output").mkdir(exist_ok=True)

        with open("graph_output/dependency_graph.pkl", "wb") as f:
            pickle.dump(self.graph, f)

        return self.graph

    def _extract_external_names(self, file_data):

        names = set()

        for import_data in file_data.get("imports", []):

            statement = import_data.get("statement")

            if statement:
                names.update(self._names_bound_by_import(statement))

        return names

    def _names_bound_by_import(self, statement):

        statement = statement.strip().rstrip(";").rstrip(",")
        names = set()

        if statement.startswith("from") and " import " in statement:

            imported_part = statement.split(" import ", 1)[1]

            for piece in imported_part.split(","):
                piece = piece.strip()

                if not piece or piece == "*":
                    continue

                bound = (
                    piece.split(" as ")[-1].strip()
                    if " as " in piece
                    else piece
                )

                if bound:
                    names.add(bound)

            return names

        if statement.startswith("import") and "{" not in statement and " from " not in statement:

            imported_part = statement[len("import"):].strip()
            for piece in imported_part.split(","):

                piece = piece.strip()

                if not piece:
                    continue

                bound = (
                    piece.split(" as ")[-1].strip()
                    if " as " in piece
                    else piece.split(".")[0].strip()
                )
                if bound:
                    names.add(bound)

            return names

        if statement.startswith("import") and " from " in statement:

            head = statement.split(" from ")[0][len("import"):].strip()
            if head.startswith("*"):

                alias = head.split(" as ")[-1].strip()

                if alias:
                    names.add(alias)

                return names

            default_part = head
            named_part = None

            if "{" in head:
                default_part, rest = head.split("{", 1)
                named_part = rest.split("}")[0]

            default_part = default_part.strip().rstrip(",").strip()

            if default_part:
                names.add(default_part)

            if named_part:

                for piece in named_part.split(","):
                    piece = piece.strip()

                    if not piece:
                        continue

                    bound = (
                        piece.split(" as ")[-1].strip()
                        if " as " in piece
                        else piece
                    )

                    if bound:
                        names.add(bound)

            return names

        return names