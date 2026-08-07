import { useState } from "react";
import { streamMessage } from "../api/stream";

export default function ChatBox() {

    const [query, setQuery] = useState("");
    const [messages, setMessages] = useState<any[]>([]);
    const [citations, setCitations] = useState<any[]>([]);


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