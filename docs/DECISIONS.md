# Architecture Decision Records (ADR)

## ADR-001: Core Architecture & Stack Selection
- **Date**: 2026-11-08
- **Decision**: Adopt a modular monolith architecture composed of a single FastAPI backend (`apps/api`), a background worker (`apps/api` worker entrypoint), and a React + TypeScript single-page application (`apps/web`), orchestrated via Docker Compose with PostgreSQL 16 (pgvector), Redis 7, and Mailpit.
- **Why**: 
  - Keeps operational complexity low while enabling high velocity and type safety across frontend and backend.
  - PostgreSQL 16 with the `pgvector` extension provides ACID transactional storage as the single source of truth and unified vector search without needing an external vector DB.
  - Redis 7 provides low-latency caching, rate limiting, and ephemeral message/task queues.
  - Mailpit provides local SMTP server & web UI for testing emails without external dependencies.

## ADR-002: Authentication Architecture & Token Strategy
- **Date**: 2026-11-08
- **Decision**: Use Argon2id for password hashing, 15-minute short-lived JWT access tokens stored in-memory in the frontend, and 14-day rotating refresh tokens stored in an `httpOnly`, `Secure`, `SameSite=Strict` cookie. Implement refresh token reuse detection that invalidates the whole token family upon replay attacks.
- **Why**: 
  - Protects against XSS (refresh token cannot be accessed via JavaScript; access token is memory-only).
  - Protects against CSRF via `SameSite=Strict` and cookie isolation.
  - Automatic token rotation with family revocation neutralizes stolen refresh token abuse immediately.

## ADR-003: AI Architecture & Grounded Retrieval
- **Date**: 2026-11-08
- **Decision**: AI search functions strictly as query parser, ranker, and explainer over opportunities existing in PostgreSQL. Output must be strictly validated (unknown IDs pruned, scores clamped, HTML stripped). Abstract LLM calls behind an `LLMProvider` interface with a `FakeProvider` for automated testing and resilience.
- **Why**: 
  - Prevents hallucination of scholarships or grants.
  - Ensures system works reliably when LLM APIs are offline or rate-limited via a deterministic full-text + structured fallback.
  - Scraped external content is treated as untrusted data to protect against prompt injection.

## ADR-004: Keyset Pagination for Opportunity Listings
- **Date**: 2026-11-08
- **Decision**: Standardize on keyset (cursor) pagination based on `(created_at, id)` or `(deadline, id)` instead of offset pagination.
- **Why**: 
  - Guarantees $O(1)$ database query performance regardless of page depth.
  - Eliminates page-drift issues when new opportunities are published or expired in real-time.

## ADR-005: Monorepo Structure & Package Sharing
- **Date**: 2026-11-08
- **Decision**: Organize repo into `apps/web` (React/Vite), `apps/api` (FastAPI/Alembic), and `packages/shared` (shared schemas and TypeScript types/contracts).
- **Why**: 
  - Enables clean separation of concerns while keeping schemas synchronized across client and server.

## ADR-006: Refresh Token Storage and Hash Strategy
- **Date**: 2026-11-08
- **Decision**: Persist only the SHA-256 cryptographic hash of refresh tokens in the `refresh_tokens` table. Pass raw high-entropy tokens only via `httpOnly` cookies. Group rotated tokens by `family_id` to allow instant complete family revocation when token reuse is detected.
- **Why**: 
  - If the database is compromised, active refresh tokens cannot be stolen or used to forge sessions.
  - Family-based revocation ensures that race-condition or stolen-token replays invalidate all attacker sessions immediately.



## ADR-007: Frontend Auth Architecture
- **Date**: 2026-11-08
- **Decision**: Consolidate all auth state and methods in a single `AuthContext.tsx` file (context + provider + `useAuth` hook). Store the JWT access token in a module-scoped variable in `api.ts` (never localStorage/sessionStorage). Use a single-flight mutex for refresh to avoid duplicate requests. All pages import `useAuth` from `context/AuthContext`.
- **Why**:
  - In-memory token storage prevents XSS-based token theft.
  - Single-flight mutex prevents refresh token race conditions.
  - Consolidated context file avoids import confusion and circular dependencies.
  - Auto-refresh on 401 in `fetchWithAuth` provides seamless session continuity.

