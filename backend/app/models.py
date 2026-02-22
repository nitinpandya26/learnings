from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    account_type: Mapped[str] = mapped_column(String(30))
    opening_balance: Mapped[float] = mapped_column(Float, default=0)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category_type: Mapped[str] = mapped_column(String(20))


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    txn_date: Mapped[datetime] = mapped_column(DateTime)
    txn_type: Mapped[str] = mapped_column(String(20))
    amount: Mapped[float] = mapped_column(Float)
    payment_mode: Mapped[str] = mapped_column(String(40))
    notes: Mapped[str | None] = mapped_column(Text)
    creates_asset: Mapped[bool] = mapped_column(Boolean, default=False)
    asset_class: Mapped[str | None] = mapped_column(String(80))
    counterparty: Mapped[str | None] = mapped_column(String(120))

    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    account: Mapped[Account] = relationship()
    category: Mapped[Category] = relationship()


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_name: Mapped[str] = mapped_column(String(120))
    asset_class: Mapped[str] = mapped_column(String(80))
    acquisition_date: Mapped[Date] = mapped_column(Date)
    acquisition_value: Mapped[float] = mapped_column(Float)
    linked_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"))
    notes: Mapped[str | None] = mapped_column(Text)


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    inserted_rows: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(40), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
