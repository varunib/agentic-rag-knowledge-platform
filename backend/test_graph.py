from graph.graph_builder import graph

result = graph.invoke(
    {
        "question": "What is RAG?",
        "model": "llama-3.3-70b-versatile",
        "session_id": "default",
        "context": "",
        "answer": "",
        "citations": [],
        "route": "",
        "web_results": "",
    }
)

print(result)