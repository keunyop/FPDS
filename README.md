# FPDS Workspace

This repository is the docs-first workspace for `FPDS` (Finance Product Data Service), the evidence-grounded financial product data platform that will later support MyBank-facing experiences.

The repository is currently `execution-ready`, not `product-implementation-in-progress`.

As of `2026-04-09`:
- `Gate A` passed on `2026-04-06`
- `WBS 2` foundation scaffolds and baseline artifacts are recorded as complete
- local toolchain and hosted dev readiness were recorded on `2026-04-09`
- actual `WBS 3` product implementation has not started and remains on hold until the Product Owner gives an explicit start instruction

## What This Repo Contains Today

- requirements, scope, planning, governance, and design documents
- foundation baselines for env, DB, storage, auth, i18n, security, observability, and route manifests
- repository harness scripts, git hooks, and CI validation
- top-level boundaries for future `app`, `api`, `worker`, `shared`, `db`, and `storage` work

This is intentionally not a running FPDS product yet.

## Start Here

- docs map: [docs/README.md](docs/README.md)
- requirements baseline: [docs/02-requirements/FPDS_Requirements_Definition_v1_5.md](docs/02-requirements/FPDS_Requirements_Definition_v1_5.md)
- execution plan: [docs/01-planning/plan.md](docs/01-planning/plan.md)
- WBS: [docs/01-planning/WBS.md](docs/01-planning/WBS.md)
- working agreement: [docs/00-governance/working-agreement.md](docs/00-governance/working-agreement.md)
- Gate A review note: [docs/00-governance/gate-a-build-start-review-note.md](docs/00-governance/gate-a-build-start-review-note.md)
- decision log: [docs/00-governance/decision-log.md](docs/00-governance/decision-log.md)
- development journal: [docs/00-governance/development-journal.md](docs/00-governance/development-journal.md)
- owner readiness guide: [docs/00-governance/pre-development-owner-preparation-guide.md](docs/00-governance/pre-development-owner-preparation-guide.md)

## Delivery Boundary

- `Prototype`: `TD Bank` plus `Savings Accounts` end-to-end feasibility validation
- `Phase 1`: Canada Big 5 deposit-product data platform plus public product grid, insight dashboard, admin console, BX-PF connector readiness, and EN/KO/JA UI
- `Phase 2`: Japan Big 5 expansion plus external SaaS or Open API

Out of scope for the current FPDS build:
- personalized recommendation
- consumer banking features
- public evidence trace exposure
- billing or subscription
- broad expansion beyond the approved country and product cutline

## Current Status Snapshot

### Ready

- Gate A document package is closed
- `WBS 2.1` to `2.10` foundation work is tracked as complete
- approved runtime and toolchain baselines are documented
- local tools are available: `uv`, `pnpm`, `psql`, `aws`
- hosted dev readiness and real dev secret preparation are recorded

### Not Started

- `WBS 3` prototype runtime work
- runtime package bootstrap
- DB migration apply on the real dev database
- snapshot capture, parsing, chunking, extraction, normalization, review flow, public UI, admin UI, and BX-PF runtime integration code

### Hold Rule

`Gate A Pass` means readiness only.
It does not mean development has already started.

Implementation still waits for:
- explicit Product Owner start instruction

## Approved Technical Baseline

- primary product language: `Python`
- browser-facing frontend language: `TypeScript`
- frontend runtime baseline: `Next.js App Router`
- API runtime baseline: `FastAPI` as a separate service
- worker baseline: separate `Python worker process`
- frontend package manager: `pnpm`
- Python package and runtime manager: `uv`
- admin auth approach: server-side session auth managed by the Python API
- dev monitoring baseline: `disabled` for the first implementation pass

These are approved baselines for future implementation.
They should not be read as evidence that the runtime has already been bootstrapped in this repo.

## Foundation Baselines In Repo

- env contract: [docs/03-design/dev-prod-environment-spec.md](docs/03-design/dev-prod-environment-spec.md)
- env examples: `.env.dev.example`, `.env.prod.example`
- config landing zone: [shared/config/README.md](shared/config/README.md)
- DB baseline: [docs/03-design/db-migration-baseline.md](docs/03-design/db-migration-baseline.md)
- DB entrypoint: [db/README.md](db/README.md)
- storage baseline: [docs/03-design/object-storage-evidence-bucket-baseline.md](docs/03-design/object-storage-evidence-bucket-baseline.md)
- storage entrypoint: [storage/README.md](storage/README.md)
- auth and security baseline: [shared/security/README.md](shared/security/README.md)
- i18n baseline: [shared/i18n/README.md](shared/i18n/README.md)
- observability baseline: [shared/observability/README.md](shared/observability/README.md)
- public route manifest: [app/public/routes.manifest.json](app/public/routes.manifest.json)
- admin route manifest: [app/admin/routes.manifest.json](app/admin/routes.manifest.json)

Rules:
- only placeholder values are committed
- real secrets stay out of git
- `dev` is the current local development shape
- `BX-PF` remains `mock` in `dev` and real write-back is `prod` only
- browser-facing surfaces must not receive direct private object access

## Local Toolchain

Expected local tools:
- `uv`
- `pnpm`
- `psql`
- `aws`

Notes:
- `psql` is installed as PostgreSQL command-line tools only. A local Postgres server is not part of the repo baseline.
- if a new tool is not visible in the current shell, restart the terminal so `PATH` reloads cleanly

## Harness Commands

Install Git hooks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/install-hooks.ps1
```

Run repository health checks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1
```

Run the full foundation baseline checks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1
```

Run the report-only cleanup audit:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1
```

Optional future project-wide checks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-project-checks.ps1
```

## What The Harness Does

- `pre-commit` only inspects staged files
- the hook can auto-fix low-risk text hygiene issues
- staged Markdown references and staged PowerShell syntax are validated
- foundation checks validate env examples, JSON artifacts, observability artifacts, and future package-script baselines
- CI remains validation-only and does not imply product implementation has started
- cleanup audit is intentionally `report-only`

## Current Top-Level Layout

- `app/` browser-facing public, admin, and prototype viewer boundaries
- `api/` public, admin, and internal API boundaries
- `db/` SQL-first migration baseline and DB notes
- `storage/` object storage and evidence bucket baseline
- `worker/` discovery, pipeline, publish, and runtime worker boundaries
- `shared/` contracts, config, domain, i18n, observability, and security modules
- `docs/` requirements, governance, planning, and design
- `scripts/harness/` repository checks, audits, and helper scripts
- `.githooks/` git hook entrypoints
- `.github/workflows/` CI validation workflows
