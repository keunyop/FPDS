# FPDS Workspace

This repository is the docs-first workspace for `FPDS` (Finance Product Data Service), the evidence-grounded financial product data platform that will later support MyBank-facing experiences.

The repository is currently `product-implementation-in-progress`.

As of `2026-04-15`:
- `Gate A` passed on `2026-04-06`
- `Gate B` passed on `2026-04-11`
- `Gate C` passed on `2026-04-13`
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
- `WBS 4.1` admin auth is now complete with a DB-backed operator account table, DB-backed session table, FastAPI auth routes, a bootstrap-admin CLI, approval-gated signup requests, and a protected Next.js admin entry shell
- `WBS 4.2` review queue is now complete with a session-protected review-task list API, a protected `/admin/reviews` queue route, active-state defaults, search, filters, sorting, and stable drill-in links
- `WBS 4.3` review decision flow is now complete with review-task detail read APIs, approve/reject/defer/edit-approve mutations, canonical product/version side effects, review/change audit emission, and a live `/admin/reviews/:reviewTaskId` decision surface with override diff preview
- `WBS 4.4` evidence trace viewer is now complete with field-selectable trace drilldown, enriched evidence metadata, parsed mapping context, and model-run references on the live `/admin/reviews/:reviewTaskId` route
- `WBS 4.5` run status is now complete with session-protected run list/detail APIs, protected `/admin/runs` and `/admin/runs/:runId` routes, run-level error summary, source processing summary, related review-task links, and usage summary
- `WBS 4.6` change history is now complete with a session-protected change-history API, a protected `/admin/changes` route, canonical event chronology, changed-field summaries, review/run drilldowns, and manual-override audit context
- `WBS 4.7` audit log baseline is now complete with a session-protected audit-log API, a protected `/admin/audit` route, append-only review/auth/trace history, and review/run drilldowns
- `WBS 4.8` LLM usage tracking is now complete with a session-protected usage dashboard API, time-range and scope filters, totals, per-model, per-agent, per-run, and trend aggregations, and anomaly drilldown candidates
- `WBS 4.9` usage dashboard v1 is now complete with provider/stage/search filters, richer scope coverage signals, concentration shares, trend deltas, and denser anomaly drilldown context on `/admin/usage`
- `WBS 4.10` operational scenario QA is now complete with automated review-to-history verification across review decision, change history, audit log, and run detail linkage, plus refreshed admin typecheck and production build evidence
- `WBS 5.1` Big 5 source registry is now complete with a committed Canada Big 5 registry catalog and per-bank `chequing`, `savings`, and `gic` source baselines
- `WBS 5.2` chequing parser expansion is now complete with catalog-backed source-id resolution across the Big 5 registries, chequing-specific extraction fields, schema-aligned chequing subtype normalization, and unit verification
- `WBS 5.3` savings parser expansion is now complete with savings-specific retrieval hints, extraction coverage for tiering or withdrawal or registered fields, and unit verification
- `WBS 5.4` GIC or term parser expansion is now complete with GIC-specific extraction fields, normalization-time term and cross-field validation alignment, and unit verification
- `WBS 5.6` aggregate dataset generation is now complete with persisted aggregate refresh snapshots plus projection, metric, ranking, and scatter source datasets for the approved public vocabulary
- `WBS 5.7` public products API is now complete with anonymous `/api/public/products` and `/api/public/filters` routes backed by the latest successful aggregate projection snapshot, shared filter vocabulary, sort options, pagination, localized labels, and freshness metadata
- `WBS 5.8` dashboard APIs are now complete with anonymous `/api/public/dashboard-summary`, `/api/public/dashboard-rankings`, and `/api/public/dashboard-scatter` routes that reuse the latest successful aggregate projection snapshot for request-time filtered summary, ranking, and scatter responses plus methodology and freshness context
- `WBS 5.9` Product Grid UI is now complete with a live Next.js public package, a `/products` catalog route, sticky public filters, result-summary chips, product-type-aware cards, and pagination
- `WBS 5.10` Insight Dashboard UI is now complete with a live `/dashboard` route, KPI cards, ranking widgets, a comparative scatter view, and query-preserved sibling navigation back to `/products`
- `WBS 5.11` grid/dashboard cross-filter is now complete with URL-based shared-scope sibling navigation plus dashboard drill-in links back into the Product Grid from breakdowns, rankings, and scatter points
- `WBS 5.12` locale rollout is now complete with EN/KO/JA query-param locale support across the public Product Grid and Insight Dashboard plus the protected admin shell and login surfaces
- `WBS 5.13` freshness/metric note wording is now complete with locale-aware public methodology/freshness note cards on `/products`, richer dashboard methodology wording on `/dashboard`, and clarified snapshot/metric/exclusion messaging for the public surface
- `WBS 5.15` source registry admin MVP is now complete with DB-backed bank and source-catalog management, source-detail generation during collection, a bank-centered `/admin/banks` workflow for bank setup plus initial coverage and bulk collection, compatibility redirects for `/admin/source-catalog`, and read-only `/admin/sources` operator routes
- the first vector-assisted retrieval bootstrap is now implemented with a pgvector `evidence_chunk_embedding` side table, deterministic local evidence-chunk embeddings for dev/test, metadata-first vector ranking, and metadata-only fallback when vector rows are unavailable
- the live admin runtime now uses a Shadcnblocks-based FPDS admin UI foundation with a compact shell, operator login, redesigned protected overview, live run diagnostics, canonical change chronology, append-only audit history, and a protected usage observability route

