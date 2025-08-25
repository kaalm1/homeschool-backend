# Homeschool Backend (FastAPI)

- Auth: JWT (demo user auto-seeded)
- DB: SQLite (upgrade to Postgres later)
- CORS: allows http://localhost:5173

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn svc.app.main:app --reload
