# weather_server.py
from typing import List
from mcp.server.fastmcp import FastMCP
import pytz
from datetime import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8005, help="Port number for MCP server")
args = parser.parse_args()

# mcp = FastMCP("Mcp", port=8005)
mcp = FastMCP("Mcp", port=args.port)


@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for location."""
    return "It's always sunny in New York"

@mcp.tool()
async def get_current_time() -> str:
    """Get current time."""
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    return now.strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    # mcp.run(transport="sse")
    mcp.run(transport="sse")