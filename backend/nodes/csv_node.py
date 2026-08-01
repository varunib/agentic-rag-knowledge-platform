from tools.csv_reader import read_csv


def csv_node(state):

    try:

        df = read_csv("sample.csv")

        state["answer"] = df.head().to_string()

    except Exception as e:

        state["answer"] = str(e)

    return state