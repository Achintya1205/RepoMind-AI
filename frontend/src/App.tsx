import { useState } from "react";
import GraphViewer from "./components/GraphViewer";
import ChatBox from "./components/ChatBox";
import Logo from "./components/Logo";

const STAGE_PROGRESS: Record<string, number> = {
    "Cloning repository...": 15,
    "Parsing source files...": 35,
    "Chunking code...": 55,
    "Building embeddings and vector index...": 75,
    "Building dependency graph...": 90,
    "Indexing complete.": 100,
};

type Tab = "chat" | "inspector";

function App() {
    const [repoUrl, setRepoUrl] = useState("");
    const [status, setStatus] = useState("");
    const [progress, setProgress] = useState(0);
    const [started, setStarted] = useState(false);
    const [error, setError] = useState("");
    const [isIndexing, setIsIndexing] = useState(false);
    const [suggestedSymbol, setSuggestedSymbol] = useState<string | undefined>();

    const [activeTab, setActiveTab] = useState<Tab>("chat");
    const [selectedNode, setSelectedNode] = useState<any>(null);
    const hasGraph = suggestedSymbol !== undefined;

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

    const handleNodeSelect = (node: any) => {
        setSelectedNode(node);

        if (node) {
            setActiveTab("inspector");
        }
    };

    return (
        <div className="flex flex-col h-screen w-screen overflow-hidden bg-ink font-sans text-[14px] text-text">
            <header className="flex items-center gap-6 h-[60px] flex-none px-5 bg-surface border-b border-border-soft relative z-30">
                <div className="flex items-center gap-2.5 flex-none">
                    <Logo active={isIndexing} />
                    <div className="font-display text-[17px] font-semibold tracking-tight whitespace-nowrap">
                        Repo<span className="text-amber">Mind</span> AI
                    </div>
                    <div className="hidden min-[900px]:block text-[11.5px] text-text-faint border-l border-border pl-3 ml-0.5 whitespace-nowrap">
                        Code intelligence, traced.
                    </div>
                </div>

                <div className="flex items-center gap-2 flex-1 max-w-[620px] ml-auto">
                    <input
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && startIndexing()}
                        placeholder="https://github.com/owner/repo"
                        disabled={isIndexing}
                        className="flex-1 h-9 px-3 bg-surface-2 border border-border rounded-md text-text text-[13px] placeholder:text-text-faint transition-colors focus:outline-none focus:border-amber-dim focus:ring-3 focus:ring-amber/20"
                    />
                    <button
                        onClick={startIndexing}
                        disabled={isIndexing || !repoUrl.trim()}
                        className="inline-flex items-center justify-center gap-1.5 h-9 px-4 rounded-md text-[13px] font-semibold whitespace-nowrap transition active:translate-y-px bg-amber text-[#16130a] enabled:hover:brightness-110 disabled:bg-surface-3 disabled:text-text-faint"
                    >
                        {isIndexing ? "Indexing…" : "Index repository"}
                    </button>
                </div>
            </header>

            {started && (progress < 100 || error) && (
                <div className="absolute left-0 right-0 top-[60px] h-0.5 bg-border-soft z-[29] overflow-hidden">
                    <div
                        className={`h-full transition-[width] duration-400 ease-out ${error ? "bg-danger" : "bg-amber"}`}
                        style={{ width: `${error ? 100 : progress}%` }}
                    />
                </div>
            )}

            <div className="flex flex-1 min-h-0">
                <div className="relative flex-1 min-w-0 bg-ink">
                    {!hasGraph && (
                        <div className="absolute inset-0 flex items-center justify-center flex-col gap-2.5 text-center p-5 pointer-events-none">
                            <h2 className="font-display text-[16px] font-semibold text-text-dim">
                                No repository indexed yet
                            </h2>
                            <p className="text-[13px] text-text-faint max-w-[320px]">
                                {error
                                    ? error
                                    : started
                                        ? status
                                        : "Paste a public GitHub repo URL above and index it to build a live dependency graph."}
                            </p>
                        </div>
                    )}

                    <GraphViewer
                        suggestedSymbol={suggestedSymbol}
                        onNodeSelect={handleNodeSelect}
                    />
                </div>

                <aside className="flex-none w-[380px] max-w-[42vw] flex flex-col bg-surface border-l border-border-soft z-20">
                    <div className="flex flex-none border-b border-border-soft">
                        <button
                            onClick={() => setActiveTab("chat")}
                            className={`flex-1 bg-transparent border-b-2 py-3 text-[12.5px] font-semibold tracking-wide transition-colors ${
                                activeTab === "chat"
                                    ? "text-amber border-amber"
                                    : "text-text-faint border-transparent hover:text-text-dim"
                            }`}
                        >
                            Chat
                        </button>
                        <button
                            onClick={() => setActiveTab("inspector")}
                            className={`flex-1 bg-transparent border-b-2 py-3 text-[12.5px] font-semibold tracking-wide transition-colors ${
                                activeTab === "inspector"
                                    ? "text-amber border-amber"
                                    : "text-text-faint border-transparent hover:text-text-dim"
                            }`}
                        >
                            Inspector
                            {selectedNode && (
                                <span className="inline-block w-1.5 h-1.5 rounded-full bg-violet ml-1.5 align-middle" />
                            )}
                        </button>
                    </div>

                    <div className="flex-1 min-h-0 flex flex-col">
                        {activeTab === "chat" && <ChatBox />}
                        {activeTab === "inspector" && (
                            <Inspector node={selectedNode} />
                        )}
                    </div>
                </aside>
            </div>
        </div>
    );
}

