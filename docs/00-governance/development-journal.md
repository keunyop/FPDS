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

## 2026-04-09 - WBS 3.1 Source Discovery Core

- WBS: `3.1`
- Status: `partial`
- Goal: start the TD savings source discovery implementation with a reproducible registry seed, deterministic source identity, and warning-aware discovery flow
- Why now: the Product Owner explicitly started WBS `3.1`, and snapshot or parsing work would be unstable without first fixing the approved TD source set in runnable code
- Outcome: added a Python discovery package under `worker/discovery/fpds_discovery`, seeded the approved 12-source TD savings registry in `worker/discovery/data/td_savings_source_registry.json`, implemented normalized URL dedupe and deterministic `source_document_id` generation, added entry-page detail discovery plus linked-PDF discovery, enforced controlled fetch rules for HTTPS and allowlisted domains, and added offline fixtures plus unit tests that cover registry output, warnings, and contract-shaped discovery payloads
- Not done: no DB persistence to `source_document` or `run_source_item` was added yet, no live snapshot capture was performed, and one current TD live PDF URL drift remains unresolved against the approved inventory baseline
- Key files: `worker/discovery/data/td_savings_source_registry.json`, `worker/discovery/fpds_discovery/discovery.py`, `worker/discovery/fpds_discovery/registry.py`, `worker/discovery/fpds_discovery/fetch.py`, `worker/discovery/fpds_discovery/url_utils.py`, `worker/discovery/tests/test_discovery.py`, `worker/discovery/README.md`
- Decisions: kept the approved source inventory as the source of truth and treated out-of-registry or excluded links as warnings instead of auto-expanding scope. Stored human registry ids like `TD-SAV-001` in `source_metadata` while generating separate deterministic `source_document_id` values from `bank_code + normalized_source_url + source_type`. Included `run_id`, `correlation_id`, `discovery_mode`, `discovery_status`, and `discovery_notes` in the output payload so the worker stays aligned with the discovery interface baseline
- Verification:
  - `python -m unittest discover -s worker/discovery/tests -t .`
  - passed
  - `python -m worker.discovery.fpds_discovery --entry-html-path worker/discovery/tests/fixtures/td_savings_entry.html --page-html "https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/every-day-savings-account=worker/discovery/tests/fixtures/td_every_day_detail.html" --page-html "https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/epremium-savings-account=worker/discovery/tests/fixtures/td_epremium_detail.html" --page-html "https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/growth-savings-account=worker/discovery/tests/fixtures/td_growth_detail.html" --page-html "https://www.td.com/ca/en/personal-banking/products/bank-accounts/account-rates=worker/discovery/tests/fixtures/td_account_rates.html" --page-html "https://www.td.com/ca/en/personal-banking/products/bank-accounts-fees-services-charges-cad-savings=worker/discovery/tests/fixtures/td_fee_summary.html" --run-id run_20260409_0001 --correlation-id corr_20260409_0001`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
- Known issues: on `2026-04-09`, the live TD page appears to expose `513796-en.pdf` where the approved inventory still lists `513796-20171030.pdf`, so live discovery against the current site will surface that as a warning until the Product Owner decides whether to keep the strict baseline or update the inventory
- Next step: decide how to handle the live `TD-SAV-007` PDF drift, then either connect discovery output to DB persistence or move directly into `3.2` snapshot capture using the new registry and source identity helpers

## 2026-04-09 - WBS 3.1 TD-SAV-007 Live URL Alignment

- WBS: `3.1`
- Status: `done`
- Goal: align the approved TD savings inventory and discovery registry with the current live `TD-SAV-007` URL selected by the Product Owner
- Why now: the Product Owner decided to update the baseline instead of keeping the previous `TD-SAV-007` PDF path as a warning-only drift
- Outcome: updated the inventory document and the discovery seed registry so `TD-SAV-007` now points to `https://www.td.com/content/dam/tdct/document/pdf/personal-banking/513796-en.pdf`, refreshed fixture HTML to match the new canonical seed, and documented that the fee summary page still exposes a second live download path outside the current 12-source baseline
- Not done: no alias handling was added for the alternate fee-summary PDF path, and no live network discovery test was added in-repo
- Key files: `docs/01-planning/td-savings-source-inventory.md`, `worker/discovery/data/td_savings_source_registry.json`, `worker/discovery/tests/fixtures/td_every_day_detail.html`, `worker/discovery/tests/fixtures/td_fee_summary.html`, `docs/00-governance/development-journal.md`
- Decisions: treated the detail-page URL as the canonical `TD-SAV-007` baseline. Kept the alternate fee-summary path documented as live context instead of widening the prototype source registry or changing source identity rules mid-slice
- Verification:
  - verified live detail-page PDF link resolves to `https://www.td.com/content/dam/tdct/document/pdf/personal-banking/513796-en.pdf`
  - verified the fee summary page still exposes `https://www.td.com/content/dam/tdct/document/pdf/econsent/accounts/513796.pdf` as a separate live download path
- Known issues: if live discovery later starts from the fee summary page and follows the alternate `513796.pdf` link directly, it will still be classified outside the current 12-source registry until alias support is intentionally added
- Next step: connect discovery output to DB persistence or begin `3.2` snapshot capture using the updated canonical `TD-SAV-007` seed

## 2026-04-09 - WBS 3.2 Snapshot Capture Core

- WBS: `3.2`
- Status: `partial`
- Goal: start the snapshot capture implementation so approved discovery sources can be fetched, stored to the approved raw object key layout, and described with DB-shaped fetch metadata
- Why now: `3.2` is the next dependency after source discovery, and parsing or chunking would be premature without a stable snapshot boundary for raw HTML or PDF preservation, retry, and reuse
- Outcome: added `worker/discovery/fpds_snapshot` with a snapshot capture service, source adapter, object key builder, filesystem or AWS CLI storage adapters, and a CLI entrypoint. Extended the shared fetch helper so snapshot capture can reuse the same allowlist-driven live fetch policy as discovery while recording final URL, content type, status, redirect count, and fetch timestamp. The snapshot result now returns DB-shaped `source_snapshot` payloads for newly stored artifacts plus per-source `run_source_item` payloads that carry `completed` or `failed` stage status and finer-grained snapshot action in `stage_metadata`. Added tests for HTML/PDF snapshot storage, source-level retry failure, and identical-fingerprint reuse
- Not done: no live object storage upload was verified against the dev bucket, no DB persistence was wired to the real dev Postgres yet, and no formal snapshot interface document was added under `shared/contracts` or `api-interface-contracts`
- Key files: `worker/discovery/fpds_snapshot/capture.py`, `worker/discovery/fpds_snapshot/storage.py`, `worker/discovery/fpds_snapshot/__main__.py`, `worker/discovery/fpds_snapshot/__init__.py`, `worker/discovery/fpds_discovery/fetch.py`, `worker/discovery/tests/test_snapshot_capture.py`, `worker/discovery/README.md`, `docs/00-governance/development-journal.md`
- Decisions: kept `fetch_status` narrow at `fetched` or `reused` for snapshot rows and kept `run_source_item.stage_status` conservative at `completed` or `failed`, with exact snapshot action left in `stage_metadata.snapshot_action`. Chose SHA-256 over raw body bytes for `checksum` and SHA-256 over `content_type + body` for `fingerprint` so raw integrity and idempotency keys stay deterministic without waiting for a fuller checksum policy document. Kept failed fetch attempts out of `source_snapshot` rows because the current schema requires `object_storage_key`, `checksum`, and `fingerprint`, and instead routed failures into `run_source_item.error_summary` and `stage_metadata`
- Verification:
  - `python -m unittest discover -s worker/discovery/tests -t .`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - blocked by an inaccessible temporary debug folder `tmp58jc15b1` created during local debugging
  - manual harness-equivalent markdown, PowerShell, and JSON validation excluding the inaccessible debug folder
  - passed
- Known issues: the inaccessible `tmp58jc15b1` debug folder still remains in the workspace and prevents the standard repo doctor full-repo scan from completing cleanly. Live snapshot execution also still depends on user-owned dev bucket access, valid AWS CLI auth, and DB migration application if persistence is added next
- Next step: connect snapshot results to real `source_document` or `source_snapshot` persistence and run a first live capture against the priority prototype sources `TD-SAV-002`, `TD-SAV-004`, `TD-SAV-007`, and `TD-SAV-008`

## 2026-04-09 - WBS 3.2 Snapshot Capture Persistence and Live Verification

- WBS: `3.2`
- Status: `done`
- Goal: finish snapshot capture by wiring live env loading, Postgres persistence, and a real dev verification run
- Why now: the Product Owner confirmed that dev bucket access and the baseline migration were ready, so `3.2` could move from capture-only code to an end-to-end runnable slice
- Outcome: added env-file loading for the snapshot CLI, with explicit env files overriding ambient process env. Added a `psql`-backed persistence layer that starts or finalizes `ingestion_run`, upserts `source_document`, inserts new `source_snapshot`, and upserts `run_source_item`. Added schema resolution so the worker prefers `FPDS_DATABASE_SCHEMA` when the required tables exist there, but falls back to `public` when the configured schema is empty and `public` contains the snapshot tables. Live snapshot capture was then verified against the dev bucket and dev Postgres for `TD-SAV-002`, `TD-SAV-004`, `TD-SAV-007`, and `TD-SAV-008`
- Not done: no parsed-document or chunk-stage persistence was added yet, and no harness fix was made for the unrelated ACL-blocked `tmp58jc15b1` folder
- Key files: `worker/discovery/env.py`, `worker/discovery/fpds_snapshot/persistence.py`, `worker/discovery/fpds_snapshot/__main__.py`, `worker/discovery/fpds_snapshot/capture.py`, `worker/discovery/fpds_snapshot/storage.py`, `worker/discovery/tests/test_snapshot_persistence.py`, `worker/discovery/README.md`, `docs/01-planning/WBS.md`
- Decisions: kept DB access dependency-free by using baseline `psql` instead of adding a Python DB driver. Treated an explicit `--env-file` as the source of truth and allowed a safe `public` schema fallback only when the configured schema does not contain the required snapshot tables. Left `run_state` as `completed` for partial-success capture runs and reserved `failed` for all-source failure
- Verification:
  - `python -m unittest discover -s worker/discovery/tests -t .`
  - passed with `15` tests
  - `python -m worker.discovery.fpds_snapshot --env-file .env.dev --persist-db --run-id run_20260409_3203 --correlation-id corr_20260409_3203 --request-id req_20260409_3203 --source-id TD-SAV-002 --source-id TD-SAV-004 --source-id TD-SAV-007 --source-id TD-SAV-008`
  - passed with `stored_count=4`, `database_schema=public`
  - `psql ... select count(*) from public.ingestion_run where run_id = 'run_20260409_3203'; select count(*) from public.run_source_item where run_id = 'run_20260409_3203'; select count(*) from public.source_snapshot where snapshot_id in (...);`
  - returned `1`, `4`, `4`
  - `python -m worker.discovery.fpds_snapshot --env-file .env.dev --persist-db --run-id run_20260409_3204 --correlation-id corr_20260409_3204 --request-id req_20260409_3204 --source-id TD-SAV-002 --source-id TD-SAV-004 --source-id TD-SAV-007 --source-id TD-SAV-008`
  - passed with `reused_count=4`, confirming DB-backed snapshot reuse
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - still blocked by `tmp58jc15b1` access denied outside this slice
- Known issues: the current dev env declares `FPDS_DATABASE_SCHEMA=fpds`, but the migrated snapshot tables actually live in `public`, so runtime schema fallback is currently masking that local setup drift. The inaccessible `tmp58jc15b1` folder still prevents a clean full-repo harness scan
- Next step: start `3.3` parsing and chunking using the now-persisted `source_snapshot` rows and verified raw object keys

## 2026-04-10 - WBS 3.3 Parse and Chunk Pipeline

- WBS: `3.3`
- Status: `done`
- Goal: turn persisted raw snapshots into parsed text and evidence-ready chunks that downstream retrieval and extraction can consume
- Why now: `3.4` evidence retrieval and every later ingestion stage depend on stable `parsed_document` and `evidence_chunk` records, so snapshot persistence alone was not enough to move the prototype forward
- Outcome: added a minimal Python worker project baseline in `pyproject.toml`, introduced `worker/pipeline/fpds_parse_chunk` with HTML parsing via `beautifulsoup4`, PDF parsing via `pypdf`, overlap-aware chunk generation, parsed artifact object storage writes, `psql`-backed persistence for `parsed_document` and `evidence_chunk`, and a CLI that can load stored snapshots from DB or a JSON snapshot manifest. Verified the stage live against dev storage and dev Postgres for `TD-SAV-002`, `TD-SAV-004`, `TD-SAV-007`, and `TD-SAV-008`, then reran the same sources to confirm parsed-document reuse on identical snapshots
- Not done: no retrieval ranking or field-to-evidence matching logic yet, no extraction prompt flow yet, and no admin trace viewer consumption code yet
- Key files: `pyproject.toml`, `worker/env.py`, `worker/pipeline/fpds_parse_chunk/parser.py`, `worker/pipeline/fpds_parse_chunk/service.py`, `worker/pipeline/fpds_parse_chunk/storage.py`, `worker/pipeline/fpds_parse_chunk/persistence.py`, `worker/pipeline/fpds_parse_chunk/__main__.py`, `worker/pipeline/tests/test_parse_chunk.py`, `worker/pipeline/README.md`, `docs/01-planning/WBS.md`
- Decisions: kept `parsed text full body -> object storage` and `chunk excerpt + metadata -> DB` aligned to the approved storage strategy. Used `section` anchors for HTML and `page` anchors for PDF. Reused existing parsed artifacts by `snapshot_id` to preserve immutable lineage and avoid duplicate chunk rows. Moved env loading to `worker/env.py` so discovery and pipeline CLIs can share the same local env behavior. Reworked parse persistence to inline large JSON payloads in SQL so Windows command-length limits do not break `psql` on chunk-heavy sources
- Verification:
  - `python -m unittest discover -s worker -t .`
  - passed with `20` tests
  - `python -m worker.pipeline.fpds_parse_chunk --env-file .env.dev --persist-db --run-id run_20260410_3301 --correlation-id corr_20260410_3301 --request-id req_20260410_3301 --source-id TD-SAV-002 --source-id TD-SAV-004 --source-id TD-SAV-007 --source-id TD-SAV-008`
  - passed with `stored_count=4`, `parsed_document_count=4`, `evidence_chunk_count=118`, `database_schema=public`
  - `python -m worker.pipeline.fpds_parse_chunk --env-file .env.dev --persist-db --run-id run_20260410_3302 --correlation-id corr_20260410_3302 --request-id req_20260410_3302 --source-id TD-SAV-002 --source-id TD-SAV-004 --source-id TD-SAV-007 --source-id TD-SAV-008`
  - passed with `reused_count=4`, confirming parsed-document reuse for the same snapshots
- Known issues: the dev database schema setting still resolves to `public` at runtime instead of the configured `fpds` schema. The current PDF path extracts page text successfully for the verified TD sources, but table-heavy PDFs will still need retrieval and extraction quality review in `3.4` and `3.5`
- Next step: start `3.4` evidence retrieval on top of the new `parsed_document_id`, `evidence_chunk_id`, page or section anchor, and excerpt metadata baseline

## 2026-04-10 - WBS 3.4 Evidence Retrieval Baseline

