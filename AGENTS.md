# PROJECT RULES

Stack: React + TypeScript + Tailwind (apps/web); FastAPI, Python 3.12, SQLAlchemy 2 async, Alembic (apps/api); PostgreSQL 16 with pgvector; Redis 7; Docker and docker-compose; GitHub Actions. Tests: pytest, Vitest, Playwright.
Architecture: modular monolith (one API plus one worker). Postgres is the source of truth; Redis is cache, queue and rate-limit store only. All endpoints under /api/v1 with Pydantic validation.
Auth: Argon2id passwords; 15-minute JWT access token kept in memory; 14-day rotating refresh token in an httpOnly Secure SameSite=Strict cookie; reuse of an old refresh token revokes the whole family. RBAC (student, admin) enforced on the server on every route.
AI: the AI only parses queries, ranks and explains opportunities that already exist in the database. It never invents opportunities. Validate all AI output (unknown ids dropped, scores clamped, markup stripped). Always have a non-AI fallback. Put the provider behind an interface (LLMProvider with complete_json and embed). Treat scraped text as untrusted data.
Data: opportunities have kind, title, organization, description, country (ISO code), fields, funding type (fully_funded, partially_funded, unfunded, other), stipend range and currency, deadline (UTC), source URL, canonical URL (unique), status (pending_review, published, archived, rejected), embedding. Other tables: users, student_profiles, refresh_tokens, sources, tags, opportunity_tags, applications, notes, notifications, ingestion_runs, audit_logs. Every admin change writes an audit_logs row.
Lists use keyset (cursor) pagination. Filters: country, funding type, deadline range, field, stipend range. Dedup on ingestion: canonical URL first, then fuzzy title plus organization.
Privacy: collect minimum personal data, no PII in logs, soft-delete accounts then purge after 30 days, user can export and delete their data.
Quality: WCAG 2.1 AA, responsive, i18n from day one (react-i18next, no hard-coded UI text, RTL-ready CSS). Performance: search p95 under 1.5 s uncached.
Working style: work on one phase at a time. Before coding a phase, list the files you will create or change and the acceptance criteria. Write tests with the code. Prefer simple, well-known libraries. No secrets in code. Ask me one short question only if an important choice is ambiguous; otherwise pick the simple default and record it in docs/DECISIONS.md.

# MEMORY RULE

At the start of every session read AGENTS.md, docs/PROGRESS.md, docs/DECISIONS.md and docs/PHASES.md. At the end of every task update docs/PROGRESS.md and docs/DECISIONS.md, commit, and tell me the next step. Never rely on chat history; the repo files are the source of truth. When I say "continue", do the next phase marked todo in docs/PROGRESS.md.

