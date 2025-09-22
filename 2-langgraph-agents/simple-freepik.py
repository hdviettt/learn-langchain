#!/usr/bin/env python3

import asyncio
import sys
import json
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv

load_dotenv()

# MCP client setup
client = MultiServerMCPClient({
    "freepik": {
        "transport": "stdio",
        "command": "node",
        "args": ["D:/MCP/mcp-servers/freepik-mcp/build/index.js"],
        "env": {
            "FREEPIK_API_KEY": "FPSXc9090585b01a4d179970e36802528be5"
        },
    },
})

async def search_images(query, limit=5):
    """Search for images using Freepik MCP"""
    tools = await client.get_tools()
    search_tool = next(t for t in tools if t.name == 'search_resources')

    try:
        result = await search_tool.ainvoke({
            'query': query,
            'limit': limit
        })
        return result
    except Exception as e:
        return f"Error: {e}"

async def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("What would you like to search for? ")

    print(f"Searching Freepik for: {query}")
    result = await search_images(query, 5)

    # Parse JSON string if needed
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {result[:200]}...")
            return

    if isinstance(result, dict) and 'data' in result:
        print(f"\nFound {len(result['data'])} results:")
        for i, item in enumerate(result['data'], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   Type: {item['image']['type']}")
            print(f"   URL: {item['url']}")
            print(f"   Downloads: {item['stats']['downloads']:,}")
    elif isinstance(result, str) and result.startswith("Error:"):
        print(f"Search failed: {result}")
    else:
        print(f"Unexpected result format: {type(result)}")

if __name__ == "__main__":
    asyncio.run(main())