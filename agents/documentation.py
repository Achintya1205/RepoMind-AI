from retrieval.hybrid_retriever import HybridRetriever
import re


class DocumentationGenerator:

    def __init__(self):
        self.retriever = HybridRetriever()


    def generate(self, query):

        chunks = self.retriever.hybrid_retrieve(query)
        symbol = None

        match = re.search(
            r"(?:for|of)\s+([A-Za-z_][A-Za-z0-9_]*)",
            query
        )

        if match:
            symbol = match.group(1)


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