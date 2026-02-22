from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from db import init_db, seed_defaults
from services import (
    add_account,
    add_asset,
    add_category,
    add_subcategory,
    add_transaction,
    compute_kpis,
    expense_forecast,
    export_excel,
    get_dashboard_dataset,
    import_excel,
    period_change,
    query_df,
)


def render_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #0f172a 0%, #111827 35%, #0b1220 100%);
            color: #e5e7eb;
        }
        [data-testid="stHeader"] { background: rgba(17, 24, 39, 0.7); }
        .hero-title { font-size: 2rem; font-weight: 700; margin-bottom: 0; color: #f8fafc; }
        .hero-subtitle { color: #94a3b8; margin-top: 4px; margin-bottom: 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### 📥 Data Hub")
        uploaded = st.file_uploader(
            "Import data from Excel",
            type=["xlsx"],
            help="Supports app export workbook and your custom ledger format columns.",
        )
        if uploaded and st.button("Run import", use_container_width=True):
            inserted, issues = import_excel(uploaded)
            st.success(f"Imported records: {inserted}")
            if issues:
                st.warning("Some rows could not be loaded.")
                st.code("\n".join(issues[:20]))

        st.download_button(
            label="Export all data to Excel",
            data=export_excel(),
            file_name="expense_manager_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def render_transactions_tab(accounts: pd.DataFrame, categories: pd.DataFrame, subcategories: pd.DataFrame) -> None:
    st.markdown("#### Add Income / Expense")
    with st.form("txn_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            txn_date = st.date_input("Date")
            txn_type = st.selectbox("Type", ["income", "expense"])
            amount = st.number_input("Amount", min_value=0.0, step=100.0)

        with c2:
            account_labels = [f"{r['name']} ({r['account_type']})" for _, r in accounts.iterrows()]
            account_label = st.selectbox("Account", options=account_labels)
            payment_mode = st.selectbox(
                "Payment mode",
                ["cash", "bank_transfer", "credit_card", "upi", "cheque", "debit_card"],
            )
            counterparty = st.text_input("Counterparty")

        with c3:
            filtered_categories = categories[categories["category_type"] == txn_type]
            cat_map = {r["name"]: int(r["id"]) for _, r in filtered_categories.iterrows()}
            category_name = st.selectbox("Category", options=list(cat_map.keys())) if cat_map else None
            sub_df = subcategories[subcategories["category_id"] == cat_map.get(category_name, -1)]
            sub_map = {r["name"]: int(r["id"]) for _, r in sub_df.iterrows()}
            sub_name = st.selectbox("Subcategory", options=["None"] + list(sub_map.keys())) if category_name else "None"

        with c4:
            creates_asset = st.checkbox("Expense creates asset")
            asset_class = st.selectbox(
                "Asset class",
                ["Mutual Funds", "Gold", "Computer", "Fixed Deposits", "Provident Fund", "Other"],
                disabled=not creates_asset,
            )
            notes = st.text_area("Notes")

        if st.form_submit_button("Save transaction", use_container_width=True) and category_name and account_label:
            account_map = {f"{r['name']} ({r['account_type']})": int(r["id"]) for _, r in accounts.iterrows()}
            payload = {
                "txn_date": str(txn_date),
                "txn_type": txn_type,
                "account_id": account_map[account_label],
                "category_id": cat_map[category_name],
                "subcategory_id": None if sub_name == "None" else sub_map[sub_name],
                "amount": float(amount),
                "payment_mode": payment_mode,
                "creates_asset": creates_asset,
                "asset_class": asset_class if creates_asset else None,
                "counterparty": counterparty,
                "notes": notes,
            }
            txn_id = add_transaction(payload)
            if creates_asset:
                add_asset(
                    asset_name=f"{asset_class} - {category_name}",
                    asset_class=asset_class,
                    acquisition_date=str(txn_date),
                    acquisition_value=float(amount),
                    linked_txn_id=txn_id,
                    notes=notes,
                )
            st.success("Transaction saved")
            st.rerun()


def render_setup_tab(categories: pd.DataFrame) -> None:
    st.markdown("#### Master data setup")
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.form("add_account", clear_on_submit=True):
            st.markdown("##### Add account")
            name = st.text_input("Account name")
            account_type = st.selectbox("Account type", ["cash", "bank", "credit_card"])
            opening_balance = st.number_input("Opening balance", value=0.0, step=100.0)
            if st.form_submit_button("Save account", use_container_width=True) and name:
                add_account(name, account_type, opening_balance)
                st.success("Account saved")
                st.rerun()

    with col2:
        with st.form("add_category", clear_on_submit=True):
            st.markdown("##### Add category")
            cname = st.text_input("Category name")
            ctype = st.selectbox("Category type", ["income", "expense", "asset"])
            if st.form_submit_button("Save category", use_container_width=True) and cname:
                add_category(cname, ctype)
                st.success("Category saved")
                st.rerun()

    with col3:
        with st.form("add_subcategory", clear_on_submit=True):
            st.markdown("##### Add subcategory")
            cat_options = {f"{r['name']} ({r['category_type']})": int(r["id"]) for _, r in categories.iterrows()}
            if cat_options:
                cat_label = st.selectbox("Category", list(cat_options.keys()))
                sname = st.text_input("Subcategory name")
                if st.form_submit_button("Save subcategory", use_container_width=True) and sname:
                    add_subcategory(cat_options[cat_label], sname)
                    st.success("Subcategory saved")
                    st.rerun()
            else:
                st.info("Create categories first")


def render_insights_tab(df: pd.DataFrame) -> None:
    st.markdown("#### Spending intelligence")
    if df.empty:
        st.info("Add or import transactions to unlock analytics.")
        return

    d = df.copy()
    d["txn_date"] = pd.to_datetime(d["txn_date"])

    c1, c2 = st.columns(2)
    with c1:
        exp_cat = d[d["txn_type"] == "expense"].groupby("category_name", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        st.plotly_chart(px.pie(exp_cat, names="category_name", values="amount", hole=0.45, title="Expense Mix by Category"), use_container_width=True)
    with c2:
        account_flow = d.groupby(["account_name", "txn_type"], as_index=False)["amount"].sum()
        st.plotly_chart(px.bar(account_flow, x="account_name", y="amount", color="txn_type", barmode="group", title="Income vs Expense by Account"), use_container_width=True)

    freq = st.selectbox(
        "Period comparison",
        ["W", "M", "Y"],
        format_func=lambda x: {"W": "Week over Week", "M": "Month over Month", "Y": "Year over Year"}[x],
    )
    trend = period_change(d, freq)
    if not trend.empty:
        st.plotly_chart(px.line(trend, x="period", y=["income", "expense", "net"], markers=True, title="Trend: Income vs Expense vs Net"), use_container_width=True)
        st.dataframe(trend.round(2), use_container_width=True)

    forecast = expense_forecast(d, periods=6)
    if not forecast.empty:
        st.plotly_chart(px.area(forecast, x="period", y="forecast_expense", title="Projected Monthly Expense"), use_container_width=True)

    st.markdown("#### Ledger")
    st.dataframe(d.sort_values("txn_date", ascending=False), use_container_width=True)


def render_assets_tab() -> None:
    st.markdown("#### Asset register")
    assets = query_df("SELECT * FROM assets ORDER BY acquisition_date DESC")
    if assets.empty:
        st.info("No assets added yet.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.treemap(assets, path=["asset_class", "asset_name"], values="acquisition_value", title="Asset Allocation"), use_container_width=True)
        with c2:
            by_class = assets.groupby("asset_class", as_index=False)["acquisition_value"].sum()
            st.plotly_chart(px.bar(by_class, x="asset_class", y="acquisition_value", title="Asset Value by Class"), use_container_width=True)
        st.dataframe(assets, use_container_width=True)

    with st.form("manual_asset", clear_on_submit=True):
        st.markdown("##### Add asset manually")
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            asset_name = st.text_input("Asset name")
        with a2:
            asset_class = st.selectbox("Asset class", ["Mutual Funds", "Gold", "Computer", "Fixed Deposits", "Provident Fund", "Other"])
        with a3:
            acq_date = st.date_input("Acquisition date")
        with a4:
            acq_value = st.number_input("Acquisition value", min_value=0.0, step=500.0)
        asset_notes = st.text_area("Notes")
        if st.form_submit_button("Save asset", use_container_width=True) and asset_name:
            add_asset(asset_name, asset_class, str(acq_date), float(acq_value), None, asset_notes)
            st.success("Asset saved")
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="Expense Manager Pro", page_icon="💎", layout="wide")
    init_db()
    seed_defaults()

    render_theme()
    st.markdown('<p class="hero-title">💎 Expense Manager Pro</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Track income, expenses, cards, accounts, and assets with modern analytics.</p>', unsafe_allow_html=True)

    render_sidebar()

    accounts = query_df("SELECT id, name, account_type FROM accounts ORDER BY name")
    categories = query_df("SELECT id, name, category_type FROM categories ORDER BY category_type, name")
    subcategories = query_df(
        """
        SELECT s.id, s.name, s.category_id, c.name AS category_name, c.category_type
        FROM subcategories s JOIN categories c ON c.id = s.category_id
        ORDER BY c.name, s.name
        """
    )
    df = get_dashboard_dataset()
    kpis = compute_kpis(df)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Income", f"₹{kpis['income']:,.0f}")
    k2.metric("Total Expense", f"₹{kpis['expense']:,.0f}")
    k3.metric("Net Savings", f"₹{kpis['net']:,.0f}")
    k4.metric("Savings Rate", f"{kpis['savings_rate']:.1f}%")

    entry_tab, master_tab, dashboard_tab, assets_tab = st.tabs(["➕ Transactions", "⚙️ Setup", "📊 Insights", "🏦 Assets"])
    with entry_tab:
        render_transactions_tab(accounts, categories, subcategories)
    with master_tab:
        render_setup_tab(categories)
    with dashboard_tab:
        render_insights_tab(df)
    with assets_tab:
        render_assets_tab()


if __name__ == "__main__":
    main()
