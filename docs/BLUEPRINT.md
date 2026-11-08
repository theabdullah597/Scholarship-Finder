# OpportunityAbroad System Blueprint & Technical Specification

This document serves as the master technical reference and single source of truth for all engineering phases of **OpportunityAbroad**.

---

## 1. System Architecture

```
                             +------------------------+
                             |    Web Application     |
                             |  (React + TS + Vite)   |
                             |  Tailwind, i18next     |
                             +-----------+------------+
                                         |
                                         | HTTPS /api/v1 (JWT Auth)
                                         v
                             +------------------------+
                             |      FastAPI API       |
                             |      (Python 3.12)     |
                             |  Pydantic v2, Auth,    |
                             |  Hybrid AI Search      |
                             +----+--------------+----+
                                  |              |
                Read/Write Models |              | Cache, Rate-limits,
                Async SQLAlchemy  |              | Queues
                                  v              v
                  +---------------+----+    +----+----------+
                  |   PostgreSQL 16    |    |    Redis 7    |
                  |     (pgvector)     |    +---------------+
                  +---------------+----+            ^
                                  ^                 |
                     Read / Write |                 | Pop jobs / Enqueue
                                  |                 |
                             +----+-----------------+----+
                             |     Background Worker     |
                             | (Ingestion, Reminders)    |
                             +---------------------------+
```

### 1.1 Components
- **`apps/web`**: Single-Page Application (SPA) built with React 18/19, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router, and `react-i18next`.
- **`apps/api`**: Asynchronous REST API built with FastAPI, Python 3.12, SQLAlchemy 2 (asyncio), Pydantic v2, and Alembic for schema migrations.
- **`apps/api` (Worker process)**: Background daemon running scheduled ingestion, RSS/API fetchers, deduplication, and automated deadline reminders.
- **PostgreSQL 16 with `pgvector`**: Single source of truth. Stores relational entities, full-text search tsvectors, and opportunity vector embeddings.
- **Redis 7**: Ephemeral store for rate limiting (token bucket / sliding window), caching search results (TTL 10 min), and job queueing.
- **Mailpit**: SMTP server and development web UI for testing transactional emails (verification, password resets, deadline reminders).

---

## 2. PostgreSQL Schema & Data Dictionary

### 2.1 Enums & Extensions
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

