from retrieval.hybrid_retriever import HybridRetriever
from agents.utils.symbol_extractor import extract_symbol


class DocumentationGenerator:

    def __init__(self, graph_tool):
        self.retriever = HybridRetriever()
        self.graph_tool = graph_tool


    def generate(self, query):

        chunks = self.retriever.hybrid_retrieve(query)

        symbol = extract_symbol(query, self.graph_tool)


        if symbol:

            filtered = [
                chunk
                for chunk in chunks
                if chunk["metadata"]["name"].lower() == symbol.lower()
            ]

            if filtered:
                chunks = filtered


        documentation = []

        for item in chunks:

            metadata = item["metadata"]

            documentation.append(
                f"""
## {metadata.get('name')}

File:
{metadata.get('file')}

Type:
{metadata.get('type')}

Lines:
{metadata.get('start_line')} - {metadata.get('end_line')}


Description:

The {metadata.get('type')} `{metadata.get('name')}` is implemented
in this module.

Relevant code:

{item['chunk']}

"""
            )


        return {
            "documentation": "\n".join(documentation),
            "citations": [
                item["metadata"]
                for item in chunks
            ]
        }