## What This Repo Contains Today

- requirements, scope, planning, governance, and design documents
- foundation baselines for env, DB, storage, auth, i18n, security, observability, and route manifests
- shared design-system baseline artifacts and template-adoption guidance for future public and admin UI implementation
- a minimal Python worker project baseline in `pyproject.toml`
- working prototype ingestion code for discovery, preflight drift checks, scheduled registry refresh artifacts, snapshot capture, parse/chunk, and evidence retrieval stages
- a pgvector-ready evidence retrieval bootstrap that keeps vector scope limited to `evidence_chunk` and preserves metadata-only fallback
- working prototype extraction code that turns retrieval matches into sparse extracted drafts with evidence-link drafts
- working prototype normalization code that maps extracted drafts into canonical candidate rows and candidate-level evidence links
- working prototype validation/routing code that recomputes candidate validation, updates candidate state, and creates prototype review tasks
- working prototype result-viewer export code and a static prototype viewer shell for read-only inspection
- a first live `FastAPI` admin service package under `api/service/` for DB-backed admin auth, session handling, and approval-gated signup requests
- a first live `Next.js` admin package under `app/admin/` with `/admin/login`, `/admin/signup`, protected `/admin`, and session-aware route gating
- a first live `Next.js` public package under `app/public/` with `/products` for the public Product Grid and `/dashboard` for the public Insight Dashboard
- a live review-queue, decision, and trace runtime slice with `GET /api/admin/review-tasks`, `GET /api/admin/review-tasks/:reviewTaskId`, protected `/admin/reviews`, and a protected `/admin/reviews/:reviewTaskId` decision-plus-trace surface
- a live run-status runtime slice with `GET /api/admin/runs`, `GET /api/admin/runs/:runId`, protected `/admin/runs`, and a protected `/admin/runs/:runId` diagnostic surface
- a live change-history runtime slice with `GET /api/admin/change-history` and a protected `/admin/changes` chronology surface
- a live audit-log runtime slice with `GET /api/admin/audit-log` and a protected `/admin/audit` append-only chronology surface
- a live LLM usage runtime slice with `GET /api/admin/llm-usage` and a dashboard-shaped usage aggregation response for totals, model, agent, run, and anomaly drilldown analysis
- a live public aggregate runtime slice with `GET /api/public/products`, `GET /api/public/filters`, `GET /api/public/dashboard-summary`, `GET /api/public/dashboard-rankings`, and `GET /api/public/dashboard-scatter` backed by `aggregate_refresh_run` plus `public_product_projection`
- a completed usage dashboard v1 surface on `/admin/usage` with provider/stage/search scoping, operational coverage summaries, concentration hotspots, trend delta signals, and richer anomaly triage context
- a completed dashboard health surface on `/admin/health/dashboard` with aggregate freshness, queue visibility, serving fallback, stale or failed state signals, and operator retry
- a completed source registry admin MVP surface with `/admin/banks` for bank setup, initial bank coverage, bank-list bulk collection, per-bank coverage collection, compatibility redirects for the older `/admin/source-catalog` entry points, and read-only `/admin/sources` plus `/admin/sources/:sourceId` for generated source detail inspection
- a Shadcnblocks-based admin UI implementation that keeps the live shell aligned to the FPDS benchmark while leaving future publish surfaces route-oriented
- a committed first successful run evidence pack with raw stage outputs and live viewer artifacts
- a committed prototype findings memo that summarizes feasibility, open quality gaps, and pre-Big-5 recommendations
- a first hardening baseline that merges product-matched current-rate evidence into TD savings normalization when supporting extraction artifacts are available
- a second hardening baseline that selectively merges governing-PDF interest rules, cleans noisy text, and separates `TD Growth` qualification logic in normalization
- a third hardening baseline that uses `TD-SAV-007` to keep zero-fee savings candidates from carrying misleading fee-waiver text
- deposit parser baselines for `chequing`, `savings`, and `gic` that now extract product-type-specific fields such as transaction bundles, savings tiering or withdrawal rules, and GIC term or redeemability signals while normalizing subtype behavior to the approved canonical taxonomy
- an aggregate refresh worker slice that builds `public_product_projection` plus dashboard metric, ranking, and scatter source datasets from the canonical product baseline
- repository harness scripts, git hooks, and CI validation
- top-level boundaries for future `app`, `api`, `worker`, `shared`, `db`, and `storage` work

