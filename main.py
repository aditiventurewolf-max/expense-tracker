from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import sqlite3

app = FastAPI()

# ── Database setup ──────────────────────────────────────────
def get_db():
    conn = sqlite3.connect("expenses.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ── Schema ───────────────────────────────────────────────────
class Expense(BaseModel):
    title: str
    amount: float
    category: str
    note: Optional[str] = None

# ── Routes ───────────────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "Expense Tracker API is running"}

@app.post("/expenses")
def add_expense(expense: Expense):
    conn = get_db()
    expense_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO expenses (id, title, amount, category, note) VALUES (?, ?, ?, ?, ?)",
        (expense_id, expense.title, expense.amount, expense.category, expense.note)
    )
    conn.commit()
    conn.close()
    return {"message": "Expense added", "id": expense_id}

@app.get("/expenses")
def get_expenses(category: Optional[str] = None):
    conn = get_db()
    if category:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE LOWER(category) = LOWER(?)", (category,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM expenses").fetchall()
    conn.close()
    return {"expenses": [dict(row) for row in rows]}

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str):
    conn = get_db()
    result = conn.execute(
        "DELETE FROM expenses WHERE id = ?", (expense_id,)
    )
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted"}

@app.put("/expenses/{expense_id}")
def update_expense(expense_id: str, expense: Expense):
    conn = get_db()
    result = conn.execute(
        """UPDATE expenses 
           SET title = ?, amount = ?, category = ?, note = ?
           WHERE id = ?""",
        (expense.title, expense.amount, expense.category, expense.note, expense_id)
    )
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense updated"}

@app.get("/expenses/summary")
def summary():
    conn = get_db()
    total = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0
    rows = conn.execute(
        "SELECT category, SUM(amount) as total FROM expenses GROUP BY category"
    ).fetchall()
    conn.close()
    return {"total": round(total, 2), "by_category": {r["category"]: round(r["total"], 2) for r in rows}}