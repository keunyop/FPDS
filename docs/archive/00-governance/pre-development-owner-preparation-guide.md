# FPDS Pre-Development Owner Preparation Guide

Version: 1.3
Date: 2026-04-07
Status: Active
Source Documents:
- `docs/01-planning/WBS.md`
- `docs/00-governance/decision-log.md`
- `docs/00-governance/raid-log.md`
- `docs/03-design/dev-prod-environment-spec.md`
- `docs/03-design/db-migration-baseline.md`
- `docs/03-design/object-storage-evidence-bucket-baseline.md`
- `docs/03-design/monitoring-error-tracking-baseline.md`
- `docs/03-design/security-access-control-design.md`
- `docs/03-design/localization-governance-and-fallback-policy.md`

---

## 1. Purpose

This document explains everything the Product Owner or infrastructure owner should prepare before WBS `3. Prototype Build` begins.

Goals:
- separate `foundation contract complete` from `actual coding readiness`
- reflect the now-fixed runtime and language baseline
- explain what still must be prepared outside git
- give a careful hosted-dev checklist that can be followed step by step
- let the next Codex session start implementation only after the environment is truly ready

This is not a development start instruction.
Actual implementation should still wait for an explicit Product Owner go decision.

---

## 2. WBS 2 Review Summary

### 2.1 What Is In Good Shape

WBS `2` is broadly complete at the contract and scaffold level.

Completed areas:
- env contract is documented and example env files exist
- DB baseline and initial migration file exist
- object storage layout baseline exists
- observability baseline and CI checks exist
- auth, i18n, security, and route skeleton scaffolds exist
- foundation checks and cleanup audit pass

This means the repository is ready for implementation planning.
It does not yet mean the repository is fully ready for runtime coding.

### 2.2 What Still Blocks Practical Start Readiness

These are the remaining practical gaps before coding:

1. Local toolchains for the chosen runtime stack are not installed yet.
2. Hosted dev Postgres is not provisioned and verified yet.
3. Hosted S3-compatible dev object storage is not provisioned and verified yet.
4. Real dev secrets do not exist yet outside git.
5. The OpenAI dev API key is not ready yet.
6. The DB baseline has not been applied and validated on a real dev Postgres yet.

### 2.3 Review Findings

High:
- Hosted dev DB and storage must be provisioned before WBS `3.1` to `3.3`.
- The baseline migration must be runnable against a real hosted Postgres before prototype implementation should proceed.
- Real secrets and OpenAI access must exist before coding starts.

Medium:
- The auth scaffold excludes logout from CSRF, while the security design says cookie-authenticated admin write routes should be protected. This should be resolved before admin auth implementation starts.
- The glossary seed uses `draft` for `term_status`, while the design baseline defines glossary entry status as `approved/deprecated`. This is a scaffold vocabulary mismatch to clean up later.

Low:
- The WBS section heading says WBS `2` is completed, but one status line in the same section still reads like a next-stage state. This is a documentation consistency issue only.

---

## 3. Fixed Baseline Before Coding

### 3.1 Product Code Language Baseline

The following is now fixed:
- primary product language: `Python`
- browser-facing frontend language: `TypeScript`

Meaning:
- crawling, parsing, extraction, normalization, and worker-heavy logic should assume Python by default
- public and admin browser-facing frontend code should assume TypeScript by default

### 3.2 Fixed Runtime Stack Baseline

The following is now fixed for the pre-WBS `3` coding baseline:

| Area | Fixed Decision |
|---|---|
| frontend package manager | `pnpm` |
| python package and runtime manager | `uv` |
| app and admin runtime | `Next.js App Router` |
| API runtime | `FastAPI` separate service |
| worker model | separate `Python worker process` |
| auth implementation approach | `Python API` managed `server-side session auth` |
| dev monitoring | `disabled` at first |

Meaning:
- frontend and backend do not need to share one runtime
- frontend and API may run separately in dev
- worker work should not be embedded into the browser runtime by default
- auth should stay cookie-session based, matching the existing security design
- dev monitoring setup is intentionally deferred for now, but structured logging rules still apply

### 3.3 What Is Still Required Before Coding

The remaining work is no longer architecture decision work.
It is now setup and verification work.

What still must be prepared:
- local developer tools for Node, pnpm, Python, uv, and Postgres client access
- hosted dev Postgres
- hosted dev S3-compatible object storage
- real dev secrets outside git
- OpenAI dev API key
- an untracked local dev env source or secure secret store
- confirmation that Codex may later use those prepared values during implementation

