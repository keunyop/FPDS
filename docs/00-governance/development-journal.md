# FPDS Development Journal

Version: 1.1
Date: 2026-04-07
Status: Active
Source Documents:
- `docs/00-governance/working-agreement.md`
- `docs/00-governance/harness-engineering-baseline.md`
- `docs/01-planning/WBS.md`
- `docs/02-requirements/scope-baseline.md`

---

## 1. Purpose

This document is the repository memory for implementation work.

Goals:
- let the next Codex session resume from the latest completed slice without rereading the whole codebase
- give the Product Owner a compact record of what changed, how it was verified, and what still remains
- keep handoff inside the repo instead of depending on chat history

This is not a full changelog. It records only the minimum context needed to continue safely.

---

## 2. When To Update

Add an entry when one of these happens:
- one meaningful WBS subtask is completed
- user-visible or operator-visible behavior changes
- an important local decision is locked in for future work
- the next slice depends on context that would otherwise be easy to lose

Do not add an entry for:
- typo-only documentation cleanup
- purely mechanical rename work
- failed experiments that were fully reverted

---

## 3. What Must Be Recorded

Each entry should include:
- date
- slice title and related WBS
- status: `done`, `partial`, or `blocked`
- why the slice was done now
- what changed
- what was intentionally not done
- key files
- decisions and constraints
- verification commands and results
- known issues
- the next natural step

---

## 4. Writing Rules

- Keep entries short and operational.
- Prefer outcome, risk, and next-step clarity over diff-level detail.
- Record only commands that were actually run.
- Separate facts from assumptions.
- End with one concrete next step.

---

## 5. Entry Template

```md
## YYYY-MM-DD - Slice Title

- WBS: `x.y`
- Status: `done | partial | blocked`
- Goal: short goal
- Why now: why this slice was the right next step
- Outcome: what changed in the product or repo
- Not done: what was intentionally left for follow-on work
- Key files: `path/a`, `path/b`
- Decisions: local decisions and constraints that future work must respect
- Verification:
  - `command`
  - result
- Known issues: remaining risk or gap
- Next step: one concrete next action
```

---

## 6. Entries

## 2026-04-07 - WBS 2.1 Repo Skeleton

- WBS: `2.1`
- Status: `done`
- Goal: create a vendor-neutral repository skeleton so WBS `2.2` to `2.10` and WBS `3.x` can start without reworking boundaries later
- Why now: foundation work needed stable app, api, worker, and shared boundaries before environment, DB, auth, storage, and route scaffolds could begin
- Outcome: added top-level `app/`, `api/`, `worker/`, and `shared/` directories plus README files that define each boundary. Split `app` into `public`, `admin`, `prototype`; `api` into `public`, `admin`, `internal`; `worker` into `discovery`, `pipeline`, `publish`, `runtime`; and `shared` into `config`, `contracts`, `domain`, `i18n`, `observability`, `security`
- Not done: no framework choice, route implementation, API handlers, worker code, DB migration, or env wiring yet
- Key files: `app/README.md`, `api/README.md`, `worker/README.md`, `shared/README.md`, `README.md`, `docs/01-planning/WBS.md`
- Decisions: kept the skeleton aligned to the public/admin/api/worker/shared boundaries from the docs without committing to a runtime framework. Kept `app/prototype` separate from the full admin area to preserve the narrower prototype scope
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1 -ReportPath harness-cleanup-audit.md`
  - passed with no findings
- Known issues: package manager and framework are still not selected, so project-wide build scripts remain inactive
- Next step: complete `WBS 2.2` environment separation and env template setup

## 2026-04-07 - WBS 2.2 Dev and Prod Env Templates

- WBS: `2.2`
- Status: `done`
- Goal: turn the approved `dev/prod` separation strategy into tracked example files and a concrete minimum config contract for upcoming scaffold work
- Why now: `2.3`, `2.4`, `2.5`, `2.7`, and `2.8` all depend on a stable answer for environment shape, secret boundaries, origins, and integration modes
- Outcome: added `.env.dev.example` and `.env.prod.example`, documented the minimum config contract in `docs/03-design/dev-prod-environment-spec.md`, expanded `shared/config/README.md`, updated the repo README, and marked `WBS 2.2` complete
- Not done: no real secrets, real domains, real database hosts, storage lifecycle rules, or real BX-PF credentials were added
- Key files: `.env.dev.example`, `.env.prod.example`, `docs/03-design/dev-prod-environment-spec.md`, `shared/config/README.md`, `.gitignore`, `docs/01-planning/WBS.md`
- Decisions: kept the model at exactly two environments, `dev` and `prod`. Treated local development as `dev`. Set `dev` to `mock` BX-PF mode and `prod` to `live` intent. Kept all real values as placeholders and added git ignore rules so future real env files stay untracked
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1 -ReportPath harness-cleanup-audit.md`
  - passed with no findings
