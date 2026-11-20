# Security risk register

## Dependency audit baseline (2026-11-20)

`npm audit --audit-level=high` currently reports transitive findings in
`esbuild`, `minimatch`, `react-router`, and `tinypool`. The available automatic
fix requires breaking upgrades to Vite, React Router, and Vitest. Do not run
`npm audit fix --force` without a compatibility review; track these upgrades as
the next dependency-maintenance task.

CI runs both npm and Python audits and preserves their reports without hiding
failures. The application hardening changes in this phase do not depend on
these toolchain packages at runtime.