- WBS: `3.4`
- Status: `done`
- Goal: add a retrieval-ready internal interface that can return candidate evidence chunks per canonical field before extraction starts
- Why now: `3.5` extraction depends on a stable way to look up chunk candidates by `parsed_document_id`, field name, and metadata scope, and the approved architecture explicitly allows metadata-only retrieval fallback before `pgvector` is ready in early dev
- Outcome: added `worker/pipeline/fpds_evidence_retrieval` with request and response models aligned to the internal evidence retrieval contract, a `psql`-backed repository that resolves the active schema and reads joined `evidence_chunk -> parsed_document -> source_snapshot -> source_document` metadata, a metadata-only retrieval service with field-aware lexical scoring, CLI support for `parsed_document_id` or registry-backed `source_id` lookup, and unit tests for ranking, metadata filtering, vector-assisted fallback behavior, and DB payload loading. Live verification was run against dev Postgres for `TD-SAV-007` and `TD-SAV-008`
- Not done: no `pgvector` similarity search yet, no embedding storage yet, and no `field_evidence_link` persistence yet because that table requires `candidate_id` or `product_version_id`, which are introduced in later stages
- Key files: `worker/pipeline/fpds_evidence_retrieval/models.py`, `worker/pipeline/fpds_evidence_retrieval/service.py`, `worker/pipeline/fpds_evidence_retrieval/persistence.py`, `worker/pipeline/fpds_evidence_retrieval/__main__.py`, `worker/pipeline/tests/test_evidence_retrieval.py`, `worker/pipeline/README.md`, `docs/01-planning/WBS.md`, `README.md`
- Decisions: treated `metadata-only` as the approved Prototype or early-dev fallback and kept `vector-assisted` as a forward-compatible request mode that currently degrades cleanly with an explicit runtime note. Did not write `field_evidence_link` rows in `3.4` because the existing DB constraint requires a downstream `candidate_id` or `product_version_id`, so this stage returns candidate chunk sets and leaves finalized linkage to extraction or canonicalization stages. Added UTF-8 `psql` decoding for retrieval because live chunk excerpts can include characters that break the default Windows code page
- Verification:
  - `python -m unittest discover -s worker -t .`
  - passed with `25` tests
  - `python -m worker.pipeline.fpds_evidence_retrieval --env-file .env.dev --run-id run_20260410_3401 --correlation-id corr_20260410_3401 --source-id TD-SAV-007 --field-name monthly_fee --field-name fee_waiver_condition --field-name eligibility_text`
  - passed with `requested_retrieval_mode=metadata-only`, `applied_retrieval_mode=metadata-only`, and chunk-level matches that included `evidence_chunk_id`, page anchor, excerpt, and score
  - `python -m worker.pipeline.fpds_evidence_retrieval --env-file .env.dev --run-id run_20260410_3402 --correlation-id corr_20260410_3402 --source-id TD-SAV-008 --retrieval-mode vector-assisted --field-name interest_payment_frequency --field-name tier_definition_text`
  - passed with `requested_retrieval_mode=vector-assisted`, `applied_retrieval_mode=metadata-only`, and an explicit fallback runtime note
- Known issues: the current retrieval scoring is heuristic and metadata-only, so quality is good enough for early extraction scaffolding but not yet the final Phase 1 hybrid target. The dev database schema still resolves to `public` instead of the configured `fpds` schema. `field_evidence_link` persistence remains blocked on later-stage candidate creation
- Next step: start `3.5` extraction using the new retrieval request shape and candidate chunk output as the evidence input boundary

## 2026-04-10 - Source Registry Refresh and Approval Policy

- WBS: `3.1` operating follow-up
- Status: `done`
- Goal: document how the TD savings source registry should stay current when bank sites change URLs, retire products, or publish new sources
- Why now: the Product Owner asked for an explicit operating strategy before moving deeper into extraction, and the current repo had the approved active registry seed but not a written refresh and approval policy
- Outcome: added `docs/03-design/source-registry-refresh-and-approval-policy.md` to define the recommended hybrid model: stable approved active registry for ingestion, drift detection during ingestion preflight, scheduled refresh runs that generate candidate diffs, and explicit human approval before promotion into the active registry. Updated the docs map and discovery README so the operating policy is discoverable from the repo entrypoints
- Not done: no scheduled refresh job, candidate diff persistence layer, admin approval UI, or registry promotion audit implementation was added yet
- Key files: `docs/03-design/source-registry-refresh-and-approval-policy.md`, `docs/README.md`, `worker/discovery/README.md`
- Decisions: rejected both extremes of `auto-update registry on every ingestion run` and `manual-only registry maintenance`. Chose an approval-first hybrid model so ingestion replay remains reproducible while source drift can still be detected quickly
- Verification:
  - reviewed `worker/discovery/fpds_discovery/registry.py` and `worker/discovery/README.md` against the new policy to confirm the current implementation already matches the `approved active registry only` baseline
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - not run for this docs-only slice
- Known issues: the policy defines target operations beyond the current implementation. Candidate registry storage, scheduled refresh execution, and approval tooling remain future work
- Next step: decide whether the next slice should add `ingestion preflight drift check` first or `scheduled refresh artifact generation` first

## 2026-04-10 - Discovery Preflight Drift Check and Refresh Artifact Generation

- WBS: `3.1` operating follow-up
- Status: `done`
- Goal: implement the first runnable operating slices behind the new registry policy: preflight drift checks before ingestion and a scheduled refresh artifact that produces candidate diffs without mutating the active registry
- Why now: the Product Owner chose the execution order explicitly, and the repo needed operator-visible signals for URL drift or source changes before moving deeper into extraction
- Outcome: added `worker/discovery/fpds_discovery/drift.py` with a lightweight source-by-source preflight checker that detects fetch failures, final URL changes, and content-type changes. Wired the snapshot capture CLI to run preflight by default and carry warning counts plus preflight summary into run output and snapshot persistence metadata. Added `worker/discovery/fpds_registry_refresh` with a refresh CLI that combines scheduled discovery output and preflight findings into a JSON artifact containing candidate diffs such as `new_source_candidate`, `redirect_detected`, and `source_missing_from_discovery`
- Not done: no scheduler integration, no candidate diff DB persistence, no active registry promotion workflow, and no admin review UI were added
- Key files: `worker/discovery/fpds_discovery/drift.py`, `worker/discovery/fpds_snapshot/__main__.py`, `worker/discovery/fpds_snapshot/capture.py`, `worker/discovery/fpds_snapshot/persistence.py`, `worker/discovery/fpds_registry_refresh/service.py`, `worker/discovery/fpds_registry_refresh/__main__.py`, `worker/discovery/tests/test_drift_preflight.py`, `worker/discovery/tests/test_registry_refresh.py`, `worker/discovery/README.md`
- Decisions: kept preflight warning-only so ingestion reproducibility stays anchored to the approved active registry. Chose JSON artifact generation for scheduled refresh instead of introducing a new DB table or approval UI in the same slice. Kept `--skip-preflight-drift-check` as an escape hatch, but enabled preflight by default for snapshot capture
- Verification:
  - `python -m unittest discover -s worker/discovery/tests -t .`
  - passed with `19` tests
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
- Known issues: scheduled refresh currently generates a local artifact only and does not persist candidate diffs. The preflight check is deliberately lightweight and does not yet compare entry-page listing drift inside the snapshot CLI path
- Next step: decide whether the next follow-up slice should persist refresh artifacts for review history or start `3.5` extraction as the mainline path

## 2026-04-10 - WBS 3.5 Extraction Flow Baseline

- WBS: `3.5`
- Status: `done`
- Goal: convert retrieval-ready evidence chunks into source-level sparse extracted drafts and persist the execution trace needed for later normalization and reviewability
- Why now: `3.6` normalization needs a stable upstream extraction boundary, and the workflow design explicitly separates `extracted draft` from downstream `normalized_candidate`
- Outcome: added `worker/pipeline/fpds_extraction` with a CLI, service, storage config, and `psql` repository. The new stage resolves the latest `parsed_document` for registry-backed `source_id` or direct `parsed_document_id`, runs metadata-only evidence retrieval across an extraction field set, derives sparse field candidates, writes extracted draft plus metadata JSON artifacts, persists one `model_execution` row per source attempt, persists a zero-token `llm_usage_record` with `heuristic-no-llm-call` metadata, and updates `run_source_item.stage_metadata` with extraction status and artifact linkage
- Not done: no external LLM call yet, no `normalized_candidate` write yet, and no `field_evidence_link` persistence yet because candidate ids are still introduced in `3.6`
- Key files: `worker/pipeline/fpds_extraction/__main__.py`, `worker/pipeline/fpds_extraction/service.py`, `worker/pipeline/fpds_extraction/persistence.py`, `worker/pipeline/fpds_extraction/storage.py`, `worker/pipeline/fpds_extraction/models.py`, `worker/pipeline/tests/test_extraction.py`, `worker/pipeline/README.md`, `worker/README.md`, `README.md`, `docs/01-planning/WBS.md`
- Decisions: treated `3.5` as `source-level sparse draft extraction` instead of canonicalization. Chose object-storage JSON artifacts as the extraction result persistence shape because the current schema has `model_execution` and `llm_usage_record` but no dedicated extraction table. Kept usage accounting honest by writing `0` tokens with explicit `heuristic-no-llm-call` metadata rather than pretending an external LLM was invoked
- Verification:
  - `python -m unittest worker.pipeline.tests.test_extraction`
  - passed with `3` tests
  - `python -m unittest discover -s worker -t .`
  - passed with `32` tests
  - `python -m worker.pipeline.fpds_extraction --help`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
- Known issues: live dev DB verification did not complete in this session because `psql` could not resolve the configured Supabase host name from the current environment. Extraction heuristics are intentionally lightweight and metadata-only, so quality is sufficient for baseline wiring but not yet final production behavior. The current stage emits evidence-link drafts inside the extracted artifact, but DB-backed `field_evidence_link` rows remain deferred until candidate creation exists
- Next step: start `3.6` normalization so extracted drafts can be merged into `normalized_candidate`

## 2026-04-10 - WBS 3.6 Normalization Mapping Baseline

- WBS: `3.6`
- Status: `done`
- Goal: map extracted draft artifacts into `normalized_candidate` rows and persist candidate-level `field_evidence_link` trace so later validation and review routing can operate on stable candidate ids
- Why now: `3.7` validation and review routing depend on `candidate_id`, canonical core fields, and persisted field-level evidence links, which only exist after normalization
- Outcome: added `worker/pipeline/fpds_normalization` with a CLI, service, storage config, and `psql` repository. The stage now resolves the latest completed extraction artifact per registry-backed `source_id`, loads extracted draft JSON from object storage, applies heuristic canonical mapping for core fields and subtype inference, computes provisional `validation_status`, `validation_issue_codes`, and `source_confidence`, writes normalized artifact JSON plus metadata JSON, persists `normalized_candidate`, persists candidate-scoped `field_evidence_link`, records one normalization `model_execution` row per source, records a zero-token `llm_usage_record`, and updates `run_source_item.stage_metadata` with candidate ids and normalization results
- Not done: no full validation engine yet, no review queue creation yet, and normalization is still source-by-source rather than multi-source product merge
- Key files: `worker/pipeline/fpds_normalization/__main__.py`, `worker/pipeline/fpds_normalization/service.py`, `worker/pipeline/fpds_normalization/persistence.py`, `worker/pipeline/fpds_normalization/storage.py`, `worker/pipeline/fpds_normalization/models.py`, `worker/pipeline/tests/test_normalization.py`, `worker/pipeline/README.md`, `worker/README.md`, `README.md`, `docs/01-planning/WBS.md`
- Decisions: set `candidate_state = draft` and left review lifecycle to later stages. Used heuristic subtype mapping against the approved Phase 1 taxonomy values and preserved the `other` fallback path. Chose to persist candidate-level `field_evidence_link` in `3.6` because `candidate_id` now exists. Also tightened all current worker `psql` runners with `ON_ERROR_STOP=1` after normalization exposed a false-positive success path when SQL errors did not stop the command
- Verification:
  - `python -m unittest worker.pipeline.tests.test_normalization`
  - passed with `4` tests
  - `python -m unittest discover -s worker -t .`
  - passed with `36` tests
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
  - `python -m worker.pipeline.fpds_normalization --env-file .env.dev --persist-db --run-id run_20260410_3603 --source-id TD-SAV-002 --source-id TD-SAV-007`
  - passed with `candidate_count=2`, `field_evidence_link_count=32`, `database_schema=public`
  - `psql ... SELECT counts for ingestion_run, normalized_candidate, field_evidence_link, model_execution, llm_usage_record, run_source_item where run_id = 'run_20260410_3603'`
  - returned `1`, `2`, `32`, `2`, `2`, `2`
- Known issues: normalization is intentionally heuristic and can still over-map noisy extracted fields. In the live run, `TD-SAV-002` normalized to `validation_status=error` with `required_field_missing`, which is acceptable for this stage because `3.7` will formalize validation and routing rather than forcing all candidates to look clean at normalization time
- Next step: start `3.7` validation and confidence routing on top of the new `normalized_candidate` and `field_evidence_link` baseline

## 2026-04-10 - WBS 3.7 Validation and Confidence Routing Baseline

- WBS: `3.7`
- Status: `done`
- Goal: formalize candidate validation and prototype review routing on top of `normalized_candidate` so the pipeline produces queued review work instead of stopping at provisional normalization output
- Why now: `3.8` internal result viewing and later review decision work both need stable `review_task` rows, updated candidate states, and a dedicated validation/routing execution trace
- Outcome: added `worker/pipeline/fpds_validation_routing` with a CLI, service, storage config, and `psql` repository. The stage now resolves the latest completed normalization artifact per registry-backed `source_id`, reloads candidate payload plus candidate-scoped evidence links, reloads active taxonomy and routing policy config from Postgres, recomputes validation issue codes and confidence, updates `normalized_candidate` state and review reason, writes validation/routing artifact JSON plus metadata JSON, persists `review_task` rows in `queued` state for Prototype routing, records one validation/routing `model_execution` row per source, records a zero-token `llm_usage_record`, and updates `run_source_item.stage_metadata` with review queue linkage
- Not done: no review decision flow yet, no canonical upsert or change assessment yet, no audit-event emission yet, and no Phase 1 auto-approve live path was exercised because the current product boundary still uses Prototype review-all routing
- Key files: `worker/pipeline/fpds_validation_routing/__main__.py`, `worker/pipeline/fpds_validation_routing/service.py`, `worker/pipeline/fpds_validation_routing/persistence.py`, `worker/pipeline/fpds_validation_routing/storage.py`, `worker/pipeline/fpds_validation_routing/models.py`, `worker/pipeline/tests/test_validation_routing.py`, `worker/pipeline/README.md`, `README.md`, `docs/01-planning/WBS.md`
- Decisions: kept `routing_mode = prototype` as the CLI default because the current repo scope is still Prototype-first. Loaded active taxonomy and routing policy values from `taxonomy_registry` and `processing_policy_config` instead of hard-coding new thresholds inside the service. Used the candidate-producing normalization run id as the persisted `review_task.run_id` so each queued task remains attached to the candidate?셲 originating run even when validation/routing is executed as a later standalone slice
- Verification:
  - `python -m unittest worker.pipeline.tests.test_validation_routing`
  - passed with `3` tests
  - `python -m unittest discover -s worker -t .`
  - passed with `39` tests
  - `python -m worker.pipeline.fpds_validation_routing --help`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
  - `python -m worker.pipeline.fpds_validation_routing --env-file .env.dev --persist-db --run-id run_20260410_3701 --source-id TD-SAV-002 --source-id TD-SAV-007`
  - passed with `queued_count=2`, `review_task_count=2`, `database_schema=public`
- Known issues: Prototype routing intentionally sends even clean candidates like `TD-SAV-007` to review, so `manual_sampling_review` remains the primary reason for pass-level items. A follow-up read-only `psql` verification command timed out in the current shell, so live persistence confirmation relies on the successful stage output and persisted-count summary from the validation CLI itself rather than an extra direct DB query transcript
- Next step: start `3.8` internal result viewer on top of the new candidate validation state, review task id, and validation artifact links

## 2026-04-10 - FPDS Design System Baseline

