import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def web_search(query: str, max_results: int = 5):

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
    )

    results = []

    for item in response.get("results", []):

        results.append(
            {
                "title": item.get("title", ""),
                "body": item.get("content", ""),
                "url": item.get("url", ""),
            }
        )

    return results