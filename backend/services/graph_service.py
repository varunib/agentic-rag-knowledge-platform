from graph.graph_builder import graph


async def run_graph(question, session_id, model):

    print("========== RUN_GRAPH EXECUTED ==========")

    state = {
        "question": question,
        "session_id": session_id,
        "model": model,
        "route": None,
        "context": "",
        "web_results": "",
        "tool_result": "",
        "memory": [],
        "answer": "",
        "citations": [],
        "confidence": 0.0,
        "verification": "",
    }

    print("Invoking LangGraph...")

    result = await graph.ainvoke(state)

    print("LangGraph Finished")

    return result