- Known issues: framework-specific env loading is still not implemented, so these files are the contract and documentation baseline rather than active runtime wiring
- Next step: complete `WBS 2.3` database and migration baseline against the new env contract

## 2026-04-07 - WBS 2.3 DB and Migration Baseline

- WBS: `2.3`
- Status: `done`
- Goal: create a first database and migration baseline that can support prototype ingestion, reviewability, canonical history, publish tracking, usage, and audit without blocking on a framework choice
- Why now: prototype foundation tasks need stable storage boundaries before source discovery, snapshot persistence, chunking, candidate generation, and review routing can be implemented safely
- Outcome: added a SQL-first Postgres migration baseline in `db/migrations/0001_initial_baseline.sql`, documented the decision in `docs/03-design/db-migration-baseline.md`, added `db/README.md`, and marked `WBS 2.3` complete
- Not done: the migration was not executed against a live database, `pgvector` was intentionally deferred, and auth-vendor/dashboard-specific tables remain follow-on work
- Key files: `db/migrations/0001_initial_baseline.sql`, `db/README.md`, `docs/03-design/db-migration-baseline.md`, `docs/01-planning/WBS.md`, `README.md`
- Decisions: chose `Postgres + plain SQL` as the baseline and kept ids as application-generated `text` for now. Kept filter-heavy fields relational and flexible canonical or candidate details in `jsonb`. Seeded Canada Big 5 bank codes, taxonomy registry rows, and routing policy placeholders so follow-on work has a stable starting point
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1 -ReportPath harness-cleanup-audit.md`
  - passed with no findings
- Known issues: `psql` is not installed in the current workspace, so SQL syntax and migration application were not validated against a running Postgres instance
- Next step: complete `WBS 2.4` object storage and evidence bucket baseline against the new DB and env contracts

## 2026-04-07 - WBS 2.4 Object Storage and Evidence Bucket Baseline

- WBS: `2.4`
- Status: `done`
- Goal: turn the approved storage strategy into a concrete object bucket and key-layout baseline so snapshot capture and parsing work can start without storage-path drift
- Why now: `3.2` snapshot capture and `3.3` parsing depend on a stable answer for private bucket boundaries, object key shape, and which storage details remain placeholders
- Outcome: added a storage baseline entrypoint in `storage/README.md`, created `storage/object-layout.example.json`, documented the contract in `docs/03-design/object-storage-evidence-bucket-baseline.md`, extended the env examples with object-storage access and subtree keys, and marked `WBS 2.4` complete
- Not done: no real bucket was provisioned, no lifecycle or encryption policy was applied, and no provider-side IAM or console setup was performed
- Key files: `storage/README.md`, `storage/object-layout.example.json`, `docs/03-design/object-storage-evidence-bucket-baseline.md`, `.env.dev.example`, `.env.prod.example`, `docs/01-planning/WBS.md`
- Decisions: kept storage vendor-neutral with an S3-compatible shape. Preferred one private bucket per environment, allowed a shared-bucket fallback only with strict `{env}/...` separation, and kept browser-facing surfaces away from raw object paths. Added env keys for storage access mode and object subtree names so follow-on code can avoid hard-coded paths
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1 -ReportPath harness-cleanup-audit.md`
  - passed with no findings
