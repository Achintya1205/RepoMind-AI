from langgraph.graph import StateGraph, START, END
from agents.tools.graph_tool import GraphTool
from agents.impact_analyzer import ImpactAnalyzer
from agents.state import AgentState
from agents.router import route_query
from agents.qa.qa_agent import QAAgent
from agents.synthesizer import Synthesizer
from agents.architecture.architecture_agent import ArchitectureAgent
from agents.debug.debug_agent import DebugAgent
from agents.refactor.refactor_agent import RefactorAgent
from agents.documentation import DocumentationGenerator
from agents.utils.symbol_extractor import extract_symbol
from agents.verifier.verifier import Verifier

MAX_RETRIES = 2

code_graph = GraphTool()
qa_agent = QAAgent()
doc_generator = DocumentationGenerator()
refactor_agent = RefactorAgent(code_graph)
impact_agent = ImpactAnalyzer(code_graph)
debug_agent = DebugAgent()
architecture_agent = ArchitectureAgent()
synthesizer = Synthesizer()

def qa_node(state: AgentState):

    print("QA Agent")

    result = qa_agent.answer(
        state["query"]
    )

    return {
        "answer": result["answer"],
        "metadata": result["sources"]
    }

def architecture_node(state: AgentState):

    print("Architecture Agent")

    result = architecture_agent.analyze()

    return {
        "answer": result["explanation"],
        "metadata": result["summary"]
    }

def debug_node(state):

    print("Debugger")

    result = debug_agent.analyze(state["query"])

    if "error" in result:
        return {
            "answer": result["error"],
            "metadata": {}
        }

    return {
        "answer": result["explanation"],
        "metadata": result
    }

def impact_node(state: AgentState):

    print("Impact Analyzer")

    symbol = extract_symbol(state["query"], code_graph)

    if symbol is None:

        return {
            "answer": (
                "Couldn't identify a known function or class name in "
                "that question. Try naming the exact symbol, e.g. "
                "\"what breaks if I change getUserById?\""
            ),
            "metadata": {}
        }

    result = impact_agent.analyze(symbol)

    return {
        "answer": result["impact"],
        "metadata": result
    }

def graph_node(state: AgentState):

    print("Graph Agent")

    symbol = extract_symbol(state["query"], code_graph)

    if symbol is None:
        return {
            "answer": (
                "Couldn't identify a known function or class name in "
                "that question."
            ),
            "metadata": {}
        }

    callees = code_graph.callees(symbol)

    if not callees:
        return {
            "answer": f"No CALLS relationships were found for {symbol}.",
            "metadata": {
                "symbol": symbol,
                "callees": []
            }
        }

    answer = (
        f"{symbol} calls:\n\n"
        + "\n".join(f"- {callee}" for callee in callees)
    )

    return {
        "answer": answer,
        "metadata": {
            "symbol": symbol,
            "callees": callees
        }
    }

def refactor_node(state):

    print("Refactor Planner")

    symbol = extract_symbol(state["query"], code_graph)

    if symbol is None:

        return {
            "answer": (
                "Couldn't identify a known function or class name in "
                "that question. Try naming the exact symbol, e.g. "
                "\"refactor getUserById\""
            ),
            "metadata": {}
        }

    result = refactor_agent.analyze(symbol)

    return {
        "answer": result["plan"],
        "metadata": result
    }


def docs_node(state):

    print("Docs Agent")

    result = doc_generator.generate(
        state["query"]
    )

    return {
        "answer": result["documentation"],
        "metadata": result["citations"]
    }


def verifier_node(state):

    # qa/docs are LLM-generated free text, so this only makes sense for
    # them - see grounded_verifier_node below. impact/refactor/architecture
    # are deterministic graph/template output (no hallucination risk to
    # check), so this is deliberately just an "did we produce anything"
    # check, not a grounding check.

    passed = bool(
        state.get("answer")
    )

    return {
        "verified": {
            "passed": passed,
            "reasons": []
        }
    }


def grounded_verifier_node(state):

    verifier = Verifier(
        state.get("metadata", []),
        code_graph
    )

    result = verifier.verify(
        state.get("answer", "")
    )

    retry_count = state.get("retry_count", 0)

    if not result["passed"]:
        retry_count += 1

    return {
        "verified": result,
        "retry_count": retry_count
    }


def route_after_grounded_verifier(state):

    if state["verified"]["passed"]:
        return "synthesizer"

    if state["retry_count"] > MAX_RETRIES:
        return "synthesizer"

    # loop back to whichever of qa/docs produced this answer, and retry
    return state["current_agent"]

def synthesizer_node(state: AgentState):

    print("Synthesizer")

    return {
        "final_answer": synthesizer.format(state)
    }

workflow = StateGraph(AgentState)
workflow.add_node("router", route_query)
workflow.add_node("graph", graph_node)
workflow.add_node("qa", qa_node)
workflow.add_node("debug", debug_node)
workflow.add_node("impact", impact_node)
workflow.add_node("refactor", refactor_node)
workflow.add_node("docs", docs_node)
workflow.add_node("verifier", verifier_node)
workflow.add_node("grounded_verifier", grounded_verifier_node)

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
        "architecture": "architecture",
        "graph": "graph"
    }   
)
workflow.add_node(
    "synthesizer",
    synthesizer_node
)

workflow.add_edge("qa", "grounded_verifier")
workflow.add_edge("debug", "verifier")
workflow.add_edge("impact", "verifier")
workflow.add_edge("graph", "verifier")
workflow.add_edge("refactor", "verifier")
workflow.add_edge("docs", "grounded_verifier")

workflow.add_edge(
    "verifier",
    "synthesizer"
)

workflow.add_conditional_edges(
    "grounded_verifier",
    route_after_grounded_verifier,
    {
        "synthesizer": "synthesizer",
        "qa": "qa",
        "docs": "docs"
    }
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
dependency_graph = code_graph