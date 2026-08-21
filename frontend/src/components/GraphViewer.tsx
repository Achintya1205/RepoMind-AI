import { useState, useEffect } from "react";
import dagre from "dagre";
import ReactFlow, { Background, Controls } from "reactflow";
import type { Node, Edge } from "reactflow";
import "reactflow/dist/style.css";

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
}

export default function GraphViewer({ suggestedSymbol, onNodeSelect }: Props) {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);
    const [query, setQuery] = useState("");
    const [selectedNode, setSelectedNode] = useState<any>(null);

    useEffect(() => {
        onNodeSelect?.(selectedNode);
    }, [selectedNode]);

    const loadGraph = (symbolOverride?: string) => {
        const symbol = symbolOverride ?? query;
        if (!symbol) return;

        fetch(`http://127.0.0.1:8000/graph/${symbol}`)
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
            });
    };

    useEffect(() => {
        if (suggestedSymbol) {
            setQuery(suggestedSymbol);
            loadGraph(suggestedSymbol);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [suggestedSymbol]);

    const selectNode = (node: any) => {
        setSelectedNode({
            ...node,
            relations: null,
            impact: null
        });

        fetch(
            `http://127.0.0.1:8000/symbol/${encodeURIComponent(node.id)}`
        )
            .then((res) => res.json())
            .then((data) => {
                setSelectedNode((current: any) => ({
                    ...current,
                    relations: data
                }));
            });

        fetch(
            `http://127.0.0.1:8000/impact/${encodeURIComponent(node.id)}`
        )
            .then((res) => res.json())
            .then((data) => {
                const affected = new Set(data.affected_nodes as string[]);

                const existingNodeIds = new Set(nodes.map((n) => n.id));
                const existingEdgeIds = new Set(edges.map((e) => e.id));

                const newNodeObjs: Node[] = (data.affected_nodes as string[])
                    .filter((id) => !existingNodeIds.has(id))
                    .map((id) => ({
                        id,
                        data: { label: readableLabel(id) },
                        position: { x: 0, y: 0 },
                        className: nodeClassName("function"),
                    }));

                const newEdgeObjs: Edge[] = (data.affected_edges || [])
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

                const layout = getLayoutedElements(
                    [...nodes, ...newNodeObjs],
                    [...edges, ...newEdgeObjs]
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
                    impact: data
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
            </div>

            <ReactFlow
                nodes={nodes}
                edges={edges}
                fitView
                onNodeClick={(_, node) => selectNode(node)}
                onPaneClick={() => setSelectedNode(null)}
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