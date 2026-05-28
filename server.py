from fastmcp import FastMCP, Context
from datetime import datetime, timedelta
import aiosqlite
import os
import json

mcp = FastMCP("Expense-Tracker")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

async def get_user_db(user_key: str):
    db_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"db_{user_key}.sqlite"
    )
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    return conn

async def init_user_db(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL UNIQUE
        )
    """)

    await conn.execute("""
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

    cursor = await conn.execute("SELECT COUNT(*) FROM categories")
    row = await cursor.fetchone()
    count = row[0]

    if count == 0:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        rows = [(cat,) for cat in config["categories"]]
        await conn.executemany("INSERT INTO categories (category) VALUES (?)", rows)

    await conn.commit()

@mcp.tool
async def add_expense(amount: float, category: str, note: str, ctx: Context) -> str:
    request = await ctx.get_http_request()
    user_key = request.headers.get("x-api-key", "default")
    conn = await get_user_db(user_key)
    await init_user_db(conn)

    cursor = await conn.execute(
        "SELECT id FROM categories WHERE category = ?",
        (category,)
    )
    valid = await cursor.fetchone()

    if not valid:
        cursor = await conn.execute("SELECT category FROM categories ORDER BY category")
        rows = await cursor.fetchall()
        await conn.close()
        options = "\n".join([f"  - {r['category']}" for r in rows])
        return f"Invalid category. Available categories:\n{options}"

    await conn.execute(
        "INSERT INTO expenses (amount, category, note, date) VALUES (?, ?, ?, ?)",
        (amount, category, note, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    await conn.commit()
    await conn.close()
    return f"Added ₹{amount} → {category} - {note}"

@mcp.tool
async def get_expenses(ctx: Context) -> str:
    request = await ctx.get_http_request()
    user_key = request.headers.get("x-api-key", "default")
    conn = await get_user_db(user_key)
    await init_user_db(conn)

    cursor = await conn.execute(
        "SELECT id, amount, category, note, date FROM expenses ORDER BY date DESC"
    )
    rows = await cursor.fetchall()
    await conn.close()

    if not rows:
        return "No expenses yet."

    result = ""
    for row in rows:
        result += f"[{row['id']}] ₹{row['amount']} | {row['category']} | {row['note']} | {row['date']}\n"
    return result

@mcp.tool
async def get_summary(ctx: Context) -> str:
    request = await ctx.get_http_request()
    user_key = request.headers.get("x-api-key", "default")
    conn = await get_user_db(user_key)
    await init_user_db(conn)

    cursor = await conn.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    """)
    rows = await cursor.fetchall()
    await conn.close()

    if not rows:
        return "No expenses yet."

    result = "Summary by category:\n"
    for row in rows:
        result += f"  {row['category']}: ₹{row['total']}\n"
    return result

@mcp.tool
async def get_expenses_by_period(period: str, ctx: Context) -> str:
    """period: 'weekly', 'monthly', 'yearly'"""
    request = await ctx.get_http_request()
    user_key = request.headers.get("x-api-key", "default")
    conn = await get_user_db(user_key)
    await init_user_db(conn)

    now = datetime.now()

    if period == "weekly":
        start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    elif period == "monthly":
        start = now.strftime("%Y-%m-01")
    elif period == "yearly":
        start = now.strftime("%Y-01-01")
    else:
        await conn.close()
        return "Invalid period. Use: weekly, monthly, or yearly"

    cursor = await conn.execute(
        "SELECT id, amount, category, note, date FROM expenses WHERE date >= ? ORDER BY date DESC",
        (start,)
    )
    rows = await cursor.fetchall()
    await conn.close()

    if not rows:
        return f"No expenses for this {period} period."

    result = f"Expenses ({period}):\n"
    total = 0
    for row in rows:
        result += f"[{row['id']}] ₹{row['amount']} | {row['category']} | {row['note']} | {row['date']}\n"
        total += row['amount']
    result += f"\nTotal: ₹{total}"
    return result

@mcp.tool
async def delete_expense(expense_id: int, ctx: Context) -> str:
    request = await ctx.get_http_request()
    user_key = request.headers.get("x-api-key", "default")
    conn = await get_user_db(user_key)
    await init_user_db(conn)

    cursor = await conn.execute(
        "SELECT id FROM expenses WHERE id = ?",
        (expense_id,)
    )
    existing = await cursor.fetchone()

    if not existing:
        await conn.close()
        return f"No expense found with id {expense_id}"

    await conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    await conn.commit()
    await conn.close()
    return f"Deleted expense #{expense_id}"

@mcp.tool
async def edit_expense(expense_id: int, amount: float, category: str, note: str, ctx: Context) -> str:
    request = await ctx.get_http_request()
    user_key = request.headers.get("x-api-key", "default")
    conn = await get_user_db(user_key)
    await init_user_db(conn)

    cursor = await conn.execute(
        "SELECT id FROM expenses WHERE id = ?",
        (expense_id,)
    )
    existing = await cursor.fetchone()

    if not existing:
        await conn.close()
        return f"No expense found with id {expense_id}"

    cursor = await conn.execute(
        "SELECT id FROM categories WHERE category = ?",
        (category,)
    )
    valid = await cursor.fetchone()

    if not valid:
        cursor = await conn.execute("SELECT category FROM categories ORDER BY category")
        rows = await cursor.fetchall()
        await conn.close()
        options = "\n".join([f"  - {r['category']}" for r in rows])
        return f"Invalid category. Available categories:\n{options}"

    await conn.execute(
        "UPDATE expenses SET amount = ?, category = ?, note = ? WHERE id = ?",
        (amount, category, note, expense_id)
    )
    await conn.commit()
    await conn.close()
    return f"Updated expense #{expense_id} → ₹{amount} | {category} | {note}"

@mcp.tool
async def add_category(category: str, ctx: Context) -> str:
    request = await ctx.get_http_request()
    user_key = request.headers.get("x-api-key", "default")
    conn = await get_user_db(user_key)
    await init_user_db(conn)

    cursor = await conn.execute(
        "SELECT id FROM categories WHERE category = ?",
        (category,)
    )
    existing = await cursor.fetchone()

    if existing:
        await conn.close()
        return f"Category '{category}' already exists"

    await conn.execute("INSERT INTO categories (category) VALUES (?)", (category,))
    await conn.commit()
    await conn.close()
    return f"Added category '{category}'"

@mcp.tool
async def delete_category(category: str, ctx: Context) -> str:
    request = await ctx.get_http_request()
    user_key = request.headers.get("x-api-key", "default")
    conn = await get_user_db(user_key)
    await init_user_db(conn)

    cursor = await conn.execute(
        "SELECT id FROM categories WHERE category = ?",
        (category,)
    )
    existing = await cursor.fetchone()

    if not existing:
        await conn.close()
        return f"Category '{category}' not found"

    await conn.execute("DELETE FROM categories WHERE category = ?", (category,))
    await conn.commit()
    await conn.close()
    return f"Deleted category '{category}'"

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)