import sqlite3
import logging
from datetime import date
from flask import Flask, render_template, request, redirect, flash, url_for

app = Flask(__name__)
app.secret_key = "expense-tracker-secret-key"

logging.basicConfig(level=logging.INFO)

DATABASE = "expenses.db"

def init_db():
    with sqlite3.connect(DATABASE) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                kind TEXT NOT NULL,
                category TEXT NOT NULL,
                transaction_date TEXT NOT NULL
            )
        """)

@app.template_filter("money")
def money(value):
    return f"₹{float(value or 0):,.2f}"

@app.route("/")
def index():
    with sqlite3.connect(DATABASE) as con:
        con.row_factory = sqlite3.Row

        transactions = con.execute(
            "SELECT * FROM transactions ORDER BY id DESC"
        ).fetchall()

        income = con.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE kind='Income'"
        ).fetchone()[0]

        expenses = con.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE kind='Expense'"
        ).fetchone()[0]

        categories = con.execute("""
            SELECT category, SUM(amount) AS total
            FROM transactions
            WHERE kind='Expense'
            GROUP BY category
            ORDER BY total DESC
        """).fetchall()

    return render_template(
        "index.html",
        transactions=transactions,
        income=income,
        expenses=expenses,
        balance=income - expenses,
        categories=categories,
        today=date.today().isoformat(),
        category_options=[
            "Food", "Transport", "Education", "Shopping",
            "Bills", "Health", "Salary", "Other"
        ]
    )

@app.route("/add", methods=["POST"])
def add_transaction():
    title = request.form.get("title", "").strip()
    kind = request.form.get("kind", "")
    category = request.form.get("category", "")
    transaction_date = request.form.get("transaction_date", "")

    try:
        amount = float(request.form.get("amount", "0"))

        if not title or len(title) > 100:
            raise ValueError

        if amount <= 0 or amount > 999999999:
            raise ValueError

        if kind not in ["Income", "Expense"]:
            raise ValueError

        if category not in [
            "Food", "Transport", "Education", "Shopping",
            "Bills", "Health", "Salary", "Other"
        ]:
            raise ValueError

        date.fromisoformat(transaction_date)

    except (ValueError, TypeError):
        flash("Please enter valid transaction details.", "error")
        return redirect(url_for("index"))

    try:
        with sqlite3.connect(DATABASE) as con:
            con.execute("""
                INSERT INTO transactions
                (title, amount, kind, category, transaction_date)
                VALUES (?, ?, ?, ?, ?)
            """, (title, amount, kind, category, transaction_date))

        flash("Transaction added successfully!", "success")

    except sqlite3.Error:
        logging.exception("Unable to save transaction")
        flash("Unable to save transaction.", "error")

    return redirect(url_for("index"))

@app.route("/delete/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):
    with sqlite3.connect(DATABASE) as con:
        con.execute(
            "DELETE FROM transactions WHERE id = ?",
            (transaction_id,)
        )

    flash("Transaction deleted.", "success")
    return redirect(url_for("index"))

init_db()

if __name__ == "__main__":
    app.run(debug=False)