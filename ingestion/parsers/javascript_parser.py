from pathlib import Path
import json

from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_javascript


class JavascriptParser:

    def __init__(self):

        self.language = Language(
            tree_sitter_javascript.language()
        )

        self.parser = Parser(self.language)

        query_path = (
            Path(__file__).parent
            / "queries"
            / "javascript.scm"
        )

        self.query = Query(
            self.language,
            query_path.read_text()
        )


    def parse_file(self, file_path):

        source = Path(file_path).read_bytes()

        tree = self.parser.parse(source)

        return tree, source


    def extract_functions(self, tree, source):

        cursor = QueryCursor(self.query)

        captures = cursor.captures(tree.root_node)

        functions = []

        names = captures.get("function.name", [])
        definitions = captures.get("function.definition", [])


        for name_node, function_node in zip(names, definitions):

            functions.append(
                {
                    "name": source[name_node.start_byte:name_node.end_byte].decode(),
                    "start_line": function_node.start_point[0] + 1,
                    "end_line": function_node.end_point[0] + 1,
                    "start_byte": function_node.start_byte,
                    "end_byte": function_node.end_byte,
                    "code": source[function_node.start_byte:function_node.end_byte].decode()
                }
            )


        return functions

    def extract_arrow_functions(self, tree, source):

        cursor = QueryCursor(self.query)

        captures = cursor.captures(tree.root_node)

        arrows = []

        names = captures.get("arrow.name", [])
        definitions = captures.get("arrow.definition", [])


        for name_node, arrow_node in zip(names, definitions):

            arrows.append(
                {
                    "name": source[name_node.start_byte:name_node.end_byte].decode(),
                    "start_line": arrow_node.start_point[0] + 1,
                    "end_line": arrow_node.end_point[0] + 1,
                    "start_byte": arrow_node.start_byte,
                    "end_byte": arrow_node.end_byte,
                    "code": source[arrow_node.start_byte:arrow_node.end_byte].decode()
                }
            )

        return arrows

    def extract_classes(self, tree, source):

        cursor = QueryCursor(self.query)

        captures = cursor.captures(tree.root_node)

        classes = []

        names = captures.get("class.name", [])
        definitions = captures.get("class.definition", [])


        for name_node, class_node in zip(names, definitions):

            classes.append(
                {
                    "name": source[name_node.start_byte:name_node.end_byte].decode(),
                    "start_line": class_node.start_point[0] + 1,
                    "end_line": class_node.end_point[0] + 1,
                    "start_byte": class_node.start_byte,
                    "end_byte": class_node.end_byte,
                    "code": source[class_node.start_byte:class_node.end_byte].decode()
                }
            )

        return classes

    def extract_imports(self, tree, source):

        cursor = QueryCursor(self.query)

        captures = cursor.captures(tree.root_node)

        imports = []

        for node in captures.get("import", []):

            imports.append(
                {
                    "statement": source[node.start_byte:node.end_byte].decode(),
                    "start_line": node.start_point[0] + 1
                }
            )

        return imports

    def extract_exports(self, tree, source):

        cursor = QueryCursor(self.query)

        captures = cursor.captures(tree.root_node)

        exports = []

        for node in captures.get("export", []):

            exports.append(
                {
                    "statement": source[node.start_byte:node.end_byte].decode(),
                    "start_line": node.start_point[0] + 1
                }
            )

        return exports
            
    def extract_calls(self, tree, source, functions):

        cursor = QueryCursor(self.query)

        captures = cursor.captures(tree.root_node)

        calls = []

        for node in captures.get("call.name", []):

            caller = None

            for function in functions:

                if (
                    function["start_byte"] <= node.start_byte
                    <= function["end_byte"]
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

        return calls
    def extract_jsx(self, tree, source):

        cursor = QueryCursor(self.query)

        captures = cursor.captures(tree.root_node)

        jsx_nodes = []

        for node in captures.get("jsx", []):

            jsx_nodes.append(
                {
                    "text": source[node.start_byte:node.end_byte].decode(),
                    "start_line": node.start_point[0] + 1
                }
            )

        return jsx_nodes


    def process_file(self, file_path):

        tree, source = self.parse_file(file_path)

        functions = (
            self.extract_functions(
                tree,
                source
            )
            +
            self.extract_arrow_functions(
                tree,
                source
            )
        )
        classes = self.extract_classes(
           tree,
           source
        )
        imports = self.extract_imports(
            tree, 
            source
        )

        exports = self.extract_exports(
            tree, 
            source
        )
        calls = self.extract_calls(
            tree,
            source,
            functions
        )
        arrows = self.extract_arrow_functions(
            tree,
            source
        )
        jsx = self.extract_jsx(
            tree, 
            source
        )

        return {
            "file": str(file_path),
            "functions": functions,
            "arrow_functions": arrows,
            "classes": classes,
            "imports": imports,
            "exports": exports,
            "calls": calls,
            "jsx": jsx,
        }


if __name__ == "__main__":

    parser = JavascriptParser()

    sample = "ingestion/parsers/sample.js"

    result = parser.process_file(sample)

    print(json.dumps(result, indent=4))