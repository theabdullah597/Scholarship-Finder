# OpportunityAbroad 🎓🌍

An AI-powered scholarship and internship discovery platform designed for students seeking global academic and professional opportunities abroad.

## Architecture Overview

- **Frontend (`apps/web`)**: React + TypeScript + Tailwind CSS + Vite + `react-i18next`
- **Backend API (`apps/api`)**: FastAPI + Python 3.12 + SQLAlchemy 2 (asyncio) + Alembic + Pydantic v2
- **Worker (`apps/api` worker entrypoint)**: Background task daemon for opportunity ingestion and deadline alerts
- **Database & Services**: PostgreSQL 16 with `pgvector`, Redis 7, Mailpit (SMTP & local web interface)
- **Shared (`packages/shared`)**: Shared types, constants, and contracts

---

## Quickstart with Docker Compose

1. Copy the example environment variables:
   ```bash
   cp .env.example .env
   ```
2. Start all services:
   ```bash
   docker compose up --build
   ```
3. Access the services:
   - **Web Application**: [http://localhost:5173](http://localhost:5173)
   - **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
   - **Mailpit Email UI**: [http://localhost:8025](http://localhost:8025)

---

## Local Development (Without Docker)

### Backend (`apps/api`)
```bash
cd apps/api
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (`apps/web`)
```bash
cd apps/web
npm install
npm run dev
```

---

## Testing & Quality Assurance

```bash
# Run backend tests
cd apps/api && pytest

# Run frontend tests
cd apps/web && npm test

# Linting and Type Checking
cd apps/api && ruff check . && mypy app
cd apps/web && npm run lint && npm run typecheck
```

---

## Project Documentation
- [Phase Roadmap](docs/PHASES.md)
- [Current Progress](docs/PROGRESS.md)
- [Architecture Decision Records](docs/DECISIONS.md)
- [System Blueprint & Schema Specification](docs/BLUEPRINT.md)
- [Agent & Contributor Rules](AGENTS.md)

