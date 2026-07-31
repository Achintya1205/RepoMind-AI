from hybrid_retriever import HybridRetriever


retriever = HybridRetriever()


results = retriever.hybrid_retrieve(
    "How does authentication work?",
    k=5
)


for r in results:

    print("\n----------------")
    print(r["chunk"]["metadata"])
    print(r["rerank_score"])