import sqlite3


def sql_agent_node(state):

    question = state["question"]

    try:
        conn = sqlite3.connect("rag.db")

        cursor = conn.cursor()

        cursor.execute(question)

        rows = cursor.fetchall()

        state["answer"] = str(rows)

        conn.close()

    except Exception as e:
        state["answer"] = str(e)

    return state