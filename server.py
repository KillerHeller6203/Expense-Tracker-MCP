from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from datetime import datetime, timedelta
import libsql_experimental as libsql
import os
import json

mcp = FastMCP("Expense-Tracker")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
TURSO_URL = os.environ.get("TURSO_URL")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN")

def get_user_db(user_key: str):
    conn = libsql.connect(
        f"expense_tracker_{user_key}.db",
        sync_url=TURSO_URL,
        auth_token=TURSO_TOKEN
    )
    conn.sync()
    return conn

def init_user_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL UNIQUE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            date TEXT NOT NULL,
            is_recurring INTEGER DEFAULT 0,
            recurrence TEXT
        )
    """)

    count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if count == 0:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        rows = [(cat,) for cat in config["categories"]]
        conn.executemany("INSERT INTO categories (category) VALUES (?)", rows)

    conn.commit()

@mcp.tool
def add_expense(amount: float, category: str, note: str) -> str:
    user_key = get_http_headers().get("x-api-key", "default")
    conn = get_user_db(user_key)
    init_user_db(conn)

    valid = conn.execute(
        "SELECT id FROM categories WHERE category = ?", (category,)
    ).fetchone()

    if not valid:
        rows = conn.execute("SELECT category FROM categories ORDER BY category").fetchall()
        conn.close()
        options = "\n".join([f"  - {r[0]}" for r in rows])
        return f"Invalid category. Available categories:\n{options}"

    conn.execute(
        "INSERT INTO expenses (amount, category, note, date) VALUES (?, ?, ?, ?)",
        (amount, category, note, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()
    return f"Added ₹{amount} → {category} - {note}"

@mcp.tool
def get_expenses() -> str:
    user_key = get_http_headers().get("x-api-key", "default")
    conn = get_user_db(user_key)
    init_user_db(conn)

    rows = conn.execute(
        "SELECT id, amount, category, note, date FROM expenses ORDER BY date DESC"
    ).fetchall()
    conn.close()

    if not rows:
        return "No expenses yet."

    result = ""
    for row in rows:
        result += f"[{row[0]}] ₹{row[1]} | {row[2]} | {row[3]} | {row[4]}\n"
    return result

@mcp.tool
def get_summary() -> str:
    user_key = get_http_headers().get("x-api-key", "default")
    conn = get_user_db(user_key)
    init_user_db(conn)

    rows = conn.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    """).fetchall()
    conn.close()

    if not rows:
        return "No expenses yet."

    result = "Summary by category:\n"
    for row in rows:
        result += f"  {row[0]}: ₹{row[1]}\n"
    return result

@mcp.tool
def get_expenses_by_period(period: str) -> str:
    """period: 'weekly', 'monthly', 'yearly'"""
    user_key = get_http_headers().get("x-api-key", "default")
    conn = get_user_db(user_key)
    init_user_db(conn)

    now = datetime.now()
    if period == "weekly":
        start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    elif period == "monthly":
        start = now.strftime("%Y-%m-01")
    elif period == "yearly":
        start = now.strftime("%Y-01-01")
    else:
        conn.close()
        return "Invalid period. Use: weekly, monthly, or yearly"

    rows = conn.execute(
        "SELECT id, amount, category, note, date FROM expenses WHERE date >= ? ORDER BY date DESC",
        (start,)
    ).fetchall()
    conn.close()

    if not rows:
        return f"No expenses for this {period} period."

    result = f"Expenses ({period}):\n"
    total = 0
    for row in rows:
        result += f"[{row[0]}] ₹{row[1]} | {row[2]} | {row[3]} | {row[4]}\n"
        total += row[1]
    result += f"\nTotal: ₹{total}"
    return result

@mcp.tool
def delete_expense(expense_id: int) -> str:
    user_key = get_http_headers().get("x-api-key", "default")
    conn = get_user_db(user_key)
    init_user_db(conn)

    existing = conn.execute(
        "SELECT id FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()

    if not existing:
        conn.close()
        return f"No expense found with id {expense_id}"

    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    return f"Deleted expense #{expense_id}"

@mcp.tool
def edit_expense(expense_id: int, amount: float, category: str, note: str) -> str:
    user_key = get_http_headers().get("x-api-key", "default")
    conn = get_user_db(user_key)
    init_user_db(conn)

    existing = conn.execute(
        "SELECT id FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()

    if not existing:
        conn.close()
        return f"No expense found with id {expense_id}"

    valid = conn.execute(
        "SELECT id FROM categories WHERE category = ?", (category,)
    ).fetchone()

    if not valid:
        rows = conn.execute("SELECT category FROM categories ORDER BY category").fetchall()
        conn.close()
        options = "\n".join([f"  - {r[0]}" for r in rows])
        return f"Invalid category. Available categories:\n{options}"

    conn.execute(
        "UPDATE expenses SET amount = ?, category = ?, note = ? WHERE id = ?",
        (amount, category, note, expense_id)
    )
    conn.commit()
    conn.close()
    return f"Updated expense #{expense_id} → ₹{amount} | {category} | {note}"

@mcp.tool
def add_category(category: str) -> str:
    user_key = get_http_headers().get("x-api-key", "default")
    conn = get_user_db(user_key)
    init_user_db(conn)

    existing = conn.execute(
        "SELECT id FROM categories WHERE category = ?", (category,)
    ).fetchone()

    if existing:
        conn.close()
        return f"Category '{category}' already exists"

    conn.execute("INSERT INTO categories (category) VALUES (?)", (category,))
    conn.commit()
    conn.close()
    return f"Added category '{category}'"

@mcp.tool
def delete_category(category: str) -> str:
    user_key = get_http_headers().get("x-api-key", "default")
    conn = get_user_db(user_key)
    init_user_db(conn)

    existing = conn.execute(
        "SELECT id FROM categories WHERE category = ?", (category,)
    ).fetchone()

    if not existing:
        conn.close()
        return f"Category '{category}' not found"

    conn.execute("DELETE FROM categories WHERE category = ?", (category,))
    conn.commit()
    conn.close()
    return f"Deleted category '{category}'"

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)