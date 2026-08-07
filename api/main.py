from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agents.graph import app

import json
import time


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


def create_initial_state(query: str):

    return {
        "query": query,
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


@api.post("/chat")
def chat(request: ChatRequest):

    initial_state = create_initial_state(request.query)

    result = app.invoke(initial_state)

    return {
        "answer": result.get("answer", ""),
        "agent": result.get("current_agent", ""),
        "citations": result.get("metadata", [])
    }



@api.post("/chat/stream")
def chat_stream(request: ChatRequest):

    initial_state = create_initial_state(request.query)


    def event_generator():

        yield f"data: {json.dumps({'type':'status','message':'Starting router...'})}\n\n"


        for chunk in app.stream(initial_state):

            for node, state in chunk.items():

                yield f"data: {json.dumps({'type':'agent','message':f'{node} completed'})}\n\n"

                time.sleep(0.2)


                if node == "qa" and state.get("answer"):

                    yield f"data: {json.dumps({'type':'answer','message':state['answer']})}\n\n"


                if node == "qa" and state.get("metadata"):

                    yield f"data: {json.dumps({'type':'citations','data':state['metadata']})}\n\n"


        yield f"data: {json.dumps({'type':'done'})}\n\n"



    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )