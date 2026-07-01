def generate_flowchart(client, topic):

    prompt = f"""
Generate a Mermaid flowchart.

Topic:
{topic}

Return ONLY Mermaid code.

Example:

graph TD
A[Start]
B[Process]
C[End]

A --> B
B --> C
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return response.choices[0].message.content