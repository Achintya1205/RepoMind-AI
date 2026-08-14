import { useState } from "react";
import GraphViewer from "./components/GraphViewer";
import ChatBox from "./components/ChatBox";

const STAGE_PROGRESS: Record<string, number> = {
    "Cloning repository...": 15,
    "Parsing source files...": 35,
    "Chunking code...": 55,
    "Building embeddings and vector index...": 75,
    "Building dependency graph...": 90,
    "Indexing complete.": 100,
};

function App() {
    const [repoUrl, setRepoUrl] = useState("");
    const [status, setStatus] = useState("");
    const [progress, setProgress] = useState(0);
    const [started, setStarted] = useState(false);
    const [error, setError] = useState("");
    const [isIndexing, setIsIndexing] = useState(false);
    const [suggestedSymbol, setSuggestedSymbol] = useState<string | undefined>();

    const startIndexing = async () => {
        if (!repoUrl.trim() || isIndexing) return;

        setStarted(true);
        setIsIndexing(true);
        setError("");
        setStatus("Starting indexing...");
        setProgress(5);

        try {
            const response = await fetch("http://127.0.0.1:8000/index/stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ repo_url: repoUrl }),
            });

            const reader = response.body?.getReader();
            if (!reader) return;

            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);

                chunk.split("\n\n").forEach((event) => {
                    if (!event.startsWith("data:")) return;

                    const data = JSON.parse(event.replace("data: ", ""));

                    if (data.type === "status") {
                        setStatus(data.message);
                        setProgress(STAGE_PROGRESS[data.message] ?? progress);
                    }

                    if (data.type === "done") {
                        setStatus(
                            `Indexed ${data.stats.files_parsed} files, ` +
                            `${data.stats.chunks_created} chunks, ` +
                            `${data.stats.graph_nodes} graph nodes`
                        );
                        setProgress(100);
                        setIsIndexing(false);
                        setSuggestedSymbol(data.stats.sample_symbol);
                    }

                    if (data.type === "error") {
                        setError(data.message);
                        setStatus("Indexing failed");
                        setIsIndexing(false);
                    }
                });
            }
        } catch (e) {
            setError("Could not reach the indexing server.");
            setStatus("Indexing failed");
            setIsIndexing(false);
        }
    };

    return (
        <div style={{ width: "100vw", height: "100vh" }}>
            <div
                style={{
                    position: "absolute",
                    zIndex: 20,
                    top: 20,
                    left: 20,
                    background: "white",
                    padding: 15,
                    borderRadius: 8,
                    width: 400
                }}
            >
                <h3>RepoMind AI</h3>

                <input
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    placeholder="Paste GitHub repository URL"
                    style={{
                        width: "100%",
                        padding: 8,
                        boxSizing: "border-box"
                    }}
                />

                <button
                    onClick={startIndexing}
                    disabled={isIndexing}
                    style={{ marginTop: 10, padding: "8px 15px" }}
                >
                    {isIndexing ? "Indexing..." : "Index Repository"}
                </button>

                {started && (
                    <div style={{ marginTop: 15 }}>
                        <p>{status}</p>

                        <div
                            style={{
                                width: "100%",
                                height: 8,
                                background: "#ddd",
                                borderRadius: 5
                            }}
                        >
                            <div
                                style={{
                                    width: `${progress}%`,
                                    height: "100%",
                                    background: error ? "#e53e3e" : "#4caf50",
                                    borderRadius: 5
                                }}
                            />
                        </div>

                        <p>{progress}%</p>

                        {error && (
                            <p style={{ color: "#e53e3e" }}>{error}</p>
                        )}
                    </div>
                )}
            </div>

            <GraphViewer suggestedSymbol={suggestedSymbol} />

            <div
                style={{
                    position: "absolute",
                    zIndex: 20,
                    bottom: 20,
                    left: 20,
                    width: 380,
                    maxHeight: "70vh",
                    overflowY: "auto",
                    background: "white",
                    borderRadius: 8,
                    boxShadow: "0 2px 12px rgba(0,0,0,0.2)",
                    padding: 15
                }}
            >
                <ChatBox />
            </div>
        </div>
    );
}

export default App;