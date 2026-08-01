import sqlite3

conn = sqlite3.connect("database/sample.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS employees(
    id INTEGER PRIMARY KEY,
    name TEXT,
    salary INTEGER
)
""")

cursor.execute("DELETE FROM employees")

cursor.execute("INSERT INTO employees(name,salary) VALUES('Alice',50000)")
cursor.execute("INSERT INTO employees(name,salary) VALUES('Bob',60000)")
cursor.execute("INSERT INTO employees(name,salary) VALUES('Charlie',70000)")

conn.commit()

conn.close()

print("Database Created")