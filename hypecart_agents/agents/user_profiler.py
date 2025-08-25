import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp.server.models import StdioServerParameters

# IMPORTANT: This path needs to be absolute for the subprocess to find it.
# We construct it relative to this file's location.
DUMMY_MCP_SERVER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'dummy_mcp_server.py')
)

# Define the MCP Toolset that connects to our dummy server
# We give it a unique name to avoid conflicts if other agents use other toolsets
API_TOOLSET_PROFILER = MCPToolset(
    name="hypecart_api_profiler_toolset",
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='python3',
            args=[DUMMY_MCP_SERVER_PATH],
        ),
        timeout=10, # Timeout for the server to start
    ),
    # We can filter for the specific tools this agent needs
    tool_filter=['get_user_profile']
)

# Define the User Profiler Agent
user_profiler_agent = LlmAgent(
    model='gemini-1.5-flash',
    name='user_profiler_agent',
    instruction="""
You are a User Profiler agent. Your sole purpose is to fetch a user's profile
using their user ID. You must use the 'get_user_profile' tool.
Do not make up information. The user ID will be provided in the prompt.
""",
    description="An agent that fetches a user's profile using the HypeCart API.",
    tools=[API_TOOLSET_PROFILER],
)