This is still not a full FPDS product yet, but the ingestion core is now actively being implemented.

## Start Here

- docs map: [docs/README.md](docs/README.md)
- development journal: [docs/00-governance/development-journal.md](docs/00-governance/development-journal.md)
- requirements baseline: [docs/02-requirements/FPDS_Requirements_Definition_v1_5.md](docs/02-requirements/FPDS_Requirements_Definition_v1_5.md)
- scope baseline: [docs/02-requirements/scope-baseline.md](docs/02-requirements/scope-baseline.md)
- execution plan: [docs/01-planning/plan.md](docs/01-planning/plan.md)
- WBS: [docs/01-planning/WBS.md](docs/01-planning/WBS.md)
- working agreement: [docs/00-governance/working-agreement.md](docs/00-governance/working-agreement.md)
- decision log: [docs/00-governance/decision-log.md](docs/00-governance/decision-log.md)
- RAID log: [docs/00-governance/raid-log.md](docs/00-governance/raid-log.md)
- Canada Big 5 source registry baseline: [docs/01-planning/canada-big5-source-registry.md](docs/01-planning/canada-big5-source-registry.md)
- design docs index: [docs/03-design/README.md](docs/03-design/README.md)
- archive index: [docs/archive/README.md](docs/archive/README.md)

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
- `WBS 4.1` admin auth is now implemented and gives the admin surface its first real runtime bootstrap plus approval-gated operator onboarding
- `WBS 4.2` review queue is now implemented and gives the admin surface its first live reviewer intake route
- `WBS 4.3` review decision flow is now implemented and lets operators complete approve/reject/defer/edit-approve actions against persisted review tasks
- `WBS 4.4` evidence trace viewer is now implemented and lets operators focus a field, inspect linked evidence, and review model-stage context on the same detail route
- `WBS 4.5` run status is now implemented and gives operators a live `/admin/runs` list plus `/admin/runs/:runId` diagnostic detail route
- `WBS 4.6` change history is now implemented and gives operators a live `/admin/changes` chronology route with review/run context and manual-override audit context
- `WBS 4.7` audit log baseline is now implemented and gives operators a live `/admin/audit` chronology route with actor, target, request, and review/run context
- `WBS 4.8` LLM usage tracking is now implemented and gives operators a live `/admin/usage` dashboard API plus protected usage analysis route
- `WBS 4.9` usage dashboard v1 is now implemented and adds richer provider or stage scoping, concentration summaries, and anomaly drilldowns on `/admin/usage`
- `WBS 4.10` operational scenario QA is now implemented and gives the repo a concrete Gate C QA artifact for the review-to-history operator path
- `WBS 5.7` public products API is now implemented and gives the repo live anonymous `/api/public/products` and `/api/public/filters` endpoints with shared public filter vocabulary, pagination, sort support, localized labels, and snapshot freshness metadata
- `WBS 5.8` dashboard APIs are now implemented and give the repo live anonymous `/api/public/dashboard-summary`, `/api/public/dashboard-rankings`, and `/api/public/dashboard-scatter` endpoints with request-time filtered summary, ranking, and scatter responses derived from the latest successful public aggregate snapshot
- `WBS 5.9` Product Grid UI is now implemented and gives the repo a live `app/public` Next.js package with `/products`, shared public filters, type-aware product cards, and pagination
- `WBS 5.10` Insight Dashboard UI is now implemented and gives the repo a live `/dashboard` route with KPI cards, ranking widgets, a product-type-aware comparative chart, methodology/freshness notes, and sibling navigation that preserves public query scope
- `WBS 5.11` grid/dashboard cross-filter is now implemented and gives the repo scope-preserving public sibling nav plus dashboard-to-grid drill-in links for breakdown, ranking, and scatter views
- `WBS 5.12` locale rollout is now implemented and gives the repo EN/KO/JA locale-aware public and admin shells with query-preserved locale switching, locale-aware labels, and locale-aware date or number formatting for UI-owned copy
- `WBS 5.13` freshness/metric note wording is now implemented and gives the repo locale-aware public methodology/freshness note cards plus clearer dashboard note wording for snapshot timing, metric semantics, exclusion rules, and public evidence non-exposure
- `WBS 5.15` source registry admin MVP is now implemented and gives the repo a live DB-backed bank and source-catalog flow with `/admin/banks` as the primary operator surface for both bank setup and coverage management, compatibility redirects for `/admin/source-catalog`, read-only `/admin/sources`, `GET/POST/PATCH /api/admin/banks`, `GET/POST/PATCH /api/admin/source-catalog`, and `POST /api/admin/source-catalog/collect`
- `WBS 5.16` dynamic product type onboarding is now implemented for the admin and collection pipeline: `/admin/product-types` now manages operator-defined product types, bank coverage pickers are registry-driven, homepage-first discovery uses stored product type definitions, hybrid candidate scoring, and page-level evidence validation, and dynamic product types flow through generic AI extraction plus normalization fallback into manual review instead of public publish
- discovery preflight drift checks and scheduled refresh artifact generation are now available under `worker/discovery/`
- the Python worker baseline and parser dependencies are now tracked in `pyproject.toml`
- the first FastAPI admin service baseline is now tracked in `api/service/pyproject.toml`
- the first Next.js admin package baseline is now tracked in `app/admin/package.json`
- the first Next.js public package baseline is now tracked in `app/public/package.json`

### In Progress

- prototype worker runtime implementation
- `WBS 5` public experience work and Big 5 expansion slices
- responsive QA follow-on slices

### Not Started

- later admin follow-on surfaces such as publish monitor and health
- BX-PF runtime integration code

### Hold Rule

The Product Owner has explicitly started WBS `5` product implementation.

Scope now includes the approved post-prototype path through `WBS 5.4`:
- Canada Big 5 source-registry baseline
- continued evidence-first expansion for `chequing`, `savings`, and `gic`
- completed parser baselines for `chequing`, `savings`, and `gic` across the worker stages using the approved registry catalog
- completed aggregate source dataset generation for the public grid and dashboard backing stores
- public-experience follow-on slices only within the approved Phase 1 cutline

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
- frontend benchmark baseline: [docs/03-design/fpds_design_system_stripe_benchmark.md](docs/03-design/fpds_design_system_stripe_benchmark.md)
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
