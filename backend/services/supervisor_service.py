from services.llm_service import generate


def supervisor_route(question, model):

    prompt = f"""
You are a routing agent.

Choose exactly ONE of these routes:

direct
document
web
calculator
sql
csv
code
vision

Return ONLY the route name.

Question:
{question}
"""

    route = generate(
        model,
        [
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    return route.strip().lower()