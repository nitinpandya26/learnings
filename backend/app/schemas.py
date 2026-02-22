from datetime import date, datetime

from pydantic import BaseModel


class AccountCreate(BaseModel):
    name: str
    account_type: str
    opening_balance: float = 0


class AccountRead(AccountCreate):
    id: int

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    category_type: str


class CategoryRead(CategoryCreate):
    id: int

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    txn_date: datetime
    txn_type: str
    amount: float
    payment_mode: str
    account_id: int
    category_id: int
    notes: str | None = None
    creates_asset: bool = False
    asset_class: str | None = None
    counterparty: str | None = None


class TransactionRead(TransactionCreate):
    id: int

    class Config:
        from_attributes = True


class DashboardKPI(BaseModel):
    income: float
    expense: float
    net: float
    savings_rate: float


class AssetCreate(BaseModel):
    asset_name: str
    asset_class: str
    acquisition_date: date
    acquisition_value: float
    linked_transaction_id: int | None = None
    notes: str | None = None


class AssetRead(AssetCreate):
    id: int

    class Config:
        from_attributes = True
