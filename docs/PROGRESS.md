# Project Progress: OpportunityAbroad

## Phase Overview

| Phase | Description | Status |
|---|---|---|
| Phase 0 | Foundations (Monorepo, Docker Compose, Postgres+pgvector, Redis, Mailpit, FastAPI Health, Tooling, CI) | in progress |
| Phase 1 | Auth & Roles (Argon2id, JWT + rotating refresh cookie, RBAC, Student & Admin contexts) | todo |
| Phase 2 | Opportunities & Admin CRUD (Models, Keyset pagination, Filters, Audit logs, Browse & Admin UI) | todo |
| Phase 3 | Ingestion (Worker, RSS/JSON/HTML fetchers, Normalizer, Deduplication, Ingestion runs) | todo |
| Phase 4 | AI Search (LLMProvider, Embeddings, Hybrid retrieval, Rerank, Redis cache, Fallback, UI) | todo |
| Phase 5 | Student Dashboard (Saved, Applications, Notes, Deadline reminders, Data export/delete) | todo |
| Phase 6 | Admin Dashboard (User management, Analytics, Broadcasts, Audit log viewer) | todo |
| Phase 7 | Hardening & Launch (Security headers, Rate limits, i18n RTL, k6 load test, K8s, Runbooks) | todo |

## Last Completed
- Initial repository setup and project memory documents (`AGENTS.md`, `CLAUDE.md`, `docs/PHASES.md`, `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/BLUEPRINT.md`).

## How to Run
- Run with Docker Compose:
  ```bash
  docker compose up --build
  ```
- Run API locally:
  ```bash
  cd apps/api
  python -m venv .venv
  .venv\Scripts\activate
  pip install -r requirements.txt
  uvicorn app.main:app --reload --port 8000
  ```
- Run Web locally:
  ```bash
  cd apps/web
  npm install
  npm run dev
  ```

## How to Test
- Backend tests:
  ```bash
  cd apps/api
  pytest
  ```
- Frontend tests:
  ```bash
  cd apps/web
  npm run test
  ```
- Linting and type-checking:
  ```bash
  # API
  cd apps/api && ruff check . && mypy app
  # Web
  cd apps/web && npm run lint && npm run typecheck
  ```

## Known Gaps
- Currently initializing Phase 0 foundation files, dependencies, and environment setup.

## Next Step
- Complete Phase 0 implementation: setup apps/api, apps/web, packages/shared, Docker Compose, Alembic, health endpoints, tests, and CI workflows.

