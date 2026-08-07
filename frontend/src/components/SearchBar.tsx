import { useState } from "react";

interface Props {
    onSearch: (symbol: string) => void;
}

export default function SearchBar({ onSearch }: Props) {

    const [symbol, setSymbol] = useState("");

    return (
        <div
            style={{
                position: "absolute",
                top: 20,
                left: 20,
                zIndex: 10,
                background: "white",
                padding: 10,
                border: "1px solid black",
                borderRadius: 8
            }}
        >

            <input
                value={symbol}
                placeholder="Search symbol..."
                onChange={(e)=>setSymbol(e.target.value)}
                style={{
                    padding: 8,
                    width: 220
                }}
            />


            <button
                onClick={() => onSearch(symbol)}
                style={{
                    marginLeft: 10,
                    padding: 8
                }}
            >
                Load
            </button>

        </div>
    );
}