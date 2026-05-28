from fastmcp.server import create_proxy
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import os

user_key = os.environ.get("MCP_USER_KEY", "default")

transport = StreamableHttpTransport(
    "https://expense-tracker-mcp-pg6c.onrender.com/mcp",
    headers={"x-api-key": user_key}
)

client = Client(transport=transport)
mcp = create_proxy(client, name="Expense Tracker Proxy")

if __name__ == "__main__":
    mcp.run()