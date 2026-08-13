import json
from pathlib import Path

import chromadb

from retrieval.embedder import Embedder


CHUNKS_PATH = Path(
    "ingestion/chunker/chunks.json"
)


class VectorStore:

    def __init__(self):

        self.client = chromadb.PersistentClient(
            path="chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name="repomind"
        )

        self.embedder = Embedder()


    def reset_collection(self):
        """
        Deletes and recreates the collection. Must be called before
        re-indexing a new repository - otherwise old embeddings from
        whatever was indexed previously stay in the store and get mixed
        into search results for the new repo.
        """

        self.client.delete_collection(name="repomind")

        self.collection = self.client.get_or_create_collection(
            name="repomind"
        )


    def index_chunks(self):

        with open(
            CHUNKS_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            chunks = json.load(f)

            if not chunks:
                print("No chunks to index.")
                return

            print(
                "Sample metadata:",
                chunks[0]["metadata"]
            )


        for i, chunk in enumerate(chunks):

            embedding = self.embedder.embed(
                chunk["content"]
            ).tolist()


            metadata = {
                k: v
                for k, v in chunk["metadata"].items()
                if v is not None
            }


            self.collection.add(
                ids=[str(i)],
                embeddings=[embedding],
                documents=[chunk["content"]],
                metadatas=[metadata]
            )


        print(
            f"Indexed {len(chunks)} chunks"
        )


    def search(self, query, k=5):

        query_embedding = self.embedder.embed(
            query
        ).tolist()


        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )


        output = []


        for i in range(
            len(results["documents"][0])
        ):

            output.append(
                {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                }
            )


        return output


if __name__ == "__main__":

    store = VectorStore()

    store.index_chunks()


    results = store.search(
        "Where is authentication implemented?",
        k=5
    )


    for result in results:

        print("\n----------------")

        print(
            result["metadata"]
        )

        print(
            result["distance"]
        )