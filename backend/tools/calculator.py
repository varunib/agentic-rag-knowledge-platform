def calculator(expression):

    try:
        return eval(expression)

    except Exception:
        return "Invalid Expression"


def calculator_tool(question):

    try:
        return calculator(question)

    except Exception:
        return "Calculator Tool Error"