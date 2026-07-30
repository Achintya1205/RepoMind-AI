from tree_sitter import Parser, Language
import tree_sitter_javascript


parser = Parser(
    Language(tree_sitter_javascript.language())
)


with open("ingestion/parsers/sample.js", "rb") as f:
    source = f.read()


tree = parser.parse(source)


def print_tree(node, source, indent=0):

    print(
        " " * indent,
        node.type,
        source[node.start_byte:node.end_byte].decode(errors="ignore")
    )

    for child in node.children:
        print_tree(child, source, indent + 2)


print_tree(tree.root_node, source)