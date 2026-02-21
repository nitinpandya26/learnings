import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path("expense_manager.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                account_type TEXT NOT NULL CHECK(account_type IN ('cash','bank','credit_card')),
                opening_balance REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_type TEXT NOT NULL CHECK(category_type IN ('income','expense','asset')),
                is_system INTEGER NOT NULL DEFAULT 0,
                UNIQUE(name, category_type)
            );

            CREATE TABLE IF NOT EXISTS subcategories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                UNIQUE(category_id, name),
                FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                txn_date TEXT NOT NULL,
                txn_type TEXT NOT NULL CHECK(txn_type IN ('income','expense')),
                account_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                subcategory_id INTEGER,
                amount REAL NOT NULL CHECK(amount >= 0),
                payment_mode TEXT NOT NULL,
                creates_asset INTEGER NOT NULL DEFAULT 0,
                asset_class TEXT,
                counterparty TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE RESTRICT,
                FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE RESTRICT,
                FOREIGN KEY(subcategory_id) REFERENCES subcategories(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_name TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                acquisition_date TEXT NOT NULL,
                acquisition_value REAL NOT NULL CHECK(acquisition_value >= 0),
                linked_transaction_id INTEGER,
                notes TEXT,
                FOREIGN KEY(linked_transaction_id) REFERENCES transactions(id) ON DELETE SET NULL
            );
            """
        )


def seed_defaults() -> None:
    with get_conn() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO accounts(name, account_type, opening_balance) VALUES(?,?,?)",
            [
                ("Cash Wallet", "cash", 0),
                ("Primary Bank", "bank", 0),
                ("Main Credit Card", "credit_card", 0),
            ],
        )

        defaults = {
            "income": [
                ("Salary", ["Base Salary", "Bonus", "Overtime"]),
                ("Business", ["Consulting", "Sales"]),
                ("Investments", ["Dividends", "Interest", "Capital Gains"]),
                ("Other Income", ["Gift", "Refund", "Reimbursement"]),
            ],
            "expense": [
                ("Housing", ["Rent", "Maintenance", "Utilities"]),
                ("Transportation", ["Fuel", "Public Transport", "Cab"]),
                ("Food", ["Groceries", "Dining Out", "Coffee"]),
                ("Healthcare", ["Insurance", "Pharmacy", "Doctor"]),
                ("Education", ["Courses", "Books"]),
                ("Lifestyle", ["Entertainment", "Shopping", "Travel"]),
                ("Financial", ["Loan EMI", "Taxes", "Fees"]),
            ],
            "asset": [
                ("Mutual Funds", ["Equity", "Debt", "Hybrid"]),
                ("Gold", ["Physical", "ETF", "Digital"]),
                ("Computer", ["Laptop", "Desktop", "Accessories"]),
                ("Fixed Deposits", ["Bank FD", "Corporate FD"]),
                ("Provident Fund", ["Personal PF", "Employer PF"]),
            ],
        }

        for ctype, groups in defaults.items():
            for cname, subs in groups:
                conn.execute(
                    "INSERT OR IGNORE INTO categories(name, category_type, is_system) VALUES(?,?,1)",
                    (cname, ctype),
                )
                cid = conn.execute(
                    "SELECT id FROM categories WHERE name=? AND category_type=?", (cname, ctype)
                ).fetchone()["id"]
                conn.executemany(
                    "INSERT OR IGNORE INTO subcategories(category_id, name) VALUES(?,?)",
                    [(cid, s) for s in subs],
                )
