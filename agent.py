
from uagents_adapter import MCPServerAdapter
from server import mcp
from uagents import Agent
import os
from dotenv import load_dotenv


load_dotenv()

# Create an MCP adapter with your MCP server
mcp_adapter = MCPServerAdapter(
    mcp_server=mcp,                    
    asi1_api_key= os.getenv("ASI_API_KEY"),  
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
