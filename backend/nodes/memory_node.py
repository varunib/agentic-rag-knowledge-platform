from services.memory_service import get_memory


async def memory_node(state):

    print("===== MEMORY NODE =====")

    history = get_memory(state["session_id"])

    print("Loaded Memory:", history)

    state["memory"] = history

    return state