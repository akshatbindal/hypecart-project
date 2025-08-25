import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp.server.models import StdioServerParameters

DUMMY_MCP_SERVER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'dummy_mcp_server.py')
)

# Define the MCP Toolset that connects to our dummy server
API_TOOLSET_VIDEO = MCPToolset(
    name="hypecart_api_video_toolset",
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='python3',
            args=[DUMMY_MCP_SERVER_PATH],
        ),
        timeout=10,
    ),
    tool_filter=['generate_video_ad']
)

# Define the Video Production Agent
video_production_agent = LlmAgent(
    model='gemini-1.5-flash',
    name='video_production_agent',
    instruction="""
You are a Video Production agent. Your job is to take a detailed Veo prompt,
user profile, and product information and use the 'generate_video_ad' tool
to create the final video ad.
""",
    description="An agent that triggers the final video ad generation.",
    tools=[API_TOOLSET_VIDEO],
)