- WBS: `design support for 1.7, 3.8, 4.x, 5.x`
- Status: `done`
- Goal: define a reusable FPDS design-system baseline, benchmarked against Stripe Dashboard and Stripe Apps design guidance, before app and admin UI implementation starts in earnest
- Why now: the Product Owner asked for a design system before public/admin UI implementation, and upcoming slices such as `3.8` internal result viewer and later admin/public surfaces need shared tokens and shell rules instead of per-screen styling drift
- Outcome: added `docs/03-design/fpds-design-system.md` to define visual principles, shell structure, status semantics, typography, color direction, component families, and admin/public surface rules. Added `shared/design/` with implementation-ready token artifacts in `fpds-design-tokens.json` and `fpds-theme.css`, plus a shared-module README so future frontend work can consume one source of truth for tokens and CSS variables
- Not done: no React component library, no Tailwind or CSS-in-JS integration, no Figma file, and no actual route implementation yet
- Key files: `docs/03-design/fpds-design-system.md`, `shared/design/README.md`, `shared/design/fpds-design-tokens.json`, `shared/design/fpds-theme.css`, `shared/README.md`, `docs/README.md`, `README.md`
- Decisions: used Stripe as a benchmark for system consistency, constrained customization, token-driven styling, and pattern-first state handling rather than attempting a visual clone. Chose a FPDS-specific palette of navy, cobalt, teal, amber, and brick red instead of Stripe-purple mimicry. Kept one shared system for public and admin surfaces, with density and layout differences handled by usage rather than separate token sets
- Verification:
  - reviewed `https://docs.stripe.com/stripe-apps/design`
  - reviewed `https://docs.stripe.com/stripe-apps/style`
  - reviewed `https://docs.stripe.com/stripe-apps/patterns`
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
- Known issues: this is a baseline document and token set, not a live component library. The exact frontend consumption pattern still needs to be chosen when app/admin runtime implementation begins
- Next step: use the new design-system baseline as the visual contract for `WBS 3.8` internal result viewer and later admin/public UI scaffolds

## 2026-04-10 - WBS 3.8 Internal Result Viewer Baseline

- WBS: `3.8`
- Status: `done`
- Goal: implement the prototype read-only internal result viewer using the new FPDS design-system baseline without prematurely committing to the full admin runtime stack
- Why now: Prototype acceptance requires operator-facing reviewability, and `3.7` now leaves the repo with stable `review_task`, `normalized_candidate`, and `field_evidence_link` rows that can be surfaced without waiting for `4.x` admin workflow work
- Outcome: added `worker/pipeline/fpds_result_viewer` as a DB-backed payload exporter that reads one persisted run, joins candidate, review, source, snapshot, and evidence metadata, maps source-document ids back to registry `source_id`, and writes both `viewer-payload.json` and browser-consumable `viewer-payload.js` into `app/prototype/`. Added a static `app/prototype/index.html` viewer shell plus CSS and JS that consume the payload and render run summary, candidate rail, highlighted fields, validation issues, canonical payload rows, and evidence excerpts in a Stripe-benchmarked FPDS layout
- Not done: no framework runtime, no admin auth, no review decision actions, no queue list operations, and no full `4.4` evidence trace viewer drilldown yet
- Key files: `worker/pipeline/fpds_result_viewer/__main__.py`, `worker/pipeline/fpds_result_viewer/persistence.py`, `worker/pipeline/fpds_result_viewer/service.py`, `worker/pipeline/tests/test_result_viewer.py`, `app/prototype/index.html`, `app/prototype/viewer.css`, `app/prototype/viewer.js`, `app/prototype/viewer-payload.js`, `app/prototype/README.md`, `worker/pipeline/README.md`, `README.md`, `docs/01-planning/WBS.md`
- Decisions: kept the viewer as a static prototype surface under `app/prototype/` instead of starting the full admin shell early. Exported DB-only payload data rather than depending on object-storage fetch at page load so the viewer can stay read-only and resilient. Scoped the UI to run summary plus evidence-linked candidate detail, explicitly leaving deep trace and mutation paths to later admin work
- Verification:
  - `python -m unittest worker.pipeline.tests.test_result_viewer`
  - passed with `3` tests
  - `python -m worker.pipeline.fpds_result_viewer --help`
  - passed
  - `python -m worker.pipeline.fpds_result_viewer --env-file .env.dev --run-id run_20260410_3701`
  - passed with `candidate_count=2`, `review_task_count=2`, `evidence_link_count=32`, `database_schema=public`
- Known issues: browser rendering is static and intentionally local-file friendly, so there is no route framework, SSR, or API fetch contract yet. The exported payload files are meant to be regenerated per run and are not a substitute for the later admin API contract
- Next step: run a live export from a persisted validation/routing run, then use the resulting viewer output as part of `3.9` first end-to-end evidence-pack verification

## 2026-04-11 - WBS 3.9 First End-to-End Run Evidence Pack

- WBS: `3.9`
- Status: `done`
- Goal: execute the first live end-to-end TD Savings prototype chain and commit enough raw outputs plus summary evidence to support prototype acceptance review
- Why now: `3.8` already gave the repo a read-only viewer, so the next required prototype artifact was a real run that covered the three target products and demonstrated evidence-linked reviewability
- Outcome: executed live discovery, snapshot, parse, extraction, normalization, validation/routing, and viewer export for the prototype source set. Committed raw stage outputs under `docs/01-planning/evidence/2026-04-11-first-successful-run/` and added a summary evidence pack document that maps the run back to acceptance criteria. The live viewer payload in `app/prototype/` now reflects the `2026-04-11` validation run covering `TD Every Day`, `TD ePremium`, and `TD Growth`
- Not done: no rerun hardening pass yet, no formal findings memo yet, and no attempt was made to convert the current `validation_error` candidates into clean pass-state output inside this slice
- Key files: `docs/01-planning/evidence/2026-04-11-first-successful-run/evidence-pack.md`, `docs/01-planning/evidence/2026-04-11-first-successful-run/discovery-output.json`, `docs/01-planning/evidence/2026-04-11-first-successful-run/snapshot-output.json`, `docs/01-planning/evidence/2026-04-11-first-successful-run/parse-output.json`, `docs/01-planning/evidence/2026-04-11-first-successful-run/extraction-output.json`, `docs/01-planning/evidence/2026-04-11-first-successful-run/normalization-output.json`, `docs/01-planning/evidence/2026-04-11-first-successful-run/validation-output.json`, `docs/01-planning/evidence/2026-04-11-first-successful-run/viewer-export-output.json`, `app/prototype/viewer-payload.json`, `app/prototype/viewer-payload.js`, `README.md`, `docs/01-planning/WBS.md`
- Decisions: used the three product detail pages as the candidate-producing scope and added `TD-SAV-005`, `TD-SAV-007`, and `TD-SAV-008` only to the snapshot/parse coverage set so the evidence pack proves `HTML detail + current values + governing PDF` coverage without pretending the current pipeline already merges multi-source product truth. Treated the resulting pack as a `Conditional Pass` input because all three target candidates remain reviewable but still have `required_field_missing` validation errors
- Verification:
  - `python -m worker.discovery.fpds_discovery --run-id run_20260411_3901_discovery --correlation-id corr_20260411_3901 --discovery-mode manual`
  - passed and written to the committed discovery artifact
  - `python -m worker.discovery.fpds_snapshot --env-file .env.dev --persist-db --run-id run_20260411_3901_snapshot --correlation-id corr_20260411_3901 --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004 --source-id TD-SAV-005 --source-id TD-SAV-007 --source-id TD-SAV-008`
  - passed with `stored_count=2`, `reused_count=4`, `failed_count=0`
  - `python -m worker.pipeline.fpds_parse_chunk --env-file .env.dev --persist-db --run-id run_20260411_3901_parse --correlation-id corr_20260411_3901 --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004 --source-id TD-SAV-005 --source-id TD-SAV-007 --source-id TD-SAV-008`
  - passed with parse coverage across all 6 scoped sources
  - `python -m worker.pipeline.fpds_extraction --env-file .env.dev --persist-db --run-id run_20260411_3901_extract --correlation-id corr_20260411_3901 --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004`
  - passed with `extracted_field_count=67`, `evidence_link_count=43`
  - `python -m worker.pipeline.fpds_normalization --env-file .env.dev --persist-db --run-id run_20260411_3901_normalize --correlation-id corr_20260411_3901 --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004`
  - passed with `candidate_count=3`, `field_evidence_link_count=43`
  - `python -m worker.pipeline.fpds_validation_routing --env-file .env.dev --persist-db --run-id run_20260411_3901_validate --correlation-id corr_20260411_3901 --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004`
  - passed with `queued_count=3`, `review_task_count=3`
  - `python -m worker.pipeline.fpds_result_viewer --env-file .env.dev --run-id run_20260411_3901_validate`
  - passed with `candidate_count=3`, `review_task_count=3`, `evidence_link_count=43`, `database_schema=public`
- Known issues: all three target product candidates still land in `validation_error` with `required_field_missing`, so the current prototype can prove reviewability and evidence lineage but not yet high-confidence canonical completeness. The discovery output still contains many expected warning-only external or out-of-registry links, which is acceptable under the registry policy but noisy for reviewers. Rerun reproducibility was not exercised in this slice
- Next step: write the `3.10` findings memo using this evidence pack as the factual baseline, with explicit recommendations for Growth eligibility handling, supporting-source merge strategy, and rerun hardening

## 2026-04-11 - WBS 3.10 Prototype Findings Memo

- WBS: `3.10`
- Status: `done`
- Goal: turn the first successful run evidence pack into a decision-quality memo that explains what the prototype has proven, what is still weak, and whether Gate B should pass now
- Why now: `3.9` produced the required live evidence artifacts, but prototype acceptance still needed an explicit interpretation of quality gaps, special-case risk, and expansion readiness before the Product Owner can make a Gate B decision
- Outcome: added `docs/01-planning/prototype-findings-memo.md` as the formal findings memo for the TD Savings prototype. The memo records that the prototype has proven end-to-end feasibility, evidence-grounded reviewability, and live viewer inspection across the three target products, while also documenting the main remaining gap: all three target candidates still failed validation with `required_field_missing`. The memo recommends treating Gate B as `Deferred` rather than `Pass` until required-field completeness improves or the Product Owner explicitly accepts the remaining prototype gaps
- Not done: no new pipeline code or live rerun was added in this slice, no Gate B decision note was written yet, and no remediation work was started for the required-field gap or supporting-source merge logic
- Key files: `docs/01-planning/prototype-findings-memo.md`, `docs/01-planning/evidence/2026-04-11-first-successful-run/evidence-pack.md`, `docs/01-planning/evidence/2026-04-11-first-successful-run/validation-output.json`, `app/prototype/viewer-payload.json`, `docs/README.md`, `docs/01-planning/WBS.md`, `README.md`
- Decisions: interpreted the current prototype outcome as `feasibility proven` but not a clean gate pass, because `docs/00-governance/stage-gate-checklist.md` says `Conditional Pass` is not the default operating mode. Framed the memo around three pre-expansion priorities: close required canonical field gaps, improve supporting-source merge, and harden Growth-style special-case normalization before Big 5 work begins
- Verification:
  - reviewed `docs/01-planning/evidence/2026-04-11-first-successful-run/evidence-pack.md`
  - reviewed `docs/01-planning/evidence/2026-04-11-first-successful-run/validation-output.json`
  - reviewed `app/prototype/viewer-payload.json`
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
- Known issues: the repo now has a findings memo, but the memo is intentionally not a Gate B decision note. The actual gate result still belongs to the Product Owner. The underlying quality issue also remains open: the prototype still needs canonical completeness improvement before it should be treated as expansion-ready
- Next step: decide whether to run a targeted hardening slice for required-field closure and supporting-source merge before the Product Owner reviews Gate B

## 2026-04-11 - Post-3.10 Hardening Slice 1: TD Savings Current-Rate Merge

- WBS: `3.10` follow-up hardening
- Status: `done`
- Goal: reduce the prototype `required_field_missing` gap without relaxing validation rules by supplementing missing savings rate fields from an evidence-backed supporting source
- Why now: the findings memo showed that the three target products were reviewable but still failed validation mainly because the target detail pages did not contribute rate fields directly, while the current-rates supporting source already contained product-specific rate tables
- Outcome: added a narrow supporting-source merge baseline to normalization. When a target TD Savings detail source is normalized and a fresh extraction artifact exists for `TD-SAV-005`, normalization now inspects the supporting artifact's retrieval matches, picks the chunk whose anchor or excerpt matches the target product, parses rate-table values, and appends `standard_rate` and `public_display_rate` for `TD Every Day` and `TD ePremium`, plus `standard_rate`, `public_display_rate`, and `promotional_rate` for `TD Growth`. The merge is evidence-linked and leaves a runtime note so the viewer and review flow can see that the candidate was supplemented from current-rate evidence rather than silently overwritten
- Not done: this is still not a general multi-source merge engine. It does not yet merge `TD-SAV-007` or `TD-SAV-008`, it does not resolve every noisy long-text field, and it is deliberately prototype-specific rather than a reusable Big 5 merge framework
- Key files: `worker/pipeline/fpds_normalization/supporting_merge.py`, `worker/pipeline/fpds_normalization/__main__.py`, `worker/pipeline/tests/test_normalization.py`, `worker/pipeline/README.md`, `README.md`
- Decisions: kept the first hardening slice inside normalization orchestration instead of changing validation rules or introducing a brand-new merge stage. Used `TD-SAV-005` only for this slice because it directly addressed the missing-rate blocker with the smallest safe change. Chose product-matched retrieval-result reuse from the stored extraction artifact instead of treating the supporting source as its own candidate-producing record
- Verification:
  - `python -m unittest worker.pipeline.tests.test_normalization`
  - passed with `7` tests
  - `python -m unittest discover -s worker -t .`
  - passed with `45` tests
  - `python -m worker.pipeline.fpds_extraction --env-file .env.dev --persist-db --run-id run_20260411_3511_extract_harden --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004 --source-id TD-SAV-005`
  - passed with `stored_count=4`, `failed_count=0`
  - `python -m worker.pipeline.fpds_normalization --env-file .env.dev --persist-db --run-id run_20260411_3512_normalize_harden --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004`
  - passed with `candidate_count=3`, all `validation_status=pass`
  - `python -m worker.pipeline.fpds_validation_routing --env-file .env.dev --persist-db --run-id run_20260411_3513_validate_harden --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004`
  - passed with `review_task_count=3`, all `validation_status=pass`, all `review_reason_code=manual_sampling_review`
- Known issues: `TD-SAV-005` extraction is still broad and can extract unrelated products if used on its own, so the new merge helper must stay product-matched. The hardening slice fixes the original validation blocker, but it does not yet prove the full generality needed for Big 5 expansion. `TD-SAV-007` and `TD-SAV-008` supporting merge remains future work
- Next step: decide whether the next hardening slice should target governing-PDF merge for `interest_calculation_method` and `fee_waiver_condition`, or whether the Product Owner wants to write the Gate B decision note first now that the three prototype targets can reach pass-state validation

## 2026-04-11 - Post-3.10 Hardening Slice 2: Governing-PDF Merge and Growth Cleanup

