# Expense Manager Pro (Python + Frontend)

A Streamlit-powered personal finance manager with:
- Income and expense tracking across **cash**, **bank**, and **credit cards**.
- Customizable categories and subcategories for both income and expenses.
- Asset creation tracking directly from expenses (Mutual Funds, Gold, Computer, FD, PF, etc.).
- Dashboard analytics (mix, account-wise views, trend lines, MoM/WoW/YoY views, and linear expense projections).
- Excel import and export for full dataset portability.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app creates `expense_manager.db` automatically.

## Excel import/export format

Export generates workbook sheets:
- `accounts`
- `categories`
- `subcategories`
- `transactions`
- `assets`

Import supports the same sheet names. If `id` columns exist they are ignored.
