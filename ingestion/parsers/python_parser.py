from pathlib import Path
import json

from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python


class PythonParser:

    def __init__(self):
        self.language = Language(tree_sitter_python.language())
        self.parser = Parser(self.language)

        query_path = (
            Path(__file__).parent
            / "queries"
            / "python.scm"
        )

        self.function_query = Query(
            self.language,
            query_path.read_text()
        )

    def parse_file(self, file_path):

        source = Path(file_path).read_bytes()

        tree = self.parser.parse(source)

        return tree, source

    def extract_entities(self, tree, source):

        cursor = QueryCursor(self.function_query)

        captures = cursor.captures(tree.root_node)

        functions = []
        classes = []
        imports = []
        decorators = []
        calls = []

        for name_node, def_node in zip(
            captures.get("function.name", []),
            captures.get("function.definition", [])
        ):

            functions.append(
                {
                    "name": source[name_node.start_byte:name_node.end_byte].decode(),
                    "start_line": def_node.start_point[0] + 1,
                    "end_line": def_node.end_point[0] + 1,
                    "start_byte": def_node.start_byte,
                    "end_byte": def_node.end_byte,
                    "code": source[def_node.start_byte:def_node.end_byte].decode()
                }
            )

        for name_node, def_node in zip(
            captures.get("class.name", []),
            captures.get("class.definition", [])
        ):

            classes.append(
                {
                    "name": source[name_node.start_byte:name_node.end_byte].decode(),
                    "start_line": def_node.start_point[0] + 1,
                    "end_line": def_node.end_point[0] + 1,
                    "start_byte": def_node.start_byte,
                    "end_byte": def_node.end_byte,
                    "code": source[def_node.start_byte:def_node.end_byte].decode()
                }
            )
        for node in captures.get("import", []):

            imports.append(
                {
                    "statement": source[node.start_byte:node.end_byte].decode(),
                    "start_line": node.start_point[0] + 1
                }
            )

        for node in captures.get("decorator", []):

            decorators.append(
                {
                    "name": source[node.start_byte:node.end_byte].decode(),
                    "start_line": node.start_point[0] + 1
                }
            )

        for node in captures.get("call.name", []):

            caller = None

            for function in functions:

                if (
                    function["start_line"] <= node.start_point[0] + 1
                    <= function["end_line"]
                ):
                    caller = function["name"]
                    break


            calls.append(
                {
                    "name": source[node.start_byte:node.end_byte].decode(),
                    "caller": caller,
                    "start_line": node.start_point[0] + 1
                }
            )

        return functions, classes, imports, decorators, calls

    def process_file(self, file_path):

        tree, source = self.parse_file(file_path)

        functions, classes, imports, decorators, calls = self.extract_entities(tree, source)
        return {
            "file": str(file_path),
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "decorators": decorators,
            "calls": calls,
        }

if __name__ == "__main__":

    parser = PythonParser()

    sample = "ingestion/parsers/sample.py"

    result = parser.process_file(sample)

    print(json.dumps(result, indent=4))