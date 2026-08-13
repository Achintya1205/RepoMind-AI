import { useState } from "react";
import { streamMessage } from "../api/stream";

export default function ChatBox() {

    const [query, setQuery] = useState("");
    const [messages, setMessages] = useState<any[]>([]);
    const [citations, setCitations] = useState<any[]>([]);
    const [isSending, setIsSending] = useState(false);

    function handleSend() {

        if (!query.trim() || isSending) return;

        setIsSending(true);
        setCitations([]);

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

            }

            if (data.type === "done") {

                setIsSending(false);

            }

        });

        setQuery("");

    }

    return (
        <div>

            {
                messages.map((msg, index) => (
                    <div key={index} style={{ marginBottom: 8 }}>
                        <b>{msg.role}</b>
                        <p style={{ margin: "2px 0" }}>{msg.text || (msg.role === "assistant" ? "..." : "")}</p>
                    </div>
                ))
            }

            {
                citations.length > 0 &&
                <div style={{ marginBottom: 8, fontSize: 13, color: "#555" }}>
                    {citations.map((c, index) => (
                        <p key={index} style={{ margin: "2px 0" }}>
                            📄 {c.file}:{c.start_line}-{c.end_line}
                        </p>
                    ))}
                </div>
            }

            <div style={{ display: "flex", gap: 8 }}>
                <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    placeholder="Ask about repository..."
                    disabled={isSending}
                    style={{ flex: 1, padding: 6 }}
                />

                <button onClick={handleSend} disabled={isSending}>
                    {isSending ? "..." : "Send"}
                </button>
            </div>

        </div>
    );
}