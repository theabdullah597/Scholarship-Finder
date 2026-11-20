# Operations runbook

## API unavailable

1. Check `/api/v1/health`, API logs, PostgreSQL health, and Redis health.
2. If the API is unhealthy after a restart, inspect the latest migration and
   database connection settings.
3. Keep the web service running only if the API can recover; otherwise show the
   maintenance page through the ingress.

## Worker stalled

1. Check worker logs for ingestion or SMTP failures.
2. Verify PostgreSQL and Redis connectivity.
3. Restart one worker replica and confirm a new `ingestion_runs` row or reminder
   execution before scaling back up.

## Security incident

1. Rotate `SECRET_KEY`, database credentials, and provider credentials.
2. Revoke refresh-token families for affected accounts.
3. Preserve audit logs and structured logs; do not copy email addresses or
   tokens into incident tickets.
4. Review dependency scan output and deploy the smallest tested patch.

## Release checklist

- Database backup completed and restore point recorded.
- Migrations applied successfully.
- Health endpoint, login, refresh, search, and admin RBAC smoke checks pass.
- Security headers and CORS allow-list verified.
- Dependency scans have been reviewed; any accepted findings are recorded in
  the release ticket with an upgrade owner and target date.
- k6 search threshold and accessibility checks pass.
