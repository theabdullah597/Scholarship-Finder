# Backup and restore

PostgreSQL is the source of truth. Run backups from a trusted host with
network access to the database and keep the output in encrypted, access-
controlled storage.

```powershell
pg_dump --format=custom --file=opportunityabroad.dump $env:DATABASE_URL
pg_restore --clean --if-exists --dbname=$env:DATABASE_URL opportunityabroad.dump
```

Before restoring, stop API and worker writes, verify the backup checksum, and
confirm the target database is the intended environment. Redis is ephemeral
and should not be restored; it will repopulate from PostgreSQL.

Perform a restore drill at least quarterly and record duration, row-count
checks, migration version, and application health results.
