from tools.web_search import web_search

print("========== TAVILY TEST ==========\n")

results = web_search("Latest AI news")

print(f"Found {len(results)} results\n")

for i, result in enumerate(results, start=1):
    print("=" * 80)
    print(f"Result {i}")
    print("Title :", result["title"])
    print("URL   :", result["url"])
    print("Body  :", result["body"][:300], "...")