from langgraph.graph import StateGraph, START, END

from state.chat_state import ChatState
from nodes.planner_node import planner_node
from nodes.retrive_node import retrive_node
from nodes.generate_node import generate_node


builder = StateGraph(ChatState)

builder.add_node("planner", planner_node)
builder.add_node("retrive", retrive_node)                  
builder.add_node("generate", generate_node)

builder.add_edge(START, "planner")
builder.add_edge("planner", "retrive")
builder.add_edge("retrive", "generate")
builder.add_edge("generate", END)

graph = builder.compile()