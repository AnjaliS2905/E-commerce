"""Separate MCP client process. Start mcp_server.py first."""
import asyncio
from fastmcp import Client
async def main():
    async with Client("http://127.0.0.1:8001/mcp") as client:
        for rid in ("NYK-0001","NYK-0002"):
            result=await client.call_tool("lookup_order",{"record_id":rid})
            print(rid, result)
if __name__=="__main__": asyncio.run(main())
