from services.llm_service import chat


async def verifier_node(state):

    prompt = f"""
You are an AI verifier.

Question:
{state["question"]}

Answer:
{state["answer"]}

If the answer is correct, reply ONLY:

PASS

Otherwise reply ONLY:

FAIL
"""

    result = chat(
        state["model"],
        prompt,
        state["question"],
    )

    state["verification"] = result.strip()

    return state