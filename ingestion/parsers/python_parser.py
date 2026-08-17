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

        matches = cursor.matches(tree.root_node)

        functions = []
        classes = []
        imports = []
        decorators = []
        call_nodes = []
        calls = []

        # Pass 1: collect all functions/classes/imports/decorators, and stash raw call nodes for pass 2 - caller attribution needs the COMPLETE functions list first, and matches() order is not
        # guaranteed to be sequential by document position, so a call can't safely be attributed inline in a single pass.
        for pattern_index, captures_dict in matches:

            if "function.name" in captures_dict:

                name_node = captures_dict["function.name"][0]
                def_node = captures_dict["function.definition"][0]

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

            elif "class.name" in captures_dict:

                name_node = captures_dict["class.name"][0]
                def_node = captures_dict["class.definition"][0]

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

            elif "import" in captures_dict:

                node = captures_dict["import"][0]

                imports.append(
                    {
                        "statement": source[node.start_byte:node.end_byte].decode(),
                        "start_line": node.start_point[0] + 1
                    }
                )

            elif "decorator" in captures_dict:

                node = captures_dict["decorator"][0]

                decorators.append(
                    {
                        "name": source[node.start_byte:node.end_byte].decode(),
                        "start_line": node.start_point[0] + 1
                    }
                )

            elif "call.name" in captures_dict:

                call_nodes.append(captures_dict["call.name"][0])

        # Pass 2: attribute each call to its enclosing function with the complete functions list available.
        for node in call_nodes:

            caller = None
            caller_span = None

            for function in functions:

                if (
                    function["start_line"] <= node.start_point[0] + 1
                    <= function["end_line"]
                ):

                    span = function["end_line"] - function["start_line"]

                    if caller_span is None or span < caller_span:
                        caller = function["name"]
                        caller_span = span

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