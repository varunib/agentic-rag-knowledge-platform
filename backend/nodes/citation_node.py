def citation_node(state):

    if state["citations"]:
        citation_text = "\n\nSources:\n"

        for citation in state["citations"]:
            citation_text += f"- {citation}\n"

        state["answer"] += citation_text

    return state