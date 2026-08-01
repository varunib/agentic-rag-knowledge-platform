import pandas as pd


def analyze_csv(file_path):

    df = pd.read_csv(file_path)

    return {
        "rows": len(df),
        "columns": list(df.columns),
        "summary": df.describe(include="all").to_string(),
    }