CREATE TYPE user_role AS ENUM ('student', 'admin');
CREATE TYPE opportunity_kind AS ENUM ('scholarship', 'internship', 'fellowship', 'grant');
CREATE TYPE funding_type AS ENUM ('fully_funded', 'partially_funded', 'unfunded', 'other');
CREATE TYPE opportunity_status AS ENUM ('pending_review', 'published', 'archived', 'rejected');
CREATE TYPE application_status AS ENUM ('saved', 'in_progress', 'submitted', 'interviewing', 'accepted', 'rejected', 'withdrawn');
CREATE TYPE ingestion_status AS ENUM ('running', 'success', 'partial_failure', 'failed');
```

### 2.2 Table Definitions

#### `users`
- `id` (UUID, PK, default `gen_random_uuid()`)
- `email` (VARCHAR(255), UNIQUE, NOT NULL, indexed)
- `password_hash` (VARCHAR(255), NOT NULL)
- `role` (`user_role`, NOT NULL, default `'student'`)
- `is_verified` (BOOLEAN, default `FALSE`)
- `verification_token` (VARCHAR(255), nullable)
- `reset_password_token` (VARCHAR(255), nullable)
- `reset_password_expires_at` (TIMESTAMPTZ, nullable)
- `is_suspended` (BOOLEAN, default `FALSE`)
- `created_at` (TIMESTAMPTZ, default `NOW()`)
- `updated_at` (TIMESTAMPTZ, default `NOW()`)
- `deleted_at` (TIMESTAMPTZ, nullable) -- Soft-delete flag; records purged after 30 days

#### `student_profiles`
- `id` (UUID, PK, default `gen_random_uuid()`)
- `user_id` (UUID, FK -> `users.id` ON DELETE CASCADE, UNIQUE, NOT NULL)
- `full_name` (VARCHAR(255), nullable)
- `citizenship` (VARCHAR(2), nullable) -- ISO 3166-1 alpha-2
- `target_countries` (TEXT[], default `'{}'`) -- Array of ISO country codes
- `fields_of_interest` (TEXT[], default `'{}'`)
- `target_degree_level` (VARCHAR(50), nullable) -- bachelors, masters, phd, postdoctoral
- `timezone` (VARCHAR(64), default `'UTC'`)
- `created_at` (TIMESTAMPTZ, default `NOW()`)
- `updated_at` (TIMESTAMPTZ, default `NOW()`)

#### `refresh_tokens`
- `id` (UUID, PK, default `gen_random_uuid()`)
- `user_id` (UUID, FK -> `users.id` ON DELETE CASCADE, NOT NULL)
- `family_id` (UUID, NOT NULL, indexed) -- All rotated tokens share a family ID
- `token_hash` (VARCHAR(255), NOT NULL, UNIQUE, indexed)
- `is_revoked` (BOOLEAN, default `FALSE`)
- `expires_at` (TIMESTAMPTZ, NOT NULL)
- `created_at` (TIMESTAMPTZ, default `NOW()`)
- `user_agent` (VARCHAR(512), nullable)
- `ip_address` (VARCHAR(64), nullable)

#### `sources`
- `id` (UUID, PK, default `gen_random_uuid()`)
- `name` (VARCHAR(255), NOT NULL)
- `source_type` (VARCHAR(32), NOT NULL) -- 'rss', 'json_api', 'html_scraper'
- `url` (TEXT, NOT NULL)
- `config` (JSONB, default `'{}'`) -- Selectors, headers, auth configs
- `is_active` (BOOLEAN, default `TRUE`)
- `fetch_interval_minutes` (INTEGER, default 720)
- `last_run_at` (TIMESTAMPTZ, nullable)
- `created_at` (TIMESTAMPTZ, default `NOW()`)
- `updated_at` (TIMESTAMPTZ, default `NOW()`)

#### `opportunities`
- `id` (UUID, PK, default `gen_random_uuid()`)
- `source_id` (UUID, FK -> `sources.id` ON DELETE SET NULL, nullable)
- `kind` (`opportunity_kind`, NOT NULL)
- `title` (VARCHAR(512), NOT NULL)
- `organization` (VARCHAR(255), NOT NULL)
- `description` (TEXT, NOT NULL)
- `country` (VARCHAR(2), NOT NULL) -- ISO 3166-1 alpha-2 code
- `fields` (TEXT[], default `'{}'`) -- e.g., ["Computer Science", "Public Health"]
- `funding_type` (`funding_type`, NOT NULL)
- `stipend_amount_min` (NUMERIC(12, 2), nullable)
- `stipend_amount_max` (NUMERIC(12, 2), nullable)
- `stipend_currency` (VARCHAR(3), nullable) -- ISO 4217 code (USD, EUR, etc.)
- `deadline` (TIMESTAMPTZ, nullable) -- Deadline in UTC
- `source_url` (TEXT, NOT NULL)
- `canonical_url` (TEXT, UNIQUE, NOT NULL) -- Unique deduplication constraint
- `status` (`opportunity_status`, NOT NULL, default `'pending_review'`, indexed)
- `embedding` (vector(1536), nullable) -- 1536-dim or provider specific vector
- `tsv` (TSVECTOR, GENERATED ALWAYS AS (to_tsvector('english', title || ' ' || organization || ' ' || description)) STORED)
- `created_at` (TIMESTAMPTZ, default `NOW()`, indexed)
- `updated_at` (TIMESTAMPTZ, default `NOW()`)

Indexes:
- `ix_opportunities_status_deadline` (`status`, `deadline`)
- `ix_opportunities_status_created_at` (`status`, `created_at`)
- `ix_opportunities_tsv` GIN (`tsv`)
- `ix_opportunities_embedding` HNSW (`embedding` vector_cosine_ops)
- `ix_opportunities_trgm_title` GIN (`title` gin_trgm_ops)

#### `tags` & `opportunity_tags`
- `tags`: `id` (UUID, PK), `name` (VARCHAR(64), UNIQUE, NOT NULL), `category` (VARCHAR(64), nullable)
- `opportunity_tags`: `opportunity_id` (UUID, FK), `tag_id` (UUID, FK), PK (`opportunity_id`, `tag_id`)

#### `applications`
- `id` (UUID, PK, default `gen_random_uuid()`)
- `user_id` (UUID, FK -> `users.id` ON DELETE CASCADE, NOT NULL)
- `opportunity_id` (UUID, FK -> `opportunities.id` ON DELETE CASCADE, NOT NULL)
- `status` (`application_status`, NOT NULL, default `'saved'`)
- `notes` (TEXT, nullable)
- `reminder_sent_14d` (BOOLEAN, default `FALSE`)
- `reminder_sent_7d` (BOOLEAN, default `FALSE`)
- `reminder_sent_1d` (BOOLEAN, default `FALSE`)
- `applied_at` (TIMESTAMPTZ, nullable)
- `created_at` (TIMESTAMPTZ, default `NOW()`)
- `updated_at` (TIMESTAMPTZ, default `NOW()`)
- UNIQUE (`user_id`, `opportunity_id`)

#### `notes`
- `id` (UUID, PK, default `gen_random_uuid()`)
- `user_id` (UUID, FK -> `users.id` ON DELETE CASCADE, NOT NULL)
- `opportunity_id` (UUID, FK -> `opportunities.id` ON DELETE CASCADE, NOT NULL)
- `content` (TEXT, NOT NULL)
- `created_at` (TIMESTAMPTZ, default `NOW()`)
- `updated_at` (TIMESTAMPTZ, default `NOW()`)

#### `notifications`
- `id` (UUID, PK, default `gen_random_uuid()`)
- `user_id` (UUID, FK -> `users.id` ON DELETE CASCADE, NOT NULL)
- `title` (VARCHAR(255), NOT NULL)
- `message` (TEXT, NOT NULL)
- `type` (VARCHAR(64), NOT NULL) -- 'deadline_reminder', 'broadcast', 'system'
- `is_read` (BOOLEAN, default `FALSE`)
- `link` (TEXT, nullable)
- `created_at` (TIMESTAMPTZ, default `NOW()`)

#### `ingestion_runs`
- `id` (UUID, PK, default `gen_random_uuid()`)
- `source_id` (UUID, FK -> `sources.id` ON DELETE CASCADE, NOT NULL)
- `status` (`ingestion_status`, NOT NULL)
- `items_found` (INTEGER, default 0)
- `items_created` (INTEGER, default 0)
- `items_updated` (INTEGER, default 0)
- `items_failed` (INTEGER, default 0)
- `error_log` (TEXT, nullable)
- `started_at` (TIMESTAMPTZ, default `NOW()`)
- `finished_at` (TIMESTAMPTZ, nullable)

#### `audit_logs`
- `id` (UUID, PK, default `gen_random_uuid()`)
- `actor_user_id` (UUID, FK -> `users.id` ON DELETE SET NULL, nullable)
- `action` (VARCHAR(128), NOT NULL) -- 'opportunity.create', 'opportunity.publish', 'user.suspend', etc.
- `target_type` (VARCHAR(64), NOT NULL) -- 'opportunity', 'user', 'source'
- `target_id` (VARCHAR(64), NOT NULL)
- `changes` (JSONB, nullable) -- Before & after state diff
- `ip_address` (VARCHAR(64), nullable)
- `created_at` (TIMESTAMPTZ, default `NOW()`, indexed)

---

## 3. REST API Contract

All endpoints reside under `/api/v1` and use Pydantic validation schemas.

### 3.1 System
- `GET /api/v1/health`: Checks DB connectivity and Redis ping. Returns `{ status: "ok"|"degraded", db: "connected", redis: "connected", version: "0.1.0" }`.

### 3.2 Authentication & User Account (`/api/v1/auth`, `/api/v1/users`)
- `POST /api/v1/auth/register`: `{ email, password, full_name? }` -> 201 Created (Sends verification email via Mailpit).
- `POST /api/v1/auth/verify-email`: `{ token }` -> 200 OK.
- `POST /api/v1/auth/login`: `{ email, password }` -> 200 OK `{ accessToken, user }` + Sets `httpOnly` `refreshToken` cookie.
- `POST /api/v1/auth/refresh`: Reads `refreshToken` cookie -> Rotates token, sets new cookie, returns `{ accessToken }`. Revokes family if reuse detected.
- `POST /api/v1/auth/logout`: Clears cookie and marks token family revoked.
- `POST /api/v1/auth/forgot-password`: `{ email }` -> 200 OK (Sends password reset token via Mailpit).
- `POST /api/v1/auth/reset-password`: `{ token, newPassword }` -> 200 OK.
- `GET /api/v1/users/me`: Returns user info & profile (Student or Admin).
- `PATCH /api/v1/users/me`: Updates profile (citizenship, fields, targets, timezone).
- `GET /api/v1/users/me/export`: Returns JSON export of all user data (GDPR).
- `DELETE /api/v1/users/me`: Soft-deletes user account (marked for purge after 30 days).

### 3.3 Opportunities (`/api/v1/opportunities`)
- `GET /api/v1/opportunities`: Keyset-paginated search & filter.
  - Query params: `cursor`, `limit` (default 20), `country`, `funding_type`, `field`, `deadline_min`, `deadline_max`, `stipend_min`, `stipend_max`, `sort` (deadline_asc, deadline_desc, created_desc).
  - Returns: `{ items: Opportunity[], next_cursor: string | null }`. (Only published for students; admins can filter by status).
- `GET /api/v1/opportunities/{id}`: Returns opportunity details.
- `POST /api/v1/opportunities`: [Admin only] Create opportunity (writes to `audit_logs`).
- `PUT /api/v1/opportunities/{id}`: [Admin only] Update opportunity (writes to `audit_logs`).
- `POST /api/v1/opportunities/{id}/publish`: [Admin only] Publish opportunity.
- `POST /api/v1/opportunities/{id}/archive`: [Admin only] Archive opportunity.
- `POST /api/v1/opportunities/bulk-moderate`: [Admin only] Bulk approve / reject with duplicate validation.

### 3.4 AI Search (`/api/v1/search`)
- `POST /api/v1/search`: `{ query: string, student_profile_context?: boolean }`
  - Parses intent via LLM (target countries, funding needs, keywords).
  - Computes query vector + full text query.
  - Performs hybrid PostgreSQL retrieval (0.6 vector similarity + 0.4 ts_rank, top 50).
  - LLM reranks and outputs structured explanations.
  - Validates IDs, clamps scores (0.0 - 1.0), strips markup.
  - Rate limited to 30 requests/hour/user via Redis. Cached in Redis for 10 minutes. Fallback to SQL full-text when provider fails.

### 3.5 Student Tracking (`/api/v1/student`)
- `GET /api/v1/student/applications`: List user's saved/applied opportunities with status.
- `POST /api/v1/student/applications`: `{ opportunity_id, status }`.
- `PATCH /api/v1/student/applications/{id}`: `{ status, notes }`.
- `DELETE /api/v1/student/applications/{id}`: Remove from tracker.
- `GET /api/v1/student/notifications`: List notifications with unread counts.
- `PATCH /api/v1/student/notifications/{id}/read`: Mark notification as read.

### 3.6 Admin (`/api/v1/admin`)
- `GET /api/v1/admin/users`: List users with role filter, suspend status.
- `POST /api/v1/admin/users/{id}/suspend`: Suspend user and revoke active tokens.
- `POST /api/v1/admin/users/{id}/restore`: Restore user.
- `GET /api/v1/admin/sources`: List ingestion sources.
- `POST /api/v1/admin/sources`: Create or update ingestion source.
- `POST /api/v1/admin/sources/{id}/run-now`: Trigger immediate ingestion job.
- `GET /api/v1/admin/ingestion-runs`: List ingestion run history.
- `GET /api/v1/admin/audit-logs`: List audit logs with actor and entity filters.
- `POST /api/v1/admin/broadcast`: Send broadcast notification to users.

---

## 4. AI Search & Reranking Plan

### 4.1 Interface Specification
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class LLMProvider(ABC):
    @abstractmethod
    async def complete_json(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Execute structured JSON completion conforming to the provided schema."""
        pass

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Return vector embeddings for a batch of strings."""
        pass
```

