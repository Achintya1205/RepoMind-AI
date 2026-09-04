import { useState, useEffect, useRef } from "react";
import dagre from "dagre";
import ReactFlow, { Background, Controls } from "reactflow";
import type { Node, Edge } from "reactflow";
import "reactflow/dist/style.css";
import { API_BASE_URL } from "../api/config";

const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
    const dagreGraph = new dagre.graphlib.Graph();

    dagreGraph.setDefaultEdgeLabel(() => ({}));
    dagreGraph.setGraph({ rankdir: "LR" });

    nodes.forEach((node) => {
        dagreGraph.setNode(node.id, {
            width: 200,
            height: 44
        });
    });

    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);

    const layoutedNodes = nodes.map((node) => {
        const pos = dagreGraph.node(node.id);

        return {
            ...node,
            position: {
                x: pos.x,
                y: pos.y
            }
        };
    });

    return {
        nodes: layoutedNodes,
        edges
    };
};

const readableLabel = (id: string) => {
    if (id.includes("::")) {
        return id.split("::").pop() as string;
    }
    return id.replace(/\\/g, "/").split("/").pop() as string;
};

const NODE_BASE =
    "font-mono text-xs font-medium px-3 py-2 rounded-md border cursor-pointer " +
    "transition-shadow max-w-[220px] overflow-hidden text-ellipsis " +
    "whitespace-nowrap text-text hover:shadow-sm";

const NODE_TYPE_CLASSES: Record<string, string> = {
    function: "bg-amber/15 border-amber/40",
    file: "bg-slateblue/15 border-slateblue/40",
    class: "bg-violet/15 border-violet/40",
};

function nodeClassName(type: string) {
    return `${NODE_BASE} ${NODE_TYPE_CLASSES[type] || NODE_TYPE_CLASSES.function}`;
}

const EDGE_STYLE = { stroke: "#3a4054", strokeWidth: 1.4 };
const EDGE_LABEL_STYLE = { fill: "#9297ac", fontSize: 10, fontFamily: "JetBrains Mono, monospace" };
const EDGE_LABEL_BG = { fill: "#1b1e27", fillOpacity: 0.9 };

interface Props {
    suggestedSymbol?: string;
    onNodeSelect?: (node: any) => void;
    totalGraphStats?: { nodes: number; edges: number } | null;
}

