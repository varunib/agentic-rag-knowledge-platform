from services.llm_service import generate


def generate_sql(question, model):

    prompt = f"""
You are an SQLite expert.

Database Schema:

employees(
    id INTEGER,
    name TEXT,
    salary INTEGER
)

Convert the user's request into ONLY a valid SQLite query.

Rules:
- Return ONLY SQL.
- Do not explain.
- No markdown.
- No ```sql.

Question:
{question}
"""

    sql = generate(
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

    return sql.strip()