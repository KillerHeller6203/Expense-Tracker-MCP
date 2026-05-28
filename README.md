![Python](https://img.shields.io/badge/python-3.12+-blue) ![FastMCP](https://img.shields.io/badge/FastMCP-latest-orange) ![Turso](https://img.shields.io/badge/database-Turso-teal) ![MCP](https://img.shields.io/badge/MCP-remote-blueviolet) ![Users](https://img.shields.io/badge/multi--user-isolated-green) ![License](https://img.shields.io/badge/license-MIT-brightgreen)

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
      "url": "https://expense-tracker-mcp-pg6c.onrender.com/mcp",
      "headers": {
        "x-api-key": "your_unique_key"
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
```

**Step 5 — Add to Claude Desktop config**

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "C:/full/path/to/venv/Scripts/python.exe",
      "args": ["C:/full/path/to/proxy.py"],
      "env": {
        "MCP_USER_KEY": "your_unique_key"
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
- Turso — persistent cloud SQLite, per-user isolated databases
- Render — free cloud hosting
- Python 3.12+

--- 

## Deploy Your Own Instance

**Step 1 — Fork this repo on GitHub**

**Step 2 — Go to [render.com](https://render.com) and sign in with GitHub**

**Step 3 — New → Web Service → Connect your forked repo**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python server.py`
- **Instance Type:** Free

**Step 4 — Hit Deploy** and use your own URL in the config.

**Step 5 — Set up Turso**

- Go to [turso.tech](https://turso.tech) and create a free account
- Create a new database
- Generate a token
- Add these as environment variables in Render:
  - `TURSO_URL` = your database URL
  - `TURSO_TOKEN` = your token

---

## Customizing Default Categories

Edit `config.json` before deploying:

```json
{
  "categories": ["Food", "Transport", "Shopping", "Health", "Entertainment", "Education", "Utilities", "Other"]
}
```
This seeds a new user's database on first connection. After that manage categories via Claude directly.


