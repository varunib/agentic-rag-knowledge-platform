def decide_route(question: str):

    q = question.lower()

    # Calculator
    if any(op in q for op in ["+", "-", "*", "/", "%"]):
        return "calculator"

    # Web Search
    if any(word in q for word in [
        "latest",
        "today",
        "news",
        "current",
        "recent",
        "weather",
        "stock",
    ]):
        return "web"

    # CSV
    # CSV
    if any(word in q for word in [
        "csv",
        "spreadsheet",
        "excel",
        "dataset",
        "table",
    ]):
        return "csv"

    # Code
    if any(word in q for word in [
        "python",
        "java",
        "code",
        "program",
        "algorithm",
    ]):
        return "code"

    # Vision
    if any(word in q for word in [
        "image",
        "picture",
        "photo",
        "vision",
    ]):
        return "vision"

    # SQL
    if any(word in q for word in [
        "database",
        "employee",
        "employees",
        "salary",
        "customer",
        "customers",
        "sql",
    ]):
        return "sql"

    # Document
    if any(word in q for word in [
        "document",
        "pdf",
        "uploaded",
        "file",
    ]):
        return "document"

    return "direct"