---

## 4. Recommended Preparation Order

Follow this order:

1. install local toolchains
2. provision hosted dev Postgres
3. provision hosted dev object storage
4. prepare local verification tools for DB and storage
5. generate and store real dev secrets outside git
6. prepare OpenAI API access
7. prepare an untracked local dev env source
8. verify readiness and send the final summary back to Codex

This order is designed to keep setup simple and to catch blockers early.

---

## 5. Step-By-Step Preparation Guide

### 5.1 Install the Local Toolchains First

Nothing else should be provisioned until the local tools exist.

Prepare these tools on your machine:

| Tool | Why You Need It |
|---|---|
| `Python 3.12` | primary language runtime for API and workers |
| `uv` | Python package and environment manager |
| `Node.js LTS` | Next.js runtime for frontend and admin |
| `pnpm` | frontend package manager |
| `psql` or equivalent Postgres client | verify hosted DB connectivity and later run migrations |
| optional `aws` CLI or provider CLI | verify S3-compatible storage access |

Recommended sequence:
1. install Python
2. install uv
3. install Node.js LTS
4. install pnpm
5. install Postgres client tools
6. install optional storage CLI if your provider benefits from it

Verify each installation in PowerShell:

```powershell
python --version
uv --version
node --version
pnpm --version
psql --version
aws --version
```

Success criteria:
- each required command works from a fresh PowerShell window
- you do not need admin repair work every time you reopen the terminal

Do not move on until `python`, `uv`, `node`, `pnpm`, and `psql` all work.

### 5.2 Prepare the Hosted Dev Postgres

The current baseline requires hosted Postgres.

What you need to prepare:
1. choose one hosted Postgres provider for `dev`
2. create one dedicated dev database, ideally named `fpds_dev`
3. create one dedicated dev DB user, ideally `fpds_dev_user`
4. generate a real password
5. keep the password outside git
6. record the host, port, DB name, user, SSL rule, and connection string
7. confirm that your machine can reach the hosted DB

Recommended naming:
- database: `fpds_dev`
- user: `fpds_dev_user`

Recommended checks:
1. confirm network reachability from your machine
2. connect with `psql`
3. run `SELECT 1;`
4. confirm you can create and inspect objects later when development starts

Example connection string shape:

```text
postgres://fpds_dev_user:replace-with-real-password@your-host:5432/fpds_dev
```

If your provider requires SSL options, keep the final working connection string in your secret store, not in git.

Important:
- do not point dev at a production Postgres cluster
- do not reuse production credentials
- do not run the FPDS schema migration yet if you want implementation start to remain a separate step
- do ensure the database is ready for Codex to apply the baseline migration later

What to record for later:
- provider name
- host
- port
- database name
- dev user name
- SSL requirement
- whether `psql` from your machine can connect successfully

### 5.3 Prepare the Hosted Dev Object Storage

The current baseline requires hosted `S3-compatible` object storage.

What you need to prepare:
1. choose one hosted storage provider
2. confirm it supports S3-compatible access or equivalent enough to match the baseline
3. create one private dev bucket
4. prefer the bucket name `fpds-dev-private`
5. create one dev-scoped access key and secret key
6. record the endpoint, region, bucket, and credential details outside git
7. verify the bucket is private
8. verify your credentials can read bucket metadata and upload a test object

Recommended logical layout:
- `dev/snapshots/...`
- `dev/parsed/...`

Recommended checks:
1. list the bucket
2. upload a harmless temporary object
3. confirm browser-public access is not enabled

If you use `aws` CLI and your provider requires a custom endpoint, the verification shape will usually be similar to:

```powershell
aws s3 ls s3://fpds-dev-private --endpoint-url https://your-storage-endpoint
```

If the provider is native AWS S3, the custom endpoint flag may not be needed.

Important:
- the bucket must stay private
- browser-facing surfaces must not receive raw object access
- do not share dev and prod credentials
- if the provider is not really S3-compatible, call that out before coding starts because it affects implementation shape

What to record for later:
- provider name
- endpoint
- region
- bucket name
- whether the bucket is private
- whether list or upload checks succeeded

### 5.4 Prepare the Local Verification Access for Hosted Infrastructure

After Postgres and storage exist, verify both from your local machine before any coding starts.

Minimum local verification checklist:

DB:
1. `psql` connects successfully
2. `SELECT 1;` succeeds
3. SSL or network settings are confirmed

Storage:
1. bucket list succeeds
2. test upload succeeds
3. bucket privacy is confirmed