- WBS: `3.10` follow-up hardening
- Status: `done`
- Goal: extend the first hardening pass so the prototype uses governing-PDF evidence more intentionally, separates `TD Growth` qualification logic more cleanly, and suppresses the noisiest long-text fields before canonical persistence
- Why now: after Slice 1, the three target candidates could already pass validation, but the Product Owner explicitly called out three remaining quality gaps before `WBS 4`: `TD-SAV-007/008` PDF merge, boosted-rate qualification separation for `TD Growth`, and noisy long-text cleanup
- Outcome: expanded `worker/pipeline/fpds_normalization/supporting_merge.py` so `TD-SAV-002`, `TD-SAV-003`, and `TD-SAV-004` now treat `TD-SAV-005`, `TD-SAV-007`, and `TD-SAV-008` as prototype supporting sources. Current-rate supplementation remains product-matched. A new selective `TD-SAV-008` merge path replaces noisy detail-page `interest_calculation_method` values with governing-PDF wording when the detail page only surfaced link text, and it can also fill `interest_payment_frequency` and `TD Growth` tier wording when stronger PDF evidence exists. An opportunistic `TD-SAV-007` hook was added for `fee_waiver_condition`, but it only applies when a specific refund-the-fee clause is present and the target field is missing or clearly noisy. The same module now performs a narrow text-cleanup pass before normalization, suppressing generic notes, fee-at-a-glance noise, and marketing-style promo text. For `TD Growth`, boosted-rate qualification is now split into cleaner `eligibility_text`, `boosted_rate_eligibility`, and `promotional_period_text` values instead of reusing one long chunk in multiple ambiguous fields
- Not done: this is still not a full general multi-source merge engine, `TD-SAV-007` merge is intentionally opportunistic rather than comprehensive, and `TD-SAV-008` interest-table extraction on its own remains broad if used outside the target-aware normalization path
- Key files: `worker/pipeline/fpds_normalization/supporting_merge.py`, `worker/pipeline/tests/test_normalization.py`, `worker/pipeline/README.md`, `README.md`, `docs/01-planning/prototype-findings-memo.md`
- Decisions: kept the second hardening slice inside normalization prep instead of broadening extraction or adding a separate merge stage. Used governing-PDF evidence only for targeted field replacement when the existing detail-page text was obviously non-canonical. Chose to suppress noisy long-text fields rather than preserve them in canonical payloads simply because extraction found nearby text
- Verification:
  - `python -m unittest worker.pipeline.tests.test_normalization`
  - passed with `9` tests
  - `python -m unittest discover -s worker -t .`
  - passed with `47` tests
  - `python -m worker.pipeline.fpds_extraction --env-file .env.dev --persist-db --run-id run_20260411_3523_extract_harden2 --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004 --source-id TD-SAV-005 --source-id TD-SAV-007 --source-id TD-SAV-008`
  - passed with `stored_count=6`, `failed_count=0`
  - `python -m worker.pipeline.fpds_normalization --env-file .env.dev --persist-db --run-id run_20260411_3524_normalize_harden2 --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004`
  - passed with `candidate_count=3`, all `validation_status=pass`, and runtime notes showing `TD-SAV-008` replacement plus noise suppression
  - `python -m worker.pipeline.fpds_validation_routing --env-file .env.dev --persist-db --run-id run_20260411_3525_validate_harden2 --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004`
  - passed with `review_task_count=3`, all `validation_status=pass`, all `review_reason_code=manual_sampling_review`
  - `python -m worker.pipeline.fpds_result_viewer --env-file .env.dev --run-id run_20260411_3525_validate_harden2`
  - passed with `candidate_count=3`, `review_task_count=3`, `evidence_link_count=43`
- Known issues: `TD-SAV-003` did not need `TD-SAV-008` replacement in the live rerun because its detail-page interest text was already specific enough, so the second slice does not yet prove that every target will always consume every supporting source. `TD-SAV-007` fee-governing merge is present in code but did not surface as a runtime note in this rerun, which means the current prototype source set still does not have a strong live `fee_waiver_condition` use case for the three savings targets
- Next step: decide whether to write the Gate B decision note now that required-field completeness and the highest-risk text-quality gaps are materially better, or run one more focused rerun-hardening slice before the Product Owner closes the gate

## 2026-04-11 - Post-3.10 Hardening Slice 3: TD-SAV-007 Fee-Governing Cleanup

- WBS: `3.10` follow-up hardening
- Status: `done`
- Goal: turn the `TD-SAV-007` fee-governing hook into a real live target improvement instead of leaving it as a dormant merge path
- Why now: after Slice 2, `TD-SAV-007` logic existed in code but had not changed any live prototype candidate. The Product Owner asked specifically to push one more level deeper until the fee-governing PDF affected a real target case
- Outcome: probed live `TD-SAV-007` retrieval and confirmed that the strongest fee-waiver evidence in the governing PDF is still general monthly-fee guidance rather than a product-specific savings waiver rule. Based on that, the normalization merge logic now uses `TD-SAV-007` to review zero-monthly-fee TD savings candidates and suppress noisy `fee_waiver_condition` values instead of preserving raw detail-page fee-table text. This now affects all three prototype targets in live reruns: `TD-SAV-002`, `TD-SAV-003`, and `TD-SAV-004` no longer carry misleading `fee_waiver_condition` values in the exported viewer payload
- Not done: `TD-SAV-007` still does not provide a positive product-specific fee-waiver fill for the prototype savings targets, because the governing PDF language is broader and more chequing-oriented than the target detail pages. This slice therefore improves correctness by suppression, not by new canonical-field population
- Key files: `worker/pipeline/fpds_normalization/supporting_merge.py`, `worker/pipeline/tests/test_normalization.py`, `worker/pipeline/README.md`, `README.md`, `app/prototype/viewer-payload.json`
- Decisions: treated `TD-SAV-007` as governing evidence that some monthly-fee waiver language exists in the broader fee document, but not as proof that the three zero-fee savings targets should persist a `fee_waiver_condition`. Preferred removing misleading fee-waiver text over forcing a weak merge simply to show a populated field
- Verification:
  - `python -m worker.pipeline.fpds_evidence_retrieval --env-file .env.dev --run-id run_20260411_3526_td007_probe --source-id TD-SAV-007 --field-name fee_waiver_condition --field-name monthly_fee --field-name public_display_fee`
  - passed and showed the strongest `fee_waiver_condition` chunk on `page-2` as generic monthly-fee guidance rather than a target-specific savings rule
  - `python -m unittest worker.pipeline.tests.test_normalization`
  - passed with `10` tests
  - `python -m unittest discover -s worker -t .`
  - passed with `48` tests
  - `python -m worker.pipeline.fpds_normalization --env-file .env.dev --persist-db --run-id run_20260411_3527_normalize_harden3 --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004`
  - passed with `candidate_count=3`, all `validation_status=pass`, and runtime notes confirming `TD-SAV-007` review plus `fee_waiver_condition` suppression
  - `python -m worker.pipeline.fpds_validation_routing --env-file .env.dev --persist-db --run-id run_20260411_3528_validate_harden3 --source-id TD-SAV-002 --source-id TD-SAV-003 --source-id TD-SAV-004`
  - passed with `review_task_count=3`, all `validation_status=pass`, all `review_reason_code=manual_sampling_review`
  - `python -m worker.pipeline.fpds_result_viewer --env-file .env.dev --run-id run_20260411_3528_validate_harden3`
  - passed with `candidate_count=3`, `review_task_count=3`, `evidence_link_count=40`
- Known issues: the fee-governing PDF still does not give the prototype a richer positive merge for savings fee-waiver rules, so this slice should be read as a precision improvement rather than a coverage expansion. A future chequing-focused slice may be a better place to reuse the positive balance-waiver language in `TD-SAV-007`
- Next step: decide whether the current prototype quality is now sufficient for a Gate B decision note, or whether one more rerun-hardening pass should focus on repeatability and operator-facing warning summarization

## 2026-04-11 - Gate B Review Note and WBS 3 Completion Assessment

- WBS: `3.10` gate closure follow-up
- Status: `done`
- Goal: convert the prototype evidence, findings memo, and post-memo hardening results into a decision-quality Gate B review note that answers whether `WBS 3` is now complete enough to move into `WBS 4`
- Why now: the prototype had already shipped all `WBS 3.1` to `3.10` slices and three focused hardening passes, but the repo still lacked the formal Gate B note that the governance checklist requires before the Product Owner can close the prototype gate with confidence
- Outcome: added `docs/00-governance/gate-b-prototype-review-note.md` as the Gate B review note. The note records that the first successful run evidence pack originally justified only a conditional prototype read because all three targets still failed validation, but that the later hardening slices closed the main blocker. The current recommendation is now Gate B `Pass`: the three TD savings target products are present, source-type coverage includes detail HTML plus current-values HTML plus governing PDF, the viewer can show evidence-linked fields, and the latest live rerun `run_20260411_3528_validate_harden3` shows all three candidates at `validation_status=pass` with `manual_sampling_review` as the only routing reason. Also updated the root `README.md`, the docs map, and the milestone tracker so the repo reflects that the gate review is now active and the old `Deferred` reading from the findings memo is no longer the latest interpretation
- Not done: did not change `docs/01-planning/WBS.md` or `docs/00-governance/roadmap.md` to mark `WBS 4` as active, because the governance model still makes Product Owner sign-off the formal stage-transition event even though the review note now recommends `Pass`
- Key files: `docs/00-governance/gate-b-prototype-review-note.md`, `README.md`, `docs/README.md`, `docs/00-governance/milestone-tracker.md`
- Decisions: treated the Gate B review note as a decision-quality recommendation rather than pretending the Product Owner approval record already exists. Marked milestone `M2` as `In Progress` to reflect active gate review instead of prematurely calling it `Done`
- Verification:
  - `python -m unittest worker.pipeline.tests.test_normalization`
  - passed with `10` tests
  - `python -m unittest discover -s worker -t .`
  - passed with `48` tests
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
- Known issues: the roadmap document still contains older progress wording and some pre-existing encoding noise, so it was left untouched in this slice pending explicit Product Owner sign-off of Gate B. The Gate B note itself is enough to support the decision, but the final status flip for `WBS 4` should happen together with approval
- Next step: Product Owner reviews the Gate B note and either approves the recommended `Pass` so `WBS 4` can move forward, or requests one more narrow hardening pass before the stage transition is recorded

## 2026-04-11 - Gate B Approval Recorded

- WBS: gate closure follow-up
- Status: `done`
- Goal: record the Product Owner approval of Gate B and update the status documents that must move with an approved stage transition
- Why now: the Gate B review note had already been prepared and the Product Owner explicitly approved it, so the repo needed the formal approval record and status propagation required by the stage-gate checklist
- Outcome: updated `docs/00-governance/gate-b-prototype-review-note.md` from draft recommendation to approved `Pass`, recorded the approval in `docs/00-governance/decision-log.md`, moved milestone `M2` to `Done`, updated `docs/01-planning/WBS.md` so `WBS 3` is marked `Completed` and `WBS 4` is marked `Next`, and refreshed the root `README.md`. The document set now consistently says: Gate B passed, the prototype stage is complete, `WBS 4` is the next approved stage, and no `WBS 4` development has started because the Product Owner requested documentation updates only
- Not done: no implementation work was started for `WBS 4`, and the `4.x` task rows themselves were intentionally left untouched because the stage is approved but not yet in active execution
- Key files: `docs/00-governance/gate-b-prototype-review-note.md`, `docs/00-governance/decision-log.md`, `docs/00-governance/milestone-tracker.md`, `docs/01-planning/WBS.md`, `README.md`
- Decisions: treated Gate B approval as a stage-transition readiness update, not as an implicit start command for the next build stage
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
- Known issues: `docs/00-governance/roadmap.md` still contains older pre-existing encoding noise in historical sections, but the current Gate B state is now added in a clean-text `Gate Update` section near the top
- Next step: wait for explicit Product Owner instruction before starting any `WBS 4` implementation work

## 2026-04-11 - Pre-WBS 4 Harness Readiness Tuning

- WBS: pre-`4.x` readiness
- Status: `done`
- Goal: close the most obvious harness mismatch before `WBS 4` starts, so future admin/frontend package bootstrap does not immediately fight the approved runtime baseline
- Why now: `WBS 4` is the next approved stage and the current harness still ran JavaScript package checks through `npm` only, while the approved baseline already fixed `pnpm` as the frontend package manager
- Outcome: updated `scripts/harness/invoke-project-checks.ps1` so auto-discovered package checks are now `pnpm-first`. The script now reads `packageManager` when present, respects `pnpm-lock.yaml` and npm lockfile signals, uses `pnpm` directly when available, and falls back to `corepack pnpm` before failing. `npm` remains supported only when the package explicitly prefers it. Updated the harness and CI baseline docs plus the root README so the package-check behavior now matches the approved runtime direction before any `WBS 4` package files are added
- Not done: no `package.json` or `pnpm-lock.yaml` exists in the repo yet, so this is a readiness fix rather than a live package-bootstrap verification. CI workflow provisioning for Node remains unchanged for now because the repo still has no tracked JavaScript package to execute
- Key files: `scripts/harness/invoke-project-checks.ps1`, `docs/00-governance/harness-engineering-baseline.md`, `docs/00-governance/foundation-ci-cd-baseline.md`, `README.md`
- Decisions: kept the harness change small and aligned it with the already approved runtime baseline instead of adding broader Node or package bootstrap automation ahead of actual `WBS 4` code
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
- Known issues: the current repo still has no JavaScript package, so the new pnpm-first path is structurally correct but not yet exercised against a real `app/admin` workspace. Once `WBS 4` package bootstrap begins, a follow-up slice may still choose to add explicit Node setup in CI if the repository moves from passive package discovery to active package execution
- Next step: if `WBS 4` starts later, keep the first package bootstrap aligned with `pnpm` by adding `packageManager` to the tracked `package.json` and committing a matching `pnpm-lock.yaml`

## 2026-04-12 - WBS 4.1 Admin Login

- WBS: `4.1`
- Status: `done`
- Goal: implement the first real admin entry slice with DB-backed operator accounts, DB-backed sessions, and a protected admin shell
- Why now: the Product Owner explicitly started `WBS 4` and chose to begin with the durable Postgres-backed account model rather than an env-only bootstrap credential
- Outcome: added `db/migrations/0002_admin_auth.sql` with `user_account`, `admin_auth_session`, and `auth_login_attempt` tables. Added a new FastAPI service package under `api/service/` with login, logout, session introspection, request-id and security-header middleware, Postgres-backed login-attempt throttling, and auth audit-event persistence. Added a bootstrap CLI for the first operator account using scrypt password hashing. Bootstrapped the first live Next.js admin package under `app/admin/` with `/admin/login`, protected `/admin`, middleware-based route gating, and a session-aware overview shell. Updated the relevant README, DB, decision, and WBS documents so the repo now records `4.1` as complete and `4.2` as next
- Not done: review queue, review decision actions, trace viewer, run status pages, and role-specific admin mutations remain follow-on slices. The current admin UI is intentionally just the login flow plus a protected overview shell
- Key files: `db/migrations/0002_admin_auth.sql`, `api/service/api_service/main.py`, `api/service/api_service/auth.py`, `api/service/api_service/bootstrap_admin_user.py`, `app/admin/package.json`, `app/admin/src/app/admin/login/page.tsx`, `app/admin/src/app/admin/page.tsx`, `docs/01-planning/WBS.md`
- Decisions: used DB-backed operator accounts from the start, with `scrypt` password hashing and server-side opaque session cookies. Kept the shared auth contract cookie name `fpds_admin_session`. Added DB-backed login-attempt tracking and temporary lockout so the first login slice already satisfies the baseline retry-threshold expectation instead of leaving brute-force handling entirely for later. Kept the UI scope narrow so `4.1` stays focused on authenticated entry rather than blending into review-queue work
- Verification:
  - `python -m unittest discover -s api/service/tests -t api/service`
  - passed with `3` tests
  - `python -m compileall api/service/api_service`
  - passed
  - `api/service/.venv/Scripts/python -c "import api_service.main; print('api-import-ok')"`
  - passed
  - `node node_modules/typescript/bin/tsc --noEmit`
  - passed
  - `node node_modules/next/dist/bin/next build`
  - passed
- Known issues: `corepack pnpm install` fetched packages and produced `pnpm-lock.yaml`, but it did not finish cleanly in this environment's link step, so local UI verification used `cmd /c npm install --no-package-lock` as a fallback without changing the tracked `packageManager` or adding `package-lock.json`. Also, a stray permission-locked temp folder left by an earlier test attempt is still blocking `repo-doctor`, so the repository health script was not rerun successfully in this slice
- Next step: build `WBS 4.2 review queue` on top of the new authenticated admin shell and session actor model
- Follow-up: hardened the admin service env-file loader after live verification exposed that `uv run --directory api/service ...` resolves relative `FPDS_ENV_FILE` from the service working directory. The loader now also checks the repo root so the documented `.env.dev` startup path works from the workspace root.
- Follow-up: fixed the Next.js 16 login page runtime contract after live dev-server verification showed that `searchParams` is now promise-based in the app router. The admin login route now awaits `searchParams` before reading `next`, so `/admin/login` renders correctly under `next dev`.

## 2026-04-12 - Admin Design-System Refresh

