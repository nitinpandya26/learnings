from datetime import datetime
from io import BytesIO

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas


def create_account(db: Session, payload: schemas.AccountCreate) -> models.Account:
    entity = models.Account(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def list_accounts(db: Session) -> list[models.Account]:
    return list(db.scalars(select(models.Account).order_by(models.Account.name)))


def create_category(db: Session, payload: schemas.CategoryCreate) -> models.Category:
    entity = models.Category(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def list_categories(db: Session) -> list[models.Category]:
    return list(db.scalars(select(models.Category).order_by(models.Category.name)))


def create_transaction(db: Session, payload: schemas.TransactionCreate) -> models.Transaction:
    account = db.get(models.Account, payload.account_id)
    category = db.get(models.Category, payload.category_id)
    if not account or not category:
        raise HTTPException(status_code=400, detail="Invalid account/category")

    entity = models.Transaction(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)

    if entity.creates_asset and entity.asset_class:
        asset = models.Asset(
            asset_name=f"{entity.asset_class} - {category.name}",
            asset_class=entity.asset_class,
            acquisition_date=entity.txn_date.date(),
            acquisition_value=entity.amount,
            linked_transaction_id=entity.id,
            notes=entity.notes,
        )
        db.add(asset)
        db.commit()
    return entity


def list_transactions(db: Session) -> list[models.Transaction]:
    return list(db.scalars(select(models.Transaction).order_by(models.Transaction.txn_date.desc())))


def list_assets(db: Session) -> list[models.Asset]:
    return list(db.scalars(select(models.Asset).order_by(models.Asset.acquisition_date.desc())))


def create_asset(db: Session, payload: schemas.AssetCreate) -> models.Asset:
    entity = models.Asset(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def compute_kpi(db: Session) -> schemas.DashboardKPI:
    txns = list_transactions(db)
    income = sum(t.amount for t in txns if t.txn_type == "income")
    expense = sum(t.amount for t in txns if t.txn_type == "expense")
    net = income - expense
    rate = (net / income * 100) if income else 0
    return schemas.DashboardKPI(income=income, expense=expense, net=net, savings_rate=rate)


def import_ledger(db: Session, file_bytes: bytes, filename: str) -> dict:
    frame = pd.read_excel(BytesIO(file_bytes))
    normalized = frame.rename(columns={c: c.strip().lower() for c in frame.columns})
    required = {"account", "category", "amount", "type", "payment_type", "date"}
    missing = required - set(normalized.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {sorted(missing)}")

    inserted = 0
    for _, row in normalized.iterrows():
        account_name = str(row.get("account", "Unknown")).strip() or "Unknown"
        acct = db.scalar(select(models.Account).where(models.Account.name == account_name))
        if not acct:
            acct = models.Account(name=account_name, account_type="bank", opening_balance=0)
            db.add(acct)
            db.flush()

        txn_type = "income" if str(row.get("type", "")).lower().startswith("inc") else "expense"
        category_name = str(row.get("category", "Uncategorized")).strip() or "Uncategorized"
        cat = db.scalar(
            select(models.Category).where(
                models.Category.name == category_name,
                models.Category.category_type == txn_type,
            )
        )
        if not cat:
            cat = models.Category(name=category_name, category_type=txn_type)
            db.add(cat)
            db.flush()

        txn = models.Transaction(
            txn_date=pd.to_datetime(row.get("date", datetime.utcnow())),
            txn_type=txn_type,
            amount=abs(float(row.get("amount", 0) or 0)),
            payment_mode=str(row.get("payment_type", "other")).lower(),
            account_id=acct.id,
            category_id=cat.id,
            notes=str(row.get("note", "")),
            counterparty=str(row.get("payee", "")),
        )
        db.add(txn)
        inserted += 1

    db.add(models.ImportJob(filename=filename, inserted_rows=inserted, status="completed"))
    db.commit()
    return {"inserted": inserted}