function readableLabel(id: string) {
    if (!id) return "";
    if (id.includes("::")) {
        return id.split("::").pop() as string;
    }
    return id.replace(/\\/g, "/").split("/").pop() as string;
}

function Inspector({ node }: { node: any }) {
    if (!node) {
        return (
            <div className="h-full flex items-center justify-center text-center text-text-faint text-[12.5px] p-6">
                Select a node in the graph to see its callers, callees, and
                change impact here.
            </div>
        );
    }

    const path = node.id?.includes("::") ? node.id.split("::")[0] : node.id;
    const risk = node.impact?.risk?.toLowerCase();
    const affectedCount = Math.max(
        (node.impact?.affected_nodes?.length || 1) - 1,
        0
    );

    const riskClasses: Record<string, string> = {
        low: "text-success bg-success/15",
        medium: "text-amber bg-amber/18",
        high: "text-danger bg-danger/15",
    };

    return (
        <div className="p-4 overflow-y-auto h-full">
            <div className="font-mono text-[15px] font-semibold text-text break-words">
                {node.data?.label}
            </div>
            <div className="font-mono text-[11.5px] text-text-faint mt-1 break-all">
                {path}
            </div>

            <div className="mt-5">
                <div className="text-[11px] font-semibold tracking-wide uppercase text-text-faint mb-2">
                    Callers
                </div>
                {!node.relations ? (
                    <div className="text-xs text-text-faint italic">Loading…</div>
                ) : node.relations.callers.length === 0 ? (
                    <div className="text-xs text-text-faint italic">None found</div>
                ) : (
                    node.relations.callers.map((c: string) => (
                        <div
                            key={c}
                            className="font-mono text-[12.5px] text-text-dim px-2.5 py-1.5 bg-surface-2 border border-border-soft rounded-md mb-1.5 break-words"
                        >
                            {readableLabel(c)}
                        </div>
                    ))
                )}
            </div>

            <div className="mt-5">
                <div className="text-[11px] font-semibold tracking-wide uppercase text-text-faint mb-2">
                    Callees
                </div>
                {!node.relations ? (
                    <div className="text-xs text-text-faint italic">Loading…</div>
                ) : node.relations.callees.length === 0 ? (
                    <div className="text-xs text-text-faint italic">None found</div>
                ) : (
                    node.relations.callees.map((c: string) => (
                        <div
                            key={c}
                            className="font-mono text-[12.5px] text-text-dim px-2.5 py-1.5 bg-surface-2 border border-border-soft rounded-md mb-1.5 break-words"
                        >
                            {readableLabel(c)}
                        </div>
                    ))
                )}
            </div>

            {node.impact && (
                <div className="mt-5">
                    <div className="text-[11px] font-semibold tracking-wide uppercase text-text-faint mb-2">
                        Impact analysis
                    </div>

                    <div>
                        <span
                            className={`inline-flex items-center gap-1.5 text-[11px] font-semibold tracking-wide px-2.5 py-0.5 rounded-full ${riskClasses[risk || "low"]}`}
                        >
                            {node.impact.risk || "Unknown"} risk
                        </span>
                        <span className="ml-2.5 text-[12.5px] text-text-dim">
                            {affectedCount} affected function
                            {affectedCount !== 1 ? "s" : ""}
                        </span>
                    </div>

                    {node.impact.summary && (
                        <div className="text-[12.5px] leading-relaxed text-text-dim mt-2.5">
                            {node.impact.summary}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default App;