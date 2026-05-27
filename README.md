![Python](https://img.shields.io/badge/python-3.10+-blue) ![FastMCP](https://img.shields.io/badge/FastMCP-latest-orange) ![SQLite](https://img.shields.io/badge/database-SQLite-lightblue) ![MCP](https://img.shields.io/badge/MCP-remote-blueviolet) ![Users](https://img.shields.io/badge/multi--user-isolated-green) ![License](https://img.shields.io/badge/license-MIT-brightgreen)

# Expense Tracker MCP

A remote MCP server that lets you track your personal expenses directly through Claude. Each user gets their own isolated database — your data is never shared with anyone else.

---

## What it does

Talk to Claude naturally to manage your expenses:

- **Add expenses** — "I spent 200 on food for lunch"
- **View expenses** — "Show me all my expenses"
- **Filter by period** — "Show my expenses this month"
- **Get a summary** — "How much have I spent per category?"
- **Edit expenses** — "Change the uber expense to 350"
- **Delete expenses** — "Delete the medicine one"
- **Manage categories** — "Add a category called Rent"

---

## Available Tools

| Tool | Description |
|------|-------------|
| `add_expense` | Add a new expense with amount, category, and note |
| `get_expenses` | List all your expenses |
| `get_summary` | Total spending grouped by category |
| `get_expenses_by_period` | Filter by `weekly`, `monthly`, or `yearly` |
| `edit_expense` | Update an existing expense |
| `delete_expense` | Remove an expense |
| `add_category` | Add a custom category |
| `delete_category` | Remove a category |

Default categories: Food, Transport, Shopping, Health, Entertainment, Education, Utilities, Other

---

## How to Connect

### Option A — Claude Pro / Paid (Direct URL)

Open your Claude Desktop config file:

- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add this:

```json
{
  "mcpServers": {
    "expense-tracker": {
      "type": "streamable-http",
      "url": "https://clear-red-swallow.fastmcp.app/mcp",
      "headers": {
        "api_key": "your_unique_key"
      }
    }
  }
}
```

Replace `your_unique_key` with anything you want — this becomes your personal identifier. Examples: `rick`, `killerheller`, `alice123`. Each unique key gets its own isolated database.

Restart Claude Desktop. Done.

---

### Option B — Claude Free (Local Proxy)

Claude free tier doesn't support remote HTTP servers directly. You need a small local proxy that runs on your machine and forwards requests to the remote server.

**Step 1 — Clone this repo**

```bash
git clone https://github.com/KillerHeller6203/Expense-Tracker-MCP.git
cd Expense-Tracker-MCP
```

**Step 2 — Set up a virtual environment**

```bash
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**Step 3 — Install dependencies**

```bash
pip install fastmcp
```

**Step 4 — Create a proxy file**

Create a new file called `proxy.py` in the project folder:

```python
from fastmcp import FastMCP

mcp = FastMCP.as_proxy(
    "https://clear-red-swallow.fastmcp.app/mcp",
    name="Expense Tracker Proxy"
)

if __name__ == "__main__":
    mcp.run()
```

**Step 5 — Add to Claude Desktop config**

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "python",
      "args": ["C:/full/path/to/proxy.py"],
      "env": {
        "api_key": "your_unique_key"
      }
    }
  }
}
```

Replace `C:/full/path/to/proxy.py` with the actual full path to your `proxy.py` file.
Replace `your_unique_key` with anything you want as your personal identifier.

Restart Claude Desktop. Done.

---

This file is only used to seed a brand new user's database on first connection. After that, use the `add_category` and `delete_category` tools to manage categories.

---

## Tech Stack

- [FastMCP](https://gofastmcp.com) — MCP server framework
- SQLite — per-user isolated databases
- Python 3.10+
