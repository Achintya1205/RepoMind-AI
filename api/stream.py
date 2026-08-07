from fastapi.responses import StreamingResponse
import json
from agents.graph import app


def event_generator(query):

    initial_state = {
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

    for event in app.stream(initial_state):
        yield f"data: {json.dumps(event)}\n\n"


def stream_chat(query):
    return StreamingResponse(
        event_generator(query),
        media_type="text/event-stream"
    )