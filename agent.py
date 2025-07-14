
from uagents_adapter import MCPServerAdapter
from server import mcp
from uagents import Agent

# Create an MCP adapter with your MCP server
mcp_adapter = MCPServerAdapter(
    mcp_server=mcp,                    
    asi1_api_key="sk_d1f44feafaea4b6896123e5573182e5edc5499b1d0554b8bbf54e8d6887ff12c",  
    model="asi1-mini"          
)

# Create a uAgent
agent = Agent(
    name="mcp_agent",
    port=8000,
    seed="mcp agent secret phrase",
    mailbox=True
)

# Include protocols from the adapter
for protocol in mcp_adapter.protocols:
    agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    # Run the MCP adapter with the agent
    mcp_adapter.run(agent)