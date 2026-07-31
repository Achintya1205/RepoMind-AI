from fastapi import FastAPI
from pydantic import BaseModel

from retrieval.hybrid_retriever import HybridRetriever


app = FastAPI(
    title="RepoMind AI"
)


retriever = HybridRetriever()


class QueryRequest(BaseModel):

    query: str
    k: int = 5



@app.get("/")
def home():

    return {
        "message": "RepoMind AI API running"
    }



@app.post("/query")
def query_repo(
    request: QueryRequest
):

    results = retriever.hybrid_retrieve(
        request.query,
        request.k
    )


    return {
        "query": request.query,
        "results": results
    }