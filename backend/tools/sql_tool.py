import sqlite3


def run_sql(query):

    conn = sqlite3.connect("database/sample.db")
    cursor = conn.cursor()

    try:
        cursor.execute(query)

        rows = cursor.fetchall()

        conn.close()

        return rows

    except Exception as e:

        conn.close()

        return f"SQL Error: {e}"