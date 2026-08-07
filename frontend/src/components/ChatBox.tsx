import { useState } from "react";
import { streamMessage } from "../api/stream";
import { getGraph } from "../api/graph";
import GraphView from "./GraphViewer";

export default function ChatBox() {

    const [query, setQuery] = useState("");
    const [messages, setMessages] = useState<any[]>([]);
    const [citations, setCitations] = useState<any[]>([]);
    const [graphData, setGraphData] = useState({
        nodes: [],
        edges: []
    });


    function handleSend() {

        if (!query.trim()) return;


        setMessages(prev => [
            ...prev,
            {
                role: "user",
                text: query
            },
            {
                role: "assistant",
                text: ""
            }
        ]);


        streamMessage(query, (data: any) => {


            if (data.type === "answer") {

                setMessages(prev => {

                    const updated = [...prev];

                    updated[updated.length - 1].text = data.message;

                    return updated;
                });

            }


            if (data.type === "citations") {

                setCitations(data.data);

                console.log("Citations:", data.data);

            }


            if (data.type === "status" || data.type === "agent") {

                console.log(data.message);

            }


        });


        setQuery("");

    }


    async function showGraph() {

        const data = await getGraph("sendToClient");

        setGraphData(data);

    }


    return (
        <div>

            {
                messages.map((msg, index) => (
                    <div key={index}>
                        <b>{msg.role}</b>
                        <p>{msg.text}</p>
                    </div>
                ))
            }


            {
                citations.map((c, index) => (
                    <p key={index}>
                        📄 {c.file}:{c.start_line}-{c.end_line}
                    </p>
                ))
            }


            <button onClick={showGraph}>
                Show Graph
            </button>


            {
                graphData.nodes.length > 0 &&
                <GraphView
                    nodes={graphData.nodes}
                    edges={graphData.edges}
                />
            }


            <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about repository..."
            />


            <button onClick={handleSend}>
                Send
            </button>


        </div>
    );
}