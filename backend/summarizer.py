def summarize_document(client, context):

    prompt = f"""
Summarize this document.

Give:

1. Executive Summary

2. Key Points

3. Important Facts

4. Conclusion

Context:

{context}
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