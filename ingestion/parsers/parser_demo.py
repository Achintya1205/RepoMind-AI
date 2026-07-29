from pathlib import Path

from tree_sitter import Language, Parser
from tree_sitter import Query, QueryCursor

import tree_sitter_python
import tree_sitter_javascript


class ParserDemo:

    def __init__(self):

        self.python_language = Language(tree_sitter_python.language())
        self.javascript_language = Language(tree_sitter_javascript.language())


    def get_parser(self, language):

        parser = Parser(language)

        return parser


    def parse_file(self, file_path, language):

        parser = self.get_parser(language)

        source = Path(file_path).read_bytes()

        tree = parser.parse(source)

        return tree, source



    def extract_functions(self, file_path, language, query_file):

        tree, source = self.parse_file(file_path, language)

        query_text = Path(query_file).read_text()

        query = Query(language, query_text)

        cursor = QueryCursor(query)

        captures = cursor.captures(tree.root_node)


        functions = []

        for node in captures.get("function.name", []):

            function_name = source[
                node.start_byte:node.end_byte
            ].decode()

            functions.append(
                {
                    "name": function_name,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1
                }
            )

        return functions



def main():

    parser = ParserDemo()


    print("\nPython Functions")
    print("----------------")

    python_functions = parser.extract_functions(
        "ingestion/parsers/sample.py",
        parser.python_language,
        "ingestion/parsers/queries/python.scm"
    )

    for func in python_functions:
        print(func)



    print("\nJavaScript Functions")
    print("-------------------")

    js_functions = parser.extract_functions(
        "ingestion/parsers/sample.js",
        parser.javascript_language,
        "ingestion/parsers/queries/javascript.scm"
    )

    for func in js_functions:
        print(func)



if __name__ == "__main__":
    main()