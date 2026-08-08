import { useState } from "react";
import GraphViewer from "./components/GraphViewer";
import ChatBox from "./components/ChatBox";

function App() {
    const [repoUrl, setRepoUrl] = useState("");
    const [status, setStatus] = useState("");
    const [progress, setProgress] = useState(0);
    const [started, setStarted] = useState(false);

    const startIndexing = () => {
        if (!repoUrl.trim()) return;

        setStarted(true);
        setStatus("Starting indexing...");
        setProgress(20);

        setTimeout(() => {
            setStatus("Parsing repository...");
            setProgress(50);
        }, 800);

        setTimeout(() => {
            setStatus("Building dependency graph...");
            setProgress(80);
        }, 1600);

        setTimeout(() => {
            setStatus("Indexing complete");
            setProgress(100);
        }, 2400);
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
                    style={{ marginTop: 10, padding: "8px 15px" }}
                >
                    Index Repository
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
                                    background: "#4caf50",
                                    borderRadius: 5
                                }}
                            />
                        </div>

                        <p>{progress}%</p>
                    </div>
                )}
            </div>

            <GraphViewer />
            <ChatBox />
        </div>
    );
}

export default App;