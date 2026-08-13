import os
import shutil
import stat
import subprocess
from pathlib import Path

from ingestion.repo_scanner.repo_scanner import scan_repository
from ingestion.parsers.javascript_parser import JavascriptParser
from ingestion.parsers.python_parser import PythonParser
from ingestion.chunker.ast_chunker import generate_chunks
from ingestion.graph_builder.builder import DependencyGraphBuilder
from ingestion.graph_builder.graph_io import save_graph

PROJECT_ROOT = Path(__file__).parent.parent

ACTIVE_REPO_DIR = PROJECT_ROOT / "active_repo"

JS_AST_OUTPUT = PROJECT_ROOT / "ingestion" / "parsers" / "output" / "javascript_ast_output.json"
PY_AST_OUTPUT = PROJECT_ROOT / "ingestion" / "parsers" / "output" / "python_ast_output.json"
CHUNKS_OUTPUT = PROJECT_ROOT / "ingestion" / "chunker" / "chunks.json"
GRAPH_OUTPUT = PROJECT_ROOT / "graph_output" / "dependency_graph.pkl"

MAX_REPO_FILES = 5000  # matches the design doc's stated repo-size cap


class IndexingError(Exception):
    pass


def _force_remove_readonly(func, path, exc_info):
    """
    shutil.rmtree can't delete read-only files on Windows, and git marks
    its .git/objects/pack/* files read-only - so removing a previously
    cloned repo fails with PermissionError/WinError 5 unless we clear
    the read-only bit first. No-op cost on Linux/Mac, where this never
    triggers since rmtree already succeeds there.
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clone_repo(repo_url):
    """
    Clones repo_url into ACTIVE_REPO_DIR, replacing whatever was indexed
    before - RepoMind-AI operates on a single active repo at a time, so
    every rebuild starts from a clean slate rather than accumulating
    unrelated repos in the same index.
    """

    import time

    last_error = None

    for attempt in range(2):

        try:

            if ACTIVE_REPO_DIR.exists():
                shutil.rmtree(ACTIVE_REPO_DIR, onerror=_force_remove_readonly)

            ACTIVE_REPO_DIR.mkdir(parents=True)

            result = subprocess.run(
                [
                    "git", "clone",
                    "--depth", "1",
                    repo_url,
                    str(ACTIVE_REPO_DIR)
                ],
                capture_output=True,
                text=True,
                timeout=180
            )

            if result.returncode != 0:
                raise IndexingError(
                    f"git clone failed: {result.stderr.strip()}"
                )

            return ACTIVE_REPO_DIR

        except (IndexingError, OSError, PermissionError) as e:

            last_error = e

            if attempt == 0:
                # Windows can briefly hold a lock on files just deleted
                # by rmtree (antivirus scanning, delayed handle release)
                # - a short pause and one retry resolves this reliably
                # without requiring the user to manually click again.
                time.sleep(1.5)
                continue

    raise IndexingError(f"git clone failed after retry: {last_error}")


def parse_repo(repo_path):

    files = scan_repository(repo_path)

    if len(files) > MAX_REPO_FILES:
        raise IndexingError(
            f"Repository has {len(files)} indexable files, which exceeds "
            f"the {MAX_REPO_FILES} file cap. Try a smaller repository."
        )

    js_parser = JavascriptParser()
    py_parser = PythonParser()

    js_results = []
    py_results = []
    failed = []

    for file_info in files:

        path = Path(file_info["path"])
        language = file_info["language"]

        try:

            if language in ("javascript", "typescript"):

                result = js_parser.process_file(path)
                result["file"] = str(path.relative_to(repo_path.parent))
                js_results.append(result)

            elif language == "python":

                result = py_parser.process_file(path)
                result["file"] = str(path.relative_to(repo_path.parent))
                py_results.append(result)

        except Exception as e:
            failed.append((str(path), str(e)))

    return js_results, py_results, failed


def index_repository(repo_url, progress=None):
    """
    Full pipeline: clone -> parse -> chunk -> embed -> graph.

    progress, if given, is called with a short status string after each
    stage completes - lets the API stream real progress instead of a
    fake timer.
    """

    def report(message):
        if progress:
            progress(message)

    report("Cloning repository...")
    repo_path = clone_repo(repo_url)

    report("Parsing source files...")
    js_results, py_results, failed = parse_repo(repo_path)

    if not js_results and not py_results:
        raise IndexingError(
            "No parseable JavaScript/TypeScript or Python files found "
            "in this repository."
        )

    JS_AST_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    import json

    with open(JS_AST_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(js_results, f, indent=2)

    with open(PY_AST_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(py_results, f, indent=2)

    report("Chunking code...")
    combined_ast = js_results + py_results
    chunks = generate_chunks(combined_ast)

    CHUNKS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(CHUNKS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    report("Building embeddings and vector index...")

    from retrieval.vector_store import VectorStore

    store = VectorStore()
    store.reset_collection()
    store.index_chunks()

    report("Building dependency graph...")
    builder = DependencyGraphBuilder(str(repo_path))
    graph = builder.build_graph(combined_ast)
    save_graph(graph, str(GRAPH_OUTPUT))

    sample_symbol = _pick_sample_symbol(graph)

    report("Indexing complete.")

    return {
        "files_parsed": len(js_results) + len(py_results),
        "files_failed": len(failed),
        "chunks_created": len(chunks),
        "graph_nodes": graph.number_of_nodes(),
        "graph_edges": graph.number_of_edges(),
        "sample_symbol": sample_symbol,
    }


def _pick_sample_symbol(graph):
    """
    Picks a real, well-connected function/class from the just-built graph
    so the frontend has something meaningful to show right after indexing,
    instead of an empty graph view or a leftover symbol name from whatever
    repo was indexed previously (which almost certainly won't exist in
    the new one).
    """

    best_node = None
    best_degree = -1

    for node, data in graph.nodes(data=True):

        if data.get("node_type") not in ("function", "class"):
            continue

        degree = graph.in_degree(node) + graph.out_degree(node)

        if degree > best_degree:
            best_degree = degree
            best_node = data.get("name")

    return best_node