from __future__ import annotations

import sqlite3
from io import BytesIO

import numpy as np
import pandas as pd

from db import get_conn

TABLES = ["accounts", "categories", "subcategories", "transactions", "assets"]
LEDGER_REQUIRED_COLUMNS = {
    "account",
    "category",
    "amount",
    "type",
    "payment_type",
    "note",
    "date",
}


ASSET_CLASS_KEYWORDS = {
    "mutual": "Mutual Funds",
    "gold": "Gold",
    "computer": "Computer",
    "laptop": "Computer",
    "fixed deposit": "Fixed Deposits",
    "fd": "Fixed Deposits",
    "provident": "Provident Fund",
    "pf": "Provident Fund",
}


def query_df(query: str, params: tuple = ()) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(query, conn, params=params)


def add_category(name: str, category_type: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO categories(name, category_type, is_system) VALUES(?,?,0)",
            (name.strip(), category_type),
        )


def add_subcategory(category_id: int, name: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subcategories(category_id, name) VALUES(?,?)",
            (category_id, name.strip()),
        )


def add_account(name: str, account_type: str, opening_balance: float) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO accounts(name, account_type, opening_balance) VALUES(?,?,?)",
            (name.strip(), account_type, opening_balance),
        )


def add_transaction(payload: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO transactions(
                txn_date, txn_type, account_id, category_id, subcategory_id,
                amount, payment_mode, creates_asset, asset_class, counterparty, notes
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                payload["txn_date"],
                payload["txn_type"],
                payload["account_id"],
                payload["category_id"],
                payload.get("subcategory_id"),
                payload["amount"],
                payload["payment_mode"],
                1 if payload.get("creates_asset") else 0,
                payload.get("asset_class"),
                payload.get("counterparty"),
                payload.get("notes"),
            ),
        )
        return int(cur.lastrowid)


