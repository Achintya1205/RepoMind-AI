export function streamMessage(
    query:string,
    onMessage:(data:any)=>void
){

const eventSource = new EventSource(
`http://127.0.0.1:8000/stream?query=${query}`
);


eventSource.onmessage = (event)=>{

    const data = JSON.parse(event.data);

    onMessage(data);

};


eventSource.onerror = ()=>{

    eventSource.close();

};

}