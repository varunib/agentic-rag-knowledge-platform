def router_node(state):

    question = state["question"].lower()

    if "sql" in question:
        state["route"] = "sql"

    elif "database" in question:
        state["route"] = "sql"

    elif "web" in question:
        state["route"] = "web"

    else:
        state["route"] = "rag"

    return state