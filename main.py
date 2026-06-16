import os
import json
import base64
import asyncio
from datetime import date, timedelta
from garminconnect import Garmin
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
import uvicorn

# Auth using pre-generated tokens
tokens_b64 = os.environ.get("GARMIN_TOKENS_B64")
if tokens_b64:
    tokens = json.loads(base64.b64decode(tokens_b64).decode())
    os.makedirs(os.path.expanduser("~/.garminconnect"), exist_ok=True)
    for filename, content in tokens.items():
        with open(os.path.expanduser(f"~/.garminconnect/{filename}"), "w") as f:
            f.write(content)

client = Garmin(os.environ["GARMIN_EMAIL"], os.environ["GARMIN_PASSWORD"])
client.login()

mcp = FastMCP("Garmin MCP")

@mcp.tool()
def get_today_stats() -> str:
    """Get today's Garmin stats: steps, calories, HR"""
    data = client.get_stats(date.today().isoformat())
    return json.dumps(data)

@mcp.tool()
def get_sleep(target_date: str = "") -> str:
    """Get sleep data. Date format: YYYY-MM-DD. Defaults to last night."""
    d = target_date or (date.today() - timedelta(days=1)).isoformat()
    data = client.get_sleep_data(d)
    return json.dumps(data)

@mcp.tool()
def get_activities(limit: int = 5) -> str:
    """Get recent Garmin activities"""
    data = client.get_activities(0, limit)
    return json.dumps(data)

@mcp.tool()
def get_hrv(target_date: str = "") -> str:
    """Get HRV data. Date format: YYYY-MM-DD. Defaults to today."""
    d = target_date or date.today().isoformat()
    data = client.get_hrv_data(d)
    return json.dumps(data)

@mcp.tool()
def get_body_battery(target_date: str = "") -> str:
    """Get body battery data for a date."""
    d = target_date or date.today().isoformat()
    data = client.get_body_battery(d)
    return json.dumps(data)

# SSE transport
sse = SseServerTransport("/messages/")

async def handle_sse(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp.run(streams[0], streams[1], mcp.create_initialization_options())

app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse),
    Mount("/messages/", app=sse.handle_post_message),
])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