Why this matters:
- Codex can only move quickly later if the hosted services are already reachable from your dev machine
- this prevents losing time during WBS `3` to firewall, SSL, or endpoint surprises

### 5.5 Generate and Store the Real Dev Secrets

The tracked env files are examples only.
Real dev values must stay outside git.

Prepare these real secrets now:
- `FPDS_DATABASE_URL`
- `FPDS_STORAGE_ACCESS_KEY`
- `FPDS_STORAGE_SECRET_KEY`
- `FPDS_ADMIN_SESSION_SECRET`
- `FPDS_ADMIN_CSRF_SECRET`
- `FPDS_CRAWLER_SHARED_SECRET`
- `FPDS_LLM_API_KEY`

PowerShell example for generating random secrets:

```powershell
[Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Maximum 256 }))
```

Run it separately for:
- session secret
- CSRF secret
- crawler shared secret

Where to store them:
- your preferred secret manager, or
- an untracked local env file that never goes into git

Do not:
- paste secrets into chat
- paste secrets into Markdown files
- edit tracked example files with real values
- reuse production credentials in dev

### 5.6 Prepare OpenAI API Access

WBS `3` prototype work will need OpenAI access once extraction and later pipeline steps begin.

What you need to do:
1. confirm the OpenAI account is usable
2. confirm billing is ready
3. create one dev API key
4. store it outside git
5. map it to `FPDS_LLM_API_KEY`

Recommended rule:
- use one dev-specific key
- do not reuse a prod key if you plan to separate environments later

Success criteria:
- the key exists
- you know where it is stored
- you are ready to place it in a local secret source later

### 5.7 Prepare the Untracked Dev Env Source

Because nothing is set up yet, you should prepare one trusted place for the real dev values.

Choose one:
- secret manager only
- untracked local env file only
- secret manager as source of truth plus local untracked env file for local runtime

Recommended local runtime shape for later development:
- app and admin run locally
- API runs locally
- worker runs locally
- Postgres and object storage remain hosted

That means the current localhost origins from `.env.dev.example` are still a good starting point:
- `FPDS_PUBLIC_WEB_ORIGIN=http://localhost:3000`
- `FPDS_ADMIN_WEB_ORIGIN=http://localhost:3001`
- `FPDS_PUBLIC_API_ORIGIN=http://localhost:4000`
- `FPDS_ADMIN_API_ORIGIN=http://localhost:4000`
- `FPDS_INTERNAL_API_ORIGIN=http://localhost:4100`

Minimum real values you should be ready to supply later:
- `FPDS_ENV=dev`
- `FPDS_RUNTIME_LABEL=local-dev`
- `FPDS_DATABASE_URL=...`
- `FPDS_DATABASE_SCHEMA=public`
- `FPDS_VECTOR_BACKEND=pgvector`
- `FPDS_VECTOR_NAMESPACE=fpds-dev`
- `FPDS_OBJECT_STORAGE_DRIVER=s3-compatible`
- `FPDS_OBJECT_STORAGE_ENDPOINT=...`
- `FPDS_OBJECT_STORAGE_REGION=...`
- `FPDS_OBJECT_STORAGE_BUCKET=...`
- `FPDS_OBJECT_STORAGE_PREFIX=dev`
- `FPDS_OBJECT_STORAGE_ACCESS_MODE=private`
- `FPDS_OBJECT_STORAGE_SIGNED_URL_MODE=internal-only`
- `FPDS_SNAPSHOT_OBJECT_PREFIX=snapshots`
- `FPDS_PARSED_OBJECT_PREFIX=parsed`
- `FPDS_PARSER_INTERMEDIATE_PREFIX=intermediate`
- `FPDS_EVIDENCE_PREFIX_ROOT=dev`
- `FPDS_EVIDENCE_RETENTION_CLASS=hot`
- `FPDS_ADMIN_AUTH_MODE=server-session`
- `FPDS_ADMIN_SESSION_SECRET=...`
- `FPDS_ADMIN_CSRF_SECRET=...`
- `FPDS_STORAGE_ACCESS_KEY=...`
- `FPDS_STORAGE_SECRET_KEY=...`
- `FPDS_CRAWLER_SHARED_SECRET=...`
- `FPDS_SOURCE_FETCH_MODE=controlled`
- `FPDS_SOURCE_FETCH_ALLOWLIST=td.com,tdcanadatrust.com`
- `FPDS_SOURCE_FETCH_BLOCK_PRIVATE_NETWORKS=true`
- `FPDS_LLM_PROVIDER=openai`
- `FPDS_LLM_MODEL=gpt-5.4-mini`
- `FPDS_LLM_API_KEY=...`
- `FPDS_BXPF_MODE=mock`
- `FPDS_ALLOWED_PUBLIC_ORIGINS=http://localhost:3000`
- `FPDS_ALLOWED_ADMIN_ORIGINS=http://localhost:3001`
- `FPDS_SECURITY_HEADERS_ENABLED=true`
- `FPDS_COOKIE_SECURE=false`
- `FPDS_COOKIE_SAMESITE=Lax`
- `FPDS_CSRF_PROTECTION_ENABLED=true`
- `FPDS_LOG_LEVEL=debug`
- `FPDS_REQUEST_ID_HEADER=x-request-id`
- `FPDS_MONITORING_PROVIDER=disabled`
- `FPDS_MONITORING_DSN=`