- Known issues: actual storage provisioning and provider-side access policy work are still external tasks, and object uploads have not been validated against a live bucket
- Next step: complete `WBS 2.7` monitoring and error tracking baseline or `WBS 3.1` source discovery depending on foundation sequencing priority

## 2026-04-07 - WBS 2.7 and 2.10 Monitoring and Foundation CI Baseline

- WBS: `2.7`, `2.10`
- Status: `done`
- Goal: add a minimum observability contract and make CI validate the foundation baseline that future runtime code will depend on
- Why now: Sprint 0 marked monitoring and CI as P0 foundation work because prototype failures need to be diagnosable before source discovery and snapshot work start in earnest
- Outcome: added a monitoring/error tracking baseline document, shared observability example artifacts for safe external errors and structured internal events, a foundation validation script, a single local-and-CI entrypoint, JSON syntax checks in the harness, broader package-script auto-discovery, and a documented CI baseline that keeps deployment automation deferred for now
- Not done: no runtime SDK integration, no alert routing, no production DSN provisioning, and no deployment automation were added
- Key files: `docs/03-design/monitoring-error-tracking-baseline.md`, `docs/00-governance/foundation-ci-cd-baseline.md`, `shared/observability/README.md`, `shared/observability/error-envelope.example.json`, `shared/observability/structured-log-event.example.json`, `scripts/harness/validate-foundation-baseline.ps1`, `scripts/harness/invoke-foundation-checks.ps1`, `.github/workflows/harness.yml`, `docs/01-planning/WBS.md`
- Decisions: kept the observability contract provider-neutral while aligning `prod` to the existing `sentry` label. Treated `request_id`, `correlation_id`, and `run_id` as separate fields. Reused PowerShell scripts inside GitHub Actions instead of duplicating logic in YAML. Left deployment steps out of scope until real infrastructure and secrets are approved
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1 -ReportPath harness-cleanup-audit.md`
  - passed with no findings
- Known issues: the repo still has no runtime package or deployment target, so conditional package checks currently skip and CI remains validation-only
- Next step: complete `WBS 2.8` security baseline or start `WBS 3.1` source discovery using the new observability contract

## 2026-04-07 - WBS 2.5, 2.6, 2.8, and 2.9 Foundation Scaffolds

- WBS: `2.5`, `2.6`, `2.8`, `2.9`
- Status: `done`
- Goal: add the remaining auth, i18n, security, and public or admin route scaffolds without forcing a runtime framework choice too early
- Why now: WBS `2` was blocked on these shared foundation contracts, and follow-on work like admin login, public UI, and source-driven prototype work needs a stable boundary before runtime code starts
- Outcome: added a vendor-neutral admin auth session contract, RBAC matrix, browser security policy scaffold, safe-fetch and secret inventory manifests, EN/KO/JA locale config and starter resource files, glossary seed data, admin and public API route manifests, and app-side public or admin route manifests with per-route shell placeholders
- Not done: no framework router, auth vendor, runtime session storage, UI components, or API handlers were implemented
- Key files: `shared/security/auth-session.contract.json`, `shared/security/browser-security-policy.json`, `shared/security/rbac-role-matrix.json`, `shared/security/safe-fetch-policy.example.json`, `shared/security/secret-inventory.example.json`, `shared/i18n/locale-config.json`, `shared/i18n/locales/en.json`, `shared/i18n/locales/ko.json`, `shared/i18n/locales/ja.json`, `shared/i18n/glossary.seed.json`, `api/admin/route-manifest.json`, `api/public/route-manifest.json`, `app/admin/routes.manifest.json`, `app/public/routes.manifest.json`, `docs/01-planning/WBS.md`, `README.md`
- Decisions: kept the scaffold vendor-neutral so the repo still does not lock `Next.js`, `Express`, `Supabase Auth`, or another runtime choice prematurely. Treated `en` as the approved fallback root and left `ko` and `ja` resources in draft status. Reserved admin login as `/admin/login` and kept admin APIs cookie-session based with CSRF required for authenticated writes
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1 -ReportPath harness-cleanup-audit.md`
  - passed with no findings
