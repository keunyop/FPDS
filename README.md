# FPDS Workspace

This repository is the docs-first workspace for `FPDS` (Finance Product Data Service), the evidence-grounded financial product data platform that will later support MyBank-facing experiences.

The repository is currently `product-implementation-in-progress`.

As of `2026-04-12`:
- `Gate A` passed on `2026-04-06`
- `Gate B` passed on `2026-04-11`
- `WBS 2` foundation scaffolds and baseline artifacts are complete
- `WBS 3.1` source discovery is complete
- `WBS 3.2` snapshot capture and persistence are complete
- `WBS 3.3` parsing/chunking is complete with live dev verification and parsed-document reuse verification
- `WBS 3.4` evidence retrieval is complete with metadata-only live verification and vector-assisted fallback behavior verification
- `WBS 3.5` extraction flow is complete with extracted-draft artifacts, `model_execution` and zero-token heuristic usage persistence, and unit verification
- `WBS 3.6` normalization mapping is complete with `normalized_candidate`, `field_evidence_link`, and live dev verification
- `WBS 3.7` validation/confidence routing is complete with candidate revalidation, `review_task` creation, and live dev verification
- `WBS 3.8` internal result viewer is complete as a static prototype viewer plus live-exportable viewer payload
- `WBS 3.9` first end-to-end run is complete with a committed evidence pack and live viewer export for the three TD savings target products
- `WBS 3.10` prototype findings memo is complete, and its original Gate B `Deferred` recommendation has now been overtaken by three post-memo hardening slices plus an approved Gate B review note
- a first post-`3.10` hardening slice is complete: normalization now supplements missing TD savings rate fields from the `TD-SAV-005` current-rates source, and a live hardening run moved all three target candidates from `validation_error` to `validation_status=pass`
- a second post-`3.10` hardening slice is complete: normalization now selectively reuses `TD-SAV-008` governing-PDF interest rules, has an opportunistic `TD-SAV-007` fee-waiver merge hook, splits `TD Growth` boosted-rate qualification into cleaner canonical fields, and suppresses several noisy long-text fields before candidate persistence
- a third post-`3.10` hardening slice is complete: `TD-SAV-007` fee-governing evidence is now used in a live target-safe way to suppress noisy `fee_waiver_condition` fields for zero-monthly-fee TD savings products instead of persisting misleading waiver text
- `WBS 4.1` admin login is now complete with a DB-backed operator account table, DB-backed session table, FastAPI auth routes, a bootstrap-admin CLI, and a protected Next.js admin entry shell
- the live admin runtime now uses a Shadcnblocks-based FPDS admin UI foundation with a compact shell, operator login, and redesigned protected overview

## What This Repo Contains Today

- requirements, scope, planning, governance, and design documents
- foundation baselines for env, DB, storage, auth, i18n, security, observability, and route manifests
- shared design-system baseline artifacts and template-adoption guidance for future public and admin UI implementation
- a minimal Python worker project baseline in `pyproject.toml`
- working prototype ingestion code for discovery, preflight drift checks, scheduled registry refresh artifacts, snapshot capture, parse/chunk, and evidence retrieval stages
- working prototype extraction code that turns retrieval matches into sparse extracted drafts with evidence-link drafts
- working prototype normalization code that maps extracted drafts into canonical candidate rows and candidate-level evidence links
- working prototype validation/routing code that recomputes candidate validation, updates candidate state, and creates prototype review tasks
- working prototype result-viewer export code and a static prototype viewer shell for read-only inspection
- a first live `FastAPI` admin service package under `api/service/` for DB-backed admin auth and session handling
- a first live `Next.js` admin package under `app/admin/` with `/admin/login`, protected `/admin`, and session-aware route gating
- a Shadcnblocks-based admin UI implementation that keeps the live shell aligned to the FPDS benchmark while leaving future review, run, publish, usage, and health surfaces route-oriented
- a committed first successful run evidence pack with raw stage outputs and live viewer artifacts
- a committed prototype findings memo that summarizes feasibility, open quality gaps, and pre-Big-5 recommendations
- a first hardening baseline that merges product-matched current-rate evidence into TD savings normalization when supporting extraction artifacts are available
- a second hardening baseline that selectively merges governing-PDF interest rules, cleans noisy text, and separates `TD Growth` qualification logic in normalization
- a third hardening baseline that uses `TD-SAV-007` to keep zero-fee savings candidates from carrying misleading fee-waiver text
- repository harness scripts, git hooks, and CI validation
- top-level boundaries for future `app`, `api`, `worker`, `shared`, `db`, and `storage` work

