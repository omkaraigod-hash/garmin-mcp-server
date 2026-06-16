import os
import json
import base64
from datetime import date, timedelta
from garminconnect import Garmin
from mcp.server.fastmcp import FastMCP

# Load tokens
tokens_b64 = os.environ.get("GARMIN_TOKENS_B64")
if tokens_b64:
    tokens = json.loads(base64.b64decode(tokens_b64).decode())
    os.makedirs(os.path.expanduser("~/.garminconnect"), exist_ok=True)
    for filename, content in tokens.items():
        with open(os.path.expanduser(f"~/.garminconnect/{filename}"), "w") as f:
            f.write(content)

client = Garmin(os.environ["GARMIN_EMAIL"], os.environ["GARMIN_PASSWORD"])
client.login()

port = int(os.environ.get("PORT", 8080))
mcp = FastMCP("Garmin MCP", host="0.0.0.0", port=port)

@mcp.tool()
def get_today_stats() -> str:
    """Get today's Garmin stats: steps, calories, HR"""
    return json.dumps(client.get_stats(date.today().isoformat()))

@mcp.tool()
def get_sleep(target_date: str = "") -> str:
    """Get sleep data. Date format: YYYY-MM-DD. Defaults to last night."""
    d = target_date or (date.today() - timedelta(days=1)).isoformat()
    return json.dumps(client.get_sleep_data(d))

@mcp.tool()
def get_activities(limit: int = 5) -> str:
    """Get recent Garmin activities"""
    return json.dumps(client.get_activities(0, limit))

@mcp.tool()
def get_hrv(target_date: str = "") -> str:
    """Get HRV data. Date format: YYYY-MM-DD. Defaults to today."""
    d = target_date or date.today().isoformat()
    return json.dumps(client.get_hrv_data(d))

@mcp.tool()
def get_body_battery(target_date: str = "") -> str:
    """Get body battery. Date format: YYYY-MM-DD. Defaults to today."""
    d = target_date or date.today().isoformat()
    return json.dumps(client.get_body_battery(d))

if __name__ == "__main__":
    mcp.run(transport="sse")
