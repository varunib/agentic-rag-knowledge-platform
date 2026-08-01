from tools.web_tool import web_search_tool
from tools.sql_tool import sql_tool

from tools.calculator import calculator_tool
from tools.csv_reader import csv_tool


def execute_tool(route, question):

    if route == "web":
        return web_search_tool(question)

    if route == "calculator":
        return calculator_tool(question)

    if route == "sql":
        return sql_tool(question)

    if route == "csv":
        return csv_tool(question)

    return None