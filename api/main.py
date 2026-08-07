from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agents.graph import app
from api.stream import stream_chat


api = FastAPI(
    title="RepoMind AI API"
)


class ChatRequest(BaseModel):
    query: str

api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/stream")
def stream(query: str):
    return stream_chat(query)

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
        "answer": result.get("answer", ""),
        "agent": result.get("current_agent", ""),
        "citations": result.get("metadata", [])
    }