## ADR-008: Python Version Constraint
- **Date**: 2026-11-08
- **Decision**: Use Python 3.13 (not 3.14) for the backend virtual environment.
- **Why**: pydantic-core requires Rust compilation via maturin, which fails on Python 3.14. Python 3.13 is the latest stable version with full binary wheel support for all dependencies.

## ADR-009: Keyset Pagination & Keyset Cursor Encoding
- **Date**: 2026-11-18
- **Decision**: Keyset pagination for opportunities is encoded as URL-safe base64 strings containing the JSON tuple `{"c": timestamp_iso, "i": uuid_str}`. Query filters dynamically compare composite ordering keys `(created_at, id)` or `(deadline, id)`.
- **Why**: 
  - Standard offset pagination exhibits $O(N)$ performance degradation and drifts when concurrent inserts/deletions take place.
  - Base64-encoded opaque cursor prevents clients from depending on underlying DB column structures while remaining completely deterministic across concurrent updates.
  - Tested and proven stable when new rows are inserted during pagination.

## ADR-010: Database Dialect Compatibility for Testing vs Production
- **Date**: 2026-11-18
- **Decision**: Define model column types using SQLAlchemy's `.with_variant()` pattern (e.g. `postgresql.JSONB().with_variant(sa.JSON(), "sqlite")` and `sa.ARRAY(sa.String).with_variant(sa.JSON(), "sqlite")`).
- **Why**:
  - Allows unit and integration tests to run with high speed and zero external service overhead on in-memory SQLite (`aiosqlite`).
  - Production deployments use full native PostgreSQL capabilities (JSONB binary indexing and native arrays).

## ADR-011: Ingestion Failure Isolation and Scheduling
- **Date**: 2026-11-20
- **Decision**: Execute ingestion on a per-source polling scheduler, record every run in `ingestion_runs`, and isolate malformed items from the rest of a source run. Fetchers preserve malformed records as invalid raw items so the engine can count and report them rather than silently dropping them.
- **Why**:
  - A source outage or malformed record must not stop other scheduled sources or valid records from being processed.
  - Explicit failure counts and partial-failure statuses give administrators actionable run history while keeping the worker alive.
  - Polling the configured `fetch_interval_minutes` keeps scheduling simple and avoids adding a second queue dependency before it is needed.

## ADR-012: Grounded Hybrid Search Resilience
- **Date**: 2026-11-20
- **Decision**: Search first retrieves only published database opportunities using a deterministic semantic-plus-lexical score (0.6/0.4), then optionally asks an `LLMProvider` to rerank the top 50. Provider output is advisory and strictly validated; Redis caches final IDs and explanations for 10 minutes, while a per-process circuit breaker and deterministic fallback keep search available.
- **Why**:
  - Retrieval remains grounded in PostgreSQL and cannot expose hallucinated or unpublished opportunities.
  - Deterministic scoring provides useful behavior in tests, local development, provider outages, and missing API credentials.
  - Caching and rate limiting protect provider cost and latency without making Redis the source of truth.

## ADR-013: Student Data Ownership and Deadline Reminders
- **Date**: 2026-11-20
- **Decision**: Store applications, notes, and notifications with explicit `user_id` ownership and enforce ownership in every student endpoint. Generate deadline reminders in the worker at 14, 7, and 1 local calendar days, using a unique `(application, milestone)` dedupe key and sending email only after the notification is committed.
- **Why**:
  - Server-side ownership predicates prevent students from reading or changing another student's private data.
  - Calendar-day calculations respect each student's timezone instead of assuming UTC midnight.
  - Database-backed dedupe makes retries safe and keeps notifications authoritative even if email delivery is unavailable.

## ADR-014: Admin Privacy and Broadcast Delivery
- **Date**: 2026-11-20
- **Decision**: Admin user listings expose a deterministic masked email (`first two local-part characters + *** + @domain`) and never return passwords or unmasked email addresses. Broadcasts reuse committed `Notification` rows and target only active users, optionally filtered by role; each campaign and user mutation writes an audit log entry.
- **Why**:
  - Masking lets administrators identify accounts without making the dashboard an unnecessary PII directory.
  - Notifications are already the source of truth for student-facing messages, so a separate campaign table is not required for this phase.
  - Persisting notifications before response completion keeps delivery visible and retry-safe, while audit rows preserve accountability for privileged actions.