- WBS: `4.1` follow-up UI hardening
- Status: `done`
- Goal: replace the first-pass admin visuals with the new benchmark-aligned FPDS design system while staying inside the current live admin scope
- Why now: the Product Owner asked for a full FPDS design-system refresh based on the Stripe benchmark document, but the only live runtime UI today is the admin login and protected overview. Refreshing those surfaces now keeps the current implementation aligned with the new design authority before `4.2+` surfaces expand
- Outcome: updated the shared FPDS design-token artifacts to the new light-only benchmark values, refreshed the admin runtime theme, replaced the old green glass-like login and overview visuals with a compact shell built around left-rail navigation, top utility, route-oriented triage panels, restrained badges, and explicit empty-state placeholders for future review/run/publish/usage/health surfaces. The login page now presents a neutral elevated operator card, and the protected overview now reads like an actual operations entry shell instead of a one-off feature announcement page
- Not done: no new admin data APIs, review queue routes, run detail routes, publish workflows, locale resources, or public `/dashboard` runtime pages were added in this slice. To avoid running ahead of current scope, future admin surfaces still remain planned placeholders rather than live pages
- Key files: `shared/design/fpds-design-tokens.json`, `shared/design/fpds-theme.css`, `app/admin/src/app/theme.css`, `app/admin/src/app/globals.css`, `app/admin/src/app/admin/login/page.tsx`, `app/admin/src/app/admin/login/LoginForm.tsx`, `app/admin/src/app/admin/page.tsx`, `docs/03-design/fpds-design-system.md`, `README.md`
- Decisions: treated `docs/03-design/fpds_design_system_stripe_benchmark.md` as the more specific authority over the older design-system baseline where the two differed. Kept the admin redesign compact, light-only, and route-oriented. Chose not to add `remember me` or SSO controls because the benchmark mentions them only as optional UI patterns and the current auth implementation does not support them yet. Also kept future admin surfaces visible as planned navigation states instead of wiring broken links or prematurely implementing `4.2+` pages
- Verification:
  - `cmd /c npm run typecheck`
  - passed in `app/admin`
  - `cmd /c npm run build`
  - passed in `app/admin`
- Known issues: the Next.js admin package cannot import workspace-level global CSS directly during production build, so `app/admin/src/app/theme.css` currently mirrors the shared design-theme export for runtime use. The shared token source of truth still remains under `shared/design/`, but future repo tooling may need a more formal frontend token-sync step once multiple apps consume the same theme
- Next step: build `WBS 4.2 review queue` inside the new shell so the first queue surface inherits the refreshed navigation, compact table density, banner vocabulary, and empty-state rules without another visual reset

## 2026-04-13 - Design Baseline Docs Realigned to Template-First Direction

- WBS: design-governance follow-up
- Status: `done`
- Goal: propagate the Product Owner's updated design-system baseline into the surrounding repo documentation so the docs set no longer describes FPDS as primarily a bespoke token-and-primitive system
- Why now: `docs/03-design/fpds-design-system.md` and `docs/03-design/fpds_design_system_stripe_benchmark.md` were updated to shift FPDS toward a `Stripe benchmark + Shadcnblocks template-first` frontend direction. Several surrounding docs still described `shared/design/` as the singular token source of truth or described future frontend work as framework-agnostic, which would make the repo hard to resume from safely
- Outcome: updated the root README, docs map, shared module summary, shared design README, and app-surface README files so they now describe the new authority split: Stripe for structural benchmark, Shadcnblocks for template/block implementation base, and FPDS for domain-specific UI behavior. Added three supporting design-governance docs: `shadcnblocks-adoption-log.md`, `shadcnblocks-block-inventory.md`, and `ui-override-register.md`, so future template/block adoption and override decisions have explicit homes in-repo
- Not done: no runtime code, `components.json`, Shadcnblocks CLI setup, premium-registry auth, or actual vendor block adoption was introduced in this slice. The new tracking docs are intentionally empty scaffolds until frontend implementation starts using them for real
- Key files: `README.md`, `docs/README.md`, `shared/README.md`, `shared/design/README.md`, `app/admin/README.md`, `app/public/README.md`, `docs/03-design/shadcnblocks-adoption-log.md`, `docs/03-design/shadcnblocks-block-inventory.md`, `docs/03-design/ui-override-register.md`
- Decisions: treated the newly edited design-system documents as the active authority and updated adjacent docs to match them rather than preserving older wording about bespoke primitives or shared token artifacts as the sole source of truth. Kept `shared/design/` documented as a bridge layer because the current repo still contains token exports there, even though the new design baseline expects future frontend source of truth to move toward `components.json` plus app-level shadcn semantic variables
- Verification:
  - `git diff --check`
  - passed
- Known issues: `docs/README.md` still contains older non-ASCII or encoding-noisy historical text outside the lines touched in this slice, so this update kept changes minimal and targeted. The new Shadcnblocks tracking docs exist, but they will not become useful until future frontend implementation records real vendor template and block adoption events
- Next step: if frontend implementation starts consuming Shadcnblocks assets, record the first adoption slice in `docs/03-design/shadcnblocks-adoption-log.md` and keep the block inventory and override register updated in the same turn

## 2026-04-13 - Admin UI Migrated to Shadcnblocks Foundation

- WBS: `4.1` UI hardening follow-up
- Status: `done`
- Goal: replace the bespoke admin login and overview UI with a real Shadcnblocks-based frontend foundation while preserving the existing FPDS admin auth and route-gating behavior
- Why now: the Product Owner updated the design baseline to make Shadcnblocks the implementation authority, provided a working `SHADCNBLOCKS_API_KEY`, and asked for the live admin runtime to move from docs-only alignment to actual vendor-first UI adoption
- Outcome: added `app/admin/components.json`, Tailwind 4 or PostCSS setup, shadcn utility wiring, and the first installed Shadcnblocks assets under `app/admin/src/components/`. Reworked the imported `login2`, `application-shell5`, `stats5`, and `banner1` blocks into FPDS-ready variants for the real operator login and protected `/admin` overview. The old `src/app/theme.css` mirror was removed and the admin app now styles directly from app-local shadcn semantic variables in `src/app/globals.css`
- Not done: no new live admin routes beyond `/admin/login` and `/admin` were added, review queue data is still not wired, and vendor-derived blocks remain directly edited rather than wrapped behind a separate FPDS component layer
- Key files: `app/admin/components.json`, `app/admin/postcss.config.mjs`, `app/admin/src/app/globals.css`, `app/admin/src/components/login2.tsx`, `app/admin/src/components/application-shell5.tsx`, `app/admin/src/components/stats5.tsx`, `app/admin/src/components/banner1.tsx`, `app/admin/src/app/admin/login/page.tsx`, `app/admin/src/app/admin/page.tsx`, `docs/03-design/shadcnblocks-adoption-log.md`
- Decisions: used `radix-nova` in `components.json` as the active admin style baseline. Installed Shadcnblocks blocks through the authenticated registry and accepted direct edits to those vendor-derived files for this first runtime slice because the stock demo content did not match FPDS operator auth or admin information architecture. Kept FPDS auth flow server-side and did not add social auth, remember-me, or preview-only dummy routes
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
- Known issues: the imported Shadcnblocks blocks depend on the `radix-ui` package and on Tailwind 4 CSS import semantics, so future block adoption should expect app-level dependency or CSS adjustments rather than assuming the registry output is immediately production-ready. Several vendor-derived files now carry FPDS-specific edits, so upgrade work should consult the new override register before replacing them wholesale
- Next step: build `WBS 4.2 review queue` on top of the new Shadcnblocks shell and prefer wrapper components for future vendor-derived page sections where possible

## 2026-04-13 - CI Markdown Link Portability Fix

- WBS: harness follow-up
- Status: `done`
- Goal: fix GitHub Actions failures caused by local Windows absolute-path Markdown links that cannot resolve in Linux CI
- Why now: the foundation checks started failing in GitHub Actions because the cleanup audit treats broken local Markdown references as errors, and the first-successful-run evidence pack plus the prototype README still used `/d:/...` links copied from a local workspace
- Outcome: replaced the broken absolute workspace links in the first successful run evidence pack and in `app/prototype/README.md` with repository-relative links that resolve both locally and in CI
- Not done: did not rewrite older historical journal text that still references the removed `app/admin/src/app/theme.css`; this slice only fixed the actively failing Markdown references
- Key files: `docs/01-planning/evidence/2026-04-11-first-successful-run/evidence-pack.md`, `app/prototype/README.md`
- Decisions: prefer repo-relative Markdown links in committed docs and evidence packs, even when local clickable absolute links are convenient inside chat or editor output
- Verification:
  - `git diff --check`
  - pending rerun after this slice
- Known issues: `tmpnf6kizz_/` still reports a permission-denied warning during broad repository scans in this environment, but it is unrelated to the Markdown link failure
- Next step: rerun the foundation checks or the cleanup audit so CI can confirm the broken-link set is cleared

## 2026-04-13 - Harness Scan Hardened Against Inaccessible Temp Directories

- WBS: harness follow-up
- Status: `done`
- Goal: stop repository-wide harness scans from failing when a stray inaccessible temp directory exists inside the workspace
- Why now: after the broken Markdown links were fixed, local foundation checks were still being interrupted by the unreadable `tmpnf6kizz_/` directory left in the repo root from an earlier failed process
- Outcome: updated the shared harness file-discovery helpers and project package discovery so recursive scans now skip unreadable paths instead of failing the whole run. The scan filters also now ignore generated or vendor directories such as `node_modules`, `.next`, and `.venv`, which keeps Markdown and JSON validation focused on repo-owned files
- Not done: the broken temp directory itself could not be deleted in this session because ACL repair and low-level removal both returned access denied
- Key files: `scripts/harness/shared.ps1`, `scripts/harness/invoke-project-checks.ps1`
- Decisions: prefer making the harness resilient to unreadable generated folders instead of assuming the workspace is always perfectly clean. Keep generated dependency or build directories out of broad repo validation by default
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1`
  - repo doctor and foundation baseline passed; the run then continued past the temp-folder failure point and stopped later on a separate local `pnpm.exe` access-denied issue
- Known issues: the inaccessible `tmpnf6kizz_/` directory still exists on disk and `git status` continues to warn about it. The remaining local harness failure is now a separate `pnpm.exe` execution-permission issue rather than a recursive-scan permission error
- Next step: if local full-harness execution is still needed in this environment, investigate the Windows `pnpm.exe` access-denied behavior separately from the temp directory

## 2026-04-13 - Foundation CI Dependency Bootstrap Fix

- WBS: harness follow-up
- Status: `done`
- Goal: stop GitHub Actions foundation checks from failing when `app/admin` package scripts run before frontend dependencies are installed
- Why now: the shared foundation entrypoint reached the live `app/admin` `typecheck` script in CI, but the Ubuntu runner had no `node_modules`, so TypeScript reported broad `next`, `react`, and package-resolution failures that were not real code regressions
- Outcome: updated `scripts/harness/invoke-project-checks.ps1` so the shared package-check entrypoint installs missing dependencies before running package scripts and prefers `corepack pnpm` for the approved frontend baseline. Updated `.github/workflows/harness.yml` so the foundation workflow now pins Node `24` and reuses the same repository entrypoint instead of reimplementing package logic in YAML. Refreshed the harness and CI baseline docs plus the root README so the new behavior is recorded in-repo
- Not done: did not add a second package workspace or change the actual `app/admin` package contents. This slice was only about making the existing shared checks runnable in CI
- Key files: `scripts/harness/invoke-project-checks.ps1`, `.github/workflows/harness.yml`, `docs/00-governance/harness-engineering-baseline.md`, `docs/00-governance/foundation-ci-cd-baseline.md`, `README.md`
- Decisions: keep dependency install orchestration inside the shared PowerShell entrypoint so local and CI behavior stay aligned. Use `actions/setup-node` only for runtime provisioning and cache setup, not for duplicating per-package install logic in workflow YAML
- Decisions: keep dependency install orchestration inside the shared PowerShell entrypoint so local and CI behavior stay aligned. Use `actions/setup-node` only for runtime provisioning, not for duplicating per-package install logic in workflow YAML. Avoid `cache: pnpm` here because the action evaluates pnpm before the shared entrypoint has a chance to resolve it through `corepack`
- Verification:
  - `git diff --check`
  - passed with line-ending warnings only
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1`
  - repo doctor passed, foundation baseline passed, `app/admin` `typecheck` passed, and the run then stopped on a separate Windows-local `next build` `spawn EPERM` failure
- Known issues: the original CI blocker from missing frontend dependencies is addressed, but this local Windows environment still has a separate `next build` `spawn EPERM` problem that should be treated independently from the GitHub Actions fix
- Next step: rerun `scripts/harness/invoke-foundation-checks.ps1` and then recheck the GitHub Actions workflow result with the new Node plus Corepack bootstrap in place

## 2026-04-13 - Customer Progress Report Draft Prepared

- WBS: delivery reporting support
- Status: `done`
- Goal: prepare a customer-facing first progress report covering project start through `2026-04-12` using a conservative status line that stays aligned to the published schedule
- Why now: the Product Owner needed a shareable written progress update for the first customer reporting cycle and explicitly wanted the external message to remain on-schedule rather than exposing the full internal lead
- Outcome: added `docs/customer-reports/customer-progress-report-2026-04-12.md` as the first customer-facing progress report draft and introduced `docs/customer-reports/` as the dedicated location for customer-shareable reporting documents. The report is written in English, summarizes the period as `On schedule`, records detailed design and Foundation Setup as complete, reports the Prototype core pipeline plus first internal end-to-end verification as complete, and keeps `Admin/Ops Core` framed as the next stage rather than over-reporting the internal lead
- Not done: did not convert this draft into a branded client template, slide deck, or bilingual version. Also did not disclose the fuller internal status line of `Gate B Pass` plus `WBS 4.1` completion because this slice intentionally preserved customer-facing buffer
- Key files: `docs/customer-reports/README.md`, `docs/customer-reports/customer-progress-report-2026-04-12.md`, `docs/00-governance/development-journal.md`
- Decisions: used a conservative external reporting line that remains factually correct while avoiding premature customer expectations about later-phase completion. Framed progress around completed foundations, prototype core implementation, and internal verification rather than around internal WBS lead indicators
- Verification:
  - `git diff --check`
  - pending
- Known issues: the report is currently a repository markdown draft only, so any final customer branding or formatting adaptation still remains a follow-on packaging task
- Next step: reuse this report draft as the base text for the customer submission and adjust wording only if the Product Owner wants a more formal or more executive-style tone

## 2026-04-13 - WBS 4.2 Review Queue