Important:
- `dev monitoring` is already fixed to `disabled`, so you do not need a hosted monitoring project before WBS `3`
- `BX-PF` remains `mock` in dev
- production values remain out of scope for this step

### 5.8 Confirm the Python and Frontend Runtime Split Is Practical

Before coding starts, confirm you are comfortable with this shape:

- browser app and admin: `Next.js App Router`
- API service: `FastAPI`
- worker: separate Python process

What this means operationally:
- frontend and backend may each have their own local start command later
- frontend and backend may each have their own dependency lock files later
- worker failures should not crash the browser runtime

You do not need to create the code or processes now.
You only need to confirm the setup assumptions are acceptable for your local workflow.

### 5.9 Decide What Can Stay Deferred

These are not required before WBS `3`:
- real BX-PF production credentials
- production storage
- production monitoring project
- GitHub deployment secrets
- production domains
- release promotion policy
- Phase 1 deployment automation

These belong to later work, not prototype start readiness.

---

## 6. Final Readiness Checklist

Mark each row `yes` or `no`.

| Check | Yes or No |
|---|---|
| Python 3.12 installed locally | yes (Python 3.14.3 is installed) |
| `uv` installed locally | yes (uv 0.11.3)|
| Node.js LTS installed locally | yes (v24.13.0) |
| `pnpm` installed locally | yes (10.33.0) |
| `psql` installed locally | yes (18.3) |
| hosted dev Postgres provisioned | yes (supabase) |
| hosted dev Postgres reachable from local machine | yes |
| hosted dev object storage provisioned | yes (aws s3) |
| hosted dev object storage is private | yes |
| hosted dev object storage reachable from local machine | yes |
| real dev secrets stored outside git | yes |
| OpenAI dev API key ready | yes |
| untracked local dev env source prepared | yes |
| `dev monitoring = disabled` confirmed | yes |
| Codex may later create or use untracked local env files during development | yes |

You are practically ready for WBS `3` only when the critical rows above are `yes`.

---

## 7. What To Send Back To Codex

Once you finish the checklist, send a compact message like this:

```md
- runtime baseline accepted: yes
- Python 3.12 installed: yes | no
- uv installed: yes | no
- Node LTS installed: yes | no
- pnpm installed: yes | no
- psql installed: yes | no
- hosted dev Postgres ready: yes | no
- hosted dev Postgres reachable locally: yes | no
- hosted dev object storage ready: yes | no
- hosted dev object storage reachable locally: yes | no
- OpenAI API key ready: yes | no
- untracked local dev env source ready: yes | no
- Codex may create or use untracked env files later: yes | no
```

Do not paste real secrets into chat.
Only report readiness and decisions.

---

## 8. Notes Before WBS 3 Starts

Before WBS `3` begins, remember:
- this guide is a preparation checklist, not a start instruction
- actual development should still wait for explicit Product Owner go
- the hosted dev database and storage should exist before prototype coding starts
- the baseline migration should be applied only when you are ready to let implementation begin
- Codex should not start implementation while hosted dev infra and local tools are still incomplete

---

## 9. Change History

| Date | Change |
|---|---|
| 2026-04-07 | Initial pre-development owner preparation guide created after WBS 2 review |
| 2026-04-07 | Rewritten as a clean hosted-dev preparation guide with step-by-step owner actions |
| 2026-04-07 | Rewritten again after the runtime stack was fixed to Next.js App Router, FastAPI, separate Python worker, pnpm, uv, server-side session auth, and disabled dev monitoring |
| 2026-04-09 | Recorded the completed owner readiness checklist response and corrected the checklist typo |
