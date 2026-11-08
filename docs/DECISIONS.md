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
