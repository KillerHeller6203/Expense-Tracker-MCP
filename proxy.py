from fastmcp.server import create_proxy

mcp = create_proxy(
    "https://expense-tracker-mcp-pg6c.onrender.com/mcp",
    name="Expense Tracker Proxy"
)

if __name__ == "__main__":
    mcp.run()