- WBS: `4.2`
- Status: `done`
- Goal: deliver the first real reviewer intake surface on top of persisted prototype `review_task` data
- Why now: `WBS 4.1` already gave the admin runtime a protected shell and DB-backed session model, while `WBS 3.7` had already persisted queueable review tasks. That made the review queue the smallest live admin slice that could add real operational value without jumping ahead to review decisions or evidence trace
- Outcome: added `GET /api/admin/review-tasks` to the FastAPI admin service with active-state defaults, search, filters, pagination, and sorting against `review_task` plus `normalized_candidate`. Added protected `/admin/reviews` and reserved `/admin/reviews/:reviewTaskId` routes in the Next.js admin app. The new queue route now shows filtered review-task counts, a table-first reviewer intake surface, queue-specific badges, pagination, and stable drill-in links while keeping decision and trace work explicitly out of this slice. The admin shell and overview were also updated so Review Queue is now a live route instead of a planned placeholder
- Not done: no review decision mutations, no trace/evidence pane, no assignment or lock metadata, no bulk actions, and no locale-resource wiring were added. The review-detail route is intentionally just a placeholder until `4.3` and `4.4`
- Key files: `api/service/api_service/main.py`, `api/service/api_service/review_queue.py`, `api/service/tests/test_review_queue.py`, `app/admin/src/app/admin/reviews/page.tsx`, `app/admin/src/app/admin/reviews/[reviewTaskId]/page.tsx`, `app/admin/src/components/fpds/admin/review-queue-surface.tsx`, `app/admin/src/components/application-shell5.tsx`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/app/admin/page.tsx`, `docs/01-planning/WBS.md`
- Decisions: defaulted the live queue to `queued` plus `deferred` so the first view stays triage-first. Added a `priority` sort that orders open states ahead of terminal ones, then error/warning validation ahead of pass, then lower confidence ahead of higher confidence. Kept the frontend bank and product-type filter options static for now instead of inventing a new facets API in the same slice. Added a placeholder detail route now so queue drill-in links stay stable without pretending that the trace viewer is already implemented
- Verification:
  - `$env:PYTHONPATH='api/service'; python -m unittest discover -s api/service/tests`
  - passed
  - `cmd /c npm run build`
  - passed in `app/admin`
  - `cmd /c npm run typecheck`
  - passed in `app/admin`
  - `git diff --check`
  - passed with line-ending warnings only
- Known issues: the queue UI currently uses static bank and product-type option lists rather than backend-provided dynamic facets. `/admin/reviews/:reviewTaskId` is only a stable placeholder route today, so review decisions still cannot be completed end-to-end from the admin UI
- Next step: implement the real review-detail data contract and decision actions on `/admin/reviews/:reviewTaskId` so the queue can hand work off to an actual operator decision surface

## 2026-04-13 - WBS 4.3 Review Decision Flow

- WBS: `4.3`
- Status: `done`
- Goal: turn the reserved review-detail route into a real operator decision surface that can complete approve, reject, defer, and edit-and-approve flows against persisted prototype `review_task` data
- Why now: `WBS 4.2` already delivered protected reviewer intake and stable drill-in links, but the queue still dead-ended at a placeholder route. The next smallest meaningful slice was to connect real detail reads, decision mutations, and the first canonical side effects so review work could complete end-to-end inside the admin runtime
- Outcome: added `GET /api/admin/review-tasks/:reviewTaskId` plus `POST /approve`, `/reject`, `/edit-approve`, and `/defer` routes to the FastAPI admin service. The new decision flow loads candidate summary, normalized fields, source context, evidence snapshot, current canonical continuity match, and append-only decision history. Mutations now update `review_task` and `normalized_candidate`, append `review_decision`, emit review audit events, and on approve or edit-approve perform the first runtime canonical upsert path by creating or updating `canonical_product`, `product_version`, product-version-scoped evidence links, and `change_event` rows. The Next.js admin route `/admin/reviews/:reviewTaskId` is now a live decision surface with approve, reject, defer, and edit-and-approve controls plus JSON override diff preview and a same-origin proxy route for submissions
- Not done: this slice does not implement the full `4.4` trace viewer, assignment or lock metadata, bulk actions, or a fully specified long-term continuity algorithm. The current canonical continuity match is intentionally conservative for the prototype scope and uses exact country, bank, family, type, subtype, and product-name matching
- Key files: `api/service/api_service/main.py`, `api/service/api_service/models.py`, `api/service/api_service/review_detail.py`, `api/service/tests/test_review_detail.py`, `app/admin/src/app/admin/reviews/[reviewTaskId]/page.tsx`, `app/admin/src/app/admin/reviews/[reviewTaskId]/decision/route.ts`, `app/admin/src/components/fpds/admin/review-detail-surface.tsx`, `app/admin/src/lib/admin-api.ts`, `README.md`, `docs/01-planning/WBS.md`
- Decisions: kept the prototype review detail trace lightweight in this slice by exposing evidence summary and excerpts rather than claiming the full trace viewer was already finished. Used a conservative exact-match continuity baseline because the workflow design explicitly leaves the detailed continuity algorithm as follow-on work. Excluded reviewer-overridden fields from product-version evidence-link cloning so manual overrides do not appear evidence-backed when they were operator-supplied
- Verification:
  - `$env:PYTHONPATH='api/service'; python -m unittest discover -s api/service/tests`
  - passed
  - `cmd /c npm run typecheck`
  - passed in `app/admin`
  - `cmd /c npm run build`
  - passed in `app/admin`
- Known issues: edit-and-approve currently uses a JSON object editor instead of a per-field structured form, which is practical for this prototype slice but not yet ideal for less technical operators. The current continuity match is intentionally exact and may need a richer identity strategy before broader bank or product-type expansion
- Next step: implement the full `4.4` trace viewer so field selection, evidence drilldown, and model-run context can support higher-confidence operator review on the same detail route

## 2026-04-13 - WBS 4.4 Evidence Trace Viewer

- WBS: `4.4`
- Status: `done`
- Goal: turn the live review-detail route into the first real evidence trace viewer so operators can inspect field-level evidence, parsed mapping context, and model-stage references before deciding
- Why now: `WBS 4.3` already landed the protected detail route and decision actions, but reviewers still had to work from a lightweight evidence snapshot instead of the trace-pane behavior required by the admin IA and API contract
- Outcome: expanded `GET /api/admin/review-tasks/:reviewTaskId` so it now returns field-trace groups, enriched evidence metadata, validation issue detail, and relevant extraction/normalization/validation model execution references. Reworked `/admin/reviews/:reviewTaskId` into a split-pane detail surface where selecting a normalized field focuses the trace pane on that field's evidence links, parsed mapping metadata, and model-run context while keeping the decision form and override preview on the same page
- Not done: this slice does not add raw parsed-artifact downloads, object-storage direct access, assignment or locking, run history pages, or a structured form-based edit-and-approve editor. It stays inside the approved review-detail route and still avoids exposing private object keys
- Key files: `api/service/api_service/review_detail.py`, `api/service/tests/test_review_detail.py`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/components/fpds/admin/review-detail-surface.tsx`, `README.md`, `api/service/README.md`, `app/admin/README.md`, `app/admin/route-shells/review-detail/README.md`, `docs/01-planning/WBS.md`
- Decisions: kept the trace viewer on the existing review-detail route instead of creating a second trace-only route so the operator can diagnose and decide without context switching. Reused persisted DB metadata only and did not introduce object fetches or raw artifact links, which keeps the trace pane aligned to the private-storage boundary from the design docs. Used stage-level model execution references for extraction, normalization, and validation rather than inventing a new per-evidence execution linkage table in this slice
- Verification:
  - `$env:PYTHONPATH='api/service'; python -m unittest discover -s api/service/tests`
  - passed
  - `cmd /c npm run typecheck`
  - passed in `app/admin`
  - `cmd /c npm run build`
  - passed in `app/admin`
  - `git diff --check`
  - passed with line-ending warnings only
- Known issues: the trace pane still depends on metadata already persisted in `field_evidence_link`, `field_mapping_metadata`, and `model_execution`, so deeper provenance such as raw parsed-body inspection or per-evidence execution lineage remains follow-on work. The edit-and-approve path still uses JSON overrides rather than a field-structured editor
- Next step: build `WBS 4.5` run status so operators can pivot from a review task into full run-level diagnosis when the trace pane suggests broader execution problems

## 2026-04-13 - WBS 4.5 Run Status

- WBS: `4.5`
- Status: `done`
- Goal: deliver the first live run diagnostics surface so operators can move from review detail into run-level execution diagnosis without leaving the protected admin runtime
- Why now: `WBS 4.4` gave reviewers field-level trace and model context, but there was still no dedicated place to explain broader run failures, partial completion, per-source processing impact, or run-linked usage after the trace suggested execution-wide issues
- Outcome: added `GET /api/admin/runs` and `GET /api/admin/runs/:runId` to the FastAPI admin service with protected run list/detail reads, run-type aliasing from persisted metadata, search, filters, pagination, derived stage summaries, source processing summaries, error-event summaries, usage aggregation, and related review-task links. Added protected `/admin/runs` and `/admin/runs/:runId` routes to the Next.js admin app with a table-first run list, partial-completion triage, run detail diagnostics, review drilldowns, and shell navigation updates so operators can move directly from review context into producing-run diagnosis
- Not done: this slice does not add retry actions, audit-history browsing, publish drilldown, correlation-grouped cross-stage rollups, or a separate run-history analytics layer. Current run detail reflects the persisted stage-scoped run records that already exist in the prototype rather than introducing a new correlation-level aggregation model in the same slice
- Key files: `api/service/api_service/run_status.py`, `api/service/api_service/main.py`, `api/service/tests/test_run_status.py`, `app/admin/src/app/admin/runs/page.tsx`, `app/admin/src/app/admin/runs/[runId]/page.tsx`, `app/admin/src/components/fpds/admin/run-status-surface.tsx`, `app/admin/src/components/fpds/admin/run-detail-surface.tsx`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/components/application-shell5.tsx`, `docs/01-planning/WBS.md`
- Decisions: mapped contract-level `run_type` from persisted `run_metadata.pipeline_stage` with fallback to `trigger_type` so the live API can meet the admin contract without a schema migration. Kept run detail metadata browser-safe by exposing only curated per-source metadata keys and by excluding private storage paths or raw object keys from the frontend payload. Used stage-specific persisted run records as the live diagnostic unit because that is the current runtime truth in the database, while keeping correlation id visible for future grouped views
- Verification:
  - `$env:PYTHONPATH='api/service'; python -m unittest discover -s api/service/tests`
  - passed
  - `cmd /c npm run build`
  - passed in `app/admin`
  - `cmd /c npm run typecheck`
  - first run failed on stale `.next/types` route validator before the new routes were reflected
  - `cmd /c npm run typecheck`
  - passed in `app/admin` after the successful build refreshed the generated route types
- Known issues: current run detail derives stage summary and error events from existing `model_execution`, `run_source_item`, and `llm_usage_record` rows because there is still no dedicated persisted stage-summary or run-error-event table. Run history also remains stage-scoped rather than correlation-grouped, so a future grouped run-history view may still be useful if operator usage shows that cross-stage diagnosis needs a higher-level aggregation surface
- Next step: implement `WBS 4.6` change history so operators can move from run diagnosis into canonical change chronology without leaving the admin shell

## 2026-04-13 - WBS 4.6 Change History

- WBS: `4.6`
- Status: `done`
- Goal: deliver the first live canonical change chronology surface so operators can inspect persisted `change_event` history without leaving the protected admin runtime
- Why now: `WBS 4.5` already gave operators run-level diagnosis, but there was still no dedicated place to explain what canonical product changes were approved over time, which fields changed, or when a manual override also emitted audit context
- Outcome: added `GET /api/admin/change-history` to the FastAPI admin service with search, bank/product-type/change-type/date filters, sorting, pagination, changed-field summaries, linked review/run context, and manual-override audit context when present. Added protected `/admin/changes` to the Next.js admin app with a table-first chronology surface, filter controls, review/run drilldowns, and admin-shell navigation updates so canonical change history is now a live operations route instead of a reserved placeholder
- Not done: this slice does not implement `/admin/products/:productId`, a separate audit-log surface, product-record drilldown, or grouped change analytics. Current change chronology stays list-first and relies on the change events already emitted during review approval and edit-approve flows
- Key files: `api/service/api_service/change_history.py`, `api/service/api_service/main.py`, `api/service/tests/test_change_history.py`, `app/admin/src/app/admin/changes/page.tsx`, `app/admin/src/components/fpds/admin/change-history-surface.tsx`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/components/application-shell5.tsx`, `README.md`, `docs/01-planning/WBS.md`
- Decisions: kept `change history` distinct from `product record` per the admin IA instead of folding current canonical truth into the same route. Exposed review and run drilldowns now because those routes are already live, but kept product-record drilldown deferred until its own surface exists. Used the existing `audit_event` table only to enrich `ManualOverride` rows rather than pulling the whole audit-log slice forward
- Verification:
  - `$env:PYTHONPATH='api/service'; python -m unittest discover -s api/service/tests`
  - passed
  - `cmd /c npm run build`
  - passed in `app/admin`
  - `cmd /c npm run typecheck`
  - first parallel run failed before the new Next.js route types were generated for `/admin/changes`
  - `cmd /c npm run typecheck`
  - passed in `app/admin` after the successful build refreshed the generated route types
- Known issues: `Product Record` drilldown is still reserved, so change history currently links only to the already-live review and run routes. `Discontinued` events are supported by the list contract but still depend on a future writer path that emits that event type
- Next step: implement `WBS 4.7` audit log baseline so operators can move from manual-override context into a broader append-only audit trail when needed

## 2026-04-13 - WBS 4.7 Audit Log Baseline

- WBS: `4.7`
- Status: `done`
- Goal: deliver the first protected append-only audit trail surface so operators can inspect review, auth, and trace-access history without leaving the admin runtime
- Why now: `WBS 4.6` already exposed manual-override audit context inside change history, but there was still no dedicated surface for broader audit chronology, actor/request metadata, or trace-access history
- Outcome: added `GET /api/admin/audit-log` to the FastAPI admin service with search, category, event type, actor type, target type, linked entity, date filters, sorting, pagination, actor snapshot enrichment, and review/run drilldowns. Added protected `/admin/audit` to the Next.js admin app with a table-first audit surface, filter controls, shell navigation updates, and route-manifest wiring. Review detail reads now also emit `evidence_trace_viewed` audit events so trace access becomes queryable alongside review decisions and auth history
- Not done: this slice does not implement privilege-change UI, config-change mutation routes, publish action writers, or the later usage-dashboard analytics surface. Publish and usage categories can be queried now but still depend on future writer paths for wider real data coverage
- Key files: `api/service/api_service/audit_log.py`, `api/service/api_service/main.py`, `api/service/api_service/review_detail.py`, `api/service/tests/test_audit_log.py`, `api/service/tests/test_review_detail.py`, `app/admin/src/app/admin/audit/page.tsx`, `app/admin/src/components/fpds/admin/audit-log-surface.tsx`, `app/admin/src/components/application-shell5.tsx`, `app/admin/src/lib/admin-api.ts`, `README.md`, `docs/01-planning/WBS.md`
- Decisions: kept audit log distinct from canonical change history so actor/request chronology does not blur into product-change chronology. Placed audit log under `Operations` in the admin shell because it is primarily an operator diagnosis surface rather than a cost or aggregate-health surface. Added trace-access audit capture at review-detail read time instead of inventing a separate trace-only route because the live detail page already owns sensitive evidence inspection
- Verification:
  - `$env:PYTHONPATH='api/service'; python -m unittest discover -s api/service/tests`
  - passed
  - `cmd /c npm run build`
  - first run failed on a JSX text token in the new audit surface, then passed after replacing the inline state-transition arrow with a JSX-safe text expression
  - `cmd /c npm run typecheck`
  - first parallel run failed before `.next/types` finished generating, then passed when rerun after the successful build
  - `git diff --check`
  - passed with line-ending warnings only
- Known issues: the audit route currently exposes the categories already emitted by live code, so publish/config/usage coverage remains sparse until those writer paths land. `evidence_trace_viewed` emits on each protected detail read, which is acceptable for append-only chronology but may warrant future aggregation or sampling if operator traffic grows significantly
- Next step: implement `WBS 4.8` LLM usage tracking so operators can move from append-only audit chronology into model-cost and anomaly diagnosis on a dedicated usage surface

## 2026-04-13 - WBS 4.8 LLM Usage Tracking

- WBS: `4.8`
- Status: `done`
- Goal: deliver the first protected LLM usage tracking slice so operators can inspect model-cost and token usage by run, agent, model, provider, and time range inside the admin runtime
- Why now: the audit trail slice was already live, and the next operator need was a dedicated surface for usage and anomaly diagnosis using the `llm_usage_record` rows already persisted by worker stages
- Outcome: added `GET /api/admin/llm-usage` to the FastAPI admin service and a protected `/admin/usage` page to the Next.js admin app. The new backend endpoint accepts time-range and scope filters for `from`, `to`, `run_id`, `agent_name`, `model_name`, `provider_name`, `stage`, and search, joins usage rows to `model_execution`, `ingestion_run`, `normalized_candidate`, and `review_task`, and returns dashboard-shaped totals plus per-model, per-agent, per-run, daily trend, and anomaly drilldown aggregates. The new admin route renders those aggregates in a compact read-only triage surface and promotes `Usage` to a live observability route in the shared shell
- Not done: no new usage writer path, billing action, quota enforcement, alerting workflow, or audit-event emission change was added in this slice. The page stays observability-only and does not introduce cost controls or policy mutation
- Key files: `api/service/api_service/main.py`, `api/service/api_service/llm_usage.py`, `api/service/tests/test_llm_usage.py`, `app/admin/src/app/admin/usage/page.tsx`, `app/admin/src/components/fpds/admin/llm-usage-surface.tsx`, `app/admin/src/components/application-shell5.tsx`, `app/admin/src/lib/admin-api.ts`, `app/admin/route-shells/usage/README.md`, `api/service/README.md`, `app/admin/README.md`, `README.md`, `docs/01-planning/WBS.md`
- Decisions: kept the response dashboard-shaped instead of paginated because the contract calls for aggregate views and anomaly candidates. Kept the frontend route read-only and aligned it to the existing triage-first admin surfaces instead of introducing a second dashboard style. Used in-memory anomaly scoring over the persisted rows because the current schema already carries the needed context but does not yet have a dedicated summary table
- Verification:
  - `$env:PYTHONPATH='api/service'; python -m unittest api.service.tests.test_llm_usage`
  - passed
  - `$env:PYTHONPATH='api/service'; python -m unittest discover -s api/service/tests`
  - passed
  - `python -m py_compile api/service/api_service/main.py api/service/api_service/llm_usage.py api/service/tests/test_llm_usage.py`
  - passed
  - `cmd /c npm run build`
  - passed in `app/admin`
  - `cmd /c npm run typecheck`
  - passed in `app/admin`