- Known issues: the route shells are documentation-first placeholders, so a future framework choice still needs to map these manifests into actual files and handlers
- Next step: start `WBS 3.1` source discovery or `4.1` admin login implementation on top of the new auth and route scaffold

## 2026-04-07 - WBS 2 Readiness Review and Owner Prep Guide

- WBS: `2.x` review support
- Status: `done`
- Goal: review whether WBS `2` is practically ready for WBS `3`, and capture the remaining Product Owner or infrastructure preparation tasks in-repo before coding starts
- Why now: the Product Owner asked for a full readiness review before WBS `3`, and the repo needed a single document that explains what still must be prepared outside git
- Outcome: reviewed the foundation artifacts, identified the remaining readiness gaps around runtime choice, real dev infra, real secrets, and unexecuted DB migration, and added `docs/00-governance/pre-development-owner-preparation-guide.md` with a step-by-step owner checklist
- Not done: no product runtime code, DB migration apply, storage provisioning, or framework selection was performed
- Key files: `docs/00-governance/pre-development-owner-preparation-guide.md`, `docs/00-governance/development-journal.md`, `docs/README.md`
- Decisions: did not lock a runtime stack on the Product Owner's behalf. The guide explicitly leaves framework, router, worker model, and auth strategy as owner decisions before coding starts. The preparation path is now written against hosted dev DB and hosted dev object storage instead of a local-only infra baseline
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1 -ReportPath harness-cleanup-audit.md`
  - passed with no findings
- Known issues: WBS `2` contracts are largely complete, but practical start readiness still depends on user-owned infrastructure and runtime choices
- Next step: have the Product Owner fill the preparation guide, then confirm the chosen runtime stack before any WBS `3` implementation work

## 2026-04-07 - Product Code Language Baseline

- WBS: `2.x` readiness support
- Status: `done`
- Goal: record the Product Owner's product-code language decision before runtime stack selection continues
- Why now: the Product Owner explicitly decided the language direction and the repo needed one documented baseline before framework and runtime choices are closed
- Outcome: fixed the product-code language baseline as `Python primary + TypeScript frontend`, updated the owner preparation guide to treat language as decided and runtime shape as still open, and recorded the decision in the decision log
- Not done: package manager, browser framework, API runtime, worker model, and auth implementation are still undecided
- Key files: `docs/00-governance/decision-log.md`, `docs/00-governance/pre-development-owner-preparation-guide.md`, `docs/00-governance/development-journal.md`
- Decisions: Python is the default language for pipeline and backend-heavy product code. TypeScript remains the default language for browser-facing public and admin frontend code. This is a language baseline only, not a full runtime-stack choice
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1 -ReportPath harness-cleanup-audit.md`
  - passed with no findings
- Known issues: runtime and framework choices still need to be made before implementation begins
- Next step: choose package manager, frontend runtime, API runtime, worker model, and auth approach on top of the new language baseline

## 2026-04-07 - Runtime Stack Baseline and Prep Guide Update