def add_asset(
    asset_name: str,
    asset_class: str,
    acquisition_date: str,
    acquisition_value: float,
    linked_txn_id: int | None,
    notes: str = "",
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO assets(asset_name, asset_class, acquisition_date, acquisition_value, linked_transaction_id, notes)
            VALUES(?,?,?,?,?,?)
            """,
            (asset_name, asset_class, acquisition_date, acquisition_value, linked_txn_id, notes),
        )


def get_dashboard_dataset() -> pd.DataFrame:
    return query_df(
        """
        SELECT t.*, a.name AS account_name, a.account_type,
               c.name AS category_name, c.category_type,
               s.name AS subcategory_name
        FROM transactions t
        JOIN accounts a ON a.id = t.account_id
        JOIN categories c ON c.id = t.category_id
        LEFT JOIN subcategories s ON s.id = t.subcategory_id
        ORDER BY txn_date DESC
        """
    )


def compute_kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"income": 0.0, "expense": 0.0, "net": 0.0, "savings_rate": 0.0}
    income = df.loc[df["txn_type"] == "income", "amount"].sum()
    expense = df.loc[df["txn_type"] == "expense", "amount"].sum()
    net = income - expense
    savings_rate = (net / income * 100) if income else 0.0
    return {
        "income": float(income),
        "expense": float(expense),
        "net": float(net),
        "savings_rate": float(savings_rate),
    }


def period_change(df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=["period", "income", "expense", "net", "expense_change_pct"]
        )
    d = df.copy()
    d["txn_date"] = pd.to_datetime(d["txn_date"])
    d["period"] = d["txn_date"].dt.to_period(freq).dt.to_timestamp()

    grouped = (
        d.pivot_table(
            index="period", columns="txn_type", values="amount", aggfunc="sum", fill_value=0
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    grouped["net"] = grouped.get("income", 0) - grouped.get("expense", 0)
    grouped["expense_change_pct"] = grouped.get("expense", 0).pct_change() * 100
    return grouped


def expense_forecast(df: pd.DataFrame, periods: int = 3) -> pd.DataFrame:
    ts = period_change(df, freq="M")
    if ts.empty or len(ts) < 2:
        return pd.DataFrame(columns=["period", "forecast_expense"])

    y = ts["expense"].to_numpy(dtype=float)
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    future_x = np.arange(len(y), len(y) + periods)
    future_y = slope * future_x + intercept
    last_period = pd.Period(ts["period"].max(), freq="M")
    future_periods = [(last_period + i).to_timestamp() for i in range(1, periods + 1)]
    return pd.DataFrame(
        {"period": future_periods, "forecast_expense": np.maximum(future_y, 0)}
    )


def export_excel() -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for table in TABLES:
            df = query_df(f"SELECT * FROM {table}")
            df.to_excel(writer, sheet_name=table, index=False)
    output.seek(0)
    return output.read()


def _infer_account_type(name: str) -> str:
    lname = name.lower()
    if "cc" in lname or "credit" in lname or "card" in lname:
        return "credit_card"
    if "cash" in lname:
        return "cash"
    return "bank"


def _infer_asset_class(*values: str) -> str | None:
    text = " ".join(v.lower() for v in values if v)
    for key, asset_class in ASSET_CLASS_KEYWORDS.items():
        if key in text:
            return asset_class
    return None


def _import_table_format(xls: dict[str, pd.DataFrame]) -> tuple[int, list[str]]:
    inserted = 0
    issues: list[str] = []
    with get_conn() as conn:
        for table in TABLES:
            if table not in xls:
                continue
            frame = xls[table]
            cols = frame.columns.tolist()
            if "id" in cols:
                frame = frame.drop(columns=["id"])
                cols = frame.columns.tolist()
            if frame.empty:
                continue
            placeholders = ",".join(["?"] * len(cols))
            col_clause = ",".join(cols)
            for _, row in frame.iterrows():
                values = [None if pd.isna(v) else v for v in row.tolist()]
                try:
                    conn.execute(
                        f"INSERT INTO {table}({col_clause}) VALUES({placeholders})", values
                    )
                    inserted += 1
                except sqlite3.IntegrityError as err:
                    issues.append(f"{table}: {err}")
    return inserted, issues


def _import_ledger_format(frame: pd.DataFrame) -> tuple[int, list[str]]:
    inserted = 0
    issues: list[str] = []

    normalized = frame.rename(columns={c: c.strip().lower() for c in frame.columns})
    missing = LEDGER_REQUIRED_COLUMNS - set(normalized.columns)
    if missing:
        return 0, [f"Ledger import missing columns: {', '.join(sorted(missing))}"]

    with get_conn() as conn:
        for _, row in normalized.iterrows():
            try:
                account_name = str(row.get("account", "Unknown")).strip()
                if not account_name:
                    account_name = "Unknown"
                account_type = _infer_account_type(account_name)
                conn.execute(
                    "INSERT OR IGNORE INTO accounts(name, account_type, opening_balance) VALUES(?,?,0)",
                    (account_name, account_type),
                )
                account_id = conn.execute(
                    "SELECT id FROM accounts WHERE name=?", (account_name,)
                ).fetchone()["id"]

                raw_type = str(row.get("type", "Expenses")).strip().lower()
                txn_type = "income" if raw_type.startswith("inc") else "expense"

                category_name = str(row.get("category", "Uncategorized")).strip() or "Uncategorized"
                conn.execute(
                    "INSERT OR IGNORE INTO categories(name, category_type, is_system) VALUES(?,?,0)",
                    (category_name, txn_type),
                )
                category_id = conn.execute(
                    "SELECT id FROM categories WHERE name=? AND category_type=?",
                    (category_name, txn_type),
                ).fetchone()["id"]

                labels = str(row.get("labels", "")).strip()
                subcategory_name = labels if labels and labels.lower() != "nan" else "General"
                conn.execute(
                    "INSERT OR IGNORE INTO subcategories(category_id, name) VALUES(?,?)",
                    (category_id, subcategory_name),
                )
                subcategory_id = conn.execute(
                    "SELECT id FROM subcategories WHERE category_id=? AND name=?",
                    (category_id, subcategory_name),
                ).fetchone()["id"]

                amount = float(row.get("amount", 0) or 0)
                amount = abs(amount)

                note = str(row.get("note", "")).strip()
                payee = str(row.get("payee", "")).strip()
                payment_mode = str(row.get("payment_type", "other")).strip().lower() or "other"
                txn_date = pd.to_datetime(row.get("date")).strftime("%Y-%m-%d")

                inferred_asset = _infer_asset_class(category_name, note, labels, payee)
                creates_asset = bool(inferred_asset) and txn_type == "expense"

                cur = conn.execute(
                    """
                    INSERT INTO transactions(
                        txn_date, txn_type, account_id, category_id, subcategory_id,
                        amount, payment_mode, creates_asset, asset_class, counterparty, notes
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        txn_date,
                        txn_type,
                        account_id,
                        category_id,
                        subcategory_id,
                        amount,
                        payment_mode,
                        1 if creates_asset else 0,
                        inferred_asset,
                        payee,
                        note,
                    ),
                )
                inserted += 1

                if creates_asset and inferred_asset:
                    conn.execute(
                        """
                        INSERT INTO assets(asset_name, asset_class, acquisition_date, acquisition_value, linked_transaction_id, notes)
                        VALUES(?,?,?,?,?,?)
                        """,
                        (
                            f"{inferred_asset} - {category_name}",
                            inferred_asset,
                            txn_date,
                            amount,
                            int(cur.lastrowid),
                            note,
                        ),
                    )
                    inserted += 1
            except Exception as err:  # noqa: BLE001
                issues.append(f"Row import failed: {err}")
    return inserted, issues


def import_excel(uploaded) -> tuple[int, list[str]]:
    xls = pd.read_excel(uploaded, sheet_name=None)
    sheet_names = list(xls.keys())
    if any(name in TABLES for name in sheet_names):
        return _import_table_format(xls)

    first_sheet = xls[sheet_names[0]] if sheet_names else pd.DataFrame()
    return _import_ledger_format(first_sheet)