### 4.2 Query Execution Pipeline
1. **Rate Limit & Cache Check**: Key `ai_search:{sha256(query + user_context)}`. If found, return cached response with header `X-Cache: HIT`.
2. **Intent Parsing**: LLM extracts structured intent:
   - `countries`: ISO codes
   - `funding_type`: fully_funded, etc.
   - `fields`: normalized disciplines
   - `semantic_keywords`: text for embedding and search
3. **Hybrid PostgreSQL Query**:
   ```sql
   WITH semantic AS (
     SELECT id, 1 - (embedding <=> :query_vec) AS vec_score
     FROM opportunities
     WHERE status = 'published' AND embedding IS NOT NULL
     ORDER BY embedding <=> :query_vec
     LIMIT 50
   ),
   textual AS (
     SELECT id, ts_rank_cd(tsv, plainto_tsquery('english', :text_query)) AS text_score
     FROM opportunities
     WHERE status = 'published' AND tsv @@ plainto_tsquery('english', :text_query)
     LIMIT 50
   )
   SELECT o.*,
          COALESCE(s.vec_score, 0) * 0.6 + COALESCE(t.text_score, 0) * 0.4 AS hybrid_score
   FROM opportunities o
   LEFT JOIN semantic s ON o.id = s.id
   LEFT JOIN textual t ON o.id = t.id
   WHERE s.id IS NOT NULL OR t.id IS NOT NULL
   ORDER BY hybrid_score DESC
   LIMIT 50;
   ```
