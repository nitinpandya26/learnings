from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import crud, schemas
from .config import settings
from .db import get_db

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}


@app.get("/accounts", response_model=list[schemas.AccountRead])
def get_accounts(db: Session = Depends(get_db)):
    return crud.list_accounts(db)


@app.post("/accounts", response_model=schemas.AccountRead)
def post_account(payload: schemas.AccountCreate, db: Session = Depends(get_db)):
    return crud.create_account(db, payload)


@app.get("/categories", response_model=list[schemas.CategoryRead])
def get_categories(db: Session = Depends(get_db)):
    return crud.list_categories(db)


@app.post("/categories", response_model=schemas.CategoryRead)
def post_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(db, payload)


@app.get("/transactions", response_model=list[schemas.TransactionRead])
def get_transactions(db: Session = Depends(get_db)):
    return crud.list_transactions(db)


@app.post("/transactions", response_model=schemas.TransactionRead)
def post_transaction(payload: schemas.TransactionCreate, db: Session = Depends(get_db)):
    return crud.create_transaction(db, payload)


@app.get("/assets", response_model=list[schemas.AssetRead])
def get_assets(db: Session = Depends(get_db)):
    return crud.list_assets(db)


@app.post("/assets", response_model=schemas.AssetRead)
def post_asset(payload: schemas.AssetCreate, db: Session = Depends(get_db)):
    return crud.create_asset(db, payload)


@app.get("/dashboard/kpis", response_model=schemas.DashboardKPI)
def dashboard_kpis(db: Session = Depends(get_db)):
    return crud.compute_kpi(db)


@app.post("/imports/ledger")
def import_ledger(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return crud.import_ledger(db, file.file.read(), file.filename)
