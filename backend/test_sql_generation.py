from services.sql_service import generate_sql

question = "Show all employees"

sql = generate_sql(
    question,
    "llama-3.3-70b-versatile",
)

print(sql)