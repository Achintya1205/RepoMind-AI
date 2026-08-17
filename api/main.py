from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agents import graph as agent_graph
from agents.graph import app
from agents.impact_explainer import ImpactExplainer

from ingestion.pipeline import index_repository, IndexingError

import json
import time
import threading
import queue as queue_module


api = FastAPI(
    title="RepoMind AI API"
)


class ChatRequest(BaseModel):
    query: str


class IndexRequest(BaseModel):
    repo_url: str


_indexing_lock = threading.Lock()

impact_explainer = ImpactExplainer()


def readable_label(node_id):
    # function/class nodes are "path::name" - show just the name.
    # file nodes are a raw path - show just the filename, not the
    # full (often long, Windows-style) path.
    node_str = str(node_id)

    if "::" in node_str:
        return node_str.split("::")[-1]

    return node_str.replace("\\", "/").split("/")[-1]


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

    dependency_graph = agent_graph.get_dependency_graph()

    nodes = {}
    edges = []
    visited_edges = set()

    for node in dependency_graph.graph.nodes:

        node_name = str(node).split("::")[-1]

        if node_name.lower() == symbol.lower():

            nodes[str(node)] = {
                "id": str(node),
                "data": {
                    "label": readable_label(node),
                    "type": "function"
                }
            }


            # outgoing
            for neighbor in dependency_graph.graph.successors(node):

                edge_data = dependency_graph.graph.get_edge_data(node, neighbor)

                if edge_data.get("edge_type") != "CALLS":
                    continue

                nodes[str(neighbor)] = {
                    "id": str(neighbor),
                    "data": {
                        "label": readable_label(neighbor),
                        "type": "function"
                    }
                }

                edge_id = f"{node}-{neighbor}"

                if edge_id not in visited_edges:

                    edges.append({
                        "id": edge_id,
                        "source": str(node),
                        "target": str(neighbor),
                        "type": "CALLS"
                    })

                    visited_edges.add(edge_id)



            # incoming
            for caller in dependency_graph.graph.predecessors(node):

                edge_data = dependency_graph.graph.get_edge_data(caller, node)

                if edge_data.get("edge_type") != "CALLS":
                    continue

                nodes[str(caller)] = {
                    "id": str(caller),
                    "data": {
                        "label": readable_label(caller),
                        "type": "function"
                    }
                }

                edge_id = f"{caller}-{node}"

                if edge_id not in visited_edges:

                    edges.append({
                        "id": edge_id,
                        "source": str(caller),
                        "target": str(node),
                        "type": "CALLS"
                    })

                    visited_edges.add(edge_id)


    # Disambiguate colliding labels (e.g. two different classes each
    # defining __init__) - only when a collision actually exists in
    # THIS result set, so the common case stays short and clean.
    from collections import Counter

    label_counts = Counter(
        n["data"]["label"] for n in nodes.values()
    )

    for node_id, node_data in nodes.items():

        label = node_data["data"]["label"]

        if label_counts[label] > 1:

            node_str = str(node_id)

            if "::" in node_str:

                filename = (
                    node_str.split("::")[0]
                    .replace("\\", "/")
                    .split("/")[-1]
                )

                node_data["data"]["label"] = f"{filename}::{label}"

    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }

@api.get("/symbol/{symbol_id:path}")
def get_symbol(symbol_id: str):

    result = {
        "callers": [],
        "callees": []
    }


    graph = agent_graph.get_dependency_graph().graph


    if symbol_id not in graph:

        return result


    # CALLERS

    for caller in graph.predecessors(symbol_id):

        edge = graph.get_edge_data(
            caller,
            symbol_id
        )

        if edge.get("edge_type") == "CALLS":

            result["callers"].append(readable_label(caller))



    # CALLEES

    for callee in graph.successors(symbol_id):

        edge = graph.get_edge_data(
            symbol_id,
            callee
        )

        if edge.get("edge_type") == "CALLS":

            result["callees"].append(readable_label(callee))



    return result

@api.get("/impact/{symbol_id:path}")
def get_impact(symbol_id: str):
    graph = agent_graph.get_dependency_graph().graph

    if symbol_id not in graph:
        return {
            "symbol": symbol_id,
            "affected_nodes": [],
            "affected_edges": [],
            "summary": None,
            "risk": "Unknown"
        }

    affected = set()

    # All callers recursively affected by changing this symbol
    stack = [symbol_id]

    while stack:
        current = stack.pop()

        for caller in graph.predecessors(current):
            edge = graph.get_edge_data(caller, current)

            if edge and edge.get("edge_type") == "CALLS":
                if caller not in affected:
                    affected.add(caller)
                    stack.append(caller)

    nodes = {symbol_id}
    nodes.update(affected)

    edges = []

    for source in nodes:
        for target in graph.successors(source):
            if target in nodes:
                edge = graph.get_edge_data(source, target)

                if edge and edge.get("edge_type") == "CALLS":
                    edges.append({
                        "id": f"{source}-{target}",
                        "source": str(source),
                        "target": str(target),
                        "type": "CALLS"
                    })

    summary = impact_explainer.explain({
        "changed_symbol": readable_label(symbol_id),
        "affected_nodes": [readable_label(n) for n in affected]
    })

    risk = (
        "High" if len(affected) > 5
        else "Medium" if len(affected) > 0
        else "Low"
    )

    return {
        "symbol": symbol_id,
        "affected_nodes": list(nodes),
        "affected_edges": edges,
        "summary": summary,
        "risk": risk
    }


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


@api.post("/index/stream")
def index_stream(request: IndexRequest):
    """
    Real dynamic repo indexing: clone -> parse -> chunk -> embed -> graph,
    streamed as it happens. index_repository() is synchronous/blocking
    (git clone, parsing, embedding all take real time), so it runs in a
    background thread and progress is relayed through a queue - this is
    the standard pattern for streaming progress out of blocking work in
    a sync FastAPI endpoint.

    On success, reload_state() is called so the already-running server
    actually starts using the newly built index/graph immediately,
    instead of requiring a restart.
    """

    progress_queue = queue_module.Queue()

    if not _indexing_lock.acquire(blocking=False):

        def already_running():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Another indexing run is already in progress. Please wait for it to finish.'})}\n\n"

        return StreamingResponse(
            already_running(),
            media_type="text/event-stream"
        )

    def run_indexing():

        try:

            def report(message):
                progress_queue.put({
                    "type": "status",
                    "message": message
                })

            stats = index_repository(
                request.repo_url,
                progress=report
            )

            agent_graph.reload_state()

            progress_queue.put({
                "type": "done",
                "stats": stats
            })

        except IndexingError as e:

            progress_queue.put({
                "type": "error",
                "message": str(e)
            })

        except Exception as e:

            progress_queue.put({
                "type": "error",
                "message": f"Unexpected error during indexing: {e}"
            })

        finally:

            _indexing_lock.release()

    thread = threading.Thread(target=run_indexing, daemon=True)
    thread.start()

    def event_generator():

        while True:

            event = progress_queue.get()

            yield f"data: {json.dumps(event)}\n\n"

            if event["type"] in ("done", "error"):
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    ) 