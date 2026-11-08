# Project Progress: OpportunityAbroad

## Phase Overview

| Phase | Description | Status |
|---|---|---|
| Phase 0 | Foundations (Monorepo, Docker Compose, Postgres+pgvector, Redis, Mailpit, FastAPI Health, Tooling, CI) | done |
| Phase 1 | Auth & Roles (Argon2id, JWT + rotating refresh cookie, RBAC, Student & Admin contexts) | todo |
| Phase 2 | Opportunities & Admin CRUD (Models, Keyset pagination, Filters, Audit logs, Browse & Admin UI) | todo |
| Phase 3 | Ingestion (Worker, RSS/JSON/HTML fetchers, Normalizer, Deduplication, Ingestion runs) | todo |
| Phase 4 | AI Search (LLMProvider, Embeddings, Hybrid retrieval, Rerank, Redis cache, Fallback, UI) | todo |
| Phase 5 | Student Dashboard (Saved, Applications, Notes, Deadline reminders, Data export/delete) | todo |
| Phase 6 | Admin Dashboard (User management, Analytics, Broadcasts, Audit log viewer) | todo |
| Phase 7 | Hardening & Launch (Security headers, Rate limits, i18n RTL, k6 load test, K8s, Runbooks) | todo |

## Last Completed
- **Phase 0 Foundations**:
  - Monorepo structure (`apps/web`, `apps/api`, `packages/shared`).
  - Docker Compose setup with PostgreSQL 16 (pgvector), Redis 7, Mailpit, API, Worker placeholder, and Web.
  - FastAPI backend with asynchronous SQLAlchemy 2 engine, Alembic migrations configuration, Redis integration, and `/api/v1/health` endpoint returning database and cache status.
  - React + TypeScript + Vite + Tailwind CSS frontend with `react-i18next` localized placeholder UI and responsive, accessible structure.
  - Test suites: Pytest for FastAPI (4 unit/integration tests passing) and Vitest for React (2 UI tests passing).
  - Code quality: Ruff linter & formatter, Mypy strict type-checking, ESLint, Pre-commit configuration, and GitHub Actions CI workflow.

## How to Run
- **Option 1: Docker Compose (All services)**:
  ```bash
  cp .env.example .env
  docker compose up --build
  ```
  - Web UI: [http://localhost:5173](http://localhost:5173)
  - API Health: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
  - Interactive API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
  - Mailpit Web Interface: [http://localhost:8025](http://localhost:8025)

- **Option 2: Local Development**:
  - **API**:
    ```bash
    cd apps/api
    .venv\Scripts\activate
    uvicorn app.main:app --reload --port 8000
    ```
  - **Web**:
    ```bash
    npm run dev:web
    ```

## How to Test
- **Run all checks across the monorepo**:
  ```bash
  # Shared package types
  npm run typecheck --workspace=packages/shared

  # Frontend checks
  npm run lint:web
  npm run typecheck:web
  npm run test:web

  # Backend checks
  cd apps/api
  .venv\Scripts\ruff check .
  .venv\Scripts\mypy app
  .venv\Scripts\pytest
  ```

## Known Gaps
- None for Phase 0. Foundations, container specs, endpoints, and CI validations are fully established.

## Next Step
- **Phase 1: Auth and roles** — Implement database models and migrations for `users`, `student_profiles`, and `refresh_tokens`; endpoints for Argon2id registration, Mailpit email verification, JWT login, rotating refresh token with family reuse detection, password reset, and `/me`; backend `require_role` guard; React `AuthContext`, login/register pages, and protected route wrappers.
