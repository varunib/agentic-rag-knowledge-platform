import io
from contextlib import redirect_stdout


def execute_python(code):

    output = io.StringIO()

    try:
        with redirect_stdout(output):
            exec(code, {})

        return output.getvalue()

    except Exception as e:
        return f"Execution Error: {e}"