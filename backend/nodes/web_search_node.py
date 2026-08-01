from duckduckgo_search import DDGS

def web_search_node(state):
    query = state["question"]

    results = []

    with DDGS() as ddgs:
        search_results = ddgs.text(query, max_results=5)

        for result in search_results:
            results.append(
                f"Title: {result['title']}\n"
                f"URL: {result['href']}\n"
                f"Snippet: {result['body']}"
            )

    state["web_results"] = "\n\n".join(results)

    return state