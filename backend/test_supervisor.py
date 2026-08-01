from services.supervisor_service import supervisor_route

questions = [
    "Show all employees",
    "Latest AI news",
    "Summarize uploaded PDF",
    "Calculate 56 * 89",
    "Analyze this CSV",
]

for q in questions:

    route = supervisor_route(
        q,
        "llama-3.3-70b-versatile",
    )

    print(q)
    print("->", route)
    print()