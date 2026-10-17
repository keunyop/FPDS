# FPDS Database Setup

Create a **new, empty development PostgreSQL database** with pgvector available
on the server. The database user must be able to create tables and the `vector`
extension. Run the following steps from the repository root in PowerShell.

## 1. Configure

```powershell
uv sync --directory api/service --frozen
if (-not (Test-Path .env.dev)) { Copy-Item .env.dev.example .env.dev }
```

Edit `.env.dev`:

- Set `FPDS_DATABASE_URL` to the empty development database.
- Keep `FPDS_ENV=dev`, the `http://localhost` origins and `FPDS_COOKIE_SECURE=false`.
- Replace the session and CSRF secret placeholders with separate random values.

## 2. Initialize

```powershell
uv run --directory api/service python -m api_service.init_local_db --env-file .env.dev
```

This applies every [migration](migrations) in order and keeps only:

- Country, product-type/taxonomy and processing-policy reference data.
- Migration records.
- One active administrator: **ID `admin` / password `admin`**.

Banks, source catalogs, collected products and operational history start empty.
Passwords are stored as salted hashes. These default credentials are for local
development only; use a unique password before hosting the application.

The command refuses production settings and databases containing existing tables,
views or sequences. On failure, all initialization changes roll back. Fix the
reported issue or check database access/pgvector, then rerun against the empty DB.
Use this command only for first installation, never to upgrade or reset an existing DB.

## 3. Start and sign in

Follow [Start locally](../README.md#5-start-locally), then open
[Admin login](http://localhost:3001/admin/login). Sign in with `admin` / `admin`
and select Canada. Add the banks and other countries you need through Admin.
