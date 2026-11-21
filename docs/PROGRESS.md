# Project Progress: OpportunityAbroad

## Phase Overview

| Phase | Description | Status |
|---|---|---|
| Phase 0 | Foundations (Monorepo, Docker Compose, Postgres+pgvector, Redis, Mailpit, FastAPI Health, Tooling, CI) | done |
| Phase 1 | Auth & Roles (Argon2id, JWT + rotating refresh cookie, RBAC, Student & Admin contexts) | done |
| Phase 2 | Opportunities & Admin CRUD (Models, Keyset pagination, Filters, Audit logs, Browse & Admin UI) | done |
| Phase 3 | Ingestion (Worker, RSS/JSON/HTML fetchers, Normalizer, Deduplication, Ingestion runs) | done |
| Phase 4 | AI Search (LLMProvider, Embeddings, Hybrid retrieval, Rerank, Redis cache, Fallback, UI) | done |
| Phase 5 | Student Dashboard (Saved, Applications, Notes, Deadline reminders, Data export/delete) | done |
| Phase 6 | Admin Dashboard (User management, Analytics, Broadcasts, Audit log viewer) | done |
| Phase 7 | Hardening & Launch (Security headers, Rate limits, i18n RTL, k6 load test, K8s, Runbooks) | done |

## Last Completed
- **Live opportunity discovery**:
  - Development startup seeds published opportunities when the opportunity table is empty, restoring browse/search data immediately after a fresh database setup.
  - The student dashboard now loads personalized published opportunities from the database using the student's target country and first field of interest.
  - Seeded ingestion sources include official UW-Madison, Arizona State University, and Fulbright listing pages for worker HTML ingestion.
  - AI search remains grounded: live or seeded opportunities are stored and moderated in PostgreSQL before they can be ranked or returned.
- **Phase 7 Hardening & Launch**:
  - **API security**: Added strict CORS methods/headers, security headers, request IDs, structured JSON logs without request PII, production secret validation, SameSite=Strict refresh cookies, and Redis-backed fixed-window throttling for authentication routes.
  - **Frontend and accessibility**: Added Arabic locale support with automatic RTL document direction, a language switcher, strict Nginx security headers, and an axe Playwright smoke check.
  - **Launch assets**: Added k6 search thresholds, dependency and Bandit scans in CI, Kubernetes manifests, encrypted PostgreSQL backup/restore guidance, an operations runbook, and a dependency risk register.
  - **Tests and validation**: 34 backend tests pass, including security-header and rate-limit cases; Ruff, frontend lint, strict typecheck, Vitest, and production build pass. Browser-based axe/k6 execution requires the local services and Playwright/k6 tooling.
- **Phase 6 Admin Dashboard**:
  - **User management**: Added admin-only user listing with masked email addresses, role assignment, suspension/restore controls, self-suspension protection, and audit records for mutations.
  - **Operations**: Added aggregate analytics, database-backed broadcasts to active users or a selected role, and action/target-filtered audit-log viewing.
  - **Frontend**: Expanded the localized admin dashboard with analytics cards, user controls, and broadcast composition while retaining role-protected admin operations.
  - **Tests and validation**: Added backend coverage for masked users, suspension audit records, broadcast recipients, and admin RBAC. Frontend lint, strict typecheck, Vitest, and production build pass; backend execution requires the repository virtual environment because the system interpreter lacks asyncpg.
- **Phase 5 Student Dashboard**:
  - **Student data**: Added applications, notes, and notifications tables with ownership constraints and migration. Students can save published opportunities, track application status, create private notes, and mark notifications read.
  - **Reminders**: Added a daily worker job for 14-, 7-, and 1-day deadline reminders using each profile timezone, unique dedupe keys, notification records, and Mailpit email delivery.
  - **Privacy**: Added user-scoped data export and soft account deletion with immediate refresh-token revocation. Cross-user application and note access is rejected.
  - **Frontend**: Extended the student dashboard with saved application tracking, private notes, notification display, export/delete controls, and save-from-opportunity-detail.
  - **Tests and validation**: 28 backend tests pass, including privacy isolation and reminder deduplication; Ruff, mypy, frontend lint, strict typecheck, nine Vitest tests, and production build pass.
- **Phase 4 AI Search**:
  - **Grounded retrieval**: Added a provider interface, deterministic `FakeProvider`, optional OpenAI-compatible adapter, query embeddings, 0.6 semantic + 0.4 lexical scoring, top-50 candidate retrieval, and validated reranking.
  - **Safety and resilience**: Search is restricted to published database opportunities; unknown provider IDs are discarded, scores are clamped, reasons are markup-stripped, fallback ranking works without AI, and a three-failure circuit breaker prevents repeated provider calls.
  - **Performance controls**: Added Redis response caching for 10 minutes and a 30 requests/hour per-user rate limit. Cache and rate-limit outages fail safely to database-backed search with warnings.
  - **API and UI**: Added authenticated `POST /api/v1/search`, embedding storage migration, shared contracts, and a localized protected search page with fallback/cached state messaging.
  - **Tests and validation**: 26 backend tests pass, including provider validation, published-only filtering, fallback, and cache behavior; Ruff, mypy, frontend lint, strict typecheck, nine Vitest tests, and production build pass.
- **Phase 3 Ingestion**:
  - **Pipeline**: Added RSS/Atom, configurable JSON API, and CSS-selector HTML fetchers; sanitized and normalized untrusted text, URLs, country codes, opportunity kinds, funding types, deadlines, and stipend values.
  - **Reliability**: Added per-source `ingestion_runs` tracking, per-item failure isolation, partial-failure status, bounded error logs, and a polling worker scheduler that runs active sources when their configured interval is due.
  - **Deduplication**: Canonical URL matching runs first, followed by fuzzy title and organization matching; reruns update existing opportunities instead of creating duplicates.
  - **Admin operations**: Added source CRUD, activation controls, synchronous run-now trigger, ingestion history, and audit records. Added the admin Sources page and shared API contracts.
  - **Tests and validation**: 24 backend tests pass, including five ingestion acceptance tests; Ruff and mypy pass; frontend lint, strict typecheck, nine Vitest tests, and production build pass.
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
- **Post-launch maintenance** — Review the dependency risk register, schedule breaking-safe toolchain upgrades, and run browser axe/k6 checks in CI infrastructure with the deployed services.
