from services.supervisor_service import supervisor_route
from services.planner_service import decide_route


async def planner_node(state):

    question = state["question"]
    model = state["model"]

    print("===== SUPERVISOR AGENT =====")

    route = supervisor_route(question, model)

    valid_routes = [
        "direct",
        "document",
        "web",
        "calculator",
        "sql",
        "csv",
        "code",
        "vision",
    ]

    if route not in valid_routes:

        print("Supervisor failed.")
        print("Fallback -> Keyword Planner")

        route = decide_route(question)

    print(f"Final Route -> {route}")

    state["route"] = route

    return state