- Known issues: current pipeline usage rows still skew heavily toward zero-token `heuristic-no-llm-call` records, so real provider traffic is still needed before anomaly ranking and cost interpretation can be judged beyond the prototype baseline
- Next step: implement `WBS 4.9` usage dashboard v1 refinements or move on to the next approved admin or ops slice once live operator feedback arrives
## 2026-04-13 - WBS 4.9 Usage Dashboard v1

- WBS: `4.9`
- Status: `done`
- Goal: turn the live `/admin/usage` baseline into a clearer dashboard-v1 surface so operators can scope, interpret, and drill into token and cost drift without leaving the admin shell
- Why now: `WBS 4.8` already exposed the protected usage route and aggregation API, but the route still felt closer to a baseline observability slice than a completed admin dashboard because provider or stage scoping, scope coverage signals, and richer anomaly context were still thin
- Outcome: expanded the protected usage page so it now supports free-text search plus provider and stage filters in addition to the existing date, run, agent, and model controls. The page now surfaces scope coverage and density signals, model/agent/run concentration hotspots, richer totals, trend deltas, and denser anomaly drilldown context. The usage aggregation backend now also returns share percentages, average cost or token density, and day-over-day trend state or summary fields so the dashboard can explain movement instead of only listing raw totals
- Not done: this slice does not add quota enforcement, alert routing, budget caps, or billing workflow. It remains a read-only observability surface and still depends on the persisted `llm_usage_record` rows already emitted by the pipeline
- Key files: `app/admin/src/app/admin/usage/page.tsx`, `app/admin/src/components/fpds/admin/llm-usage-surface.tsx`, `api/service/api_service/llm_usage.py`, `app/admin/README.md`, `api/service/README.md`, `app/admin/route-shells/usage/README.md`, `README.md`, `docs/01-planning/WBS.md`
- Decisions: kept the route inside the existing Shadcnblocks-based admin shell and improved density through composition instead of adding a second dashboard style. Reused the existing `/api/admin/llm-usage` contract shape and extended it with share or trend interpretation fields rather than introducing a separate usage-summary endpoint. Kept provider and stage as optional scope filters because the backend already had the needed metadata and operator diagnosis benefits from exposing it directly
- Verification:
  - `$env:PYTHONPATH='api/service'; python -m unittest api.service.tests.test_llm_usage`
  - passed
  - `$env:PYTHONPATH='api/service'; python -m unittest discover -s api/service/tests`
  - passed
  - `cmd /c npm run typecheck`
  - passed in `app/admin`
  - `cmd /c npm run build`
  - passed in `app/admin`
- Known issues: usage quality is still only as representative as the current prototype traffic, and the anomaly heuristics still operate on the persisted row set rather than a dedicated historical summary store. Locale resources for this route also remain follow-on work under the broader admin i18n slice
- Next step: move to the next approved admin or ops surface, or revisit usage once live provider traffic justifies alerting, quota, or budget-governance follow-up
## 2026-04-13 - WBS 4.10 Operational Scenario QA

- WBS: `4.10`
- Status: `done`
- Goal: close the final `WBS 4` task by producing explicit Gate C QA evidence for the operator path from review decision into history, audit, and run drilldown
- Why now: `WBS 4.1` through `4.9` already gave the admin runtime all required protected surfaces, but the last row in the WBS still needed a scenario-style verification slice proving that those surfaces stay linked together in operator terms instead of only existing as isolated feature slices
- Outcome: added `api/service/tests/test_ops_scenario_qa.py` as a dedicated scenario test that exercises `edit_approve`, canonical change-event side effects, manual-override audit emission, change-history linkage, audit-log linkage, and run-detail continuity together. Updated `app/admin/tsconfig.json` so the standalone TypeScript check resolves the current Next-generated `.next/types` validator imports cleanly during QA. Created `docs/00-governance/wbs-4-ops-scenario-qa-summary.md` and `docs/00-governance/gate-c-admin-ops-review-note.md`, updated the milestone tracker and WBS row, refreshed the root README plus package READMEs, and corrected the roadmap gate update so the repo now records `4.10` as complete and carries a documented Gate C `Pass` recommendation
- Not done: did not mark `WBS 5` active, did not add a recorded browser demo artifact, and did not add a Gate C approval entry to the decision log because the governance model still makes Product Owner sign-off the formal stage-transition event
- Key files: `api/service/tests/test_ops_scenario_qa.py`, `app/admin/tsconfig.json`, `docs/00-governance/wbs-4-ops-scenario-qa-summary.md`, `docs/00-governance/gate-c-admin-ops-review-note.md`, `docs/00-governance/milestone-tracker.md`, `docs/01-planning/WBS.md`, `README.md`, `api/service/README.md`, `app/admin/README.md`, `docs/00-governance/roadmap.md`
- Decisions: treated this slice as gate-evidence closeout rather than new surface work, and kept the stage-transition boundary explicit so engineering can recommend `Pass` without silently consuming the Product Owner's approval role
- Verification:
  - `$env:PYTHONPATH='api/service'; python -m unittest api.service.tests.test_ops_scenario_qa`
  - passed
  - `$env:PYTHONPATH='api/service'; python -m unittest discover -s api/service/tests`
  - passed
  - `cmd /c npm run typecheck`
  - passed in `app/admin`
  - `cmd /c npm run build`
  - passed in `app/admin`
- Known issues: the remaining open item is governance, not implementation. Product Owner approval is still needed on the new Gate C note before `WBS 5` can become the formally active stage
- Next step: Product Owner reviews the QA summary and Gate C note, then records `Pass` or `Deferred` and decides whether to unlock `WBS 5`

## 2026-04-13 - WBS 5.1 Big 5 Source Registry

- WBS: `5.1`
- Status: `done`
- Goal: close the Canada Big 5 source-registry baseline so `5.2`, `5.3`, and `5.4` can start from committed source files instead of prototype-only TD scope
- Why now: the Product Owner explicitly approved `WBS 5` start, and parser expansion would stay blocked without an approved active registry beyond the existing TD savings prototype seed
- Outcome: added a committed registry catalog plus `15` per-bank or product-type registry files covering `RBC`, `TD`, `BMO`, `SCOTIA`, and `CIBC` across `chequing`, `savings`, and `gic`. Added a catalog loader and tests that verify the `5 x 3` matrix and loadability of every registry file. Added a planning baseline document that fixes the `5.1` completeness cutline as `approved active baseline for parser expansion`, updated the worker README to explain the new catalog boundary, generalized a few TD-specific discovery messages, and refreshed governance or status documents to reflect Gate C approval, WBS 5 start, and `5.1` completion
- Not done: did not implement new bank-specific discovery fixtures, live crawling automation, parser logic for non-TD banks, or public UI runtime code. Some future supporting PDFs and low-confidence edge pages remain intentionally deferred to later approved registry refresh or parser slices
- Key files: `worker/discovery/data/source_registry_catalog.json`, `worker/discovery/data/*.json`, `worker/discovery/fpds_discovery/catalog.py`, `worker/discovery/tests/test_registry_catalog.py`, `docs/01-planning/canada-big5-source-registry.md`, `docs/01-planning/WBS.md`, `docs/00-governance/decision-log.md`, `docs/00-governance/milestone-tracker.md`, `docs/00-governance/roadmap.md`, `README.md`
- Decisions: kept the existing TD savings registry unchanged as the prototype truth source. Treated `5.1 complete` as an approved active baseline for all Big 5 banks and all in-scope product types, while leaving future source enrichment to the registry refresh approval flow. Allowed clearly standalone USD savings variants only as `P1`
- Verification:
  - `python -m unittest discover -s worker/discovery/tests -t .`
  - passed
- Known issues: current runnable offline discovery fixtures still target TD savings, so future bank-specific discovery rule differences will need coverage as `5.2` to `5.4` progress. A few bank source URLs were chosen from currently published official consumer pages and may still need later promotion or deprecation if the banks change their public lineup
- Next step: implement `WBS 5.2` chequing parser expansion against the new registry catalog and add the first non-TD discovery or parser fixtures

## 2026-04-13 - WBS 5.2 Chequing Parser Expansion

- WBS: `5.2`
- Status: `done`
- Goal: make `chequing` a first-class runnable parser path instead of a registry-only placeholder
- Why now: `5.1` closed the Canada Big 5 source-registry baseline, and the next blocker was getting chequing-specific fields and taxonomy behavior through the worker stages with real test coverage
- Outcome: expanded evidence-retrieval hints and extraction heuristics for chequing-only fields such as `included_transactions`, `unlimited_transactions_flag`, `interac_e_transfer_included`, `overdraft_available`, `cheque_book_info`, `student_plan_flag`, and `newcomer_plan_flag`. Updated normalization so chequing requiredness is validated at normalization time, integer field values are preserved, student/newcomer stay orthogonal flags or tags, and chequing subtype inference now aligns with the approved schema (`standard`, `package`, `interest_bearing`, `premium`, `other`). Also updated worker CLI source-id resolution so parse, retrieval, extraction, normalization, validation, and viewer export can resolve catalog-managed Big 5 source ids without manually swapping the default TD savings registry file
- Not done: this slice did not add bank-specific chequing supporting-merge logic, live chequing evidence packs, public UI work, or the later `5.3` savings and `5.4` GIC parser expansion
- Key files: `worker/discovery/fpds_discovery/catalog.py`, `worker/pipeline/fpds_evidence_retrieval/service.py`, `worker/pipeline/fpds_extraction/service.py`, `worker/pipeline/fpds_normalization/service.py`, `worker/pipeline/fpds_parse_chunk/__main__.py`, `worker/pipeline/fpds_extraction/__main__.py`, `worker/pipeline/fpds_normalization/__main__.py`, `worker/pipeline/fpds_validation_routing/__main__.py`, `worker/pipeline/fpds_result_viewer/__main__.py`, `worker/pipeline/tests/test_extraction.py`, `worker/pipeline/tests/test_normalization.py`
- Decisions: kept TD savings supporting-merge logic intentionally narrow instead of forcing a premature cross-bank merge layer into `5.2`. Matched chequing subtype behavior to the canonical schema and kept `student` or `newcomer` as flags or tags rather than subtype values
- Verification:
  - `python -m unittest worker.discovery.tests.test_registry_catalog worker.pipeline.tests.test_extraction worker.pipeline.tests.test_normalization worker.pipeline.tests.test_validation_routing`
  - passed
  - `python -m py_compile worker/discovery/fpds_discovery/catalog.py worker/pipeline/fpds_parse_chunk/__main__.py worker/pipeline/fpds_evidence_retrieval/__main__.py worker/pipeline/fpds_evidence_retrieval/service.py worker/pipeline/fpds_extraction/__main__.py worker/pipeline/fpds_extraction/service.py worker/pipeline/fpds_normalization/__main__.py worker/pipeline/fpds_normalization/service.py worker/pipeline/fpds_validation_routing/__main__.py worker/pipeline/fpds_result_viewer/__main__.py`
  - passed
  - `python -m unittest discover -s worker -t .`
  - passed
  - `git diff --check`
  - passed with line-ending warnings only
- Known issues: chequing parser coverage is now wired through the worker stages, but the supporting-source merge layer still remains TD savings-specific and later bank-level exceptions still belong in `5.5`
- Next step: implement `WBS 5.3` savings parser expansion against the same catalog-backed runner path

## 2026-04-13 - WBS 5.3 and 5.4 Savings and GIC Parser Expansion

- WBS: `5.3`, `5.4`
- Status: `done`
- Goal: extend the catalog-backed parser path so `savings` and `gic` become first-class product types across extraction, normalization, and validation instead of relying on prototype-era partial behavior
- Why now: `5.2` closed the chequing slice and left the remaining approved product-type coverage work concentrated in savings detail-field coverage and GIC term or redeemability handling
- Outcome: expanded evidence-retrieval hints and extraction heuristics so savings runs now pull tiering, withdrawal-limit, and registered signals more deliberately, while GIC runs can extract `term_length_text`, `term_length_days`, `redeemable_flag`, `non_redeemable_flag`, `compounding_frequency`, `payout_option`, and `registered_plan_supported`. Updated normalization so GIC candidates now enforce term-value validity, required minimum deposit or term presence, and redeemability cross-field consistency at normalization time, with non-redeemable subtype inference checked before the broader redeemable match. Added focused unit coverage for savings-specific extraction and normalization fields plus GIC extraction, normalization, and validation-routing cross-field behavior, and refreshed repo status docs plus the worker README to reflect completed `5.3` and `5.4`
- Not done: this slice did not add bank-specific supporting-source merge rules beyond the existing TD savings prototype path, did not create live Big 5 savings or GIC evidence packs, and did not start `5.5` per-bank normalization exceptions
- Key files: `worker/pipeline/fpds_evidence_retrieval/service.py`, `worker/pipeline/fpds_extraction/service.py`, `worker/pipeline/fpds_normalization/service.py`, `worker/pipeline/tests/test_extraction.py`, `worker/pipeline/tests/test_normalization.py`, `worker/pipeline/tests/test_validation_routing.py`, `worker/pipeline/README.md`, `docs/01-planning/WBS.md`, `README.md`
- Decisions: kept the current savings supporting-merge layer TD-specific instead of widening scope into `5.5`. Treated GIC term normalization as heuristic coverage for clear single-term phrases while still allowing `term_length_text` to satisfy requiredness when only human-readable term text is available
- Verification:
  - `python -m unittest worker.pipeline.tests.test_extraction`
  - passed
  - `python -m unittest worker.pipeline.tests.test_normalization worker.pipeline.tests.test_validation_routing`
  - passed
  - `python -m py_compile worker/pipeline/fpds_extraction/service.py worker/pipeline/fpds_evidence_retrieval/service.py worker/pipeline/fpds_normalization/service.py worker/pipeline/tests/test_extraction.py worker/pipeline/tests/test_normalization.py worker/pipeline/tests/test_validation_routing.py`
  - passed
  - `python -m unittest discover -s worker -t .`
  - passed
  - `git diff --check`
  - passed with line-ending warnings only
- Known issues: broader Big 5 savings and GIC quality still depends on future per-bank exception handling and live source verification. The current GIC term-to-days heuristic intentionally handles clear single-term phrases and leaves multi-term ranges primarily in `term_length_text`
- Next step: implement `WBS 5.5` per-bank normalization rule hardening for Big 5 savings and GIC edge cases

## 2026-04-13 - WBS 5.5 Normalization Hardening Baseline

- WBS: `5.5`
- Status: `done`
- Goal: turn `WBS 5.5` from a placeholder row into a concrete hardening slice with explicit scope, boundaries, and completion signals before implementation starts
- Why now: `5.2` to `5.4` closed parser coverage, but the remaining row for `5.5` still only said `bank별 예외 처리`, which was too vague to protect the next slice from hidden scope growth or from bleeding into public API/UI work
- Outcome: strengthened the `WBS 5.5` row and added a scope baseline that fixes the slice around bank-matched supporting-source merge, savings and GIC edge-case normalization, targeted chequing follow-up only when needed for schema alignment, regression coverage, and explicit manual-review deferrals. Also made the boundary against registry expansion and public API/UI work explicit so `5.6` and later slices stay separated
- Not done: no worker code, test fixture, registry, or public-surface changes were made in this slice
- Key files: `docs/01-planning/WBS.md`, `docs/00-governance/development-journal.md`
- Decisions: kept `5.5` focused on normalization hardening rather than discovery expansion or a generic merge-engine redesign. Framed the exit signal around evidence-grounded, reviewable per-bank rules so the public aggregate slice does not absorb unresolved bank-specific ambiguity by accident
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
  - `git diff --check -- docs/01-planning/WBS.md docs/00-governance/development-journal.md`
  - passed
