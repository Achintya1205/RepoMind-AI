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
            width: 220,
            height: 60
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

const nodeStyle = (type: string) => {
    if (type === "function") {
        return {
            background: "#90ee90",
            padding: 10,
            borderRadius: 8
        };
    }

    if (type === "file") {
        return {
            background: "#87ceeb",
            padding: 10,
            borderRadius: 8
        };
    }

    return {
        background: "#ffa500",
        padding: 10,
        borderRadius: 8
    };
};

interface Props {
    suggestedSymbol?: string;
}

export default function GraphViewer({ suggestedSymbol }: Props) {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);
    const [query, setQuery] = useState("");
    const [selectedNode, setSelectedNode] = useState<any>(null);

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
                    style: nodeStyle(node.data.type)
                }));

                const formattedEdges = data.edges.map((edge: any) => ({
                    id: edge.id,
                    source: edge.source,
                    target: edge.target,
                    label: edge.type
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
                const affected = new Set(data.affected_nodes);

                setNodes((currentNodes) =>
                    currentNodes.map((n) => ({
                        ...n,
                        style: {
                            ...n.style,
                            opacity: affected.has(n.id) ? 1 : 0.2
                        }
                    }))
                );

                setEdges((currentEdges) =>
                    currentEdges.map((e) => ({
                        ...e,
                        style: {
                            ...e.style,
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
        <div style={{ width: "100vw", height: "100vh" }}>
            <div
                style={{
                    position: "absolute",
                    zIndex: 10,
                    top: 20,
                    left: 20,
                    background: "white",
                    padding: 10
                }}
            >
                <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                />

                <button onClick={() => loadGraph()}>
                    Load
                </button>
            </div>

            <ReactFlow
                nodes={nodes}
                edges={edges}
                fitView
                onNodeClick={(_, node) => selectNode(node)}
            >
                <Background />
                <Controls />
            </ReactFlow>

            {selectedNode && (
                <div
                    style={{
                        position: "absolute",
                        right: 20,
                        top: 20,
                        width: 350,
                        maxHeight: "90vh",
                        overflowY: "auto",
                        background: "white",
                        padding: 20,
                        border: "1px solid black",
                        zIndex: 10
                    }}
                >
                    <h3>
                        {selectedNode.data.label}
                    </h3>

                    <p>
                        <b>Path:</b>
                        <br />
                        {selectedNode.id.includes("::")
                            ? selectedNode.id.split("::")[0]
                            : selectedNode.id}
                    </p>

                    {selectedNode.relations && (
                        <>
                            <div style={{ marginTop: 10 }}>
                                <b>Callers:</b>

                                {selectedNode.relations.callers.length === 0 ? (
                                    <p style={{ color: "#888" }}>None found</p>
                                ) : (
                                    selectedNode.relations.callers.map(
                                        (x: string) => (
                                            <p key={x}>{x}</p>
                                        )
                                    )
                                )}
                            </div>

                            <div style={{ marginTop: 10 }}>
                                <b>Callees:</b>

                                {selectedNode.relations.callees.length === 0 ? (
                                    <p style={{ color: "#888" }}>None found</p>
                                ) : (
                                    selectedNode.relations.callees.map(
                                        (x: string) => (
                                            <p key={x}>{x}</p>
                                        )
                                    )
                                )}
                            </div>
                        </>
                    )}

                    {selectedNode.impact && (
                        <>
                            <hr />

                            <h3>Impact Analysis</h3>

                            <p>
                                <b>Affected nodes:</b>{" "}
                                {selectedNode.impact.affected_nodes?.length || 0}
                            </p>

                            <p>
                                <b>Risk:</b>{" "}
                                {selectedNode.impact.risk || "Not available"}
                            </p>

                            {selectedNode.impact.summary && (
                                <p>
                                    <b>Summary:</b>
                                    <br />
                                    {selectedNode.impact.summary}
                                </p>
                            )}
                        </>
                    )}
                </div>
            )}
        </div>
    );
}