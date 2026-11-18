# Project Progress: OpportunityAbroad

## Phase Overview

| Phase | Description | Status |
|---|---|---|
| Phase 0 | Foundations (Monorepo, Docker Compose, Postgres+pgvector, Redis, Mailpit, FastAPI Health, Tooling, CI) | done |
| Phase 1 | Auth & Roles (Argon2id, JWT + rotating refresh cookie, RBAC, Student & Admin contexts) | done |
| Phase 2 | Opportunities & Admin CRUD (Models, Keyset pagination, Filters, Audit logs, Browse & Admin UI) | done |
| Phase 3 | Ingestion (Worker, RSS/JSON/HTML fetchers, Normalizer, Deduplication, Ingestion runs) | todo |
| Phase 4 | AI Search (LLMProvider, Embeddings, Hybrid retrieval, Rerank, Redis cache, Fallback, UI) | todo |
| Phase 5 | Student Dashboard (Saved, Applications, Notes, Deadline reminders, Data export/delete) | todo |
| Phase 6 | Admin Dashboard (User management, Analytics, Broadcasts, Audit log viewer) | todo |
| Phase 7 | Hardening & Launch (Security headers, Rate limits, i18n RTL, k6 load test, K8s, Runbooks) | todo |

## Last Completed
- **Phase 2 Opportunities & Admin CRUD**:
  - **Database schema & migration**: `sources`, `opportunities`, `tags`, `opportunity_tags`, and `audit_logs` created with comprehensive btree, unique, and compound indexes (`ix_opportunities_status_deadline`, `ix_opportunities_status_created_at`, `ix_opportunities_canonical_url`).
  - **Public Endpoints**:
    - `GET /api/v1/opportunities`: multi-attribute filtering (kind, country, funding, field, deadline range, stipend range, include_expired), sorting (`created_desc`, `deadline_asc`, `deadline_desc`), and keyset (cursor) pagination. Public and students strictly see only published opportunities; expired deadlines excluded by default.
    - `GET /api/v1/opportunities/{id}`: single opportunity detail with full tags and metadata.
  - **Admin Endpoints (`/api/v1/admin/opportunities`)**:
    - `POST /api/v1/admin/opportunities`: create opportunity with canonical URL deduplication check and fuzzy `(title, organization)` check. Records `opportunity.create` audit log row.
    - `PATCH /api/v1/admin/opportunities/{id}`: patch opportunity fields with duplicate verification. Records `opportunity.patch` audit log row with diff.
    - `POST /api/v1/admin/opportunities/{id}/verify`: transition to published with `opportunity.verify` audit log row.
    - `POST /api/v1/admin/opportunities/{id}/archive`: transition to archived with `opportunity.archive` audit log row.
    - `POST /api/v1/admin/opportunities/bulk-moderate`: batch approve, reject, or archive multiple opportunities with individual audit log records.
    - `GET /api/v1/admin/audit-logs`: query system audit logs.
  - **Seed script**: `app/scripts/seed_opportunities.py` seeding 30 realistic international opportunities across diverse countries (DE, CH, GB, US, SE, JP, FR, AU, CA, KR, SG, SA, KE) with tags and funding levels.
  - **Frontend UI**:
    - `Browse` page (`/opportunities`) with filter sidebar synchronized to URL search params (`useSearchParams`), card grid, and "Load More" keyset cursor pagination.
    - `OpportunityDetail` page (`/opportunities/:id`) showing full metadata, stipend, deadline, tags, and link-out to official portal.
    - `AdminOpportunities` page (`/admin/opportunities`) under role-guarded ProtectedRoute featuring full listings table, status filtering, creation modal with validation, inline verify/archive actions, and bulk moderation toolbar.
    - Full localization via `react-i18next` with zero hard-coded strings.
  - **Tests**:
    - Backend: 7 comprehensive pytest cases covering filter combinations, keyset cursor stability during concurrent row insertions, student visibility enforcement, admin RBAC guards, canonical URL duplicate detection, and audit log generation. Total 19 backend tests passing.
    - Frontend: 4 Vitest test cases covering browse page rendering, URL filter synchronization, opportunity detail rendering, and admin modal creation. Total 9 frontend tests passing across 3 test suites.
    - All monorepo checks passing: Ruff, Mypy (29 files), ESLint (0 warnings), TypeScript strict (shared & web).

## How to Run
- **Option 1: Docker Compose (All services)**:
  ```bash
  cp .env.example .env
  docker compose up --build
  ```
  - Web UI: [http://localhost:5173](http://localhost:5173)
  - Opportunities Browse: [http://localhost:5173/opportunities](http://localhost:5173/opportunities)
  - Admin Opportunities: [http://localhost:5173/admin/opportunities](http://localhost:5173/admin/opportunities)
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
  - **Seed 30 Sample Opportunities**:
    ```bash
    cd apps/api
    .venv\Scripts\activate
    python -m app.scripts.seed_opportunities
    ```

## How to Test
- **Run all checks across the monorepo**:
  ```bash
  # Shared package types
  npm run typecheck --workspace=packages/shared

  # Frontend checks
  npm run lint:web        # ESLint (0 warnings enforced)
  npm run typecheck:web   # TypeScript strict
  npm run test:web        # Vitest (9 tests across 3 suites)

  # Backend checks
  cd apps/api
  .venv\Scripts\ruff check .     # Linting
  .venv\Scripts\mypy app         # Type checking (29 files)
  .venv\Scripts\pytest -v        # 19 tests
  ```

## Known Gaps
- **Docker not installed** on dev machine — all testing is local only.
- **Playwright browsers** not installed — E2E spec exists but `npx playwright install chromium` needed before running.
- **React `act()` warnings** in test stderr — cosmetic noise from async state updates in AuthProvider, does not affect test correctness. Standard React 18 behavior.

## Next Step
- **Phase 3: Ingestion** — Worker daemon and scheduler; fetchers for RSS, JSON API, and HTML; normalizer; deduplication engine (canonical URL first, then fuzzy title plus organization); `ingestion_runs` table and tracking; admin source management UI, run-now trigger, and ingestion run history viewer.