- Known issues: the concrete per-bank rule inventory still belongs to the future implementation slice, so this entry clarifies the cutline but does not yet name every bank/product exception that will be encoded
- Next step: implement `WBS 5.5` using the new scope baseline to drive the first bank-rule inventory, representative fixtures, and regression-backed normalization changes

## 2026-04-13 - WBS 5.6 Aggregate Dataset Generation

- WBS: `5.6`
- Status: `done`
- Goal: generate the aggregate source datasets that the later public products and dashboard APIs can read from instead of joining live canonical tables directly
- Why now: after the `5.5` scope baseline was clarified, the Product Owner explicitly deferred `5.5` implementation and approved moving directly to `5.6` so the public aggregate backing store could be built without waiting for the later bank-specific hardening pass
- Outcome: added a new aggregate refresh migration and worker slice that reads the current canonical deposit dataset, flattens it into `public_product_projection`, and generates persisted `dashboard_metric_snapshot`, `dashboard_ranking_snapshot`, and `dashboard_scatter_snapshot` rows. The new worker also records `aggregate_refresh_run` attempts, marks failed refreshes, and applies the approved public bucket vocabulary for fee, minimum balance, minimum deposit, and term ranges. Added focused tests for bucket assignment, KPI totals, ranking order, scatter coverage, and psql-backed persistence wiring. Updated WBS and status docs so `5.5` is explicitly deferred and `5.6` is explicitly complete
- Not done: this slice did not implement `GET /api/public/products`, dashboard APIs, filter counts, public UI routes, or the deferred per-bank normalization hardening from `5.5`
- Key files: `db/migrations/0003_aggregate_refresh.sql`, `worker/pipeline/fpds_aggregate_refresh/__main__.py`, `worker/pipeline/fpds_aggregate_refresh/models.py`, `worker/pipeline/fpds_aggregate_refresh/service.py`, `worker/pipeline/fpds_aggregate_refresh/persistence.py`, `worker/pipeline/tests/test_aggregate_refresh.py`, `docs/01-planning/WBS.md`, `docs/03-design/product-grid-information-architecture.md`, `worker/pipeline/README.md`, `README.md`
- Decisions: kept the slice DB-backed and aggregate-row-oriented instead of introducing object-storage artifacts for this stage. Stored the approved bucket boundaries in the product-grid IA doc so later APIs and UI work share the same filter vocabulary. Treated the current metric snapshot as the persisted aggregate baseline for the active public scope while leaving richer filtered API behavior to the later public API slices
- Verification:
  - `python -m unittest worker.pipeline.tests.test_aggregate_refresh`
  - passed
  - `python -m py_compile worker/pipeline/fpds_aggregate_refresh/__main__.py worker/pipeline/fpds_aggregate_refresh/models.py worker/pipeline/fpds_aggregate_refresh/service.py worker/pipeline/fpds_aggregate_refresh/persistence.py worker/pipeline/tests/test_aggregate_refresh.py`
  - passed
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
  - `git diff --check -- db/migrations/0003_aggregate_refresh.sql worker/pipeline/fpds_aggregate_refresh worker/pipeline/tests/test_aggregate_refresh.py docs/01-planning/WBS.md docs/03-design/product-grid-information-architecture.md worker/pipeline/README.md README.md docs/00-governance/decision-log.md docs/00-governance/development-journal.md`
  - passed with line-ending warnings only
- Known issues: `5.5` bank-specific normalization hardening is still deferred, so the aggregate rows now reflect the current canonical quality baseline rather than a future bank-exception-complete state
- Next step: implement `WBS 5.7` public products API on top of `public_product_projection`

## 2026-04-14 - WBS 5.7 and 5.8 Public Aggregate APIs

- WBS: `5.7`, `5.8`
- Status: `done`
- Goal: expose the approved public product-grid and dashboard read APIs on top of the aggregate snapshot baseline from `5.6`
- Why now: `5.6` had already created the public aggregate backing store, and the next approved slice was to make that data reachable through anonymous read-only APIs before public UI work starts
- Outcome: added live `GET /api/public/products`, `GET /api/public/filters`, `GET /api/public/dashboard-summary`, `GET /api/public/dashboard-rankings`, and `GET /api/public/dashboard-scatter` routes to the FastAPI service. Added public query normalization, shared localized label helpers, latest-successful-snapshot freshness resolution, projection-backed filtering, public sort and pagination behavior, dashboard summary breakdowns, ranking priority rules, and product-type-aware scatter defaults plus empty-state notes. Also expanded the service config to load public CORS origins and added focused unit coverage for public products, filters, dashboard summary, rankings, scatter, and config parsing
- Not done: this slice did not build the public Next.js UI routes, did not add per-scope precomputed dashboard snapshots beyond the existing `all_active_products` aggregate rows, and did not implement the deferred `5.5` bank-specific normalization hardening
- Key files: `api/service/api_service/main.py`, `api/service/api_service/config.py`, `api/service/api_service/public_common.py`, `api/service/api_service/public_products.py`, `api/service/api_service/public_dashboard.py`, `api/service/tests/test_public_products.py`, `api/service/tests/test_public_dashboard.py`, `api/service/tests/test_config.py`, `api/public/README.md`, `api/service/README.md`, `docs/03-design/api-interface-contracts.md`, `docs/01-planning/WBS.md`, `README.md`
- Decisions: implemented the Product Owner-approved `option 1` approach for `5.8`: dashboard APIs now derive request-time filtered results from the latest successful `public_product_projection` snapshot instead of waiting for precomputed dashboard rows for every possible filter scope. Kept the dashboard metric, ranking, and scatter vocabulary aligned to the approved docs while documenting this narrower implementation detail in the contract docs
- Verification:
  - `python -m py_compile api/service/api_service/public_common.py api/service/api_service/public_products.py api/service/api_service/public_dashboard.py api/service/api_service/main.py api/service/api_service/config.py api/service/tests/test_public_products.py api/service/tests/test_public_dashboard.py api/service/tests/test_config.py`
  - passed
  - `$env:PYTHONPATH='api/service'; python -m unittest api.service.tests.test_public_products api.service.tests.test_public_dashboard api.service.tests.test_config`
  - passed
  - `$env:PYTHONPATH='api/service'; python -m unittest api.service.tests.test_run_status api.service.tests.test_llm_usage`
  - passed
  - `$env:PYTHONPATH='api/service'; python -m unittest discover -s api/service/tests`
  - passed
  - `git diff --check`
  - passed with line-ending warnings only
- Known issues: because the current FastAPI app shares one global CORS middleware for both public and admin surfaces, the service currently allows the combined public/admin origin set with credentials enabled at the app level even though public routes remain anonymous and read-only. Also, dashboard responses are filtered at request time from `public_product_projection`, not from per-filter persisted dashboard scope rows
- Next step: implement `WBS 5.9` Product Grid UI against the new public products and filters routes

## 2026-04-14 - WBS 5.9 Product Grid UI

- WBS: `5.9`
- Status: `done`
- Goal: turn the new public products and filters APIs into the first live public browsing surface
- Why now: `5.7` and `5.8` had already closed the aggregate-backed public read APIs, so the next approved slice was to stand up the public Next.js package and render the Product Grid against those endpoints
- Outcome: added a live `app/public` Next.js package with the approved `radix-nova` public theme layer, a `/products` route that parses shared public filters from the query string, server-fetches anonymous product and filter data, renders the approved heading/filter-summary/card-grid/pagination anatomy, and links to a lightweight `/dashboard` placeholder so the sibling navigation is not broken before `5.10`. The Product Grid now surfaces sticky filter controls, active-filter chips, product-type-aware metric emphasis, freshness messaging, empty-state handling, and paginated product cards for the current public aggregate scope
- Not done: this slice did not implement the actual dashboard UI from `5.10`, did not add the `5.11` cross-filter choreography beyond preserving query-string scope, and did not start the `5.12` locale rollout or `5.14` responsive QA follow-on work
- Key files: `app/public/package.json`, `app/public/src/app/layout.tsx`, `app/public/src/app/products/page.tsx`, `app/public/src/components/fpds/public/product-grid-surface.tsx`, `app/public/src/lib/public-api.ts`, `app/public/README.md`, `docs/01-planning/WBS.md`, `README.md`
- Decisions: kept the public app as its own Next.js package under `app/public/` instead of mixing public routes into the admin package. Fetched global filter vocabulary separately from filtered product results so users can still expand multi-select scope instead of having the option list collapse to only the already-selected bank or product type. Left `/dashboard` intentionally lightweight so `5.9` closes the Product Grid without pretending that `5.10` dashboard behavior is already implemented
- Verification:
  - `corepack pnpm install`
  - partially succeeded for `app/public` package contents but the local `pnpm` link step did not finish cleanly in this environment
  - `node node_modules\\typescript\\bin\\tsc --noEmit`
  - passed
  - `node node_modules\\next\\dist\\bin\\next build`
  - blocked because the local `pnpm` install did not finish creating the `next` binary link in `app/public/node_modules`
- Known issues: the new public package typechecks, but a full Next.js production build could not be completed in this environment because repeated `pnpm install` attempts left `next` in a partial link state under `app/public/node_modules`. The placeholder `/dashboard` route exists only to keep sibling navigation working until `5.10`
- Next step: implement `WBS 5.10` Insight Dashboard UI on top of the existing public dashboard APIs and the new public package shell

## 2026-04-14 - WBS 5.9 build verification follow-up

- WBS: `5.9`
- Status: `done`
- Goal: finish the blocked production-build verification for the new public package without changing approved Product Grid scope
- Outcome: repaired `app/public` so it now uses a fully local pnpm-style `node_modules` layout rooted inside `app/public/node_modules` instead of the earlier broken partial install or cross-package junction workaround. Also tightened `app/public/tsconfig.json` to exclude backup `node_modules.*` folders from typecheck scope
- Key files: `app/public/tsconfig.json`, `docs/00-governance/development-journal.md`
- Decisions: kept the product code unchanged and treated this as an environment recovery slice. Because the local `pnpm.exe` shim returned access-denied and `corepack pnpm` could not reach the npm registry in this restricted environment, rebuilt the public package's pnpm junction structure from the already-working `app/admin/node_modules` layout so every junction target resolves inside `app/public/node_modules`
- Verification:
  - `cmd /c npm run typecheck`
  - passed in `app/public`
  - `cmd /c npm run build`
  - passed in `app/public`
- Known issues: the WinGet-installed `pnpm.exe` remains unusable in this environment and `corepack pnpm` still depends on blocked network access, so this fix restores a valid local package layout but does not resolve the host-level package-manager restriction itself. The placeholder `/dashboard` route still remains intentionally lightweight until `5.10`
- Next step: implement `WBS 5.10` Insight Dashboard UI on top of the verified public package shell

## 2026-04-14 - WBS 5.10 Insight Dashboard UI

- WBS: `5.10`
- Status: `done`
- Goal: implement the public Insight Dashboard UI on top of the aggregate-backed dashboard APIs from `5.8`
- Why now: `5.9` had already established the live public package, shared public filter vocabulary, and sibling route structure, so the next smallest meaningful slice was to turn `/dashboard` from a placeholder into a real market-insight surface
- Outcome: replaced the placeholder `/dashboard` route with a live server-rendered dashboard page that reads the current public scope from the query string, fetches summary, ranking, scatter, and filter metadata in parallel, and renders KPI cards, bank/product-type breakdowns, ranking widgets, a comparative scatter view, and methodology/freshness notes. Added shared public-query parsing and href builders so `/products` and `/dashboard` preserve the same scope vocabulary and added active-state top navigation for the public app shell
- Not done: this slice did not add the `5.11` cross-filter choreography beyond preserving and removing query-string scope, did not start the `5.12` locale rollout, and did not complete the `5.14` responsive QA sweep
- Key files: `app/public/src/app/dashboard/page.tsx`, `app/public/src/components/fpds/public/dashboard-surface.tsx`, `app/public/src/components/fpds/public/public-nav.tsx`, `app/public/src/lib/public-query.ts`, `app/public/src/lib/public-api.ts`, `app/public/src/app/products/page.tsx`, `app/public/src/components/fpds/public/product-grid-surface.tsx`, `README.md`, `app/public/README.md`, `docs/01-planning/WBS.md`
- Decisions: reused the existing Product Grid query vocabulary instead of inventing dashboard-only filter keys. Kept scope adjustment on the Product Grid sibling route so `5.10` closes the dashboard surface without silently pulling `5.11` cross-filter choreography into the same slice. Left the `/` redirect unchanged so landing-route scope stays stable while public follow-on work is still in progress
- Verification:
  - `cmd /c npm run typecheck`
  - passed in `app/public`
  - `cmd /c npm run build`
  - passed in `app/public`
- Known issues: the shell-level top navigation still switches between `/products` and `/dashboard` without preserving the current query string; the in-page sibling links do preserve scope. Locale-specific copy and full responsive QA remain follow-on work
- Next step: implement `WBS 5.11` grid/dashboard cross-filter choreography so the public app can move between both surfaces without losing active scope
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
| 2026-04-09 | Added the WBS 3.1 source discovery core entry |
| 2026-04-09 | Added the WBS 3.1 TD-SAV-007 live URL alignment entry |
| 2026-04-09 | Added the WBS 3.2 snapshot capture core entry |
| 2026-04-09 | Added the WBS 3.2 snapshot capture persistence and live verification entry |
| 2026-04-10 | Added the WBS 3.4 evidence retrieval, source-registry policy, drift-check follow-up, WBS 3.5 extraction, and WBS 3.6 normalization entries |
| 2026-04-10 | Added the WBS 3.7 validation/routing, FPDS design-system, and WBS 3.8 internal result viewer entries |
| 2026-04-11 | Added the WBS 3.9 first successful run evidence-pack entry |
| 2026-04-11 | Added the WBS 3.10 prototype findings memo entry |
| 2026-04-11 | Added the post-3.10 hardening slice 1 entry for TD Savings current-rate merge |
| 2026-04-12 | Added the WBS 4.1 DB-backed admin login implementation entry |
| 2026-04-13 | Added the WBS 4.2 review queue implementation entry |
| 2026-04-13 | Added the WBS 4.3 review decision flow implementation entry |
| 2026-04-13 | Added the WBS 4.4 evidence trace viewer implementation entry |
| 2026-04-13 | Added the WBS 4.5 run status implementation entry |
| 2026-04-13 | Added the WBS 4.6 change history implementation entry |
| 2026-04-13 | Added the WBS 4.7 audit log baseline implementation entry |
| 2026-04-13 | Added the WBS 4.8 LLM usage tracking implementation entry |
| 2026-04-13 | Added the WBS 4.9 usage dashboard v1 implementation entry |
| 2026-04-13 | Added the WBS 4.10 operational scenario QA entry plus Gate C recommendation artifacts |
| 2026-04-13 | Added the WBS 5.1 Big 5 source registry baseline entry and recorded WBS 5 start context |
| 2026-04-13 | Added the WBS 5.2 chequing parser expansion entry and verification results |
| 2026-04-13 | Added the combined WBS 5.3 and 5.4 savings and GIC parser expansion entry and verification results |
| 2026-04-13 | Added the WBS 5.5 normalization hardening baseline entry and clarified its scope boundary in the WBS |
| 2026-04-13 | Added the WBS 5.6 aggregate dataset generation entry, approved bucket baseline, and WBS 5.5 defer context |
| 2026-04-14 | Added the combined WBS 5.7 and 5.8 public aggregate API implementation entry and verification results |
| 2026-04-14 | Added the WBS 5.9 Product Grid UI implementation entry and verification results |
| 2026-04-14 | Added the WBS 5.10 Insight Dashboard UI implementation entry and verification results |
