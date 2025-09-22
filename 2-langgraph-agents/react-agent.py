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
import json
# from tools import add, subtract, multiply, web_search

## LANGGRAPH NODES AND STATE
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent

## MCP
from langchain_mcp_adapters.client import MultiServerMCPClient

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
      }
    }
    }
)

# Get MCP tools asynchronously
async def get_mcp_tools():
    return await client.get_tools()

mcp_tools = asyncio.run(get_mcp_tools())

# Create custom wrapper tools that work with LangGraph
@tool
def search_freepik_images(query: str, limit: int = 5) -> str:
    """Search for images on Freepik. Returns JSON string with search results."""
    async def _search():
        search_tool = next(t for t in mcp_tools if t.name == 'search_resources')
        # Pass the search parameters correctly - the parameter is 'term' not 'query'
        result = await search_tool.ainvoke({
            'term': query,
            'limit': limit,
            'order': 'relevance'
        })
        return result

    result = asyncio.run(_search())

    # Parse JSON if it's a string
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            if 'data' in parsed:
                # Format the results nicely
                items = []
                for item in parsed['data'][:limit]:
                    items.append({
                        'title': item['title'],
                        'type': item['image']['type'],
                        'url': item['url'],
                        'downloads': item['stats']['downloads'],
                        'image_url': item['image']['source']['url']
                    })
                return json.dumps(items, indent=2)
        except json.JSONDecodeError:
            pass

    return str(result)

@tool
def get_freepik_resource_details(resource_id: str) -> str:
    """Get detailed information about a specific Freepik resource by ID."""
    async def _get_details():
        detail_tool = next(t for t in mcp_tools if t.name == 'get_resource')
        result = await detail_tool.ainvoke({'id': resource_id})
        return result

    result = asyncio.run(_get_details())
    return str(result)

# Use custom tools instead of MCP tools directly
tools = [search_freepik_images, get_freepik_resource_details]

# Call the chat model and bind tools
model = ChatAnthropic(model = "claude-sonnet-4-20250514").bind_tools(tools)

# Define function for model invoking
def model_call(state:AgentState) -> AgentState:
    system_prompt = SystemMessage(content=
        "You are my AI assistant with access to Freepik image search. I can help you find images, vectors, and other resources from Freepik. Use the search_freepik_images tool to search for images and get_freepik_resource_details for detailed information about specific resources."
    )
    response = model.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}


# Define function to check if the agent should continue or end
def should_continue(state: AgentState): 
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls: 
        return "end"
    else:
        return "continue"
    

# BUILD THE GRAPH
graph = StateGraph(AgentState)
graph.add_node("our_agent", model_call)

tool_node = ToolNode(tools=tools)
graph.add_node("tools", tool_node)
graph.set_entry_point("our_agent")
graph.add_conditional_edges(
    "our_agent",
    should_continue,
    {
        "continue": "tools",
        "end": END,
    },
)
graph.add_edge("tools", "our_agent")

app = graph.compile()

# STREAM THE APP
def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            try:
                message.pretty_print()
            except UnicodeEncodeError:
                # Handle Unicode encoding issues on Windows
                print(f"Message type: {type(message).__name__}")
                if hasattr(message, 'content'):
                    print(f"Content: {message.content.encode('ascii', 'ignore').decode('ascii')}")
                else:
                    print(f"Message: {str(message).encode('ascii', 'ignore').decode('ascii')}")

inputs = {"messages": [("user", input())]}
print_stream(app.stream(inputs, stream_mode="values"))
