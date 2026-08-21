import { useState, useRef, useEffect } from "react";
import { streamMessage } from "../api/stream";

export default function ChatBox() {

    const [query, setQuery] = useState("");
    const [messages, setMessages] = useState<any[]>([]);
    const [citations, setCitations] = useState<any[]>([]);
    const [isSending, setIsSending] = useState(false);

    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
    }, [messages]);

    function handleSend() {

        if (!query.trim() || isSending) return;

        const sentQuery = query;

        setIsSending(true);
        setCitations([]);
        setQuery("");

        setMessages(prev => [
            ...prev,
            {
                role: "user",
                text: sentQuery
            },
            {
                role: "assistant",
                text: ""
            }
        ]);

        streamMessage(sentQuery, (data: any) => {

            if (data.type === "answer") {

                setMessages(prev => {

                    const updated = [...prev];
                    const last = { ...updated[updated.length - 1], text: data.message };
                    updated[updated.length - 1] = last;

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

    }

    const isEmpty = messages.length === 0;

    return (
        <div className="flex flex-col h-full min-h-0">

            <div className="flex-1 min-h-0 overflow-y-auto p-4 flex flex-col gap-3" ref={scrollRef}>

                {isEmpty && (
                    <div className="flex-1 flex items-center justify-center text-center text-text-faint text-[12.5px] p-6">
                        Ask a question about the indexed repository - e.g.
                        "How does authentication work?" or "What breaks if
                        I change getUserById?"
                    </div>
                )}

                {
                    messages.map((msg, index) => {
                        const isLastAssistant =
                            msg.role === "assistant" && index === messages.length - 1;
                        const isTyping = isLastAssistant && isSending && !msg.text;
                        const isUser = msg.role === "user";

                        return (
                            <div
                                key={index}
                                className={`flex flex-col gap-1 max-w-[92%] ${isUser ? "self-end items-end" : "self-start items-start"}`}
                            >
                                <span className="text-[10.5px] font-semibold tracking-wide uppercase text-text-faint">
                                    {msg.role}
                                </span>

                                {isTyping ? (
                                    <div className="inline-flex gap-1 px-3.5 py-3 rounded-xl rounded-bl-[3px] bg-surface-2 border border-border-soft">
                                        <span className="typing-dot w-[5px] h-[5px] rounded-full bg-text-faint" />
                                        <span className="typing-dot w-[5px] h-[5px] rounded-full bg-text-faint" />
                                        <span className="typing-dot w-[5px] h-[5px] rounded-full bg-text-faint" />
                                    </div>
                                ) : (
                                    <div
                                        className={`px-3.5 py-2.5 rounded-xl text-[13px] leading-relaxed whitespace-pre-wrap break-words ${
                                            isUser
                                                ? "bg-surface-3 text-text rounded-br-[3px]"
                                                : "bg-surface-2 border border-border-soft text-text rounded-bl-[3px]"
                                        }`}
                                    >
                                        {msg.text}
                                    </div>
                                )}
                            </div>
                        );
                    })
                }

            </div>

            {
                citations.length > 0 &&
                <div className="px-4 py-2.5 border-t border-border-soft flex flex-wrap gap-1.5 flex-none">
                    {citations.map((c, index) => (
                        <span
                            key={index}
                            className="font-mono text-[11px] text-violet bg-violet/15 border border-violet/30 rounded-full px-2.5 py-0.5"
                        >
                            {c.file}:{c.start_line}-{c.end_line}
                        </span>
                    ))}
                </div>
            }

            <div className="flex gap-2 p-3 border-t border-border-soft flex-none">
                <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    placeholder="Ask about the repository…"
                    disabled={isSending}
                    className="flex-1 h-[38px] px-3 bg-surface-2 border border-border rounded-md text-text text-[13px] placeholder:text-text-faint focus:outline-none focus:border-amber-dim focus:ring-3 focus:ring-amber/20"
                />

                <button
                    onClick={handleSend}
                    disabled={isSending || !query.trim()}
                    className="inline-flex items-center justify-center h-[38px] px-4 rounded-md text-[13px] font-semibold whitespace-nowrap transition active:translate-y-px bg-amber text-[#16130a] enabled:hover:brightness-110 disabled:bg-surface-3 disabled:text-text-faint"
                >
                    {isSending ? "…" : "Send"}
                </button>
            </div>

        </div>
    );
}