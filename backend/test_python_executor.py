from tools.python_executor import execute_python

code = """
for i in range(5):
    print(i)
"""

result = execute_python(code)

print(result)