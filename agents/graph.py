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
from agents.utils.greeting import is_greeting
from agents.verifier.verifier import Verifier
from agents.impact_explainer import ImpactExplainer

MAX_RETRIES = 2

code_graph = GraphTool()
qa_agent = QAAgent()
doc_generator = DocumentationGenerator(code_graph)
refactor_agent = RefactorAgent(code_graph)
impact_agent = ImpactAnalyzer(code_graph)
debug_agent = DebugAgent()
architecture_agent = ArchitectureAgent()
impact_explainer = ImpactExplainer()
synthesizer = Synthesizer()

def qa_node(state: AgentState):

    print("QA Agent")

    if is_greeting(state["query"]):

        return {
            "answer": (
                "Hi! I can answer questions about the currently indexed "
                "repository. Try asking something like \"How does "
                "authentication work?\" or \"What does the Signer class do?\""
            ),
            "metadata": []
        }

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
        "answer": impact_explainer.explain(result),
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


def reload_state():
    """
    Reconstructs every agent/tool object so a completed re-index actually
    takes effect on a running server, instead of requiring a restart.

    Each of these loads its data at construction time - GraphTool reads
    dependency_graph.pkl, KeywordSearch reads chunks.json, VectorStore
    opens chroma_db - so recreating them is what "picks up" a freshly
    built index. The compiled LangGraph `app` does NOT need rebuilding:
    its node functions look up these names in this module's global scope
    at call time, not at compile time, so reassigning the globals here is
    enough for every subsequent app.invoke()/app.stream() to use fresh data.
    """

    global code_graph, qa_agent, doc_generator, refactor_agent
    global impact_agent, debug_agent, architecture_agent, dependency_graph

    code_graph = GraphTool()
    qa_agent = QAAgent()
    doc_generator = DocumentationGenerator(code_graph)
    refactor_agent = RefactorAgent(code_graph)
    impact_agent = ImpactAnalyzer(code_graph)
    debug_agent = DebugAgent()
    architecture_agent = ArchitectureAgent()

    dependency_graph = code_graph


def get_dependency_graph():
    """
    Accessor for other modules (e.g. api/main.py) to always read the
    CURRENT graph. A plain `from agents.graph import dependency_graph`
    elsewhere would copy a reference at import time and go stale the
    moment reload_state() reassigns it here - this function always
    returns whatever the module global currently points to.
    """
    return dependency_graph