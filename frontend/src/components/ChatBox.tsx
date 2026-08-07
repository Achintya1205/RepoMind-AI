import { useState } from "react";
import { sendMessage } from "../api/chat";


export default function ChatBox(){

    const [query,setQuery] = useState("");
    const [messages,setMessages] = useState<any[]>([]);


    async function handleSend(){

        if(!query.trim()) return;


        setMessages(prev=>[
            ...prev,
            {
                role:"user",
                text:query
            }
        ]);


        const result = await sendMessage(query);


        setMessages(prev=>[
            ...prev,
            {
                role:"assistant",
                text:result.answer
            }
        ]);


        setQuery("");

    }


    return (
        <div>

            {
                messages.map((msg,index)=>(
                    <div key={index}>
                        <b>{msg.role}</b>
                        <p>{msg.text}</p>
                    </div>
                ))
            }


            <input
                value={query}
                onChange={(e)=>setQuery(e.target.value)}
                placeholder="Ask about repository..."
            />


            <button onClick={handleSend}>
                Send
            </button>


        </div>
    );
}