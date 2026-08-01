from langgraph.graph import StateGraph, START, END

from state.chat_state import ChatState

from nodes.memory_node import memory_node
from nodes.planner_node import planner_node
from nodes.retrieve_node import retrieve_node
from nodes.generate_node import generate_node
from nodes.verifier_node import verifier_node
from nodes.tool_node import tool_node


builder = StateGraph(ChatState)

# Register Nodes
builder.add_node("memory", memory_node)
builder.add_node("planner", planner_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("tool", tool_node)
builder.add_node("generate", generate_node)
builder.add_node("verify", verifier_node)

# Start
builder.add_edge(START, "memory")
builder.add_edge("memory", "planner")


# Planner Routing
def planner_router(state):

    route = state.get("route", "direct")

    if route == "document":
        return "retrieve"

    elif route in ["web", "calculator", "sql", "csv"]:
        return "tool"

    return "generate"


builder.add_conditional_edges(
    "planner",
    planner_router,
    {
        "retrieve": "retrieve",
        "tool": "tool",
        "generate": "generate",
    },
)

# Flow
builder.add_edge("retrieve", "generate")
builder.add_edge("tool", "generate")
builder.add_edge("generate", "verify")


# Reflection Loop
def verifier_router(state):

    # SQL, Web, Calculator don't need RAG verification
    if state["route"] != "document":
        return END

    verification = state.get("verification", "")

    if "PASS" in verification:
        return END

    return "retrieve"


builder.add_conditional_edges(
    "verify",
    verifier_router,
    {
        END: END,
        "retrieve": "retrieve",
    },
)

graph = builder.compile()