from langchain_mcp_adapters.client import  MultiServerMCPClient
import asyncio


async def main():
    client = MultiServerMCPClient(
        {
            "image": {
                "transport": "http",  # Local subprocess communication
                # Absolute path to your image_server.py file
                "url": "http://localhost:9000/mcp",
            }
        }
    )

    tools = await client.get_tools()
    print(tools)

asyncio.run(main())
