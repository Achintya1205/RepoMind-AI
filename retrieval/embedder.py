from sentence_transformers import SentenceTransformer


class Embedder:

    def __init__(self):

        self.model = SentenceTransformer(
            "BAAI/bge-small-en-v1.5"
        )

    def embed(self, text):

        embedding = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return embedding


if __name__ == "__main__":

    embedder = Embedder()

    embedding = embedder.embed(
        "Hello World"
    )

    print(type(embedding))
    print(len(embedding))