# Project Phases: OpportunityAbroad

## Phase 0: Foundations
- **Status**: todo
- **Goal**: Set up monorepo (`apps/web`, `apps/api`, `packages/shared`), docker-compose with pgvector Postgres 16, Redis 7, Mailpit, api, worker placeholder, and web; configure Alembic; implement `/api/v1/health` returning db and redis status; set up linting, type-checking, test tooling, pre-commit configuration, and GitHub Actions running lint and tests.
- **Acceptance Criteria**: `docker compose up` works, health endpoint returns 200 with DB and Redis checks, web shows a placeholder page, and CI commands pass locally.

## Phase 1: Auth and Roles
- **Status**: todo
- **Goal**: Implement models and migrations for `users`, `student_profiles`, `refresh_tokens`; endpoints for register, verify email (Mailpit), login, refresh with rotation and reuse detection, logout, forgot and reset password, GET and PATCH `/me`; server-side `require_role` dependency; script to seed/create first admin; React AuthContext, Login, Register, Forgot Password, and ProtectedRoute.
- **Acceptance Criteria**: Register, verify, log in, stay logged in after refresh, log out; student gets 403 on admin routes; all test suites pass.

## Phase 2: Opportunities and Admin CRUD
- **Status**: todo
- **Goal**: Implement models and migrations for `opportunities`, `sources`, `tags`, `audit_logs`; public list endpoint with filters, sorting, and keyset (cursor) pagination; detail endpoint; admin create, edit, verify, archive, bulk approve or reject with duplicate detection and audit rows; frontend browse page with URL-synced filters; admin table and form; seed script for 30 sample opportunities.
- **Acceptance Criteria**: Filters combine correctly, cursors stay stable, students see only published items.

## Phase 3: Ingestion
- **Status**: todo
- **Goal**: Implement ingestion worker and scheduler; fetchers for RSS, JSON API, and HTML; normalizer; deduplication (canonical URL first, then fuzzy title + organization); `ingestion_runs`; admin source management, run-now trigger, run history, and moderation queue.
- **Acceptance Criteria**: Three sources ingest on schedule, reruns create no duplicates, failures are counted and do not crash/stop a run.

## Phase 4: AI Search
- **Status**: todo
- **Goal**: Implement `LLMProvider` interface with a real adapter and `FakeProvider` for tests; embeddings generation; `POST /search` with query parsing, hybrid retrieval (0.6 vector, 0.4 full text, top 50), rerank with reasons, output validation, non-AI fallback, Redis cache (10 min), rate limits (30 per hour per user), and circuit breaker; frontend search UI.
- **Acceptance Criteria**: Works with and without the provider; cached responses under 300 ms; no result references a missing opportunity.

## Phase 5: Student Dashboard
- **Status**: todo
- **Goal**: Implement models and endpoints for `applications`, `notes`, `notifications`; save opportunities, track application status, add notes; daily deadline reminder background job at 14, 7, and 1 days before deadlines (no duplicates, user time zone); frontend notification bell; user data export and account self-deletion.
- **Acceptance Criteria**: Reminders arrive in Mailpit; users cannot see or modify other users' private data.

## Phase 6: Admin Dashboard
- **Status**: todo
- **Goal**: Implement admin user management (role assignment, suspend, restore), analytics overview page, broadcast notifications, audit log viewer, and masked email privacy controls.
- **Acceptance Criteria**: Every admin action writes an `audit_logs` record; suspended users cannot log in or refresh tokens.

## Phase 7: Hardening and Launch
- **Status**: todo
- **Goal**: Apply security headers, CSP, CORS allow-list, rate limits on auth routes, dependency and static vulnerability scans; axe accessibility checks and fixes; second locale (i18n / RTL-ready); k6 load test script; production Dockerfiles; Kubernetes manifests; structured logging, Prometheus metrics, backup and restore docs, and operations runbooks.
- **Acceptance Criteria**: Launch checklist complete and all remaining risks catalogued.

