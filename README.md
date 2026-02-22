# Expense Manager Pro (Python + Frontend)

Modern Streamlit-based personal finance app for:
- Income and expense tracking across **cash**, **bank**, and **credit cards**.
- Customizable categories and subcategories.
- Asset creation tracking from expenses (Mutual Funds, Gold, Computer, FD, PF, etc.).
- Dashboard analytics (category mix, account flow, WoW/MoM/YoY trends, and projections).
- Excel import and export.

## Run locally (VS Code friendly)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Then open `http://localhost:8501`.

The app creates `expense_manager.db` automatically.

## Supported Excel import formats

### 1) Native app export format
Workbook can include sheets:
- `accounts`
- `categories`
- `subcategories`
- `transactions`
- `assets`

### 2) Custom ledger format (single sheet)
The import now supports your ledger columns, including:
- `account`
- `category`
- `currency`
- `amount`
- `ref_currency_amount`
- `type` (Income / Expenses)
- `payment_type`
- `payment_type_local`
- `note`
- `date`
- `gps_latitude`
- `gps_longitude`
- `gps_accuracy_in_meters`
- `warranty_in_month`
- `transfer`
- `payee`
- `labels`
- `envelope_id`
- `custom_category`

How mapping works:
- `account` -> account name (auto-creates account if missing).
- `type` -> transaction type (`Income` => income, `Expenses` => expense).
- `amount` -> absolute value is stored.
- `category` -> category (auto-creates by transaction type).
- `labels` -> subcategory (falls back to `General`).
- `payment_type` -> payment mode.
- `payee` -> counterparty.
- `note` -> notes.
- `date` -> transaction date.
- Asset-like categories/notes (Mutual, Gold, Computer, FD, PF, etc.) auto-create asset records for expense rows.

## Export

Export generates an Excel workbook with normalized application sheets:
- `accounts`
- `categories`
- `subcategories`
- `transactions`
- `assets`
