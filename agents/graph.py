from langgraph.graph import StateGraph, START, END
from agents.tools.graph_tool import GraphTool
from agents.impact_analyzer import ImpactAnalyzer
from agents.impact_reasoner import ImpactReasoner
from agents.impact_explainer import ImpactExplainer
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
from agents.utils.chunk_lookup import ChunkStore
from agents.verifier.verifier import Verifier

MAX_RETRIES = 2
RETRY_NODE_BY_CATEGORY = {
    "qa": "qa",
    "docs": "docs",
    "impact_analysis": "impact",
    "debug": "debug",
    "refactor": "refactor",
}


def _build_chunk_store():

    try:
        return ChunkStore()
    except (FileNotFoundError, OSError):
        return None


code_graph = GraphTool()
chunk_store = _build_chunk_store()

qa_agent = QAAgent()
doc_generator = DocumentationGenerator(code_graph)
refactor_agent = RefactorAgent(code_graph, chunk_store=chunk_store)
impact_agent = ImpactAnalyzer(code_graph)
impact_reasoner = ImpactReasoner(chunk_store=chunk_store, graph_tool=code_graph)
impact_explainer = ImpactExplainer()
debug_agent = DebugAgent(graph_tool=code_graph, chunk_store=chunk_store)
architecture_agent = ArchitectureAgent(chunk_store=chunk_store)
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

    result = architecture_agent.analyze(state["query"])

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
            "metadata": []
        }

    return {
        "answer": result["explanation"],
        "metadata": _symbol_metadata(
            [result["location"]["function"]] + result["callers"]
        )
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
            "metadata": []
        }

    result = impact_agent.analyze(symbol)

    answer = impact_reasoner.explain(result, query=state["query"])

    return {
        "answer": answer,
        "metadata": _symbol_metadata(
            [result["changed_symbol"]] + result["affected_nodes"]
        )
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
            "metadata": []
        }

    result = refactor_agent.analyze(symbol, query=state["query"])

    return {
        "answer": result["plan"],
        "metadata": _symbol_metadata(
            [result["symbol"]] + result["affected_files"]
        )
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


def _symbol_metadata(names):

    seen = set()
    out = []

    for name in names:

        short_name = name.split("::")[-1] if "::" in name else name

        if not short_name or short_name in seen:
            continue

        seen.add(short_name)
        out.append({"name": short_name})

    return out


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

    return RETRY_NODE_BY_CATEGORY.get(
        state["current_agent"],
        "synthesizer"
    )


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
workflow.add_edge("debug", "grounded_verifier")
workflow.add_edge("impact", "grounded_verifier")
workflow.add_edge("graph", "verifier")
workflow.add_edge("refactor", "grounded_verifier")
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
        "docs": "docs",
        "debug": "debug",
        "impact": "impact",
        "refactor": "refactor"
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

    global code_graph, chunk_store, qa_agent, doc_generator, refactor_agent
    global impact_agent, impact_reasoner, debug_agent, architecture_agent
    global dependency_graph

    code_graph = GraphTool()
    chunk_store = _build_chunk_store()

    qa_agent = QAAgent()
    doc_generator = DocumentationGenerator(code_graph)
    refactor_agent = RefactorAgent(code_graph, chunk_store=chunk_store)
    impact_agent = ImpactAnalyzer(code_graph)
    impact_reasoner = ImpactReasoner(chunk_store=chunk_store, graph_tool=code_graph)
    debug_agent = DebugAgent(graph_tool=code_graph, chunk_store=chunk_store)
    architecture_agent = ArchitectureAgent(chunk_store=chunk_store)

    dependency_graph = code_graph


def get_dependency_graph():

    return dependency_graph