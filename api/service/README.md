# FPDS Admin API Service

This package is the first live runtime slice for `WBS 4.1 admin login`.

Current scope:
- DB-backed admin user accounts
- DB-backed admin sessions
- login, logout, and session introspection routes
- login failure tracking and auth audit events
- bootstrap CLI for the first operator account

Current routes:
- `POST /api/admin/auth/login`
- `POST /api/admin/auth/logout`
- `GET /api/admin/auth/session`
- `GET /healthz`

## Local Run

Apply the DB baseline in order:

```powershell
psql $env:FPDS_DATABASE_URL -f db/migrations/0001_initial_baseline.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0002_admin_auth.sql
```

Create the first operator account:

```powershell
cd api/service
uv run python -m api_service.bootstrap_admin_user --env-file ..\..\.env.dev --email admin@example.com --display-name "Admin Operator" --role admin
```

Run the API:

```powershell
cd ..\..
$env:FPDS_ENV_FILE=".env.dev"
uv run --directory api/service uvicorn api_service.main:app --reload --host localhost --port 4000
```

## Notes

- Passwords are hashed with Python's built-in `scrypt`.
- The session cookie is still `fpds_admin_session` per the shared auth contract.
- Login throttling is DB-backed with per-account lockout and recent-attempt checks.
- Later admin write routes can reuse the stored session and CSRF token model.
- The settings loader now resolves a relative `FPDS_ENV_FILE` from either the current working directory or the repo root, so `.env.dev` works both from the workspace root and from inside `api/service`.
