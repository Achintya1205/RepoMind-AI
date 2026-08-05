from langgraph.graph import StateGraph, START, END

from agents.state import AgentState
from agents.router import route_query

from agents.synthesizer import Synthesizer
from agents.architecture.architecture_agent import ArchitectureAgent
from agents.debug.debug_agent import DebugAgent
from agents.refactor.refactor_agent import RefactorAgent

refactor_agent = RefactorAgent()
debug_agent = DebugAgent()
architecture_agent = ArchitectureAgent()
synthesizer = Synthesizer()

def qa_node(state: AgentState):

    print("QA Agent")

    return {
        "answer": "Handled by QA agent"
    }

def architecture_node(state: AgentState):

    print("Architecture Agent")

    result = architecture_agent.analyze()

    return {
        "answer": result["explanation"],
        "metadata": result["summary"]
    }

def debug_node(state: AgentState):

    print("Debugger")

    result = debug_agent.analyze(
        state["query"]
    )

    return {
        "answer": result["explanation"],
        "metadata": result
    }


def impact_node(state: AgentState):

    print("Impact Analyzer")

    return {
        "answer": "Handled by Impact Analyzer"
    }


def refactor_node(state):

    print("Refactor Planner")

    result = refactor_agent.analyze(
        "sendToClient"
    )

    return {
        "answer": result["plan"],
        "metadata": result
    }


def docs_node(state: AgentState):

    print("Docs Agent")

    return {
        "answer": "Handled by Docs Agent"
    }


def verifier_node(state: AgentState):

    print("Verifier")

    return {
        "verified": {
            "passed": True,
            "reasons": []
        }
    }

def synthesizer_node(state: AgentState):

    print("Synthesizer")

    return {
        "final_answer": synthesizer.format(state)
    }

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
        "docs": "docs",
        "architecture": "architecture"
    }
)
workflow.add_node(
    "synthesizer",
    synthesizer_node
)

workflow.add_edge("qa", "verifier")
workflow.add_edge("debug", "verifier")
workflow.add_edge("impact", "verifier")
workflow.add_edge("refactor", "verifier")
workflow.add_edge("docs", "verifier")

workflow.add_edge(
    "verifier",
    "synthesizer"
)
workflow.add_node(
    "architecture",
    architecture_node
)
workflow.add_edge(
    "architecture",
    "verifier"
)

workflow.add_edge(
    "synthesizer",
    END
)

app = workflow.compile()