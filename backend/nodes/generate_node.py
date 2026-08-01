from services.llm_service import generate
from services.memory_service import save_message
from rag import build_system_prompt


async def generate_node(state):

    context = state.get("context", "")
    web_results = state.get("web_results", "")
    tool_result = state.get("tool_result", "")

    extra_context = ""

    if web_results:
        extra_context += "\nWeb Search Results:\n" + web_results

    if tool_result:
        extra_context += "\nTool Output:\n" + tool_result

    prompt = build_system_prompt(
        context,
        state["question"],
        extra_context,
    )

    answer = generate(
        state["model"],
        [
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": state["question"],
            },
        ],
    )

    state["answer"] = answer

    save_message(
        state["session_id"],
        "user",
        state["question"],
    )

    save_message(
        state["session_id"],
        "assistant",
        answer,
    )

    return state