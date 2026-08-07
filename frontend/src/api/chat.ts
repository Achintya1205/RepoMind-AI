import axios from "axios";

const api = axios.create({
    baseURL: "http://127.0.0.1:8000"
});


export async function sendMessage(query: string) {

    const response = await api.post("/chat", {
        query
    });

    return response.data;
}