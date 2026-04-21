# Admin API Boundary

Use this area for `/api/admin/*` endpoints.

Planned scope:
- review tasks
- runs
- change history
- publish
- usage
- dashboard health
- auth session routes and session introspection

Current scaffold:
- `route-manifest.json` lists the reserved admin routes and their auth or CSRF expectations.
- `auth/README.md` captures the login, logout, and session route baseline.
- `../service/` now contains the live FastAPI admin runtime through review, runs, usage, and dashboard health, including the aggregate refresh queue and manual retry endpoints.

The route manifest remains the contract source of truth, while runtime code now lives in the separate service package.
