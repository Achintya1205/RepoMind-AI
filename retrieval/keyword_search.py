import json
from pathlib import Path

from rank_bm25 import BM25Okapi


CHUNKS_PATH = Path(
    "ingestion/chunker/chunks.json"
)


class KeywordSearch:

    def __init__(self):

        with open(
            CHUNKS_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            self.chunks = json.load(f)


        self.documents = []

        for chunk in self.chunks:

            text = (
                chunk["content"]
                + " "
                + chunk["metadata"]["name"]
            )

            self.documents.append(
                text.lower().split()
            )


        self.bm25 = BM25Okapi(
            self.documents
        )


    def search(self, query, k=5):

        tokens = query.lower().split()

        scores = self.bm25.get_scores(
            tokens
        )


        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )


        results = []


        for index, score in ranked[:k]:

            results.append(
                {
                    "content": self.chunks[index]["content"],
                    "metadata": self.chunks[index]["metadata"],
                    "score": float(score)
                }
            )


        return results



if __name__ == "__main__":

    searcher = KeywordSearch()


    results = searcher.search(
        "login",
        k=5
    )


    for result in results:

        print("\n----------------")
        print("NAME:", result["metadata"]["name"])
        print("TYPE:", result["metadata"]["type"])
        print("SCORE:", result["score"])
       