export default function GraphViewer({ suggestedSymbol, onNodeSelect, totalGraphStats }: Props) {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);
    const [query, setQuery] = useState("");
    const [selectedNode, setSelectedNode] = useState<any>(null);
    const [viewedSymbol, setViewedSymbol] = useState<string | undefined>();
    const [highlightedSymbol, setHighlightedSymbol] = useState<string | undefined>();

    const latestClickedNodeId = useRef<string | null>(null);

    useEffect(() => {
        onNodeSelect?.(selectedNode);
    }, [selectedNode]);

    const loadGraph = (symbolOverride?: string) => {
        const symbol = symbolOverride ?? query;
        if (!symbol) return;

        fetch(`${API_BASE_URL}/graph/${symbol}`)
            .then((res) => res.json())
            .then((data) => {
                const formattedNodes = data.nodes.map((node: any) => ({
                    id: node.id,
                    data: {
                        label: node.data.label
                    },
                    className: nodeClassName(node.data.type),
                }));

                const formattedEdges = data.edges.map((edge: any) => ({
                    id: edge.id,
                    source: edge.source,
                    target: edge.target,
                    label: edge.type,
                    style: EDGE_STYLE,
                    labelStyle: EDGE_LABEL_STYLE,
                    labelBgStyle: EDGE_LABEL_BG,
                    labelBgPadding: [4, 2] as [number, number],
                    labelBgBorderRadius: 3,
                }));

                const layout = getLayoutedElements(
                    formattedNodes,
                    formattedEdges
                );

                setNodes(layout.nodes);
                setEdges(layout.edges);
                setViewedSymbol(symbol);
                setHighlightedSymbol(undefined);
                setSelectedNode(null);
            });
    };

    useEffect(() => {
        if (suggestedSymbol) {
            setQuery(suggestedSymbol);
            loadGraph(suggestedSymbol);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [suggestedSymbol]);

    const clearHighlighting = () => {
        latestClickedNodeId.current = null;

        setSelectedNode(null);
        setHighlightedSymbol(undefined);

        setNodes((current) =>
            current.map((n) => ({ ...n, style: { opacity: 1 } }))
        );

        setEdges((current) =>
            current.map((e) => ({ ...e, style: { ...EDGE_STYLE, opacity: 1 } }))
        );
    };

    const selectNode = (node: any) => {
        latestClickedNodeId.current = node.id;

        setSelectedNode({
            ...node,
            relations: null,
            impact: null
        });
        setHighlightedSymbol(node.data?.label ?? node.id);

        fetch(
            `${API_BASE_URL}/symbol/${encodeURIComponent(node.id)}`
        )
            .then((res) => res.json())
            .then((data) => {
                if (latestClickedNodeId.current !== node.id) return; 

                setSelectedNode((current: any) => ({
                    ...current,
                    relations: data
                }));
            });
        const shortName = node.data?.label ?? readableLabel(node.id);

        Promise.all([
            fetch(`${API_BASE_URL}/impact/${encodeURIComponent(node.id)}`).then((r) => r.json()),
            fetch(`${API_BASE_URL}/graph/${encodeURIComponent(shortName)}`).then((r) => r.json()),
        ]).then(([impactData, graphData]) => {
            if (latestClickedNodeId.current !== node.id) return;

            const affected = new Set(impactData.affected_nodes as string[]);

            const existingNodeIds = new Set(nodes.map((n) => n.id));
            const existingEdgeIds = new Set(edges.map((e) => e.id));

            const impactNodeObjs: Node[] = (impactData.affected_nodes as string[])
                .filter((id) => !existingNodeIds.has(id))
                .map((id) => ({
                    id,
                    data: { label: readableLabel(id) },
                    position: { x: 0, y: 0 },
                    className: nodeClassName("function"),
                }));

            const impactEdgeObjs: Edge[] = (impactData.affected_edges || [])
                .filter((e: any) => !existingEdgeIds.has(e.id))
                .map((e: any) => ({
                    id: e.id,
                    source: e.source,
                    target: e.target,
                    label: e.type,
                    style: EDGE_STYLE,
                    labelStyle: EDGE_LABEL_STYLE,
                    labelBgStyle: EDGE_LABEL_BG,
                    labelBgPadding: [4, 2] as [number, number],
                    labelBgBorderRadius: 3,
                }));

            const mergedNodeIds = new Set([
                ...existingNodeIds,
                ...impactNodeObjs.map((n) => n.id),
            ]);
            const mergedEdgeIds = new Set([
                ...existingEdgeIds,
                ...impactEdgeObjs.map((e) => e.id),
            ]);

            const calleeNodeObjs: Node[] = (graphData.nodes || [])
                .filter((n: any) => !mergedNodeIds.has(n.id))
                .map((n: any) => ({
                    id: n.id,
                    data: { label: n.data.label },
                    position: { x: 0, y: 0 },
                    className: nodeClassName(n.data.type),
                }));

            const calleeEdgeObjs: Edge[] = (graphData.edges || [])
                .filter((e: any) => !mergedEdgeIds.has(e.id))
                .map((e: any) => ({
                    id: e.id,
                    source: e.source,
                    target: e.target,
                    label: e.type,
                    style: EDGE_STYLE,
                    labelStyle: EDGE_LABEL_STYLE,
                    labelBgStyle: EDGE_LABEL_BG,
                    labelBgPadding: [4, 2] as [number, number],
                    labelBgBorderRadius: 3,
                }));

            const layout = getLayoutedElements(
                [...nodes, ...impactNodeObjs, ...calleeNodeObjs],
                [...edges, ...impactEdgeObjs, ...calleeEdgeObjs]
            );

            setNodes(
                layout.nodes.map((n) => ({
                    ...n,
                    style: {
                        opacity: affected.has(n.id) ? 1 : 0.25
                    }
                }))
            );

            setEdges(
                layout.edges.map((e) => ({
                    ...e,
                    style: {
                        ...EDGE_STYLE,
                        opacity:
                            affected.has(e.source) &&
                            affected.has(e.target)
                                ? 1
                                : 0.15
                    }
                }))
            );

            setSelectedNode((current: any) => ({
                ...current,
                impact: impactData
            }));
        });
    };

    return (
        <>
            <div className="absolute top-4 left-4 z-10 flex gap-2">
                <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && loadGraph()}
                    placeholder="Jump to symbol…"
                    className="w-[220px] h-[34px] px-3 bg-surface border border-border rounded-md text-text text-[12.5px] shadow-sm focus:outline-none focus:border-violet-dim focus:ring-3 focus:ring-violet/20"
                />
                <button
                    onClick={() => loadGraph()}
                    className="inline-flex items-center justify-center h-[34px] px-4 rounded-md border border-border text-text-dim text-[12.5px] font-semibold bg-transparent hover:border-text-faint hover:text-text transition"
                >
                    Go
                </button>
                {viewedSymbol && (
                    <button
                        onClick={() => loadGraph(viewedSymbol)}
                        title="Reload just the base neighborhood, discarding everything added by clicking around"
                        className="inline-flex items-center justify-center h-[34px] px-4 rounded-md border border-border text-text-dim text-[12.5px] font-semibold bg-transparent hover:border-text-faint hover:text-text transition"
                    >
                        Reset view
                    </button>
                )}
            </div>

            {viewedSymbol && (
                <div className="absolute top-[58px] left-4 z-10 flex flex-col gap-1.5">
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-surface/90 border border-border-soft rounded-md text-[11.5px] text-text-dim">
                        <span>
                            Showing neighborhood of{" "}
                            <span className="font-mono text-amber">{viewedSymbol}</span>
                            {" "}({nodes.length} nodes shown)
                        </span>
                        {totalGraphStats && (
                            <span className="text-text-faint border-l border-border pl-2 ml-1">
                                repo total: {totalGraphStats.nodes} nodes · {totalGraphStats.edges} edges
                            </span>
                        )}
                    </div>

                    {highlightedSymbol ? (
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-violet/15 border border-violet/30 rounded-md text-[11.5px] text-violet">
                            <span>
                                Highlighting blast radius of{" "}
                                <span className="font-mono">{highlightedSymbol}</span>
                                {" "}— dimmed nodes aren't reached by it
                            </span>
                            <button
                                onClick={clearHighlighting}
                                className="text-[10.5px] font-semibold underline decoration-dotted hover:text-text"
                            >
                                clear
                            </button>
                        </div>
                    ) : (
                        <div className="px-3 py-1 text-[11px] text-text-faint">
                            Click any node to trace what calls it — the canvas grows as you explore.
                        </div>
                    )}
                </div>
            )}

            <ReactFlow
                nodes={nodes}
                edges={edges}
                fitView
                onNodeClick={(_, node) => selectNode(node)}
                onPaneClick={() => clearHighlighting()}
                proOptions={{ hideAttribution: true }}
            >
                <Background color="#232734" gap={22} />
                <Controls position="bottom-right" />
            </ReactFlow>

            {nodes.length > 0 && (
                <div className="absolute bottom-4 left-4 z-10 flex gap-3.5 px-3.5 py-2 bg-surface border border-border-soft rounded-md shadow-sm">
                    <div className="flex items-center gap-1.5 text-[11px] text-text-dim">
                        <span className="w-2 h-2 rounded-sm bg-amber" />
                        Function
                    </div>
                    <div className="flex items-center gap-1.5 text-[11px] text-text-dim">
                        <span className="w-2 h-2 rounded-sm bg-slateblue" />
                        File
                    </div>
                    <div className="flex items-center gap-1.5 text-[11px] text-text-dim">
                        <span className="w-2 h-2 rounded-sm bg-violet" />
                        Class
                    </div>
                </div>
            )}
        </>
    );
}