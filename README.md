# FPDS Startup Guide

FPDS collects and validates official financial-product information.
This guide runs FPDS API and FPDS Admin locally.

## 1. Prerequisites

Install Git, Node.js 24, pnpm 10.33.0, Python 3.12 and uv.
You also need access to a development PostgreSQL database with FPDS migrations applied.
For a new database, follow the [database setup guide](db/README.md) first
(PostgreSQL with pgvector and the `psql` client are required).

## 2. Clone and install

Run these commands in PowerShell:

```powershell
git clone https://github.com/keunyop/FPDS.git
cd FPDS
uv sync --frozen
uv sync --directory api/service --frozen
pnpm --dir app/admin install --frozen-lockfile
```

The root Python environment runs collection workers; the API has its own environment.
Run all remaining commands from the repository root.

## 3. Configure

Create local configuration files if they do not already exist:

```powershell
if (-not (Test-Path .env.dev)) { Copy-Item .env.dev.example .env.dev }
if (-not (Test-Path app/admin/.env.local)) { Copy-Item app/admin/.env.example app/admin/.env.local }
```

Edit `.env.dev`:

- Set `FPDS_DATABASE_URL` to your development database connection string.
- Replace `FPDS_ADMIN_SESSION_SECRET` and `FPDS_ADMIN_CSRF_SECRET` with separate long random values.
- Keep the example's `localhost` origins and `FPDS_COOKIE_SECURE=false` for local HTTP.

In `app/admin/.env.local`, keep:

```dotenv
FPDS_ADMIN_API_ORIGIN=http://localhost:4000
```

Keep secrets out of Git. Storage and provider credentials are needed for actual
collection; see the [Worker guide](worker/README.md) and [environment configuration](docs/03-design/dev-prod-environment-spec.md).

## 4. Create the first admin

Skip this step if you already have an operator account in the configured database.

```powershell
uv run --directory api/service python -m api_service.bootstrap_admin_user --env-file .env.dev --login-id admin --display-name "Admin Operator" --role admin
```

Enter a password of at least 8 characters when prompted.

## 5. Start locally

Open two PowerShell terminals at the repository root. Keep both running.

**Terminal 1 - FPDS API**

```powershell
$env:FPDS_ENV_FILE = '.env.dev'
uv run --directory api/service uvicorn api_service.main:app --reload --host localhost --port 4000
```

**Terminal 2 - FPDS Admin**

```powershell
pnpm --dir app/admin run dev
```

## 6. Check

1. Open [API health](http://localhost:4000/healthz) and check for `"status":"ok"`.
2. Open [Admin login](http://localhost:3001/admin/login), sign in and select an active country.
3. Open Overview and Banks. A new database starts without collected products.

Use `localhost` consistently rather than mixing it with `127.0.0.1`.
Press `Ctrl+C` in each terminal to stop the servers.

For further work: [development guide](descent/FPDS_Admin_개발_가이드.md),
[Admin](app/admin/README.md), [API](api/service/README.md),
[Public app](app/public/README.md).
