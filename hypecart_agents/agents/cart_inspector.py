import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp.server.models import StdioServerParameters

DUMMY_MCP_SERVER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'dummy_mcp_server.py')
)

# Define the MCP Toolset that connects to our dummy server
API_TOOLSET_CART = MCPToolset(
    name="hypecart_api_cart_toolset",
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='python3',
            args=[DUMMY_MCP_SERVER_PATH],
        ),
        timeout=10,
    ),
    tool_filter=['get_user_cart']
)

# Define the Cart Inspector Agent
cart_inspector_agent = LlmAgent(
    model='gemini-1.5-flash',
    name='cart_inspector_agent',
    instruction="""
You are a Cart Inspector agent. Your only job is to get the contents of a user's
shopping cart by their user ID. Use the 'get_user_cart' tool.
The user ID will be provided in the prompt.
""",
    description="An agent that fetches a user's cart from the HypeCart API.",
    tools=[API_TOOLSET_CART],
)
