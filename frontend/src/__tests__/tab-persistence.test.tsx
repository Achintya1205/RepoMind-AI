import { describe, it, expect, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { useState } from "react";

afterEach(() => {
    cleanup();
});

function StatefulPanel({ label }: { label: string }) {
    const [messages, setMessages] = useState<string[]>([]);
    return (
        <div>
            <div data-testid={`${label}-count`}>{messages.length}</div>
            <button onClick={() => setMessages((m) => [...m, "msg"])}>
                add-{label}
            </button>
        </div>
    );
}

function OldTabs() {
    const [tab, setTab] = useState<"chat" | "inspector">("chat");
    return (
        <div>
            <button onClick={() => setTab("chat")}>chat-tab</button>
            <button onClick={() => setTab("inspector")}>inspector-tab</button>
            {tab === "chat" && <StatefulPanel label="chat" />}
            {tab === "inspector" && <StatefulPanel label="inspector" />}
        </div>
    );
}

function NewTabs() {
    const [tab, setTab] = useState<"chat" | "inspector">("chat");
    return (
        <div>
            <button onClick={() => setTab("chat")}>chat-tab</button>
            <button onClick={() => setTab("inspector")}>inspector-tab</button>
            <div className={tab === "chat" ? "" : "hidden"}>
                <StatefulPanel label="chat" />
            </div>
            <div className={tab === "inspector" ? "" : "hidden"}>
                <StatefulPanel label="inspector" />
            </div>
        </div>
    );
}

describe("tab-switching state persistence", () => {
    it("OLD pattern: chat state is LOST when switching tabs away and back (reproduces the reported bug)", () => {
        render(<OldTabs />);

        fireEvent.click(screen.getByText("add-chat"));
        expect(screen.getByTestId("chat-count").textContent).toBe("1");

        fireEvent.click(screen.getByText("inspector-tab"));
        fireEvent.click(screen.getByText("chat-tab"));

        expect(screen.getByTestId("chat-count").textContent).toBe("0");
    });

    it("NEW pattern: chat state SURVIVES switching tabs away and back (the fix)", () => {
        render(<NewTabs />);

        fireEvent.click(screen.getByText("add-chat"));
        expect(screen.getByTestId("chat-count").textContent).toBe("1");

        fireEvent.click(screen.getByText("inspector-tab"));
        fireEvent.click(screen.getByText("chat-tab"));

        expect(screen.getByTestId("chat-count").textContent).toBe("1");
    });
});