4. **LLM Rerank & Explanations**:
   - Sends the top 20 retrieved summaries to `complete_json` to score (0-1) and provide a 1-sentence "match_reason" explaining why it matches the student query.
5. **Sanitization & Validation**:
   - Drops any opportunity IDs not present in the candidate database results.
   - Clamps match score between 0.0 and 1.0.
   - Strips any HTML tags or script injection from explanation strings.
6. **Fallback Mechanism**:
   - If LLM provider raises an exception, times out (circuit breaker triggers after 3 consecutive failures), or is disabled: fall back directly to SQL hybrid/full-text ordering without AI reranking.

---

## 5. Security, Privacy & Compliance Plan

1. **Password Security**: Argon2id hashing with conservative memory and time costs via `passlib` / `pwdlib` / `argon2-cffi`.
2. **Token Security**:
   - Access token: JWT with 15-minute expiration, HS256/RS256, kept in-memory by React client.
   - Refresh token: High-entropy cryptographic random string, hashed before persistence in PostgreSQL. Issued via `httpOnly`, `Secure`, `SameSite=Strict` cookie with 14-day lifetime.
   - Reuse Detection: When a refresh token is reused, all tokens in the `family_id` are marked revoked, and all active sessions for that family are terminated.
3. **Role-Based Access Control (RBAC)**:
   - Dependencies: `get_current_user`, `require_role(["admin"])`, `require_role(["student", "admin"])`.
   - Verified on every server route independently of client-reported claims.
4. **Privacy & GDPR Compliance**:
   - Minimal personal data collection (email, optional name, educational interests).
   - Zero PII in application logs: email addresses masked (`j***@domain.com`), passwords and authorization headers stripped by logging middleware.
   - Data Export: `GET /api/v1/users/me/export` provides a machine-readable JSON archive.
   - Account Deletion: Soft-deletes user record and schedules an automated 30-day permanent purge.
5. **Input Validation & Scraped Data Sanitization**:
   - All external scraped data (HTML/RSS) treated as hostile input. HTML is sanitized with `bleach` or `nh3` before database insertion.

---

## 6. Frontend Architecture, i18n & Accessibility

- **Localization (i18n)**: Handled via `react-i18next`. All static user-facing text resides in locale JSON files (`src/locales/en.json`, `src/locales/ar.json`, etc.).
- **RTL Compatibility**: Use logical Tailwind classes (`ps-`, `pe-`, `ms-`, `me-`, `text-start`, `text-end`) and set `dir="rtl"` dynamically when language changes.
- **Accessibility (a11y)**: WCAG 2.1 AA compliant. Semantic HTML, ARIA attributes for modals and dropdowns, keyboard navigable, verified with `@axe-core/react` in development and Playwright axe scans.

