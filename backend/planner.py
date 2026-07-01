def generate_project_plan(client, topic):

    prompt = f"""
Create a complete project plan.

Project:
{topic}

Include:

Problem Statement

Features

Tech Stack

Database Design

API Design

Deployment

Timeline
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