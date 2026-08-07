import { useState } from "react";
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

export default function GraphViewer() {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [edges, setEdges] = useState<Edge[]>([]);
    const [query, setQuery] = useState("useAuthorization");
    const [selectedNode, setSelectedNode] = useState<any>(null);

    const loadGraph = () => {
        fetch(`http://127.0.0.1:8000/graph/${query}`)
            .then(res => res.json())
            .then(data => {
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

    const selectNode = (node: any) => {
        setSelectedNode({
            ...node,
            relations: null
        });

        fetch(
            `http://127.0.0.1:8000/symbol/${encodeURIComponent(node.id)}`
        )
            .then(res => res.json())
            .then(data => {
                setSelectedNode({
                    ...node,
                    relations: data
                });
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

                <button onClick={loadGraph}>
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
                        background: "white",
                        padding: 20,
                        border: "1px solid black",
                        zIndex: 10
                    }}
                >
                    <h3>
                        {selectedNode.data.label.split("::")[1] || "File"}
                    </h3>

                    <p>
                        <b>Path:</b>
                        <br />
                        {selectedNode.data.label.split("::")[0]}
                    </p>

                    {selectedNode.relations && (
                        <>
                            <b>Callers:</b>
                            {selectedNode.relations.callers.map((x: string) => (
                                <p key={x}>{x}</p>
                            ))}

                            <b>Callees:</b>
                            {selectedNode.relations.callees.map((x: string) => (
                                <p key={x}>{x}</p>
                            ))}
                        </>
                    )}
                </div>
            )}
        </div>
    );
}