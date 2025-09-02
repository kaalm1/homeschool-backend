# Homeschool Backend (FastAPI)

- Auth: JWT (demo user auto-seeded)
- DB: SQLite (upgrade to Postgres later)
- CORS: allows http://localhost:5173

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn svc.app.main:app --reload --log-level debug     
````

## Migration
```bash
export DATABASE_URL=postgresql://postgres@localhost/homeschool_db
alembic upgrade head
alembic revision --autogenerate -m "initial migration" 
```

## Database
````bash
psql -U postgres -d homeschool_db
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO homeschool_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO homeschool_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO homeschool_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO homeschool_user;

psql
DROP DATABASE homeschool_db;
CREATE DATABASE homeschool_db;