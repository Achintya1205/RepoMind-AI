from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agents.graph import dependency_graph
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

@api.get("/graph/{symbol}")
def get_graph(symbol: str):

    nodes = {}
    edges = []
    visited_edges = set()

    for node in dependency_graph.graph.nodes:

        node_name = str(node).split("::")[-1]

        if node_name.lower() == symbol.lower():

            nodes[str(node)] = {
                "id": str(node),
                "data": {
                    "label": str(node),
                    "type": "function"
                }
            }


            # outgoing
            for neighbor in dependency_graph.graph.successors(node):

                nodes[str(neighbor)] = {
                    "id": str(neighbor),
                    "data": {
                        "label": str(neighbor),
                        "type": "function"
                    }
                }

                edge_id = f"{node}-{neighbor}"

                if edge_id not in visited_edges:

                    edges.append({
                        "id": edge_id,
                        "source": str(node),
                        "target": str(neighbor)
                    })

                    visited_edges.add(edge_id)



            # incoming
            for caller in dependency_graph.graph.predecessors(node):

                nodes[str(caller)] = {
                    "id": str(caller),
                    "data": {
                        "label": str(caller),
                        "type": "function"
                    }
                }

                edge_id = f"{caller}-{node}"

                if edge_id not in visited_edges:

                    edges.append({
                        "id": edge_id,
                        "source": str(caller),
                        "target": str(node)
                    })

                    visited_edges.add(edge_id)


    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }

@api.get("/symbol/{symbol_id:path}")
def get_symbol(symbol_id: str):

    symbol_id = symbol_id.replace("/", "\\")

    result = {
        "callers": [],
        "callees": []
    }


    graph = dependency_graph.graph


    if symbol_id not in graph:

        print("NOT FOUND:", symbol_id)

        return result


    print("FOUND:", symbol_id)


    # CALLERS

    for caller in graph.predecessors(symbol_id):

        edge = graph.get_edge_data(
            caller,
            symbol_id
        )

        if edge.get("edge_type") == "CALLS":

            result["callers"].append(caller)



    # CALLEES

    for callee in graph.successors(symbol_id):

        edge = graph.get_edge_data(
            symbol_id,
            callee
        )

        if edge.get("edge_type") == "CALLS":

            result["callees"].append(callee)



    return result




@api.post("/chat")
def chat(request: ChatRequest):

    initial_state = create_initial_state(
        request.query
    )

    result = app.invoke(initial_state)


    return {
        "answer": result.get("final_answer", ""),
        "agent": result.get("current_agent", ""),
        "citations": result.get("metadata", [])
    }




@api.post("/chat/stream")
def chat_stream(request: ChatRequest):

    initial_state = create_initial_state(
        request.query
    )


    def event_generator():

        yield f"data: {json.dumps({'type':'status','message':'Starting router...'})}\n\n"


        for chunk in app.stream(initial_state):

            for node, state in chunk.items():

                yield f"data: {json.dumps({'type':'agent','message':f'{node} completed'})}\n\n"


                time.sleep(0.2)


                if state.get("answer"):

                    yield f"data: {json.dumps({'type':'answer','message':state['answer']})}\n\n"


                if state.get("metadata"):

                    yield f"data: {json.dumps({'type':'citations','data':state['metadata']})}\n\n"



        yield f"data: {json.dumps({'type':'done'})}\n\n"



    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )