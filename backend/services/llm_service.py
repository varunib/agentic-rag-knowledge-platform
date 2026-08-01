import os
from dotenv import load_dotenv
from groq import Groq

# Load .env from the backend folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Optional: Debug (remove later)
print("GROQ API Loaded:", os.getenv("GROQ_API_KEY") is not None)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def chat(model, system_prompt, question):

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        temperature=0.7,
        max_tokens=1024,
    )

    return response.choices[0].message.content


def generate(model, messages):

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )

    return response.choices[0].message.content


def stream_generate(model, messages):

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
        stream=True,
    )

    for chunk in stream:

        if (
            chunk.choices
            and chunk.choices[0].delta.content
        ):
            yield chunk.choices[0].delta.content