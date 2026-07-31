from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict):

    # user interaction
    query: str
    conversation_history: List[str]

    # retrieval output
    retrieved_chunks: List[Dict[str, Any]]

    # graph output
    graph_results: List[Dict[str, Any]]

    # workflow tracking
    retry_count: int
    current_agent: str

    # final response
    answer: str