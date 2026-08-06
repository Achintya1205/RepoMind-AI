from fastapi import FastAPI
from pydantic import BaseModel

from agents.graph import app


api = FastAPI(
    title="RepoMind AI API"
)


class ChatRequest(BaseModel):
    query: str



@api.post("/chat")
def chat(request: ChatRequest):

    initial_state = {
        "query": request.query,
        "conversation_history": [],

        "retrieved_chunks": [],
        "graph_results": [],

        "retry_count": 0,
        "current_agent": "",

        "answer": "",
        "verified": {},

        "final_answer": {},
        "metadata": []
    }


    result = app.invoke(initial_state)


    return {
        "answer": result.get("answer"),
        "agent": result.get("current_agent"),
        "citations": result.get("metadata")
    }