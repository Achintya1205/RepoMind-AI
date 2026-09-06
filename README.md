# RepoMind AI

 Paste any public GitHub repo and get a live dependency graph plus grounded, citation-backed Q&A over the codebase — every answer points back to the exact `file:line` it came from.

## Demo

https://github.com/user-attachments/assets/ac51ace8-4b1a-4eeb-8005-0f26bc76b712

## What It Does

Most AI coding assistants answer questions from a language model's general training data, or from a shallow text search over a repo. RepoMind AI is built differently: it parses a real codebase into an actual AST-based dependency graph, retrieves real code chunks through a hybrid search pipeline, and verifies every generated answer against that graph before returning it. If the model claims "function A calls function B," that claim is checked against a real `CALLS` edge — if the edge doesn't exist, the answer is rejected and retried.

The result is a system that can answer both semantic questions ("how does authentication work?") and structural questions ("what breaks if I change this function?") with evidence.

## Architecture

```
GitHub URL
   │
   ▼
Clone (git clone --depth 1)
   │
   ▼
Parse (tree-sitter: Python + JS/TS ASTs)
   │
   ├──────────────► Chunk (per function/class) ──► Embed (ChromaDB) + BM25 index
   │
   └──────────────► Build dependency graph (NetworkX: IMPORTS / DEFINES / CALLS edges)
                          │
                          ▼
User Query ──► Router ──► Agent ──► Verifier (checks claims against the graph) ──► Answer
                  │           │
                  │           └─ pulls evidence from retrieval layer AND/OR graph layer
                  │
                  └─ classifies intent: qa / architecture / impact / debug / refactor / docs
```

Two independent sources of truth feed every agent:

- **Retrieval layer** — BM25 keyword search + ChromaDB vector search, merged and reranked with a CrossEncoder, for semantic "where is X" style questions.
- **Dependency graph** — a NetworkX `DiGraph` built from tree-sitter ASTs, for exact structural facts: who calls what, what imports what, what would be affected by a change.

This split matters: the LLM is free to reason in natural language, but any claim that touches real structure (a caller, a call edge, an import) is grounded against the graph rather than left to the model's judgment.

## The Six Agents

| Agent | Triggered by | What it does |
|---|---|---|
| **QA** | General questions | Retrieves relevant code via hybrid search, answers with inline citations |
| **Architecture** | "explain the structure/design" | Summarizes real graph statistics (file/function counts, entry points, most-imported modules) and narrates component relationships |
| **Impact Analysis** | "what breaks if I change X" | Traverses the graph's `CALLS` edges backward (BFS) to find every direct and indirect caller, tagged by hop distance |
| **Debug** | Stack traces / error messages | Parses the trace to locate the failing function, pulls its real callers from the graph, and reasons about likely root cause |
| **Refactor** | "how should I refactor X" | Uses ground-truth callers to propose a concrete, evidence-based refactor plan instead of generic advice |
| **Docs** | "generate documentation for X" | Writes documentation strictly from the retrieved source, with per-section citations |

All agents route through a `grounded_verifier` node that re-checks graph-related claims in the generated text and retries (capped at 2 attempts) if an unsupported claim is detected.

## Dependency Graph

Built with `tree-sitter` (AST parsing) + `NetworkX` (graph structure):

- **Nodes**: `file`, `function`, `class` — each function/class node is keyed as `path/to/file.py::functionName`
- **Edges**: `DEFINES` (file → symbol), `IMPORTS` (file → file, resolved across relative/absolute Python imports and `@/`-alias JS/TS imports), `CALLS` (function → function, resolved same-file first, then via imports, then by unique name)
- Import resolution handles Python's relative-import dot-counting and JS/TS path aliases per-file, since repo root can't be assumed fixed at parse time

The graph is what makes "what breaks if I change this?" answerable as a real BFS traversal instead of an LLM guess.

## Retrieval Pipeline

1. **BM25** keyword search over all chunked functions/classes
2. **Vector search** via ChromaDB, using `BAAI/bge-small-en-v1.5` embeddings
3. Results merged and deduplicated
4. **Reranked** with `cross-encoder/ms-marco-MiniLM-L-6-v2` for final relevance ordering

The reranker was deliberately downsized from a larger cross-encoder to fit within a 512MB free-tier deployment ceiling, trading a small amount of ranking quality for the ability to run at all in a constrained environment.

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | FastAPI, LangGraph, ChromaDB, BM25 (rank-bm25), tree-sitter, NetworkX |
| LLM | Gemini API |
| Frontend | React, Vite, TypeScript, Tailwind CSS, React Flow (graph visualization) |
| Deployment | Render (API), Vercel (frontend) |

## Getting Started

```bash
# Backend
pip install -r requirements.txt
uvicorn api.main:api --reload

# Frontend
cd frontend
npm install
npm run dev
```

Paste a public GitHub repo URL into the app and click **Index repository**. Indexing streams live progress via Server-Sent Events (`POST /index/stream`): clone → parse → chunk → embed → build graph.

## Key API Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /index/stream` | Clone + index a repo, streaming progress |
| `POST /chat/stream` | Ask a question, streaming the agent's answer |
| `GET /graph/{symbol}` | Fetch the local call-graph neighborhood of a symbol |
| `GET /impact/{symbol_id}` | Compute the full upstream blast radius of a symbol |

## Evaluation

Retrieval quality against hand-labeled golden datasets:

```bash
python -m evaluation.test_retrieval --all
```

Graph correctness against an independently computed ground truth (a separate BFS over `CALLS` edges, not the system's own logic):

```bash
python -m evaluation.test_graph_ground_truth
```

## License

MIT