# Expense Manager 2.0 (Radical Redesign)

This repository is now rebuilt as a modern full-stack app:

- **Frontend**: Next.js 14 + Tailwind + shadcn-style UI + TanStack Table + Recharts
- **Backend**: FastAPI + SQLAlchemy 2 + Alembic
- **Database**: PostgreSQL
- **Optional**: Redis (add only when profiling shows bottlenecks)

---

## Project structure

- `backend/` FastAPI service, models, Alembic migrations
- `frontend/` Next.js app with dashboard, table, and chart components
- `docker-compose.yml` local PostgreSQL

---

## Detailed VS Code testing guide

## 1) Prerequisites

Install these first:

- VS Code
- Python 3.11+
- Node.js 20+
- Docker Desktop (recommended for PostgreSQL)

Install VS Code extensions:

- Python
- Pylance
- ESLint
- Tailwind CSS IntelliSense

---

## 2) Open workspace

1. Open VS Code.
2. `File -> Open Folder` and select this repo folder.
3. Open terminal (`Ctrl+``).

---

## 3) Start PostgreSQL

From repo root:

```bash
docker compose up -d postgres
```

Verify DB is running:

```bash
docker ps
```

---

## 4) Backend setup (FastAPI)

```bash
cd backend
python -m venv .venv
```

Activate env:

- **macOS/Linux**
  ```bash
  source .venv/bin/activate
  ```
- **Windows PowerShell**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

Install packages:

```bash
pip install -r requirements.txt
```

Create `.env` from example:

```bash
cp .env.example .env
```

Run migrations:

```bash
alembic upgrade head
```

Start API:

```bash
uvicorn app.main:app --reload --port 8000
```

Test API in browser:

- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

---

## 5) Frontend setup (Next.js)

In a **new terminal**:

```bash
cd frontend
npm install
```

Set API base URL:

```bash
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local
```

Run frontend:

```bash
npm run dev
```

Open `http://localhost:3000`.

---

## 6) Functional test checklist in VS Code

1. Open `http://localhost:8000/docs`
2. Create 1 account via `POST /accounts`
3. Create 1 category via `POST /categories`
4. Add 2 transactions via `POST /transactions` (one income, one expense)
5. Call `GET /dashboard/kpis` and verify totals
6. Refresh `http://localhost:3000`
7. Verify:
   - KPI cards render
   - Recharts bar chart shows Income/Expense
   - TanStack table displays transactions

---

## 7) Ledger import test (your Excel format)

Use endpoint `POST /imports/ledger` from Swagger:

- Upload your xlsx with columns such as:
  - `account`, `category`, `amount`, `type`, `payment_type`, `date`
  - Optional: `note`, `payee`, etc.

Expected behavior:

- Missing accounts/categories are auto-created.
- Expense and income rows are inserted into `transactions`.
- Import summary returns inserted row count.

---

## 8) Common troubleshooting

- **`alembic: command not found`**
  - Ensure backend `.venv` is active.

- **DB connection refused**
  - Check Docker PostgreSQL container is running.

- **Frontend cannot reach API**
  - Verify `.env.local` has `NEXT_PUBLIC_API_BASE=http://localhost:8000`
  - Restart `npm run dev`.

- **CORS issue**
  - Update `EXPENSE_CORS_ORIGINS` in backend `.env`.

---

## 9) Useful dev commands

Backend:

```bash
python -m py_compile app/main.py app/models.py app/crud.py app/schemas.py
```

Frontend:

```bash
npm run build
```

Stop DB:

```bash
docker compose down
```

