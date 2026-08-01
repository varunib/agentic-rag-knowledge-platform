from tools.calculator import calculator


def calculator_node(state):

    state["answer"] = str(calculator(state["question"]))

    return state