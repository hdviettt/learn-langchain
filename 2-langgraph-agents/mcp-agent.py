# IMPORTS
## FOR DATA TYPES
from typing import Annotated, Sequence, TypedDict

## OPEN AI MODEL WITH LANGCHAIN
from langchain_openai import ChatOpenAI

## ANTHROPIC MODEL WITH LANGCHAIN
from langchain_anthropic import ChatAnthropic

## MESSAGES FOR LANGGRAPH
from langchain_core.messages import BaseMessage # The foundational class for all message types in LangGraph
from langchain_core.messages import ToolMessage # Passes data back to LLM after it calls a tool such as the content and the tool_call_id
from langchain_core.messages import SystemMessage # Message for providing instructions to the LLM
from langgraph.graph.message import add_messages

## LANGGRAPH TOOLS
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
# from tools import add, subtract, multiply, web_search

## LANGGRAPH NODES AND STATE
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent

## MCP
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

# FOR LOADING ENVIRONMENT VARIABLES
from dotenv import load_dotenv
import asyncio

## load .env
load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# MCP
client = MultiServerMCPClient(
    {
    "freepik": {
      "transport": "stdio",
      "command": "node",
      "args": ["D:/MCP/mcp-servers/freepik-mcp/build/index.js"],
      "env": {
        "FREEPIK_API_KEY": "FPSXc9090585b01a4d179970e36802528be5"
      },
    },
    }
)

# Get tools from MCP client asynchronously
async def get_tools():
    return await client.get_tools()

tools = asyncio.run(get_tools())



# Try with explicit model instead of string
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-20250514")
agent = create_react_agent(model, tools)

try:
    response = agent.invoke({"messages": input()})
    print(response["messages"][-1].content)
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()

