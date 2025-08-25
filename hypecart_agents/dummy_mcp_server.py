import asyncio
import json
import datetime
import random
import string

# MCP Server Imports
from mcp import types as mcp_types
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# --- Dummy Data ---

DUMMY_USER_PROFILES = {
    "user123": {
        "name": "Raj",
        "demographics": {"age_range": "25-34", "location": "Mumbai, India"},
        "behavioral_patterns": {"shopping_style": "impulse_buyer", "preferred_tone": "casual_friendly"},
        "context": {"current_season": "monsoon", "mood_indicators": "adventure_seeking"}
    }
}

DUMMY_CARTS = {
    "user123": {
        "items": [{"productId": "product456", "name": "Nike Air Max Trail Running Shoes", "quantity": 1}],
        "last_modified": datetime.datetime.now(datetime.UTC).isoformat()
    }
}

# --- Tool Functions ---

async def get_user_profile(user_id: str) -> dict:
    """Fetches the profile for a given user ID."""
    print(f"MCP Server: Called get_user_profile with user_id={user_id}")
    return DUMMY_USER_PROFILES.get(user_id, {"error": "User not found"})

async def get_user_cart(user_id: str) -> dict:
    """Fetches the cart contents for a given user."""
    print(f"MCP Server: Called get_user_cart with user_id={user_id}")
    return DUMMY_CARTS.get(user_id, {"error": "Cart not found"})

async def generate_video_ad(script: str, user_profile: dict, product_info: dict) -> dict:
    """Simulates generating a video ad based on a script and other data."""
    print(f"MCP Server: Called generate_video_ad with script='{script}'")
    video_id = "vid_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    video_url = f"https://fake-storage.googleapis.com/hypecart-videos/{video_id}.mp4"
    return {"status": "success", "video_url": video_url}

# --- MCP Server Setup ---

app = Server("hypecart-dummy-api-server")

# Define the tools the server will expose
TOOLS = {
    "get_user_profile": get_user_profile,
    "get_user_cart": get_user_cart,
    "generate_video_ad": generate_video_ad,
}

TOOL_SCHEMAS = [
    mcp_types.Tool(
        name="get_user_profile",
        description="Fetches the profile for a given user ID.",
        inputSchema={"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]},
    ),
    mcp_types.Tool(
        name="get_user_cart",
        description="Fetches the cart contents for a given user ID.",
        inputSchema={"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]},
    ),
    mcp_types.Tool(
        name="generate_video_ad",
        description="Generates a video ad from a script, user profile, and product info.",
        inputSchema={
            "type": "object",
            "properties": {
                "script": {"type": "string"},
                "user_profile": {"type": "object"},
                "product_info": {"type": "object"},
            },
            "required": ["script", "user_profile", "product_info"],
        },
    ),
]

@app.list_tools()
async def list_mcp_tools() -> list[mcp_types.Tool]:
    """MCP handler to list tools this server exposes."""
    print("MCP Server: Received list_tools request.")
    return TOOL_SCHEMAS

@app.call_tool()
async def call_mcp_tool(name: str, arguments: dict) -> list[mcp_types.Content]:
    """MCP handler to execute a tool call requested by an MCP client."""
    print(f"MCP Server: Received call_tool request for '{name}' with args: {arguments}")

    if name in TOOLS:
        try:
            tool_function = TOOLS[name]
            result = await tool_function(**arguments)
            response_text = json.dumps(result, indent=2)
            return [mcp_types.TextContent(type="text", text=response_text)]
        except Exception as e:
            error_text = json.dumps({"error": f"Failed to execute tool '{name}': {str(e)}"})
            return [mcp_types.TextContent(type="text", text=error_text)]
    else:
        error_text = json.dumps({"error": f"Tool '{name}' not implemented by this server."})
        return [mcp_types.TextContent(type="text", text=error_text)]

# --- MCP Server Runner ---

async def run_mcp_stdio_server():
    """Runs the MCP server, listening for connections over standard input/output."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        print("MCP Stdio Server: Starting handshake with client...")
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=app.name,
                server_version="0.1.0",
                capabilities=app.get_capabilities(notification_options=NotificationOptions()),
            ),
        )
        print("MCP Stdio Server: Run loop finished or client disconnected.")

if __name__ == "__main__":
    print("Launching Dummy MCP Server for HypeCart...")
    try:
        asyncio.run(run_mcp_stdio_server())
    except KeyboardInterrupt:
        print("\nDummy MCP Server stopped by user.")
