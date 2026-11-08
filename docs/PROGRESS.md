# Project Progress: OpportunityAbroad

## Phase Overview

| Phase | Description | Status |
|---|---|---|
| Phase 0 | Foundations (Monorepo, Docker Compose, Postgres+pgvector, Redis, Mailpit, FastAPI Health, Tooling, CI) | done |
| Phase 1 | Auth & Roles (Argon2id, JWT + rotating refresh cookie, RBAC, Student & Admin contexts) | done |
| Phase 2 | Opportunities & Admin CRUD (Models, Keyset pagination, Filters, Audit logs, Browse & Admin UI) | todo |
| Phase 3 | Ingestion (Worker, RSS/JSON/HTML fetchers, Normalizer, Deduplication, Ingestion runs) | todo |
| Phase 4 | AI Search (LLMProvider, Embeddings, Hybrid retrieval, Rerank, Redis cache, Fallback, UI) | todo |
| Phase 5 | Student Dashboard (Saved, Applications, Notes, Deadline reminders, Data export/delete) | todo |
| Phase 6 | Admin Dashboard (User management, Analytics, Broadcasts, Audit log viewer) | todo |
| Phase 7 | Hardening & Launch (Security headers, Rate limits, i18n RTL, k6 load test, K8s, Runbooks) | todo |

## Last Completed
- **Phase 1 Auth & Roles**:
  - **Database models & migration**: `users` (Argon2id hash, email verification, role enum), `student_profiles` (citizenship, target countries, fields of interest, degree level, timezone), `refresh_tokens` (SHA-256 hash, family-based grouping, revocation tracking). Alembic migration creates all three tables with indexes.
  - **Auth endpoints** (`/api/v1/auth/*`): register, verify-email, login (sets httpOnly refresh cookie), refresh (rotation with family reuse detection/revocation), logout, forgot-password, reset-password.
  - **User endpoints** (`/api/v1/users/*`): GET /me (returns user + profile), PATCH /me (update profile fields with eager-load fix).
  - **RBAC**: `require_role` dependency; admin test route at GET `/api/v1/admin/test-rbac`; students get 403 on admin routes.
  - **Security**: Argon2id hashing via passlib, 15-min JWT access tokens, 14-day rotating httpOnly Secure SameSite=Strict refresh cookies, SHA-256 token storage, family-based revocation on reuse.
  - **Email**: Async SMTP service for verification and password reset emails (Mailpit for local dev).
  - **Admin script**: `app/scripts/create_admin.py` to seed the first admin user.
  - **React frontend**: AuthContext with in-memory JWT, auto-refresh on 401, Login, Register, VerifyEmail, ForgotPassword, ResetPassword, Dashboard, AdminDashboard pages. ProtectedRoute with optional role guard. All UI text via react-i18next. RTL-ready with logical CSS properties.
  - **Tests**: 12 pytest (Argon2id hashing, register+verify, login+cookie, token rotation+reuse revocation, logout, forgot+reset password, RBAC 403/200, GET+PATCH /me, health checks). 5 vitest (App home page, system status, Login form, Register form, ProtectedRoute redirect).
  - **Playwright E2E** spec written (`e2e/login-journey.spec.ts`) — browsers not installed yet (known gap).

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
  - **Create first admin** (requires running API with DB):
    ```bash
    cd apps/api
    .venv\Scripts\activate
    python -m app.scripts.create_admin
    ```

## How to Test
- **Run all checks across the monorepo**:
  ```bash
  # Shared package types
  npm run typecheck --workspace=packages/shared

  # Frontend checks
  npm run lint:web        # ESLint (0 warnings enforced)
  npm run typecheck:web   # TypeScript strict
  npm run test:web        # Vitest (5 tests)

  # Backend checks
  cd apps/api
  .venv\Scripts\ruff check .     # Linting
  .venv\Scripts\mypy app         # Type checking (24 files)
  .venv\Scripts\pytest -v        # 12 tests
  ```

## Known Gaps
- **Docker not installed** on dev machine — all testing is local only.
- **Playwright browsers** not installed — E2E spec exists but `npx playwright install chromium` needed before running.
- **React `act()` warnings** in test stderr — cosmetic noise from async state updates in AuthProvider, does not affect test correctness. Standard React 18 behavior.

## Next Step
- **Phase 2: Opportunities & Admin CRUD** — Implement models and migrations for `opportunities`, `sources`, `tags`, `opportunity_tags`, `audit_logs`; public list endpoint with filters, sorting, and keyset (cursor) pagination; detail endpoint; admin create, edit, verify, archive, bulk approve/reject with duplicate detection and audit rows; frontend browse page with URL-synced filters; admin table and form; seed 30 sample opportunities.
