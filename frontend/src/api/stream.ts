import { API_BASE_URL } from "./config";
export async function streamMessage(query: string, onMessage: (data: any) => void) {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
    });

    const reader = response.body?.getReader();

    if(!reader) return;
    const decoder = new TextDecoder();

    while(true){

        const {done,value}=await reader.read();
        if(done) break;

        const chunk = decoder.decode(value);
        chunk
        .split("\n\n")
        .forEach(event=>{
            if(event.startsWith("data:")){
                const data = JSON.parse(
                    event.replace("data: ","")
                );
                onMessage(data);
            }
        });
    }
}