This is still not a full FPDS product yet, but the ingestion core is now actively being implemented.

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
- `WBS 3.1` to `3.4` have runnable code and verification records in-repo
- `WBS 3.5` extraction now has runnable code and unit verification records in-repo
- `WBS 3.6` normalization now has runnable code and live dev verification records in-repo
- `WBS 3.7` validation and routing now has runnable code and live dev verification records in-repo
- `WBS 3.8` prototype viewer now has runnable export code and a browser-viewable static shell in-repo
- `WBS 3.9` now has a live first end-to-end evidence pack in-repo for the three prototype target products
- `WBS 3.10` now has a written findings memo, and three follow-up hardening slices have already cleared the original `required_field_missing` validation gap, added selective `TD-SAV-008` PDF merge, improved `TD Growth` qualification cleanup, and removed misleading zero-fee `fee_waiver_condition` fields using `TD-SAV-007` evidence in live reruns
- Gate B is now closed as `Pass`
- `WBS 4.1` admin login is now implemented and gives the admin surface its first real runtime bootstrap
- discovery preflight drift checks and scheduled refresh artifact generation are now available under `worker/discovery/`
- the Python worker baseline and parser dependencies are now tracked in `pyproject.toml`
- the first FastAPI admin service baseline is now tracked in `api/service/pyproject.toml`
- the first Next.js admin package baseline is now tracked in `app/admin/package.json`

### In Progress

- prototype worker runtime implementation
- `WBS 4` admin and ops runtime bootstrap beyond login

### Not Started

- full public UI, the remaining admin surfaces after login, and review decision runtime code
- BX-PF runtime integration code
- public frontend package bootstrap

### Hold Rule

The Product Owner has explicitly started WBS `3` product implementation.

Scope still remains constrained to the approved prototype boundary:
- `TD Bank`
- `Savings Accounts`
- ingestion and reviewability-first slices before broader public or admin build-out

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

These remain the approved baselines for the broader runtime.
Current implementation evidence is still heaviest in the Python worker path, but the first live admin frontend and API packages now exist as well.

## Foundation Baselines In Repo

- env contract: [docs/03-design/dev-prod-environment-spec.md](docs/03-design/dev-prod-environment-spec.md)
- design-system baseline: [docs/03-design/fpds-design-system.md](docs/03-design/fpds-design-system.md)
- Stripe benchmark + template-first baseline: [docs/03-design/fpds_design_system_stripe_benchmark.md](docs/03-design/fpds_design_system_stripe_benchmark.md)
- env examples: `.env.dev.example`, `.env.prod.example`
- config landing zone: [shared/config/README.md](shared/config/README.md)
- design landing zone: [shared/design/README.md](shared/design/README.md)
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
- JavaScript package checks are `pnpm-first`, and the shared project-check entrypoint installs missing dependencies when a tracked package has no local `node_modules`
- CI remains validation-only and does not imply product implementation has started
- cleanup audit is intentionally `report-only`

## Current Top-Level Layout

- `app/` browser-facing public, admin, and prototype viewer boundaries
- `api/` public, admin, and internal API boundaries
- `db/` SQL-first migration baseline and DB notes
- `storage/` object storage and evidence bucket baseline
- `worker/` discovery, pipeline, publish, and runtime worker boundaries
- `shared/` contracts, config, design, domain, i18n, observability, and security modules
- `docs/` requirements, governance, planning, and design
- `scripts/harness/` repository checks, audits, and helper scripts
- `.githooks/` git hook entrypoints
- `.github/workflows/` CI validation workflows
