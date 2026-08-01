from services.llm_service import stream_generate

messages = [
    {
        "role": "user",
        "content": "Explain Artificial Intelligence in 100 words."
    }
]

for token in stream_generate(
    "llama-3.3-70b-versatile",
    messages,
):
    print(token, end="", flush=True)