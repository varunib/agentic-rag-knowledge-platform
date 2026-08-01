from tools.web_search import web_search
from tools.calculator import calculator
from tools.sql_tool import run_sql
from services.sql_service import generate_sql
from tools.csv_tool import analyze_csv
from tools.python_executor import execute_python
from services.llm_service import generate


async def tool_node(state):

    route = state["route"]
    question = state["question"]

    print(f"Tool Node Route: {route}")

    if route == "web":

        results = web_search(question)

        text = ""

        for item in results:
            text += f"""
Title: {item['title']}
Content: {item['body']}
URL: {item['url']}

"""

        state["tool_result"] = text

    elif route == "calculator":

        try:
            state["tool_result"] = str(calculator(question))
        except Exception:
            state["tool_result"] = "Calculation failed."

    elif route == "sql":

        sql = generate_sql(
            question,
            state["model"],
        )

        print("Generated SQL:", sql)

        result = run_sql(sql)

        state["tool_result"] = str(result)

    elif route == "code":

        prompt = f"""
Generate ONLY executable Python code.

Do NOT explain.
Do NOT use markdown.
Do NOT use ```python.

Task:
{question}
"""

        code = generate(
            state["model"],
            [
                {
                    "role": "system",
                    "content": prompt,
            },
            {
                "role": "user",
                "content": question,
            },
            ],
        )

        print("Generated Python Code:")
        print(code)

        output = execute_python(code)

        state["tool_result"] = f"""
Generated Code:

{code}

Output:

{output}
"""

    elif route == "csv":

        result = analyze_csv("data/employees.csv")

        state["tool_result"] = str(result)

    elif route == "vision":

        state["tool_result"] = (
            "Vision module will be implemented next."
        )

    else:

        state["tool_result"] = ""

    return state