- WBS: `2.x` readiness support
- Status: `done`
- Goal: lock the minimum runtime stack for WBS `3` readiness and update the owner-preparation guide so it reflects concrete setup steps instead of open architecture choices
- Why now: the Product Owner approved the recommended runtime stack and asked for a more complete pre-development guide based on those fixed choices
- Outcome: fixed the runtime baseline as `Next.js App Router + pnpm` for frontend, `FastAPI` as a separate API service, a separate Python worker process, `uv` for Python package/runtime management, Python API managed server-side session auth, and `dev monitoring = disabled`. Rewrote the owner-preparation guide so it now explains the full hosted-dev setup path from local tool installation through hosted Postgres, hosted S3-compatible storage, secret creation, OpenAI access, and readiness handoff
- Not done: no runtime packages were installed by Codex, no hosted infrastructure was provisioned, and no product code was written
- Key files: `docs/00-governance/pre-development-owner-preparation-guide.md`, `docs/00-governance/decision-log.md`, `docs/00-governance/raid-log.md`, `docs/00-governance/development-journal.md`
- Decisions: runtime shape is no longer open for WBS `3` readiness. What remains is setup and verification only
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1 -ReportPath harness-cleanup-audit.md`
  - passed with no findings
- Known issues: actual hosted dev infra, local toolchain installation, and real secrets are still user-owned preparation work
- Next step: have the Product Owner complete the hosted-dev setup checklist and report readiness back before any WBS `3` implementation starts

## 2026-04-08 - Local Toolchain Install Baseline

- WBS: `2.x` readiness support
- Status: `done`
- Goal: install the approved local toolchain needed for the chosen runtime baseline so follow-on setup and verification work can run on this machine
- Why now: the Product Owner explicitly asked for local installation of `uv`, `pnpm`, `psql`, and `aws` CLI, and `psql` had already been called out as missing in the DB baseline entry
- Outcome: installed `uv`, `pnpm`, and `aws` CLI with `winget`. Installed PostgreSQL command-line tools so `psql` is available without intentionally locking in a local Postgres server configuration. Updated `README.md` with a short local-toolchain note
- Not done: no hosted dev infrastructure, no local database initialization, no AWS authentication, and no project package/bootstrap commands were run
- Key files: `README.md`, `docs/00-governance/development-journal.md`
- Decisions: kept the `psql` installation narrow by using PostgreSQL CLI tools only instead of treating a local database server as part of the repo baseline. Left real AWS credentials and DB connection setup out of scope
- Verification:
  - `uv --version`
  - passed with `0.11.3`
  - `pnpm --version`
  - passed with `10.33.0`
  - `aws --version`
  - passed with `aws-cli/2.34.26`
  - `psql --version`
  - passed with `PostgreSQL 18.3`
- Known issues: existing terminal sessions may need a restart before the updated `PATH` is visible without manual refresh
- Next step: connect the new local toolchain to the hosted dev setup checklist when the Product Owner is ready

## 2026-04-09 - Owner Readiness Checklist Returned

- WBS: `2.x` readiness support
- Status: `done`
- Goal: record the completed pre-development readiness checklist in-repo so WBS `3` readiness does not depend on chat history
- Why now: the Product Owner returned concrete setup results for local tools, hosted dev infrastructure, secrets, and local verification access
- Outcome: recorded that the local toolchain, hosted Supabase dev Postgres, hosted AWS S3 dev object storage, real dev secrets, OpenAI dev API key, and untracked local dev env source are all ready. Corrected the checklist typo `yse` to `yes`
- Not done: no product code has been started, no untracked env files have been generated by Codex yet, and no DB migration or runtime bootstrap has been run
- Key files: `docs/00-governance/pre-development-owner-preparation-guide.md`, `docs/00-governance/development-journal.md`
- Decisions: treat the returned checklist as practical readiness for WBS `3` preparation work, while still requiring explicit Product Owner go before any implementation starts. Noted one baseline variance: local Python is `3.14.3` instead of the guide's target `3.12`
- Verification:
  - reviewed the completed checklist in `docs/00-governance/pre-development-owner-preparation-guide.md`
  - confirmed every readiness row is now marked `yes`
- Known issues: Python `3.14.3` is newer than the declared `3.12` baseline, so package compatibility should be watched during bootstrap and may justify a `3.12` runtime env if dependency support lags
- Next step: wait for explicit Product Owner instruction to start development, then create or use untracked local env files and begin the first approved WBS `3` slice

## 2026-04-09 - Root README Status Refresh

- WBS: `2.x` documentation support
- Status: `done`
- Goal: align the root README with the authoritative docs so it shows current readiness clearly without implying that WBS `3` implementation has already begun
- Why now: the previous README mixed Gate A readiness, completed foundation scaffolds, and implementation-sounding wording in a way that could be misread after the latest readiness updates
- Outcome: rewrote the root `README.md` to present the repo as `execution-ready` rather than `implementation-in-progress`, added the explicit hold rule for Product Owner start approval, reflected the approved runtime baseline, linked the key governance and readiness docs, and kept the harness and local toolchain guidance easy to find
- Not done: no product code, package bootstrap, DB migration apply, or runtime start commands were added
- Key files: `README.md`, `docs/00-governance/development-journal.md`
- Decisions: the root README should describe what is already approved and prepared, but it must not read as a signal that actual development has started. Runtime decisions are documented as approved baselines only, not as bootstrapped repo state
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
- Known issues: no content validation issues were reported by the harness after the README refresh
- Next step: wait for the next Product Owner documentation or development-start instruction

## 2026-04-09 - Harness Startup Read Order Update

- WBS: `2.x` documentation support
- Status: `done`
- Goal: make the harness startup reading order explicitly include `development-journal.md` alongside `AGENTS.md` and root `README.md`
- Why now: the Product Owner wanted the resume-memory document to be part of the required pre-work reading flow, not only a post-slice handoff artifact
- Outcome: updated `AGENTS.md` to tell the agent to read the root `README.md` and `docs/00-governance/development-journal.md` before starting work, added the development journal to the harness required-file list in `scripts/harness/shared.ps1`, and rewrote the harness baseline doc in clean ASCII with the new startup read order called out directly
- Not done: no product code, runtime bootstrap, or workflow automation beyond the documentation and harness file-list update was added
- Key files: `AGENTS.md`, `scripts/harness/shared.ps1`, `docs/00-governance/harness-engineering-baseline.md`, `docs/00-governance/development-journal.md`
- Decisions: the development journal is now part of the startup context set because it carries the latest resume-safe implementation memory that may not be visible from README or AGENTS alone
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
- Known issues: no harness validation issues were reported after the startup read-order update
- Next step: use the new startup read order in the next session that begins substantive work

---

## 7. Change History

| Date | Change |
|---|---|
| 2026-04-07 | Initial development journal created |
| 2026-04-07 | Rewrote the journal in clean UTF-8 text and added the WBS 2.2 entry |
| 2026-04-07 | Added the runtime-stack baseline entry and updated its verification results after rerunning foundation checks |
| 2026-04-07 | Added the WBS 2.3 DB and migration baseline entry |
| 2026-04-07 | Added the WBS 2.4 object storage and evidence bucket baseline entry |
| 2026-04-07 | Added the combined WBS 2.7 and 2.10 monitoring and foundation CI baseline entry |
| 2026-04-07 | Added the combined WBS 2.5, 2.6, 2.8, and 2.9 foundation scaffold entry |
| 2026-04-07 | Added the WBS 2 readiness review and owner preparation guide entry |
| 2026-04-07 | Added the product code language baseline entry: Python primary plus TypeScript frontend |
| 2026-04-07 | Added the runtime stack baseline and detailed hosted-dev preparation update |
| 2026-04-08 | Added the local toolchain installation baseline entry and README note |
| 2026-04-09 | Added the owner readiness checklist return entry and recorded the completed setup status |
| 2026-04-09 | Added the root README status refresh entry |
| 2026-04-09 | Added the harness startup read order update entry |
