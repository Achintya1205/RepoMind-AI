from langgraph.graph import StateGraph, START, END

from agents.state import AgentState
from agents.router import route_query

def qa_node(state: AgentState):

    print("QA Agent")

    return {
        "answer": "Handled by QA agent"
    }


def debug_node(state: AgentState):

    print("Debugger")

    return {
        "answer": "Handled by Debugger"
    }


def impact_node(state: AgentState):

    print("Impact Analyzer")

    return {
        "answer": "Handled by Impact Analyzer"
    }


def refactor_node(state: AgentState):

    print("Refactor Planner")

    return {
        "answer": "Handled by Refactor Planner"
    }


def docs_node(state: AgentState):

    print("Docs Agent")

    return {
        "answer": "Handled by Docs Agent"
    }


def verifier_node(state: AgentState):

    print("Verifier")

    return state

workflow = StateGraph(AgentState)
workflow.add_node("router", route_query)
workflow.add_node("qa", qa_node)
workflow.add_node("debug", debug_node)
workflow.add_node("impact", impact_node)
workflow.add_node("refactor", refactor_node)
workflow.add_node("docs", docs_node)
workflow.add_node("verifier", verifier_node)

workflow.add_edge(
    START,
    "router"
)

workflow.add_conditional_edges(
    "router",
    lambda state: state["current_agent"],
    {
        "qa": "qa",
        "debug": "debug",
        "impact_analysis": "impact",
        "refactor": "refactor",
        "docs": "docs"
    }
)

workflow.add_edge("qa", "verifier")
workflow.add_edge("debug", "verifier")
workflow.add_edge("impact", "verifier")
workflow.add_edge("refactor", "verifier")
workflow.add_edge("docs", "verifier")

workflow.add_edge("verifier", END)

app = workflow.compile()