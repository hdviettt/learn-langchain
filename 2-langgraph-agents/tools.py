## LANGGRAPH TOOLS
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

## IMPORT TAVILY
from langchain_tavily import TavilySearch


@tool
def add(a: int, b:int):
    """This is an addition function that adds 2 numbers together"""

    return a + b 

@tool
def subtract(a: int, b: int):
    """Subtraction function"""
    return a - b

@tool
def multiply(a: int, b: int):
    """Multiplication function"""
    return a * b

@tool
def web_search(query: str):
    """A web search tool that uses Tavily to search the web"""
    search = TavilySearch(
        max_results=5,
        topic="general"
    )
    return search.invoke(query)
