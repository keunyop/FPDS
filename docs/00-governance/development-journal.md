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

## 2026-04-14 - WBS 5.11 Grid and Dashboard Cross-Filter

- WBS: `5.11`
- Status: `done`
- Goal: close the shared public cross-filter slice so `/products` and `/dashboard` keep the same scope and the dashboard can drill back into the Product Grid without losing context
- Why now: `5.9` and `5.10` had already established both public sibling surfaces on the same query vocabulary, but the top shell still dropped scope and the dashboard still lacked exact drill-in choreography
- Outcome: added a shared-scope URL helper for the public app, made the public sibling nav preserve the active public scope across `/products` and `/dashboard`, and added dashboard-to-grid drill-in links from bank/product-type breakdowns, ranking rows, and scatter points. Ranking drill-ins now carry an aligned Product Grid sort, and single-type drill-ins prune hidden bucket filters before opening the grid so cross-filter state stays meaningful
- Not done: this slice did not add a duplicate full filter form to `/dashboard`, did not implement locale rollout from `5.12`, and did not close the broader responsive QA sweep from `5.14`
- Key files: `app/public/src/lib/public-query.ts`, `app/public/src/components/fpds/public/public-nav.tsx`, `app/public/src/components/fpds/public/dashboard-surface.tsx`, `app/public/src/components/fpds/public/product-grid-surface.tsx`, `app/public/src/app/layout.tsx`, `docs/03-design/product-grid-information-architecture.md`, `docs/01-planning/WBS.md`, `app/public/README.md`, `README.md`
- Decisions: kept shared state URL-based and limited cross-surface carryover to the shared public scope vocabulary rather than carrying Product Grid-only paging/sort state or Dashboard-only axis-preset state through sibling navigation. Kept the Product Grid as the owner of the full filter form and treated the dashboard as a scope-aware summary surface with drill-back actions instead of duplicating filter controls
- Verification:
  - `cmd /c npm run typecheck`
  - passed in `app/public`
  - `cmd /c npm run build`
  - passed in `app/public`
- Known issues: the public header brand link and the `/` redirect still intentionally land on the default Product Grid route instead of preserving current scope. Locale-specific copy and the broader responsive QA sweep remain follow-on work
- Next step: implement `WBS 5.12` locale rollout for the public and admin UI on top of the now-stable public cross-filter behavior

## 2026-04-14 - WBS 5.12 EN/KO/JA Locale Rollout

- WBS: `5.12`
- Status: `done`
- Goal: apply the approved EN/KO/JA locale baseline to the live public and admin UI without violating the source-language preservation rules from the localization governance docs
- Why now: `5.9` to `5.11` had already stabilized the live public surfaces and `4.1` to `4.10` had already stabilized the protected admin shell, so the next approved slice was to wire locale selection, fallback-safe UI copy, and locale-preserving navigation across both packages
- Outcome: added locale-aware runtime helpers for the public and admin packages, introduced visible EN/KO/JA switch controls in the public header and admin shell or login surface, preserved `locale` through sibling nav, redirects, pagination, and protected route transitions, and localized UI-owned labels, shell copy, metadata, and formatting on the live public `/products` and `/dashboard` routes plus the admin login, overview, review queue, and run-status surfaces
- Not done: this slice did not add machine translation for source-derived product, evidence, or condition text; did not change the approved `selected locale -> en -> safe fallback` policy; and did not close the broader responsive QA sweep from `5.14`
- Key files: `app/public/src/lib/public-locale.ts`, `app/public/src/components/fpds/public/public-header.tsx`, `app/public/src/components/fpds/public/public-nav.tsx`, `app/public/src/components/fpds/public/product-grid-surface.tsx`, `app/public/src/components/fpds/public/dashboard-surface.tsx`, `app/public/src/app/layout.tsx`, `app/public/src/app/page.tsx`, `app/public/src/app/products/page.tsx`, `app/public/src/app/dashboard/page.tsx`, `app/admin/src/lib/admin-i18n.ts`, `app/admin/src/components/admin-locale-switcher.tsx`, `app/admin/src/components/admin-locale-document-sync.tsx`, `app/admin/src/components/application-shell5.tsx`, `app/admin/src/components/login2.tsx`, `app/admin/src/components/fpds/admin/review-queue-surface.tsx`, `app/admin/src/components/fpds/admin/run-status-surface.tsx`, `app/admin/src/app/layout.tsx`, `app/admin/src/app/admin/login/page.tsx`, `app/admin/src/app/admin/page.tsx`, `app/admin/src/app/admin/reviews/page.tsx`, `app/admin/src/app/admin/runs/page.tsx`, `app/public/README.md`, `app/admin/README.md`, `shared/i18n/README.md`, `docs/01-planning/WBS.md`, `README.md`
- Decisions: kept locale state URL-based so the public sibling routes and protected admin routes remain resumable and reviewable without introducing a separate client-only locale store. Kept source-derived product names, descriptions, evidence excerpts, and conditions in their original source language instead of translating or duplicating persisted content. Localized only UI-owned labels, helper text, and formatting so the runtime still matches the approved localization governance boundary
- Verification:
  - `cmd /c npm run typecheck`
  - passed in `app/public`
  - `cmd /c npm run build`
  - passed in `app/public`
  - `cmd /c npm run typecheck`
  - passed in `app/admin`
  - `cmd /c npm run build`
  - passed in `app/admin`
- Known issues: the locale rollout currently lives in app-local helper modules rather than a shared runtime package, and the broader screenshot or responsive regression sweep still belongs to `5.14`
- Next step: execute `WBS 5.13` freshness and metric note wording plus `WBS 5.14` responsive QA on top of the now-locale-aware public and admin shells

## 2026-04-15 - WBS 5.13 Freshness and Metric Notes

- WBS: `5.13`
- Status: `done`
- Goal: make the public Product Grid and Insight Dashboard explain freshness, metric meaning, exclusion rules, and public evidence boundaries in locale-aware wording
- Why now: `5.12` had already stabilized EN/KO/JA locale handling across the live public surfaces, so the next approved slice was to close the remaining note wording gap called out in the WBS and design docs
- Outcome: added note-card treatment to the public Product Grid so `/products` now explains how card metrics are prioritized by product type and how public freshness behaves for the current scope. Refined the public dashboard note wording so `/dashboard` now carries richer methodology copy aligned to the aggregate rules, plus more consistent localized chart/ranking/fallback/freshness messaging around the existing public note surfaces
- Not done: this slice did not add a separate `/methodology` route, did not widen the public API contract beyond the existing dashboard note field, and did not start the broader responsive QA sweep from `5.14`
- Key files: `app/public/src/components/fpds/public/product-grid-surface.tsx`, `app/public/src/components/fpds/public/dashboard-surface.tsx`, `api/service/api_service/public_dashboard.py`, `docs/01-planning/WBS.md`, `README.md`, `app/public/README.md`
- Decisions: treated `5.13` as a public note-presentation slice rather than a larger contract redesign. Kept note ownership mostly UI-side for Product Grid presentation while making the dashboard methodology note API-backed so the existing dashboard note slot could stay intact and locale-aware without adding a new response shape
- Verification:
  - `cmd /c npm run typecheck`
  - passed in `app/public`
  - `cmd /c npm run build`
  - passed in `app/public`
  - `$env:PYTHONPATH='api/service'; python -m unittest api.service.tests.test_public_dashboard`
  - passed
- Known issues: some public locale copy still remains app-local instead of coming from one shared runtime package, and `5.14` responsive QA is still the next separate slice
- Next step: execute `WBS 5.14` responsive QA across the locale-aware public Product Grid and Insight Dashboard

## 2026-04-15 - Public Hydration Warning Guard

- WBS: `5.14`
- Status: `done`
- Goal: remove noisy public-app hydration warnings caused by browser-injected root HTML attributes without changing public page behavior
- Why now: the `/products` route was raising a hydration mismatch warning in browser dev tools, and the reported diff showed an extra `crxemulator` attribute on the root `<html>` element rather than a product-surface render mismatch
- Outcome: added `suppressHydrationWarning` to the public app root `<html>` in `app/public/src/app/layout.tsx` so extension-injected attributes on the root element no longer raise a misleading hydration warning during local development
- Not done: this slice did not suppress deeper subtree mismatches, did not change public data rendering, and did not alter locale or formatting behavior
- Key files: `app/public/src/app/layout.tsx`, `docs/00-governance/development-journal.md`
- Decisions: kept the fix intentionally narrow at the root layout because the observed mismatch was extension-driven and isolated to `<html>`. Avoided broad suppression lower in the tree so real public-surface hydration bugs would still surface
- Verification:
  - `cmd /c npm run typecheck`
  - passed in `app/public`
  - `cmd /c npm run build`
  - passed in `app/public`
- Known issues: if a real mismatch appears inside the public app subtree later, React will still surface it; this guard only quiets root-level browser-extension attribute drift
- Next step: continue `WBS 5.14` responsive QA across the locale-aware public Product Grid and Insight Dashboard

## 2026-04-15 - Interim Phase 1 No-BXPF Test Checklist

- WBS: `5.14`, `6.x` support
- Status: `done`
- Goal: document a safe interim test boundary so the team can keep validating Phase 1 work while BX-PF publish remains externally blocked
- Why now: BX-PF readiness is outside the current repo and schedule pressure makes it important to separate "publish blocked" from "all other Phase 1 verification blocked"
- Outcome: added a dedicated governance checklist that states what can be tested now without BX-PF, what must remain explicitly out of scope, which FPDS-owned records already persist approved product data internally, and what evidence to capture for interim QA execution
- Not done: this slice did not implement BX-PF connector code, publish monitor routes, retry/reconciliation runtime behavior, or a completed release-hardening pack
- Key files: `docs/00-governance/phase-1-no-bxpf-test-checklist.md`, `docs/README.md`, `docs/00-governance/development-journal.md`
- Decisions: kept the checklist as an interim QA baseline rather than a scope change. Explicitly separated FPDS internal approval/persistence/public/admin verification from BX-PF publish verification so later release readiness work still has a clear remaining boundary
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1`
  - passed
- Known issues: the checklist helps preserve schedule and testing momentum, but it does not reduce the remaining `WBS 6.x` publish/readiness work required for Phase 1 release sign-off
- Next step: execute the new checklist against the current dev environment and capture a dated QA evidence note with pass/hold results plus representative screenshots and ids

## 2026-04-15 - Source Registry Admin MVP Doc Baseline

- WBS: `5.15` planning support
- Status: `done`
- Goal: document the minimum approved direction for DB-backed source registry management before implementation starts
- Why now: the Product Owner approved admin-side direct source editing and multi-select collection, but asked to lock the docs baseline first and keep the first feature slice intentionally small
- Outcome: updated the requirements, source-registry policy, admin information architecture, and WBS so they now agree on four points: source registry operational source of truth moves to the DB, admin can edit source rows directly in the UI, source-selected collection means full candidate-producing ingestion through `normalized_candidate`, and candidate-producing scope remains role-aware with `detail` sources as the default primary scope
- Not done: no DB schema, API, UI route, migration, or runtime collection changes were implemented in this slice
- Key files: `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`, `docs/03-design/source-registry-refresh-and-approval-policy.md`, `docs/03-design/admin-information-architecture.md`, `docs/01-planning/WBS.md`, `docs/00-governance/development-journal.md`
- Decisions: kept the MVP narrow by deferring diff-heavy registry approval workflow, scheduler governance UI, and generalized auto-discovery management. Explicitly retired JSON as the ongoing operational source of truth once the DB-backed registry lands, while allowing existing JSON files to remain as historical/seed artifacts
- Verification:
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1`
  - passed after rerunning outside the sandbox because the first in-sandbox `app/admin` build attempt hit Windows `spawn EPERM`
- Known issues: the repo runtime still uses file/catalog-oriented source management today, so these documents define the target implementation baseline rather than describing an already-completed runtime
- Next step: design the DB schema and admin/API MVP for `/admin/sources` and `source-collections` before starting implementation

## 2026-04-15 - WBS 5.15 Source Registry Admin MVP Implementation

- WBS: `5.15`
- Status: `done`
- Goal: implement the minimum live admin slice for DB-backed source registry editing plus source-selected candidate-producing collection
- Why now: the documentation baseline for `5.15` was already approved, and the next Phase 1 operator gap was the lack of a live source-management surface that could directly own source rows and launch full collection from the admin console
- Outcome: added a new `source_registry_item` table plus migration, DB-seeded source-registry service utilities, protected admin CRUD and collection-launch APIs, a background collection runner that groups selected sources by bank/product scope and executes snapshot through validation with temporary registry payloads, and live `/admin/sources` plus `/admin/sources/:sourceId` UI routes with filtering, create/edit, multi-select collect, and recent run linkage
- Scope notes: the MVP keeps direct admin editing intentionally simple, uses the DB as the operational source of truth, treats JSON registry files as first-boot seed artifacts only, defines collect as full candidate-producing ingestion through `normalized_candidate`, and constrains primary candidate production to selected `detail` sources while auto-including the current TD savings supporting sources already required by the live normalization path
- Key files: `db/migrations/0004_source_registry_admin.sql`, `api/service/api_service/source_registry_utils.py`, `api/service/api_service/source_registry.py`, `api/service/api_service/source_collection_runner.py`, `api/service/api_service/main.py`, `api/service/api_service/models.py`, `api/service/tests/test_source_registry.py`, `app/admin/src/app/admin/sources/page.tsx`, `app/admin/src/app/admin/sources/[sourceId]/page.tsx`, `app/admin/src/components/fpds/admin/source-registry-surface.tsx`, `app/admin/src/components/fpds/admin/source-detail-surface.tsx`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/components/application-shell5.tsx`, `api/admin/route-manifest.json`, `app/admin/routes.manifest.json`, `README.md`, `api/service/README.md`, `app/admin/README.md`
- Decisions: kept the collection launch asynchronous behind an API-side runner instead of adding queue infrastructure in this slice, reused existing worker modules via temporary grouped registry files instead of rewriting the worker entrypoints first, and limited supporting-source auto-inclusion to the already-proven TD savings merge path so the MVP would not silently broaden candidate-producing scope
- Verification:
  - `python -m unittest discover -s api/service/tests -t api/service`
  - passed
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
  - `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1`
  - passed
- Known issues: source-registry bootstrap still seeds from the committed JSON catalog when the DB table is empty, collection progress currently relies on the existing run surfaces rather than a dedicated source-collection status UI, and supporting-source auto-inclusion is still intentionally narrow rather than generalized across all Big 5 banks and product families
- Next step: exercise the new `/admin/sources` flow against the live dev database with representative Big 5 selections and decide whether the next slice should focus on collection progress ergonomics, generalized supporting-source rules, or explicit DB import/export tooling for source-registry administration

## 2026-04-15 - WBS 5.15 Source Registry Unique Scope Fix

- WBS: `5.15`
- Status: `done`
- Goal: fix the first live `/admin/sources` bootstrap failure caused by reused bank rates URLs across multiple product types
- Why now: the first manual source-registry screen test hit a `UniqueViolation` while seeding `source_registry_item` because RBC reuses the same rates page URL for both `chequing` and `savings`, which exposed that the original uniqueness scope was too narrow
- Outcome: updated the source-registry uniqueness model so the DB now treats `(bank_code, product_type, normalized_url, source_type)` as the logical uniqueness boundary, added a follow-up migration to repair databases that already applied `0004`, and updated the API-service run instructions so local operators apply the fix before testing `/admin/sources`
- Key files: `db/migrations/0004_source_registry_admin.sql`, `db/migrations/0005_source_registry_unique_scope_fix.sql`, `api/service/README.md`, `docs/00-governance/development-journal.md`
- Verification:
  - `python -m unittest discover -s api/service/tests -t api/service`
  - passed
- Known issues: existing local databases that already applied `0004` still need `0005_source_registry_unique_scope_fix.sql` run once before `/admin/sources` bootstrap can succeed
- Next step: apply `0005_source_registry_unique_scope_fix.sql` to the live dev DB, restart the API, and rerun the source-registry screen smoke test

## 2026-04-15 - WBS 5.15 Source Registry Null-Filter Query Fix

- WBS: `5.15`
- Status: `done`
- Goal: fix the follow-up `/admin/sources` list failure caused by nullable filter parameters in the source-registry list SQL
- Why now: after the uniqueness fix, the next live screen request failed with `psycopg.errors.AmbiguousParameter` because PostgreSQL could not infer the type of nullable filter parameters in the `WHERE (%(field)s IS NULL OR ...)` pattern
- Outcome: replaced the nullable-parameter SQL pattern with a dynamic typed WHERE-clause builder that only binds filters actually provided by the request, and added a unit test that verifies empty-filter list requests now execute with an empty parameter map
- Key files: `api/service/api_service/source_registry.py`, `api/service/tests/test_source_registry.py`, `docs/00-governance/development-journal.md`
- Verification:
  - `python -m unittest discover -s api/service/tests -t api/service`
  - passed
  - `python -m py_compile api/service/api_service/source_registry.py api/service/tests/test_source_registry.py`
  - passed
- Known issues: local testers still need the earlier `0005_source_registry_unique_scope_fix.sql` applied if their DB already contains the original `0004` constraint
- Next step: restart the API service and rerun the `/admin/sources` smoke test with empty filters first, then continue with create/edit/collect checks

## 2026-04-15 - WBS 5.15 Bank and Source-Catalog Admin Refinement

- WBS: `5.15`
- Status: `done`
- Goal: realign the source-registry admin MVP so operators manage banks and source catalog coverage while generated source rows stay read-only
- Why now: Product Owner clarified that operators should not edit low-level source detail directly; they should manage a bank list and bank-plus-product coverage, then let collection auto-fill the generated source registry
- Outcome: added `bank` plus `source_registry_catalog_item` management routes and migration support, auto-generated bank codes from bank creation, introduced source-catalog-driven collection that materializes source rows before launching ingestion, converted `/admin/sources` and `/admin/sources/:sourceId` to read-only inspection surfaces, added `/admin/banks`, `/admin/banks/:bankCode`, `/admin/source-catalog`, and `/admin/source-catalog/:catalogItemId`, and updated the requirements/design/README docs to match the new operating model
- Key files: `db/migrations/0006_bank_catalog_management.sql`, `api/service/api_service/source_catalog.py`, `api/service/api_service/main.py`, `api/service/api_service/models.py`, `api/service/tests/test_source_catalog.py`, `api/service/tests/test_source_registry.py`, `app/admin/src/app/admin/banks/page.tsx`, `app/admin/src/app/admin/banks/[bankCode]/page.tsx`, `app/admin/src/app/admin/source-catalog/page.tsx`, `app/admin/src/app/admin/source-catalog/[catalogItemId]/page.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/bank-detail-surface.tsx`, `app/admin/src/components/fpds/admin/source-catalog-surface.tsx`, `app/admin/src/components/fpds/admin/source-catalog-detail-surface.tsx`, `app/admin/src/components/fpds/admin/source-registry-surface.tsx`, `app/admin/src/components/fpds/admin/source-detail-surface.tsx`, `app/admin/src/components/application-shell5.tsx`, `app/admin/routes.manifest.json`, `api/admin/route-manifest.json`, `README.md`, `app/admin/README.md`, `api/service/README.md`, `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`, `docs/03-design/admin-information-architecture.md`, `docs/03-design/source-registry-refresh-and-approval-policy.md`, `docs/01-planning/WBS.md`
- Verification:
  - `python -m unittest discover -s api/service/tests -t api/service`
  - passed
  - `pnpm run typecheck`
  - passed
  - `pnpm run build`
  - passed
- Known issues: the admin UI still keeps legacy `/admin/sources/create`, `/admin/sources/collect`, and `/admin/sources/:sourceId/update` route handlers only to satisfy current Next route validation and legacy compatibility, but the intended operator workflow no longer uses them
- Next step: run the full foundation harness and then do a live manual smoke test that creates a bank, creates a source catalog item, launches collection, and verifies generated source rows appear in `/admin/sources`

## 2026-04-16 - API Service Worker Import Path Fix

- WBS: `5.15`
- Status: `done`
- Goal: fix the API startup failure when running `uv run --directory api/service uvicorn api_service.main:app`
- Why now: the new `source_catalog.py` module imported `worker.discovery...` directly, but `uv run --directory api/service` only guarantees `api/service` on the import path, not the repo root
- Outcome: added a small repo-root import-path guard in `api/service/api_service/source_catalog.py` before the `worker.discovery` imports so the API can start from the documented `api/service` working directory again
- Key files: `api/service/api_service/source_catalog.py`, `docs/00-governance/development-journal.md`
- Verification:
  - `api/service/.venv/Scripts/python.exe -c "import sys; sys.path.insert(0, r'...\\api\\service'); import api_service.main; print('ok')"`
  - passed
- Known issues: none beyond the existing Windows-specific harness need to rerun builds with enough time budget
- Next step: restart the FastAPI service and continue with the manual bank/source-catalog smoke test

## 2026-04-16 - Admin Hydration Warning Guard

- WBS: `5.14`
- Status: `done`
- Goal: remove noisy admin-app hydration warnings caused by browser-injected root HTML attributes without changing admin page behavior
- Why now: the `/admin/login` route raised a hydration mismatch warning in browser dev tools, and the reported diff showed an extra `crxemulator` attribute on the root `<html>` element rather than an admin-surface render mismatch
- Outcome: added `suppressHydrationWarning` to the admin app root `<html>` in `app/admin/src/app/layout.tsx` so extension-injected attributes on the root element no longer raise a misleading hydration warning during local development
- Not done: this slice did not suppress deeper subtree mismatches, did not change admin auth or locale behavior, and did not alter login rendering
- Key files: `app/admin/src/app/layout.tsx`, `docs/00-governance/development-journal.md`
- Decisions: kept the fix intentionally narrow at the root layout because the observed mismatch was extension-driven and isolated to `<html>`. Avoided broad suppression lower in the tree so real admin-surface hydration bugs would still surface
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
- Known issues: if a real mismatch appears inside the admin app subtree later, React will still surface it; this guard only quiets root-level browser-extension attribute drift
- Next step: rerun the `/admin/login` smoke check in local dev to confirm the warning is gone while keeping subtree hydration checks intact

## 2026-04-16 - Bank Registry Modal Workflow Refresh

- WBS: `5.15`
- Status: `done`
- Goal: move the bank admin flow to a search-first list with modal-based add and detail editing so operators do not leave `/admin/banks` for routine bank management
- Why now: Product Owner requested that the bank list sit directly under search and that both add-bank and bank-detail work open in modals instead of forcing a second page transition
- Outcome: reordered `/admin/banks` so search is followed immediately by the bank list, replaced the inline create section with an `Add bank` dialog, switched bank-name clicks to open an editable bank-detail dialog, then refreshed both dialogs to use the requested Shadcnblocks `offer-modal4` shell plus its `field` and `input-group` primitives while keeping the direct `/admin/banks/:bankCode` route as a compatibility deep link
- Not done: this slice did not change the source-catalog workflow, did not remove the direct bank-detail page route, and did not add new backend APIs
- Key files: `app/admin/src/app/admin/banks/page.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/bank-detail-surface.tsx`, `app/admin/src/components/fpds/admin/bank-create-dialog-content.tsx`, `app/admin/src/components/fpds/admin/bank-detail-dialog-content.tsx`, `app/admin/src/components/offer-modal4.tsx`, `app/admin/src/components/ui/dialog.tsx`, `app/admin/src/components/ui/field.tsx`, `app/admin/src/components/ui/input-group.tsx`, `app/admin/src/components/ui/textarea.tsx`, `app/admin/README.md`
- Decisions: kept the modal state URL-addressable through query params so refresh and shareable local QA links still restore the active add/detail modal. Reused the existing bank detail and create proxy routes instead of widening the API surface. Installed the requested Shadcnblocks `offer-modal4` block and adapted its shell as the modal foundation instead of keeping a bespoke dialog wrapper
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
- Known issues: the list now prefers the modal workflow, but the direct `/admin/banks/:bankCode` route remains in place for compatibility and route-level fallback behavior
- Next step: smoke test the revised `/admin/banks` flow in local dev and decide whether source-catalog coverage should adopt the same modal pattern later

## 2026-04-16 - Bank Registry Modal Width Tuning

- WBS: `5.15`
- Status: `done`
- Goal: keep the requested Shadcnblocks `offer-modal4` base while resizing the bank add and detail dialogs so the full workflow fits a single desktop screen more reliably
- Why now: Product Owner clarified that `offer-modal4` should be used as the implementation base, but the bank workflow still needed FPDS look-and-feel and a wider layout because the imported shell was too narrow for practical admin use
- Outcome: widened the shared modal shell, reduced its large-screen left rail, aligned its color treatment with the existing FPDS admin surface, shortened dialog copy, and changed the bank create/detail forms to use two-column top rows plus shorter textarea height so the content fits without the cramped tall layout from the vendor default
- Not done: this slice did not change modal routing, did not alter the bank backend APIs, and did not apply the same width treatment to other admin workflows
- Key files: `app/admin/src/components/offer-modal4.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/bank-create-dialog-content.tsx`, `app/admin/src/components/fpds/admin/bank-detail-dialog-content.tsx`, `app/admin/README.md`
- Decisions: kept the Shadcnblocks block as the implementation foundation, but treated it as a vendor primitive rather than a fixed visual spec so the resulting dialog could follow FPDS tone, spacing, and width requirements
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
- Known issues: actual viewport fit still depends on browser zoom level and local font rendering, so final ergonomic validation should happen in a real `/admin/banks` browser session
- Next step: smoke test add-bank and bank-detail modals in local dev at the Product Owner's usual browser zoom and decide whether the same widened shell should be standardized for source-catalog modals later

## 2026-04-16 - Bank Registry Language and Homepage Cleanup

- WBS: `5.15`
- Status: `done`
- Goal: align the bank-management UI with the approved EN/KO/JA operator language vocabulary, restore missing homepage URLs on existing seeded banks, and simplify the bank list columns
- Why now: Product Owner requested that the bank modal language selector use English, Korean, and Japanese, reported that currently registered banks were showing blank homepage URLs, and asked to remove the low-value `Updated` column from the bank list
- Outcome: changed the bank create and detail surfaces to use `English`, `Korean`, and `Japanese` options backed by `en`, `ko`, and `ja`, removed the `Updated` column from `/admin/banks`, and added a safe seed-profile backfill in the admin API so existing registry banks recover missing homepage URL, normalized homepage URL, and source-language values without overwriting already populated fields
- Not done: this slice did not change source-catalog field labels, did not alter the public UI locale policy, and did not override non-empty bank profile values that operators may already have edited manually
- Key files: `app/admin/src/components/fpds/admin/bank-create-dialog-content.tsx`, `app/admin/src/components/fpds/admin/bank-detail-dialog-content.tsx`, `app/admin/src/components/fpds/admin/bank-detail-surface.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `api/service/api_service/source_catalog.py`, `api/service/tests/test_source_catalog.py`, `app/admin/README.md`
- Decisions: kept the bank field named as source language even though the selectable values now mirror the approved EN/KO/JA operator language set. Implemented homepage repair as a missing-field-only backfill from the committed Big 5 seed registry so routine page loads can heal older local DB rows without wiping customized bank records
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
  - `api/service/.venv/Scripts/python.exe -m unittest tests.test_source_catalog`
  - passed
- Known issues: seed backfill only helps banks that exist in the committed seed registry, so manually created banks with genuinely missing homepage URLs still need operator edits
- Next step: reload `/admin/banks` in local dev and confirm the existing Big 5 bank rows now show homepage URLs without requiring a manual resave

## 2026-04-16 - Bank Profile Audit Schema Fix

- WBS: `5.15`
- Status: `done`
- Goal: restore successful bank-profile updates after the bank homepage edit flow started failing with a 500 from the admin API
- Why now: editing a bank homepage URL triggered `psycopg.errors.UndefinedColumn` because the source-catalog audit writer still inserted into the pre-runtime `audit_event` column shape instead of the current canonical audit schema
- Outcome: updated the source-catalog audit writer to use the live `audit_event` contract with `event_category`, `actor_id`, `actor_role_snapshot`, `diff_summary`, `source_ref`, and `occurred_at`, and added a unit test that locks the catalog audit insert shape to the current schema
- Not done: this slice did not change bank editing UX, did not add a DB migration, and did not alter audit-log list rendering
- Key files: `api/service/api_service/source_catalog.py`, `api/service/tests/test_source_catalog.py`, `docs/00-governance/development-journal.md`
- Decisions: matched the source-catalog audit insert pattern to the existing source-registry and review-detail implementations instead of introducing a second audit schema variant or a compatibility shim
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest tests.test_source_catalog`
  - passed
  - `pnpm run typecheck`
  - passed in `app/admin`
- Known issues: none identified beyond needing a live browser retry to confirm the previously failing BMO update path is clear
- Next step: retry editing a bank homepage in `/admin/banks` and confirm the audit event now persists cleanly with the update

## 2026-04-16 - Source Catalog Modal Workflow Refresh

- WBS: `5.15`
- Status: `done`
- Goal: move source-catalog add and detail work into modals so operators can stay on the filtered `/admin/source-catalog` list the same way they now do on `/admin/banks`
- Why now: Product Owner requested that the source-catalog `Create coverage` area and detail view follow the same modal workflow already applied to the bank registry screen
- Outcome: replaced the inline `Create coverage` form with an `Add coverage` modal, switched source-catalog row detail from a page transition to an editable detail modal, preserved the direct `/admin/source-catalog/:catalogItemId` route as a compatibility deep link, and kept collection launch anchored on the list surface so operators can add coverage and then collect without losing filter context
- Not done: this slice did not remove the direct source-catalog detail page route, did not change generated-source read-only behavior, and did not alter the backend API surface
- Key files: `app/admin/src/app/admin/source-catalog/page.tsx`, `app/admin/src/components/fpds/admin/source-catalog-surface.tsx`, `app/admin/src/components/fpds/admin/source-catalog-create-dialog-content.tsx`, `app/admin/src/components/fpds/admin/source-catalog-detail-dialog-content.tsx`, `app/admin/README.md`
- Decisions: reused the existing `offer-modal4` shell and the bank-screen URL-addressable modal pattern instead of introducing a second source-catalog-specific modal state system. Kept collect action on the list header because that action is list-scoped rather than item-detail-scoped
- Verification:
  - `pnpm run build`
  - passed in `app/admin`
  - `pnpm run typecheck`
  - passed in `app/admin`
- Known issues: direct detail-page compatibility remains in place for now, so there are still two valid entry points into source-catalog detail during the transition
- Next step: smoke test `/admin/source-catalog` in local dev by opening `Add coverage`, clicking an existing row into detail modal, and confirming that filter state survives modal open and close

## 2026-04-16 - Source Catalog Modal Density Tuning

- WBS: `5.15`
- Status: `done`
- Goal: remove the low-value `Updated` column from the source-catalog list and reshape the source-catalog detail modal so its key content fits on one screen more reliably
- Why now: Product Owner reported that the `Coverage list` still showed an unnecessary `Updated` column and that the source-catalog detail modal stacked too much content vertically to fit comfortably within one viewport
- Outcome: removed the `Updated` column from the source-catalog list, narrowed the table minimum width accordingly, and reworked the detail modal into a two-column desktop layout with compact summary cards on the left and a shorter recent-run panel on the right while limiting the in-modal run history preview to the latest three runs
- Not done: this slice did not change source-catalog routing, did not remove the direct compatibility route, and did not alter collection or generated-source backend behavior
- Key files: `app/admin/src/components/fpds/admin/source-catalog-surface.tsx`, `app/admin/src/components/fpds/admin/source-catalog-detail-dialog-content.tsx`, `docs/00-governance/development-journal.md`
- Decisions: kept the recent history visible inside the modal but constrained it to a smaller preview so the operator still gets run context without turning the modal into a long scrolling surface
- Verification:
  - `pnpm run build`
  - passed in `app/admin`
  - `pnpm run typecheck`
  - passed in `app/admin`
- Known issues: the modal still relies on viewport height and browser zoom level, so final comfort should be confirmed in a real browser session at the Product Owner's usual zoom
- Next step: reopen a populated source-catalog detail modal in local dev and confirm the summary, form, and run preview all fit without clipping on the target desktop viewport

## 2026-04-17 - Source Collection Runner Reliability Fix

- WBS: `5.15`
- Status: `done`
- Goal: restore Big 5 source-catalog collection runs after operator testing exposed misleading `fpds_parse_chunk failed with exit code 1` errors on a BMO chequing collection attempt
- Why now: the failing run log showed two separate problems in the collection path: snapshot capture still respected only the env starter allowlist instead of the active registry domains, and downstream worker stages were launched from the API service virtualenv so worker-only dependencies like `bs4` were missing at runtime
- Outcome: updated discovery, registry-refresh, and snapshot CLIs to merge registry `allowed_domains` into the env allowlist; changed the API-side source-collection runner to launch worker stages through the repo-root `uv` project environment; and filtered downstream parse/extraction/normalization work to only the sources whose snapshots were actually stored or reused so all-failed snapshot runs now stop with a clearer collection-stage error
- Not done: this slice did not change the admin UI, did not broaden the static `.env.dev.example` starter allowlist, and did not add retry UX for failed collections
- Key files: `api/service/api_service/source_collection_runner.py`, `api/service/tests/test_source_collection_runner.py`, `api/service/README.md`, `worker/discovery/fpds_discovery/fetch.py`, `worker/discovery/fpds_discovery/__main__.py`, `worker/discovery/fpds_snapshot/__main__.py`, `worker/discovery/fpds_registry_refresh/__main__.py`, `worker/discovery/tests/test_discovery.py`
- Decisions: kept the SSRF-safe env allowlist model but treated registry domains as an approved extension of that allowlist for registry-scoped runs. Preferred running worker stages via repo-root `uv` instead of duplicating worker dependencies into the API package because the worker/runtime boundary is already an approved architecture split
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest tests.test_source_collection_runner tests.test_source_catalog tests.test_source_registry`
  - passed
  - `api/service/.venv/Scripts/python.exe -m unittest worker.discovery.tests.test_discovery`
  - passed
- Known issues: a collection can still fail later on genuine source fetch drift or parsing issues, but the run should now report the true failing stage instead of masking snapshot failures behind a missing worker dependency
- Next step: rerun the BMO chequing source-catalog collection from `/admin/source-catalog` and confirm that generated sources, run history, and candidate counts now progress past snapshot and parse successfully

## 2026-04-17 - Homepage-First Source Catalog Collection Fix

- WBS: `5.15`
- Status: `done`
- Goal: realign source-catalog collection so operators manage only bank profiles plus product coverage while the system regenerates collection sources from the bank homepage instead of reusing stale seeded detail URLs
- Why now: Product Owner testing showed BMO chequing collection no longer crashed at parse time but still produced `0` candidates, and the deeper cause was that source-catalog collection still preferred committed Big 5 seed rows plus product-entry homepages instead of a bank-homepage-driven discovery path
- Outcome: changed seeded bank homepage defaults to bank-level personal landing pages, added automatic repair for legacy managed bank rows that still stored product-entry URLs, switched source-catalog materialization to regenerate sources from the bank homepage on every collect, broadened collection launch to include generated entry/supporting rows alongside detail targets, and added homepage-generation tests that lock the new flow
- Not done: this slice did not add a new admin UI field for product hub hints, did not remove the underlying committed Big 5 registry assets, and did not add manual retry UX for low-yield homepage discovery
- Key files: `api/service/api_service/source_catalog.py`, `api/service/api_service/source_registry_utils.py`, `api/service/tests/test_source_catalog.py`, `api/service/README.md`
- Decisions: treated source-catalog coverage as a homepage-first discovery contract rather than a seed-detail selection contract. Kept the committed Big 5 entry URLs only as internal fallback hints for known banks so the operator-facing model can stay at `bank homepage + product type`
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest tests.test_source_catalog tests.test_source_registry tests.test_source_collection_runner`
  - passed in `api/service`
  - `api/service/.venv/Scripts/python.exe -m unittest worker.discovery.tests.test_discovery`
  - passed
- Known issues: candidate yield still depends on what the live homepage and discovered hub pages expose, so genuinely sparse or heavily scripted bank pages may still need follow-on discovery heuristics later
- Next step: refresh `/admin/banks` once so legacy managed homepage URLs repair, then rerun the affected source-catalog collection and confirm that generated sources now come from homepage discovery rather than the old seed detail set

## 2026-04-17 - Bank-Centered Coverage Workflow Consolidation

- WBS: `5.15`
- Status: `done`
- Goal: remove the standalone source-catalog operator screen from the normal admin flow and fold coverage management directly into the bank workflow so operators manage one bank at a time in one place
- Why now: Product Owner decided the separate `Source Catalog` screen was adding unnecessary model-driven complexity, and requested that bank coverage be added and collected directly from the bank modal while keeping the FPDS visual system and the Shadcnblocks modal foundation
- Outcome: moved the operator coverage workflow into the `/admin/banks` detail modal with a structured two-section layout, removed the bank modal left rail, added inline coverage creation and per-coverage collect actions, changed the bank list to show comma-separated product coverage labels instead of only a count, removed the source-catalog nav entry, and converted `/admin/banks/:bankCode`, `/admin/source-catalog`, and `/admin/source-catalog/:catalogItemId` into compatibility redirects back into the bank-centered modal flow
- Not done: this slice did not remove the underlying source-catalog API routes, did not delete the legacy source-catalog UI components from the repo, and did not add inline editing of existing coverage status or product type inside the new bank modal
- Key files: `api/service/api_service/source_catalog.py`, `api/service/tests/test_source_catalog.py`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/components/offer-modal4.tsx`, `app/admin/src/components/application-shell5.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/bank-detail-dialog-content.tsx`, `app/admin/src/components/fpds/admin/bank-coverage-section.tsx`, `app/admin/src/app/admin/banks/[bankCode]/page.tsx`, `app/admin/src/app/admin/source-catalog/page.tsx`, `app/admin/src/app/admin/source-catalog/[catalogItemId]/page.tsx`, `README.md`, `app/admin/README.md`, `docs/03-design/admin-information-architecture.md`
- Decisions: treated `source_catalog` as a backend coverage entity that still powers collection APIs, but no longer as a primary operator navigation surface. Kept compatibility redirects instead of hard-deleting the old routes so existing deep links and route manifests stay valid during the transition. Used the existing Shadcnblocks `offer-modal4` shell without its left panel for bank flows so the denser bank-plus-coverage content fits the FPDS admin use case more cleanly
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
  - `.\.venv\Scripts\python.exe -m unittest tests.test_source_catalog`
  - passed in `api/service`
- Known issues: existing coverage rows are collectable and inspectable from the bank modal, but they are not yet editable inline; operators would still need a follow-on slice if status or product-type mutation must stay available after the source-catalog screen removal
- Next step: smoke test `/admin/banks` by opening a populated bank modal, adding missing coverage, launching collect from a coverage card, and confirming the bank list coverage labels and generated-source counts refresh as expected

## 2026-04-17 - Initial Coverage and Bank-List Bulk Collect

- WBS: `5.15`
- Status: `done`
- Goal: let operators attach coverage at bank creation time, keep per-coverage collect inside the bank detail modal, and add multi-bank bulk collect from the bank list while explicitly deferring free-form product-type onboarding
- Why now: Product Owner wanted the bank workflow to handle more of the real operator job in one place, but also agreed that truly dynamic product-type management would expand into discovery, AI scoring, and parser-contract work beyond the safe scope of the current admin slice
- Outcome: bank creation now accepts optional initial coverage for the current supported product families, bank list payloads now include attached coverage items so `/admin/banks` can multi-select banks and bulk-launch collection across all selected coverage rows, and the bank create modal plus bank list UI were updated to expose those actions without reopening the older source-catalog surface
- Not done: this slice did not ship a live product-type management menu, did not add searchable free-form product-type onboarding, and did not widen the discovery/parser contracts beyond the current canonical `chequing`, `savings`, and `gic` coverage set
- Key files: `api/service/api_service/models.py`, `api/service/api_service/source_catalog.py`, `api/service/tests/test_source_catalog.py`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/lib/admin-product-types.ts`, `app/admin/src/components/fpds/admin/bank-create-dialog-content.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `README.md`, `app/admin/README.md`, `api/service/README.md`, `docs/03-design/admin-information-architecture.md`, `docs/01-planning/WBS.md`
- Decisions: kept initial coverage creation in the bank create write flow so bank plus coverage setup stays atomic from the operator perspective. Reused the existing source-catalog collection API for bulk collect instead of creating a second bank-specific collect endpoint. Deferred dynamic product-type onboarding into new `WBS 5.16` planning because the AI-assisted homepage discovery contract is larger than a UI-only slice
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
  - `.\.venv\Scripts\python.exe -m unittest tests.test_source_catalog`
  - passed in `api/service`
- Known issues: initial coverage selection and add-coverage inside bank detail still use the current fixed product-family list rather than a searchable registry, and bank-list selection currently operates at the bank level rather than letting operators pick an arbitrary subset of coverage rows from the list itself
- Next step: smoke test `/admin/banks` by adding a bank with initial coverage, selecting multiple banks in the list, running `Collect selected`, and then confirming the corresponding coverage cards and generated-source counts refresh after the run is launched

## 2026-04-17 - Dynamic Product Type Requirement Capture

- WBS: `5.16`
- Status: `done`
- Goal: record the Product Owner's requested free-form product type capability in the authoritative requirement and design documents without accidentally implying that the feature is already live
- Why now: Product Owner clarified that product types should eventually be operator-defined and AI-usable for homepage-first discovery, but also agreed that the runtime scope is too large for the current admin slice and should be deferred cleanly
- Outcome: updated the requirements baseline, admin information architecture, source-registry policy, and WBS so the repo now explicitly captures a later `/admin/product-types` management surface, searchable product type `name` and `description`, AI-assisted homepage discovery usage of those definitions, and the need for parser/normalization/validation fallback rules before the feature can ship
- Not done: this slice did not add a live product type management route, DB table, API, or UI, and it did not widen the current runtime beyond the fixed canonical `chequing`, `savings`, and `gic` coverage set
- Key files: `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`, `docs/03-design/admin-information-architecture.md`, `docs/03-design/source-registry-refresh-and-approval-policy.md`, `docs/01-planning/WBS.md`, `docs/00-governance/development-journal.md`
- Decisions: kept the requirement explicit enough to guide later design while also preserving the current operational boundary that only the fixed Phase 1 product types are live today
- Verification:
  - document-only update; no code/runtime checks required
- Known issues: the requirements doc now contains both current-state and deferred-state product type language, so future implementation work should keep those two scopes distinct rather than treating the deferred capability as already approved for immediate build
- Next step: when `WBS 5.16` starts, design the product type registry schema, the AI discovery scoring/prompt contract, and the parser/normalization fallback behavior before building UI

## 2026-04-17 - Source Catalog Duplicate-Scope Collection Fix

- WBS: `5.15`
- Status: `done`
- Goal: stop homepage-first bank coverage collection from crashing when the same generated bank URL is discovered under two roles and collides on the source registry unique scope
- Why now: Product Owner hit a live `POST /api/admin/source-catalog/collect` failure for BMO chequing because the materialized source set generated the same normalized URL as both `entry` and `detail`, while the DB correctly enforces uniqueness by bank, product type, normalized URL, and source type
- Outcome: generated source rows are now deduped by the DB-backed unique scope before persistence, duplicate-scope ties prefer `detail` over non-candidate roles, and source upsert now targets the real unique scope and returns the persisted row identity so reruns can reuse existing source ids safely

## 2026-04-17 - Dynamic Product Type Onboarding Implementation

- WBS: `5.16`
- Status: `done`
- Goal: make product types operator-managed and usable by homepage-first discovery without introducing a new per-type hardcoded parser branch for every future deposit product
- Why now: Product Owner approved implementing the deferred dynamic product type onboarding slice, but explicitly wanted the runtime to stay flexible by using generic AI-assisted discovery, extraction, and normalization fallback instead of one-off parser logic per new product type
- Outcome: added `product_type_registry` plus migration `0007`, live `/api/admin/product-types` read/write routes, a new `/admin/product-types` management screen, registry-backed product type search in the bank create and add-coverage flows, homepage-first discovery prompts that include product type name/description/keywords, collection-plan metadata that carries product type definitions into worker stages, generic AI extraction and normalization fallback for dynamic product types, and review-first validation routing that keeps those dynamic candidates out of auto-publish paths
- Not done: this slice did not widen public product/grid/dashboard publishing to dynamic product types, did not implement scheduler-driven discovery refresh, and did not run the new migration against a live database from this session
- Key files: `db/migrations/0007_dynamic_product_type_onboarding.sql`, `api/service/api_service/product_types.py`, `api/service/api_service/source_catalog.py`, `api/service/api_service/source_registry.py`, `worker/pipeline/fpds_ai_runtime.py`, `worker/pipeline/fpds_extraction/service.py`, `worker/pipeline/fpds_normalization/service.py`, `worker/pipeline/fpds_validation_routing/service.py`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx`, `app/admin/src/components/fpds/admin/bank-coverage-section.tsx`, `app/admin/src/app/admin/product-types/page.tsx`
- Decisions: kept built-in `chequing`, `savings`, and `gic` behavior intact while routing new operator-defined types through a generic AI fallback contract. Forced dynamic types into manual review even in non-prototype routing so the canonical/public surfaces do not silently absorb unsupported mappings. Synced dynamic product types into taxonomy as an `other` subtype to preserve safe downstream validation semantics without pretending subtype coverage is complete
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `python -m unittest tests.test_product_types tests.test_source_catalog tests.test_source_registry tests.test_source_collection_runner`
  - passed in `api/service`
  - `python -m unittest worker.pipeline.tests.test_extraction worker.pipeline.tests.test_normalization worker.pipeline.tests.test_validation_routing`
  - passed in repo root
- Known issues: dynamic product types currently rely on the configured OpenAI provider for the richer fallback path; if the provider is not configured, the system stays on heuristic mode and still routes outcomes conservatively into review. This slice also leaves test-generated temp artifacts in `tmp/` unless they are cleaned separately
- Next step: apply migration `0007` in the target database, create one real dynamic product type in `/admin/product-types`, attach it to a bank, and smoke test a collect run to confirm the provider-backed discovery and review flow in the live environment
- Not done: this slice did not change homepage scoring heuristics, did not widen the source uniqueness contract, and did not add a new operator-facing error surface in the admin UI
- Key files: `api/service/api_service/source_catalog.py`, `api/service/tests/test_source_catalog.py`, `docs/00-governance/development-journal.md`
- Decisions: kept the DB uniqueness rule as the source of truth and aligned generation/upsert behavior to it instead of allowing multiple rows for the same normalized page. When the same page can act as both a catalog hub and a candidate-producing detail page, the candidate-producing `detail` role now wins
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest tests.test_source_catalog tests.test_source_collection_runner`
  - passed in `api/service`
- Known issues: this fix addresses duplicate-scope generation inside the homepage materialization path, but genuinely different pages can still fail later in the collection pipeline if fetch or parse behavior drifts
- Next step: rerun the failed BMO chequing collect action from `/admin/banks` and confirm the collection now launches past source materialization into run execution

## 2026-04-17 - Homepage Discovery No-Detail Handling and AI Resolution

- WBS: `5.15`
- Status: `done`
- Goal: make homepage-first coverage collection resilient when homepage fetch or link extraction fails, while still giving operators a truthful no-detail outcome and an AI-assisted path to approved seed detail pages
- Why now: Product Owner reran the BMO chequing collect action after the duplicate-scope fix and the admin action still ended as a failed run because snapshot capture was pointed at a homepage-derived entry URL that timed out. The desired operator contract is that homepage discovery should not fail the admin action just because the homepage is slow or empty, and AI should be able to resolve the approved seed detail targets from homepage context
- Outcome: homepage generation no longer turns the homepage itself into a fallback `detail` source, source-catalog collect now returns a successful no-detail result when discovery cannot identify candidate-producing detail rows, and existing active detail rows stay preserved instead of being inactivated by a degraded discovery pass. Added an OpenAI Responses API-backed resolver that can map homepage context plus approved seed detail hints to same-domain detail URLs, and updated the admin collect messages so operators can see when discovery finished without launching a run plus the first discovery note
- Not done: this slice does not yet persist model-execution or token-usage records for the AI-assisted homepage resolver, and it still depends on the environment having `FPDS_LLM_PROVIDER=openai` plus `FPDS_LLM_API_KEY` configured before the AI path can run live
- Key files: `api/service/api_service/source_catalog.py`, `api/service/tests/test_source_catalog.py`, `api/service/README.md`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/components/fpds/admin/bank-coverage-section.tsx`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/source-catalog-surface.tsx`, `app/admin/README.md`, `docs/00-governance/development-journal.md`
- Decisions: treat `no detail sources discovered` as an operator-visible outcome rather than a failed collect action; only replace the existing active source scope when new detail rows are actually discovered; keep the AI resolver constrained to approved seed detail hints and same-domain HTML URLs so the model can help recover detail-page scope without widening the product boundary
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest tests.test_source_catalog tests.test_source_collection_runner`
  - `pnpm run typecheck`
  - passed in `api/service` and `app/admin`
- Known issues: the AI resolver currently reports its outcome through discovery notes only, so deeper operational observability still relies on audit history and follow-up collection results rather than a dedicated resolver diagnostics surface
- Next step: rerun BMO chequing collect from `/admin/banks` and confirm either that AI-assisted homepage discovery produces detail sources and launches a run, or that the UI cleanly reports a no-detail outcome without creating a failed run

## 2026-04-18 - Product Type Create Audit Fix and Delete Support

- WBS: `5.16`
- Status: `done`
- Goal: fix the live `POST /api/admin/product-types` failure and finish the missing product-type lifecycle controls so operator-defined types can be created and removed safely
- Why now: Product Owner hit a real admin runtime error while creating a dynamic product type. The request reached the create path, but the follow-up audit insert still used columns that do not exist on the current `audit_event` schema. The same surface also still lacked an operator-facing delete action for dynamic types
- Outcome: aligned product-type audit inserts to the actual live `audit_event` schema, added backend delete support for non-built-in product types, blocked deletion when a type is still referenced by bank coverage or generated source rows, added an admin delete action on `/admin/product-types`, and tightened the product-type unit tests so the audit SQL shape and delete guard behavior are both covered
- Not done: this slice did not add bulk delete, did not introduce soft-delete history for product types, and did not widen built-in product types beyond the existing read-only rule
- Key files: `api/service/api_service/product_types.py`, `api/service/api_service/main.py`, `api/service/tests/test_product_types.py`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx`, `app/admin/src/app/admin/product-types/[productTypeCode]/delete/route.ts`, `api/service/README.md`, `app/admin/README.md`, `docs/00-governance/development-journal.md`
- Decisions: kept delete as a guarded hard delete for operator-defined types only. If a type is already in active bank coverage or generated source scope, the API now rejects deletion with a clear conflict message instead of silently inactivating or orphaning dependent rows
- Verification:
  - `python -m unittest tests.test_product_types`
  - passed in `api/service`
  - `pnpm run typecheck`
  - passed in `app/admin`
- Known issues: dynamic product type delete currently checks live bank-coverage and source-registry references only; it does not yet expose a richer dependency drilldown in the UI, so operators still get a blocking message rather than a linked “where used” list
- Next step: retry product type creation in `/admin/product-types`, then verify edit and delete on a fresh unused dynamic type and separately confirm that deletion is correctly blocked once the type is attached to bank coverage

## 2026-04-18 - Product Type Modal Workflow Alignment

- WBS: `5.16`
- Status: `done`
- Goal: align `/admin/product-types` to the same list-plus-modal interaction model already used by `/admin/banks`
- Why now: Product Owner wanted product type onboarding to feel consistent with the existing bank workflow instead of mixing a list view with a permanently embedded create form and inline edits
- Outcome: replaced the split registry-plus-sidebar layout with a bank-style list surface, moved create into an `OfferModal4` add modal, moved edit/delete into a detail modal opened from the list row, added server-side detail loading for the active product type, and kept built-in types readable from the same modal while leaving them non-editable
- Not done: this slice did not add list selection or bulk actions for product types, and it did not add usage-drilldown links when delete is blocked by existing bank/source references
- Key files: `app/admin/src/app/admin/product-types/page.tsx`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx`, `app/admin/src/components/fpds/admin/product-type-create-dialog-content.tsx`, `app/admin/src/components/fpds/admin/product-type-detail-dialog-content.tsx`, `app/admin/src/lib/admin-api.ts`, `app/admin/README.md`, `docs/00-governance/development-journal.md`
- Decisions: matched the Banks UX pattern closely instead of inventing a lighter variation for product types. That means list context stays anchored, add opens through a query-param modal state, and detail work happens in the same modal family rather than inline card editing
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
- Known issues: if a product type code is placed directly into the query string but no longer exists, the page currently stays on the filtered list without opening the detail modal rather than auto-clearing the stale query param
- Next step: smoke test `/admin/product-types` by opening add, creating a dynamic type, reopening it from the list detail modal, editing it, and deleting an unused type while confirming Banks-style context retention

## 2026-04-18 - Destructive Confirm Dialog Standardization

- WBS: `5.16`
- Status: `done`
- Goal: replace browser-native delete confirmation with a reusable FPDS admin destructive confirm dialog aligned to the requested Shadcnblocks destructive alert-dialog pattern
- Why now: Product Owner asked for site-wide delete confirmations to stop using `window.confirm` and instead use a consistent modal treatment that matches the rest of the admin surface
- Outcome: added shared `alert-dialog` UI primitives plus a reusable destructive confirm block, wired the product-type delete action to that dialog, and documented the expectation that future operator-facing delete actions should use the shared component instead of native browser confirms
- Not done: this slice only converted the one active delete confirmation currently present in the admin app; future delete actions should reuse the same component when they are introduced
- Key files: `app/admin/src/components/ui/alert-dialog.tsx`, `app/admin/src/components/fpds/admin/destructive-confirm-dialog.tsx`, `app/admin/src/components/fpds/admin/product-type-detail-dialog-content.tsx`, `app/admin/README.md`, `docs/00-governance/development-journal.md`
- Decisions: standardized on a reusable modal component rather than styling each delete flow ad hoc, and kept the copy explicit about dependency-blocked deletes so operators understand why a destructive action may still fail after confirmation

## 2026-04-18 - Bank Create URL Guard and Delete Lifecycle

- WBS: `5.15`
- Status: `done`
- Goal: stop `/api/admin/banks` from crashing on scheme-less homepage input and finish the missing bank delete lifecycle so `/admin/banks` matches the product-type modal flow more closely
- Why now: Product Owner hit a live bank-create failure by entering a homepage without `http(s)://`, and the bank detail modal still allowed update only even though newly added operator-managed banks should also be removable from the same workflow
- Outcome: bank create and update now normalize scheme-less homepage values to `https://...` before URL validation, invalid homepage input now returns a 422-style domain error instead of a server 500, the API now exposes guarded `DELETE /api/admin/banks/:bankCode`, and the bank detail modal now includes the shared destructive confirm dialog plus delete action routing
- Not done: bank delete intentionally stops when collected source documents or downstream candidate/product/public snapshot rows already exist; this slice did not add a richer dependency drilldown or a deeper runtime-data purge workflow
- Key files: `api/service/api_service/source_catalog.py`, `api/service/api_service/main.py`, `api/service/tests/test_source_catalog.py`, `app/admin/src/app/admin/banks/[bankCode]/delete/route.ts`, `app/admin/src/components/fpds/admin/bank-detail-dialog-content.tsx`, `api/service/README.md`, `app/admin/README.md`, `docs/00-governance/development-journal.md`
- Decisions: treat missing URL scheme as operator input cleanup rather than as a hard error, but keep non-http(s) values invalid; allow bank delete only while the bank is still in the admin-managed setup layer and block it once runtime or published history exists so we do not orphan evidence, candidates, or public projections

## 2026-04-18 - Discovery Fetch Timeout Control for Slow Bank Pages

- WBS: `5.15`
- Status: `done`
- Goal: reduce avoidable source-collection failures on slower bank sites by making discovery and snapshot fetch timeout configurable and less aggressive by default
- Why now: Product Owner ran BMO chequing collect and the run failed during snapshot capture because all four selected detail pages timed out under the current fixed 20-second fetch policy, even though the operator flow and AI-assisted homepage discovery had already selected a plausible detail scope
- Outcome: `DiscoveryFetchPolicy.from_env()` now reads `FPDS_SOURCE_FETCH_TIMEOUT_SECONDS`, the default timeout was raised from 20 seconds to 45 seconds, env examples and the discovery/runtime docs were updated, and unit coverage now checks both the default and an explicit env override
- Not done: this slice does not add per-bank timeout tuning, browser-like user-agent overrides, or richer retry telemetry in the run UI; it only makes the existing timeout policy more realistic and operable
- Key files: `worker/discovery/fpds_discovery/fetch.py`, `worker/discovery/tests/test_discovery.py`, `.env.dev.example`, `.env.prod.example`, `worker/discovery/README.md`, `docs/03-design/dev-prod-environment-spec.md`, `docs/00-governance/development-journal.md`
- Decisions: kept one shared timeout control for discovery, preflight drift, and snapshot capture instead of adding a bank-specific override system, because the immediate product value is operational recovery from slow-but-public pages rather than a more complex fetch policy matrix

## 2026-04-18 - Homepage Discovery Quality Design Baseline

- WBS: `5.16`
- Status: `done`
- Goal: define the next discovery-quality design step without replacing the current homepage-first, DB-backed source-registry architecture
- Why now: Product Owner asked how FPDS can materially improve homepage-first discovery quality while preserving the current operator workflow. The requested direction was to promote AI from fallback to bounded parallel scorer, strengthen product-type-description usage, and add page-level evidence scoring before `detail` promotion
- Outcome: added a dedicated design baseline for homepage discovery quality that keeps deterministic candidate generation, adds AI parallel scoring over bounded candidates, requires stronger product-type-description grounding, and introduces page-level evidence scoring as the main guardrail before generated `detail` rows are promoted. Linked the design back into requirements, source-registry operations policy, the docs map, and the decision log
- Not done: this was a documentation-only slice. It did not implement the new scorer, persist discovery-scoring metadata, or widen run-detail diagnostics yet
- Key files: `docs/03-design/homepage-discovery-scoring-enhancement.md`, `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`, `docs/03-design/source-registry-refresh-and-approval-policy.md`, `docs/00-governance/decision-log.md`, `docs/README.md`, `docs/00-governance/development-journal.md`
- Decisions: pushed back on jumping directly to vector-first or browser-default discovery. The approved direction is a bounded hybrid scorer that fits the existing architecture and should deliver better semantic matching and explainability with lower implementation risk
- Verification:
  - documentation review only; no runtime code or tests changed

## 2026-04-18 - Homepage Discovery Hybrid Scoring Implementation Slice 1

- WBS: `5.16`
- Status: `done`
- Goal: implement the first bounded runtime slice from the approved homepage-discovery scoring design without replacing the existing bank-homepage-first registry architecture
- Why now: Product Owner asked to move from documentation into code by adding the AI parallel scorer contract, page-level evidence scoring, and generated-source discovery metadata persistence while keeping the current collection workflow intact
- Outcome: homepage-first discovery in `api_service.source_catalog` now builds a bounded HTML candidate set, uses stronger product-type-description terms in heuristic scoring, calls an OpenAI-based parallel candidate scorer when configured, validates tentative detail pages with page-level evidence scoring before promotion, persists structured `discovery_metadata` on generated `source_registry_item` rows, carries that metadata into the source-collection runner payload, and exposes the persisted explainability block on `/admin/sources/:sourceId`
- Not done: this slice did not widen run detail with a separate discovery diagnostics panel, did not persist discovery-stage `model_execution` or `llm_usage_record` rows, and did not redesign the no-detail bank/source-catalog collect summaries yet
- Key files: `api/service/api_service/source_catalog.py`, `api/service/api_service/source_registry.py`, `api/service/api_service/source_collection_runner.py`, `db/migrations/0008_discovery_metadata_persistence.sql`, `api/service/tests/test_source_catalog.py`, `api/service/tests/test_source_registry.py`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/components/fpds/admin/source-detail-surface.tsx`, `api/service/README.md`, `app/admin/README.md`, `README.md`, `docs/03-design/homepage-discovery-scoring-enhancement.md`, `docs/00-governance/development-journal.md`
- Decisions: kept the implementation narrowly focused on generated-source explainability and source-detail inspection instead of also widening run diagnostics in the same slice; added a dedicated `source_registry_item.discovery_metadata` JSONB column rather than trying to overload `purpose` or rely only on transient collect-response notes
- Verification:
  - `python -m unittest tests.test_source_catalog tests.test_source_registry`
  - `python -m unittest tests.test_source_collection_runner`
  - `python -m compileall api_service`
  - `pnpm run typecheck`

## 2026-04-19 - Source Catalog Collect Async Queue and Snapshot Hardening

- WBS: `5.15`, `5.16`
- Status: `done`
- Goal: stop bank-wide collect from failing at the admin request layer when homepage discovery runs too long, and reduce bank-scope snapshot wall-clock blowups when several slow source pages time out in sequence
- Why now: Product Owner hit a real `/admin/source-catalog/collect` failure where the Next.js proxy waited about 5 minutes for the admin API to return headers and then raised `UND_ERR_HEADERS_TIMEOUT`, while the downstream BMO chequing run still showed per-source read timeouts across four selected detail pages
- Outcome: `POST /api/admin/source-catalog/collect` now creates run rows immediately and returns a queued background response instead of doing homepage discovery and source materialization inline. A new `source_catalog_collection_runner` now performs homepage-first source generation in the background, reuses the precreated run ids, and then hands successful detail scope into the existing collection stages. Snapshot capture now fetches multiple sources concurrently inside a run, and the shared discovery/snapshot fetch timeout baseline moved from `45` to `90` seconds so slower Big 5 pages get a larger read window without making bank-wide collection wall-clock time grow linearly per source
- Not done: this slice did not add a dedicated queued-job dashboard outside `/admin/runs`, did not add per-bank fetch-policy overrides, and did not guarantee success against every hostile/sluggish bank page pattern
- Key files: `api/service/api_service/source_catalog.py`, `api/service/api_service/source_catalog_collection_runner.py`, `api/service/api_service/source_registry.py`, `worker/discovery/fpds_discovery/fetch.py`, `worker/discovery/fpds_snapshot/capture.py`, `worker/discovery/fpds_snapshot/__main__.py`, `api/service/tests/test_source_catalog.py`, `api/service/tests/test_source_catalog_collection_runner.py`, `worker/discovery/tests/test_discovery.py`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/components/fpds/admin/bank-registry-surface.tsx`, `app/admin/src/components/fpds/admin/bank-coverage-section.tsx`, `app/admin/src/components/fpds/admin/source-catalog-surface.tsx`, `api/service/README.md`, `app/admin/README.md`, `worker/discovery/README.md`, `.env.dev.example`, `.env.prod.example`
- Decisions: treated the request-layer timeout and the downstream source fetch timeout as separate problems and fixed both. Kept the existing run-detail surface as the main operator diagnosis path instead of inventing a second collection-progress surface in the same slice. Reused the existing run ids and source-collection plan builder so the queued source-catalog path stays compatible with the established run, review, and audit linkage patterns
- Verification:
  - `python -m unittest api.service.tests.test_source_catalog api.service.tests.test_source_catalog_collection_runner api.service.tests.test_source_registry`
  - `python -m unittest worker.discovery.tests.test_discovery worker.discovery.tests.test_snapshot_capture`
  - `pnpm run typecheck`
  - `python -m compileall api\service\api_service worker\discovery`
- Known issues: the background no-detail outcome now appears in `/admin/runs` instead of as a fully computed immediate toast payload, and the existing `api.service.tests.test_source_collection_runner` temp-dir tests are still awkward under the current Windows sandbox because OS temp writes can be denied during automated execution even when the runner logic itself is unchanged
- Next step: rerun BMO bank-wide collect from `/admin/banks`, confirm the admin action returns immediately with queued run ids, and then inspect the resulting run detail to see whether the longer timeout plus concurrent snapshot fetches clear the current BMO read-timeout pattern or whether BMO now needs a bank-specific fetch-policy follow-up

## 2026-04-19 - Source Catalog Background Runner Preserved Detail Fallback Fix

- WBS: `5.15`, `5.16`
- Status: `done`
- Goal: stop queued bank-wide source-catalog runs from being marked as `Partial completion` when homepage rediscovery fails to generate replacement detail rows but the bank still has an existing active detail scope that should remain collectible
- Why now: Product Owner reran bank-wide collect after the async queue change and saw many Big 5 runs complete with `Homepage discovery produced no detail sources eligible for collection.` even though the run metadata still showed existing bank/product source ids that should have been reused
- Outcome: the background `source_catalog_collection_runner` now reloads the current active source-registry scope for the bank/product when homepage materialization produces no replacement detail rows. If preserved active detail rows still exist, the runner reuses that preserved scope for downstream collection instead of closing the run as degraded with zero source items. Only truly empty active detail scope now ends as the no-detail partial-completion outcome
- Not done: this slice did not redesign the run-status UI wording, and it did not change the homepage discovery scorer or page-evidence thresholds themselves
- Key files: `api/service/api_service/source_catalog_collection_runner.py`, `api/service/tests/test_source_catalog_collection_runner.py`, `api/service/README.md`, `docs/00-governance/development-journal.md`
- Decisions: kept the fix in the background runner instead of widening the source-catalog materialization contract, because the bug was in how the queued path interpreted preserved scope rather than in the preservation rule itself
- Verification:
  - `python -m unittest api.service.tests.test_source_catalog_collection_runner`
  - passed
- Known issues: if homepage discovery and the preserved active scope are both empty, the run still correctly lands in partial completion with the no-detail summary
- Next step: rerun a previously affected bank-wide collect and confirm `/admin/runs` now shows normal source-item counts for preserved-scope banks instead of zero-item partial completions

## 2026-04-19 - Source Catalog Per-Run Isolation and Worker Stage Timeout Guard

- WBS: `5.15`, `5.16`
- Status: `done`
- Goal: stop bank-wide async collect from leaving most runs permanently in `Started` when one product-type runner hangs mid-batch
- Why now: Product Owner reran bank-wide collect and saw only the first few BMO runs progress while most later CIBC/RBC/Scotia/TD runs stayed at `0 source items` and `Started` with no error summary, which indicated one sequential background process had stalled before it reached the remaining runs
- Outcome: source-catalog async launch now starts one background subprocess per bank/product run instead of one sequential process for the entire bank-wide batch, so one hung run cannot block later runs from starting or completing. The downstream `source_collection_runner` now also enforces a configurable `FPDS_SOURCE_COLLECTION_STAGE_TIMEOUT_SECONDS` timeout for each worker stage and raises a clear failure summary when that watchdog trips, preventing indefinitely `started` runs when a worker subprocess stops returning
- Not done: this slice did not redesign the `/admin/runs` UI or eliminate normal fetch timeout failures on slow bank pages; it focused on preventing indefinite stuck states and improving operator-visible closure
- Key files: `api/service/api_service/source_catalog.py`, `api/service/api_service/source_catalog_collection_runner.py`, `api/service/api_service/source_collection_runner.py`, `api/service/tests/test_source_catalog.py`, `api/service/tests/test_source_collection_runner.py`, `.env.dev.example`, `.env.prod.example`, `docs/03-design/dev-prod-environment-spec.md`, `api/service/README.md`, `docs/00-governance/development-journal.md`
- Decisions: preferred per-run subprocess isolation over adding more orchestration around the existing sequential batch runner because the product value is operational containment and predictable run closure, not keeping a large bank collect inside one long-lived controller process
- Verification:
  - `python -m unittest api.service.tests.test_source_catalog api.service.tests.test_source_catalog_collection_runner api.service.tests.test_source_collection_runner api.service.tests.test_source_registry`
  - `python -m compileall api\service\api_service`
- Known issues: genuinely slow sites can still fail with snapshot read timeouts, but those runs should now close as `failed` instead of leaving unrelated later runs stuck in `started`
- Next step: rerun a bank-wide collect and confirm that later bank/product runs progress independently even if an earlier run times out or fails

## 2026-04-19 - BMO Browser Snapshot Fallback

- WBS: `5.15`, `5.16`
- Status: `done`
- Goal: stop BMO chequing and similar BMO detail-source collects from failing at snapshot capture with repeated read timeouts
- Why now: the Product Owner reran a single BMO chequing collect and all four detail sources failed in snapshot capture after three attempts each, with `The read operation timed out` even though the pages are reachable in a normal browser
- Outcome: the shared discovery fetch layer now supports a targeted browser fallback path for domains in `FPDS_SOURCE_BROWSER_FALLBACK_DOMAINS`. When normal HTTPS fetches time out, reset, or return certain anti-bot statuses for those domains, the worker uses a local headless browser with a more browser-like profile to render the page and stores a PDF snapshot instead of failing the run outright. The downstream parse stage already supports `application/pdf`, so BMO HTML sources can continue through parse and extraction with only a content-type warning instead of a hard snapshot failure. HTML-only fetch paths still reject non-HTML fallback payloads so homepage discovery and page-evidence scoring do not accidentally ingest PDF fallback bytes as page HTML
- Not done: this slice did not add a Linux browser-packaging story or remove every possible bank-specific fetch quirk; it focused on the current BMO failure mode visible on the Product Owner's machine
- Key files: `worker/discovery/fpds_discovery/fetch.py`, `worker/discovery/tests/test_discovery.py`, `.env.dev.example`, `.env.prod.example`, `docs/03-design/dev-prod-environment-spec.md`, `api/service/README.md`, `docs/00-governance/development-journal.md`
- Decisions: preferred a narrow browser fallback over further timeout increases because live probing showed BMO was resetting or stalling non-browser clients on this machine while headless Edge could still render the same URLs
- Verification:
  - `python -m unittest worker.discovery.tests.test_discovery worker.discovery.tests.test_snapshot_capture`
- Known issues: if no supported browser executable is installed and `FPDS_SOURCE_BROWSER_EXECUTABLE` is not set, eligible BMO fetches will still fail and now report a missing-browser fallback error instead of an opaque read timeout
- Next step: rerun the BMO chequing collect and confirm the run advances past snapshot capture with stored snapshots plus a warning for HTML-to-PDF fallback rather than failing all sources

## 2026-04-20 - Review Detail List-Value Trace Fix

- WBS: `4.4`
- Status: `done`
- Goal: stop `/api/admin/review-tasks/:reviewTaskId` from returning `500` when a normalized candidate payload contains list-valued fields
- Why now: opening review detail failed in the live admin flow with `TypeError: cannot use 'list' as a set element`, which blocked the review trace surface for candidates that carry array-like normalized fields
- Outcome: replaced the review-detail module's repeated `value in {None, ""}` checks with one shared helper that safely treats only `None` and empty-string values as empty. The review-detail response can now keep non-empty list values in both `candidate.field_items` and `field_trace_groups` without raising an unhashable-type error
- Not done: this slice did not change the review-detail UI layout, did not alter normalization output shapes, and did not add special list formatting beyond the existing JSON-style frontend rendering
- Key files: `api/service/api_service/review_detail.py`, `api/service/tests/test_review_detail.py`, `docs/00-governance/development-journal.md`
- Decisions: kept the fix narrow to review-detail serialization instead of coercing list-valued candidate fields into strings earlier in the pipeline, because list payloads are valid normalized data and should remain inspectable in the trace view
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest api.service.tests.test_review_detail`
  - passed
  - `api/service/.venv/Scripts/python.exe -m unittest api.service.tests.test_ops_scenario_qa`
  - passed
- Known issues: review detail still renders list and object values through the existing frontend `JSON.stringify` fallback, so the route is stable again but deeply nested values may still deserve future UX polish if operators find them hard to scan
- Next step: reload the failing review detail page in local dev and confirm the previously failing review task now opens with trace cards for list-valued fields

## 2026-04-20 - Review Detail Dedicated Product Name Override

- WBS: `4.3`, `4.4`
- Status: `done`
- Goal: let operators correct approved product names through a dedicated review-detail input instead of typing `product_name` inside raw override JSON
- Why now: Product Owner asked for a safer review-detail workflow for product-name corrections after confirming that the existing `Edit approval override JSON` field was too free-form for a core identity field
- Outcome: review detail now exposes a dedicated `Approved product name` input above the JSON override textarea, blocks `product_name` inside the raw JSON field, and includes product-name edits in the diff preview used by `Edit & approve`. The approval backend now trims product-name overrides, uses the approved name when matching or updating canonical products, and persists the corrected canonical `product_name` during edit-approve flows
- Not done: this slice did not replace the remaining JSON override workflow for other fields, did not backfill older review decisions, and did not change the source-derived candidate name stored on the original normalized candidate row
- Key files: `app/admin/src/components/fpds/admin/review-detail-surface.tsx`, `api/service/api_service/review_detail.py`, `api/service/tests/test_review_detail.py`, `api/service/tests/test_ops_scenario_qa.py`, `app/admin/README.md`, `api/service/README.md`, `docs/00-governance/development-journal.md`
- Decisions: kept the existing generic JSON override path for non-name field edits, but treated `product_name` as a safer dedicated control because it affects canonical continuity more directly than routine field-value fixes. The backend still accepts `product_name` in override payloads for compatibility, but the first-party admin UI now steers operators to the dedicated input and rejects duplicate `product_name` edits in the JSON box
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest api.service.tests.test_review_detail api.service.tests.test_ops_scenario_qa`
  - passed
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
- Known issues: after an edited approval, the review-detail page still reflects the original source-derived candidate heading until future work teaches the closed-task detail view to foreground the approved canonical name or latest override result
- Next step: open a live review detail, change only the dedicated product-name field, submit `Edit & approve`, and confirm the diff preview plus resulting canonical product snapshot reflect the corrected name

## 2026-04-20 - Review Detail Approved Name Display Fix

- WBS: `4.4`
- Status: `done`
- Goal: make review detail visibly reflect approved product-name edits after an `Edit & approve` decision is already stored
- Why now: Product Owner confirmed that the edit history showed a product-name override had been saved, but the review-detail screen still looked unchanged because the page header continued to show only the original candidate name
- Outcome: the review-detail header and summary now resolve the displayed product name from the latest decision-history product-name override first, then the current canonical product snapshot, and only fall back to the original candidate name when no approved name exists yet. When the approved name differs from the source-derived candidate name, the page now also shows the original candidate name as supporting context instead of silently replacing it
- Not done: this slice did not rewrite the candidate summary cards to pretend the normalized candidate row itself changed, and it did not add a separate “approved vs source name” comparison card beyond the lighter inline context line
- Key files: `app/admin/src/components/fpds/admin/review-detail-surface.tsx`, `docs/00-governance/development-journal.md`
- Decisions: kept the source-derived candidate payload intact for traceability, but changed the page-level display priority so closed review tasks foreground what was actually approved rather than what the model originally proposed
- Verification:
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
- Known issues: the candidate summary section still shows the original normalized field values for traceability, so operators will now see the approved name in the header while lower trace cards continue to reflect the source-derived candidate payload unless a future slice adds a dedicated approved-payload pane
- Next step: reload the previously edited review task and confirm the header now shows the approved product name while still preserving the original candidate name as context

## 2026-04-20 - Review Detail Candidate Name Sync on Edit Approve

- WBS: `4.3`, `4.4`
- Status: `done`
- Goal: make `candidate.product_name` itself persist the reviewer-corrected name after `Edit & approve`
- Why now: Product Owner asked for the original candidate name in review detail to become the edited product name instead of only showing the correction through decision history or canonical-product display priority
- Outcome: edit-approve now updates `normalized_candidate.product_name` and synchronizes `candidate_payload.product_name` to the approved name alongside the existing canonical-product update. Review detail can therefore load the edited product name directly from the stored candidate record on later page loads instead of relying only on display-layer fallback logic
- Not done: this slice did not generalize the same persistence rule to every manual-override field; it stays narrowly scoped to product-name synchronization
- Key files: `api/service/api_service/review_detail.py`, `api/service/tests/test_ops_scenario_qa.py`, `api/service/README.md`, `docs/00-governance/development-journal.md`
- Decisions: kept the persistence change narrow to `product_name` because that is the field the Product Owner explicitly asked to treat as part of the candidate record after review. Other edit-approve overrides still remain review-decision deltas rather than fully mutating the stored candidate payload baseline
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest api.service.tests.test_review_detail api.service.tests.test_ops_scenario_qa`
  - passed
- Known issues: review detail may still show original source-derived values for other overridden fields because this slice intentionally did not widen candidate-record mutation beyond `product_name`
- Next step: reopen a review task whose product name was edited and confirm the candidate summary as well as the page header now load the corrected product name directly from the stored candidate row

## 2026-04-20 - Candidate Product Name Backfill SQL

- WBS: `4.3`, `4.4`
- Status: `done`
- Goal: add a separate SQL script that backfills already-stored review tasks so older `edit_approve` product-name overrides also update `normalized_candidate.product_name`
- Why now: Product Owner asked for a standalone SQL after confirming that the runtime fix only helps future edits, while previously stored review decisions still need one-time DB repair
- Outcome: added `db/migrations/0009_backfill_review_edit_approved_candidate_product_name.sql`, which finds the latest non-empty `product_name` override from each candidate's `edit_approve` decision history and backfills both `normalized_candidate.product_name` and `candidate_payload.product_name`. Updated DB and API service README files to include the new script in the documented apply order
- Not done: this slice did not execute the SQL against a live database from Codex, and it did not broaden the backfill to other override fields beyond `product_name`
- Key files: `db/migrations/0009_backfill_review_edit_approved_candidate_product_name.sql`, `db/README.md`, `api/service/README.md`, `docs/00-governance/development-journal.md`
- Decisions: kept the backfill idempotent and narrow. It uses the latest stored `edit_approve` decision per candidate, trims whitespace-only names away, and updates rows only when the stored candidate name or `candidate_payload.product_name` still differs from the approved override
- Verification:
  - manual SQL review of `db/migrations/0009_backfill_review_edit_approved_candidate_product_name.sql`
  - README apply-order updates reviewed in `db/README.md` and `api/service/README.md`
- Known issues: Codex did not run the SQL because this workspace has no live Postgres target attached in-session, so DB execution and result verification still need to happen against your environment
- Next step: run `psql $env:FPDS_DATABASE_URL -f db/migrations/0009_backfill_review_edit_approved_candidate_product_name.sql` against the target database, then reload the affected review detail and confirm the candidate name now matches the approved product name

## 2026-04-20 - Approved Review Reopen for Edit Approve

- WBS: `4.3`
- Status: `done`
- Goal: let operators reopen already-approved review tasks for a follow-up `Edit & approve` correction
- Why now: Product Owner asked to reopen approved reviews so previously approved tasks can still receive a controlled edit pass without creating a separate recovery workflow
- Outcome: the review-detail API now exposes `edit_approve` as the only mutation action for `approved` tasks, and the backend decision guard now allows `approved -> edit_approve` while still keeping `rejected` and already-`edited` tasks closed. This preserves a narrow correction path instead of fully reopening every terminal state
- Not done: this slice did not reopen approved tasks for `reject` or `defer`, and it did not allow already-`edited` tasks to be edited again
- Key files: `api/service/api_service/review_detail.py`, `api/service/tests/test_review_detail.py`, `api/service/tests/test_ops_scenario_qa.py`, `app/admin/README.md`, `api/service/README.md`, `docs/00-governance/development-journal.md`
- Decisions: limited the reopen path to `approved` plus `edit_approve` only. That is the smallest change that satisfies the operator correction need without weakening the broader terminal-state model for rejected or already-edited work
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest api.service.tests.test_review_detail api.service.tests.test_ops_scenario_qa`
  - passed
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
- Known issues: a previously approved task will now move to `edited` after the follow-up correction, so operators should treat that path as a controlled post-approval fix rather than as a no-history overwrite
- Next step: reopen one approved review in the admin UI, confirm only `Edit & approve` is available, and verify the follow-up correction lands as an appended decision-history entry with review state `edited`

## 2026-04-20 - Edited Review Reopen for Additional Edit Approve

- WBS: `4.3`
- Status: `done`
- Goal: keep already-`edited` review tasks editable through the same `Edit & approve` path instead of making them read-only after the first correction
- Why now: Product Owner reported that the review detail still showed the read-only message after a first edit because the task had already moved from `approved` to `edited`, which the prior fix still treated as closed
- Outcome: review-detail action availability and backend decision guards now allow both `approved` and `edited` tasks to run another `edit_approve`. Rejected tasks remain closed, and the correction flow still stays append-only through additional decision-history entries
- Not done: this slice did not reopen rejected tasks and did not add a separate “reopen” state; it only widened the existing post-approval correction path
- Key files: `api/service/api_service/review_detail.py`, `api/service/tests/test_review_detail.py`, `api/service/tests/test_ops_scenario_qa.py`, `app/admin/README.md`, `api/service/README.md`, `docs/00-governance/development-journal.md`
- Decisions: extended the narrow correction path from `approved` to `edited` because an approved task becomes `edited` immediately after the first correction, and keeping that state closed would make the first reopen fix feel broken in normal operator use
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest api.service.tests.test_review_detail api.service.tests.test_ops_scenario_qa`
  - passed
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
- Known issues: repeated edit passes continue to append history while leaving the review state as `edited`, so operators need to read decision history to understand how many post-approval corrections have already happened
- Next step: reload the previously read-only edited review and confirm the decision form now shows `Edit & approve` instead of the closed-task message

## 2026-04-20 - Repeated Edit Approve Product Version Constraint Fix

- WBS: `4.3`
- Status: `done`
- Goal: stop repeated `Edit & approve` on the same candidate from failing with `product_version_approved_candidate_id_key` unique-constraint errors
- Why now: after reopening edited reviews, Product Owner hit a live `500` because the backend tried to create another `product_version` row with the same `approved_candidate_id`, but the schema only allows one direct candidate-to-version link per candidate
- Outcome: repeated post-approval edit passes now insert new `product_version` rows with `approved_candidate_id = NULL` when the review task is already in `approved` or `edited`. The first approval keeps the candidate link, while later correction versions still append normally without violating the unique constraint
- Not done: this slice did not redesign the schema or remove the existing unique constraint; it fixed the runtime write path to respect the current data model
- Key files: `api/service/api_service/review_detail.py`, `api/service/tests/test_ops_scenario_qa.py`, `docs/00-governance/development-journal.md`
- Decisions: treated `approved_candidate_id` as the original direct approval link rather than as a field that must be copied onto every later correction version. That keeps the current schema intact and avoids an unnecessary migration while still allowing repeated edit passes
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest api.service.tests.test_review_detail api.service.tests.test_ops_scenario_qa`
  - passed
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
- Known issues: if you want every later correction version to preserve an explicit candidate foreign key rather than `NULL`, that would need a broader schema change instead of this runtime fix
- Next step: retry the same repeated `Edit & approve` flow in local dev and confirm the request now succeeds without the unique-constraint error

## 2026-04-20 - BMO Product Name Extraction Hardening

- WBS: `3.5`, `5.3`
- Status: `done`
- Goal: stop BMO savings detail collects from deriving section labels like `B E N E F I T S` as `product_name`
- Why now: Product Owner found that BMO product pages were collecting the correct detail URLs but still saving the wrong product name because the current extraction heuristic trusted the first PDF chunk line after the BMO browser-snapshot fallback
- Outcome: product-name extraction now scores multiple early lines across the parsed evidence chunks instead of blindly taking the first line. The heuristic now downranks navigation or CTA text, recognizes generic section labels even when PDF text spacing splits them into `B E N E F I T S`, and strips wrappers such as `... FAQs` or `Explore the features of ...` so BMO PDF fallback pages can still resolve titles like `Savings Amplifier Account`
- Not done: this slice did not rerun a live BMO collection from the admin UI inside the session, and it did not redesign the broader PDF parsing pipeline beyond the title-selection heuristic
- Key files: `worker/pipeline/fpds_extraction/service.py`, `worker/pipeline/tests/test_extraction.py`, `docs/00-governance/development-journal.md`
- Decisions: kept the fix inside extraction rather than adding BMO-only registry overrides. The heuristic stays evidence-first by reading multiple candidate lines from the parsed document and only using cleaned title-like text when it scores above generic section or CTA lines
- Verification:
  - `python -m unittest worker.pipeline.tests.test_extraction`
  - passed
  - `python -m unittest worker.pipeline.tests.test_extraction worker.pipeline.tests.test_normalization`
  - passed
- Known issues: live BMO pages still arrive through the targeted browser-to-PDF fallback, so future quality work may still want parser-level cleanup for cookie-banner or navigation noise that appears in the rendered PDFs
- Next step: rerun the BMO savings collect flow against the real page and confirm the stored candidate product names now resolve to the account title instead of `B E N E F I T S`

## 2026-04-20 - Worker Psql Windows Command-Length Hardening

- WBS: `3.2`, `3.3`, `3.5`, `3.6`, `3.7`, `3.8`, `5.6`
- Status: `done`
- Goal: stop Big 5 collection runs from failing on Windows when worker persistence sends large JSON payloads to `psql` through `-v key=value` command-line arguments
- Why now: Product Owner reported that the CIBC savings collect failed at the snapshot stage with `FileNotFoundError: [WinError 206] The filename or extension is too long`, which pointed to a local worker persistence bug rather than a bank-site fetch failure
- Outcome: added a shared worker `psql` helper that strips large `-v` payloads off the process command line, rewrites `:'var'` placeholders to stdin-safe hex-decoded expressions, and sends the variable content through the `psql` input stream instead. Snapshot persistence now uses that helper, and the same fix was applied to the downstream worker persistence modules so parse, extraction, normalization, validation, result-viewer export, evidence retrieval, and aggregate refresh do not hit the same Windows command-length limit later in the run
- Not done: this slice did not rerun the live CIBC savings collect from the admin UI inside the session, and it did not change the homepage-first source-selection quality that still allows low-confidence supporting CIBC pages into the generated registry scope
- Key files: `worker/psql_cli.py`, `worker/discovery/fpds_snapshot/persistence.py`, `worker/pipeline/fpds_parse_chunk/persistence.py`, `worker/pipeline/fpds_extraction/persistence.py`, `worker/pipeline/fpds_normalization/persistence.py`, `worker/pipeline/fpds_validation_routing/persistence.py`, `worker/pipeline/fpds_result_viewer/persistence.py`, `worker/pipeline/fpds_evidence_retrieval/persistence.py`, `worker/pipeline/fpds_aggregate_refresh/persistence.py`, `worker/discovery/tests/test_psql_cli.py`, `docs/00-governance/development-journal.md`
- Decisions: fixed the issue at the shared worker `psql` boundary instead of adding a snapshot-only workaround. That keeps the SQL text mostly unchanged, avoids widening the live schema surface, and hardens the other worker stages that still used the same `-v` argument pattern
- Verification:
  - `python -m unittest worker.discovery.tests.test_psql_cli`
  - passed
  - `python -m unittest worker.discovery.tests.test_snapshot_persistence`
  - passed
  - `python -m unittest worker.pipeline.tests.test_parse_chunk worker.pipeline.tests.test_extraction worker.pipeline.tests.test_normalization worker.pipeline.tests.test_validation_routing worker.pipeline.tests.test_result_viewer worker.pipeline.tests.test_evidence_retrieval worker.pipeline.tests.test_aggregate_refresh`
  - passed
- Known issues: this fixes the Windows command-length failure, but it does not reduce overscoped generated-source batches such as CIBC savings pulling unrelated low-confidence supporting pages and PDFs into the run
- Next step: rerun the failing CIBC savings collect in local dev and confirm the snapshot stage now persists successfully instead of failing before `run_source_item` rows are written

## 2026-04-20 - Failed Run Retry From Run Detail

- WBS: `4.5`, `5.15`
- Status: `done`
- Goal: let operators retry failed collection runs directly from `/admin/runs/:runId` instead of leaving the run detail screen to reconstruct the same collect action elsewhere
- Why now: Product Owner asked for a run-detail retry path after diagnosing failed collection runs, especially when the failure root cause was local runtime behavior rather than a bad bank source
- Outcome: added `POST /api/admin/runs/:runId/retry` plus a matching admin proxy route and run-detail action button. Failed run detail now shows retry availability for supported collection runs, and retrying creates a fresh queued run while linking the original run as `retried` and the new run as its next attempt. The current implementation supports failed `source_catalog_collection` and `source_collection` runs, which are the collection-safe run types with enough persisted scope metadata to reconstruct their input safely
- Not done: this slice does not retry arbitrary internal stage runs such as standalone snapshot, parse, extraction, or normalization attempts. Those remain diagnostic-only because replaying a partial stage without its parent collection context would be riskier and less predictable
- Key files: `api/service/api_service/run_retry.py`, `api/service/api_service/main.py`, `api/service/api_service/run_status.py`, `api/service/api_service/source_registry.py`, `api/service/api_service/source_catalog.py`, `api/service/tests/test_run_retry.py`, `api/service/tests/test_run_status.py`, `api/service/tests/test_source_catalog.py`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/app/admin/runs/[runId]/page.tsx`, `app/admin/src/app/admin/runs/[runId]/retry/route.ts`, `app/admin/src/components/fpds/admin/run-detail-surface.tsx`, `app/admin/README.md`, `api/service/README.md`, `docs/00-governance/development-journal.md`
- Decisions: kept the retry feature narrow to failed collection runs only. That gives operators a practical recovery path without pretending every failed ingestion sub-stage can be safely replayed in isolation. The original failed run now moves to `retried`, so default run-list filters may hide it unless operators include the `retried` state
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest api.service.tests.test_run_retry api.service.tests.test_run_status api.service.tests.test_source_catalog api.service.tests.test_source_registry`
  - passed
  - `api/service/.venv/Scripts/python.exe -m unittest api.service.tests.test_ops_scenario_qa`
  - passed
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
- Known issues: if a failed run's stored metadata is incomplete, unsupported, or expands back into multiple run groups during reconstruction, the retry endpoint returns a controlled error instead of forcing an unsafe replay
- Next step: retry a live failed `source_catalog_collection` run from `/admin/runs/:runId` and confirm the button redirects into the new queued attempt while the original run now shows `Retried by`

## 2026-04-20 - CIBC Review Validation Clarification And Money Extraction Hardening

- WBS: `3.5`, `4.2`, `4.4`
- Status: `done`
- Goal: explain why a completed CIBC savings collect still produced review tasks with `error`, reduce misleading money extraction on those candidates, and make the review UI distinguish validation errors from run failures more clearly
- Why now: Product Owner reported confusion because `run_20260420_203122_cibc_savings_collect_e_X9pLAb` completed successfully while two review tasks still showed `error`. Investigation showed the run itself had succeeded, but candidate validation failed because the fetched CIBC HTML exposed unresolved `RDS%rate[...]` placeholders instead of canonical numeric savings rates. The same candidates also had noisy money extraction such as `monthly_fee = 200000.00`
- Outcome: money extraction is now field-aware for `monthly_fee`, `public_display_fee`, `minimum_balance`, and `minimum_deposit`. The extractor now reads money values near the relevant label instead of grabbing the first dollar amount in the chunk, which stops CIBC savings review payloads from treating values like `$200,000` or unrelated contribution limits as fees. On the admin side, review queue and review detail now label `error` and `warning` badges as `Validation Error` and `Validation Warning` so operators do not read candidate-validation state as a run-execution failure
- Not done: this slice did not eliminate the CIBC review errors entirely. The current raw CIBC savings HTML still does not expose canonical numeric rates in a form the heuristic pipeline can store, so those candidates continue to require review until a larger bank-specific rate-capture slice lands
- Key files: `worker/pipeline/fpds_extraction/service.py`, `worker/pipeline/tests/test_extraction.py`, `app/admin/src/components/fpds/admin/review-detail-surface.tsx`, `app/admin/src/components/fpds/admin/review-queue-surface.tsx`, `docs/00-governance/development-journal.md`
- Decisions: kept the data fix narrow and safe. Instead of weakening validation or pretending unresolved placeholder strings satisfy required canonical savings-rate fields, the slice fixes the clearly wrong money extraction and clarifies the UI label so the remaining `Validation Error` still reflects a real data-quality gap
- Verification:
  - `python -m unittest worker.pipeline.tests.test_extraction`
  - passed
  - `pnpm run typecheck`
  - passed in `app/admin`
- Known issues: CIBC savings still needs a follow-on source-specific solution if we want those candidates to auto-pass validation. The underlying page content currently persists unresolved rate placeholders, so canonical numeric rate extraction remains incomplete
- Next step: rerun the CIBC savings collect after this extraction fix and confirm the review payload no longer shows impossible fee values, then decide whether the next slice should target CIBC-specific rate capture or supporting-source merge logic

## 2026-04-20 - Multi-Bank Collection Partial-Failure Hardening And Generic Title Cleanup

- WBS: `3.2`, `3.5`, `3.6`, `5.15`
- Status: `done`
- Goal: stop mixed-bank collection batches from failing the whole run when a subset of sources fails snapshot or parse, and reduce the generic marketing-title noise that was creating low-quality review tasks across RBC, Scotia, and TD
- Why now: Product Owner ran three banks together and surfaced two classes of problems. First, some sources failed for generic reasons such as stale `http://` links, stale `404` pages, and encrypted PDFs that local `pypdf` could not open without extra crypto support. Those per-source failures still cascaded into run-level `fpds_extraction failed with exit code 1` because the source-collection runner passed every snapshot-success source into downstream stages even when parse or extraction had already failed for part of the set. Second, review tasks showed recurring cross-bank extraction noise such as `Benefits of ...` or `More Great ... Features` becoming `product_name`, `Monthly Fee Free` being read as nonzero fees, `90 days old` becoming a false term length, and `next business day` falsely tagging products as business banking
- Outcome: hardened `source_collection_runner` so each downstream stage now filters its input to the source ids that actually succeeded in the previous stage. Snapshot, parse, extraction, and normalization success are now chained explicitly, so one bad PDF or stale source no longer causes extraction to crash on missing parsed documents for unrelated survivors. Discovery fetch now upgrades allowlisted `http://` URLs to `https://` before validation and marks `404` fetches as non-retryable so snapshot capture fails them once instead of wasting repeated attempts. Extraction title cleanup now strips wrappers like `Benefits of ...`, `About ...`, and `What are ...`, downranks trailing `... Features` headings, treats fee labels followed by `Free` as zero, and requires term-like context before turning day/month/year phrases into `term_length_*`. Normalization now infers GIC subtype from a wider set of evidence fields and no longer tags a product as `business` just because text mentions a `business day`
- Not done: this slice does not make encrypted AES PDFs parse locally without the missing crypto dependency, and it does not auto-heal stale registry URLs like the dead Scotia savings page. Those sources still fail individually, but they no longer take down otherwise healthy runs. Some review tasks for broad category pages will also still require human review because the source page itself does not expose a clean single-product payload
- Key files: `api/service/api_service/source_collection_runner.py`, `api/service/tests/test_source_collection_runner.py`, `worker/discovery/fpds_discovery/fetch.py`, `worker/discovery/fpds_snapshot/capture.py`, `worker/discovery/tests/test_discovery.py`, `worker/discovery/tests/test_snapshot_capture.py`, `worker/pipeline/fpds_extraction/service.py`, `worker/pipeline/fpds_normalization/service.py`, `worker/pipeline/tests/test_extraction.py`, `worker/pipeline/tests/test_normalization.py`, `docs/00-governance/development-journal.md`
- Decisions: fixed the run fragility at the orchestration boundary instead of weakening stage-level validation or pretending missing parse artifacts are acceptable input to extraction. Kept the fetch fix generic by canonicalizing allowlisted `http://` links to `https://` rather than bank-specific registry overrides. For review quality, preferred conservative heuristic cleanup over bank-specific title maps so the same fix helps TD `Benefits of ...` GIC pages, RBC `... Features` headings, and Scotia generic subtype text
- Verification:
  - `python -m unittest tests.test_source_collection_runner`
  - passed in `api/service`
  - `python -m unittest worker.discovery.tests.test_discovery worker.discovery.tests.test_snapshot_capture`
  - passed
  - `python -m unittest worker.pipeline.tests.test_extraction worker.pipeline.tests.test_normalization`
  - passed
- Known issues: stale registry links will still surface as failed source items until the registry materialization slice learns how to replace or suppress them proactively. Encrypted PDFs that require unavailable AES crypto support still fail parse on this machine, but the surviving HTML and PDF sources now continue through the run instead of causing downstream stage crashes
- Next step: rerun the previously failing RBC chequing and Scotia chequing/savings collects, confirm they finish as partial completion instead of failed runs, and then review whether the remaining stale-source rows should become a separate registry-refresh cleanup slice

## 2026-04-20 - Partial-Failure Hardening Live Rerun Verification

- WBS: `3.2`, `3.5`, `3.6`, `5.15`
- Status: `done`
- Goal: confirm that the interrupted partial-failure hardening slice actually fixes the previously failed live source-catalog runs instead of only passing unit tests
- Why now: the prior session was interrupted before we could verify the real failed runs, so the repo still had confusing live logs that showed RBC and Scotia collections dying in extraction with `No parsed document was found...`
- Outcome: confirmed that the live failure logs predated the hardening patch. `api/service/api_service/source_collection_runner.py` was last modified after the stored failed RBC and Scotia logs, and rerunning the same stored source-catalog plans against the live dev DB now completes successfully. `run_20260420_222518_rbc_chequing_collect_IYDOM_51`, `run_20260420_222518_scotia_chequing_collect_h6WIxrEK`, and `run_20260420_222518_scotia_savings_collect_b1zEZ9d_` all reached validation/routing instead of crashing in extraction. The Scotia savings rerun still carried one expected source-level `404` snapshot failure plus one candidate-level `validation_error`, but the run completed and queued review work instead of failing the whole batch
- Not done: this slice did not add new runtime code because the filtering fix was already present in the working tree. It also did not resolve the stale Scotia savings source URL or the remaining savings candidate validation gap
- Key files: `docs/00-governance/development-journal.md`, `api/service/api_service/source_collection_runner.py`, `tmp/source-catalog-collections/run_20260420_222518_rbc_chequing_collect_IYDOM_51.log`, `tmp/source-catalog-collections/run_20260420_222518_scotia_chequing_collect_h6WIxrEK.log`, `tmp/source-catalog-collections/run_20260420_222518_scotia_savings_collect_b1zEZ9d_.log`
- Decisions: treated this as a verification-and-closeout slice rather than widening scope into extra lineage or run-status redesign work. The current runner filtering is sufficient to prevent the original extraction crash on the reproduced live runs
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest api.service.tests.test_run_retry api.service.tests.test_run_status api.service.tests.test_source_catalog api.service.tests.test_source_registry api.service.tests.test_source_collection_runner`
  - passed
  - `python -m unittest worker.discovery.tests.test_psql_cli worker.discovery.tests.test_discovery worker.discovery.tests.test_snapshot_capture`
  - passed
  - `python -m unittest worker.pipeline.tests.test_extraction worker.pipeline.tests.test_normalization`
  - passed
  - `pnpm run typecheck`
  - passed in `app/admin`
  - `pnpm run build`
  - passed in `app/admin`
  - `api/service/.venv/Scripts/python.exe -m api_service.source_catalog_collection_runner --plan-path tmp/source-catalog-collections/run_20260420_222518_rbc_chequing_collect_IYDOM_51.json`
  - completed successfully; run reached validation/routing and finished
  - `api/service/.venv/Scripts/python.exe -m api_service.source_catalog_collection_runner --plan-path tmp/source-catalog-collections/run_20260420_222518_scotia_chequing_collect_h6WIxrEK.json`
  - completed successfully; run reached validation/routing and finished
  - `api/service/.venv/Scripts/python.exe -m api_service.source_catalog_collection_runner --plan-path tmp/source-catalog-collections/run_20260420_222518_scotia_savings_collect_b1zEZ9d_.json`
  - completed successfully; run reached validation/routing and finished with source-level partial data quality issues instead of a run-level extraction crash
- Known issues: Scotia savings still has a dead `404` source URL in the generated scope, and one savings candidate still lands in review with `validation_error`. Those are real data-quality follow-ons, not orchestration failures
- Next step: separate the remaining Scotia savings stale-source cleanup from the already-fixed orchestration bug, then decide whether the next slice should focus on registry materialization cleanup or source-specific validation improvement

## 2026-04-20 - Scotia Savings Seed Scope Refresh and Money Master Follow-up

- WBS: `3.6`, `5.15`
- Status: `done`
- Goal: close the two remaining Scotia savings follow-ups by fixing the stale preserved-scope `404` and the Money Master savings validation gap
- Why now: after the partial-failure hardening verification, Scotia savings still reused an old active `SCOTIA-SAV-005` row when homepage discovery preserved existing detail scope, so the run kept carrying a dead U.S. Dollar savings URL even though the seed JSON had already been corrected. At the same time, `SCOTIA-SAV-004` Money Master still lacked rate fields and landed in review with `validation_error`
- Outcome: updated the Scotia savings seed registry URL for `SCOTIA-SAV-005` and added a focused preserved-scope refresh step in `source_catalog_collection_runner` so active seeded rows are rewritten from the current seed baseline before preserved detail scope is reused. This removed the stale `404` from the live Scotia savings run and changed `SCOTIA-SAV-005` snapshot capture from fetch failure to successful HTML capture on `https://www.scotiabank.com/ca/en/personal/bank-accounts/savings-accounts/us-dollar-interest-account.html`. Also extended normalization supporting-merge logic so `SCOTIA-SAV-004` can borrow `standard_rate` and `public_display_rate` from `SCOTIA-SAV-006`, which moved Money Master from `validation_error` to `validation_status=pass` in the live rerun
- Not done: `SCOTIA-SAV-005` now reaches normalization and validation, but it still lands in review with `required_field_missing`. This is a new real content or parser gap that was previously masked by the dead URL, and it should be treated as the next separate savings-quality slice rather than part of the stale-link fix
- Key files: `api/service/api_service/source_catalog_collection_runner.py`, `api/service/tests/test_source_catalog_collection_runner.py`, `worker/discovery/data/scotia_savings_source_registry.json`, `worker/discovery/tests/test_registry_catalog.py`, `worker/pipeline/fpds_normalization/supporting_merge.py`, `worker/pipeline/tests/test_normalization.py`, `tmp/source-collections/run_20260420_222518_scotia_savings_collect_b1zEZ9d_.registry.json`, `tmp/source-catalog-collections/run_20260420_222518_scotia_savings_collect_b1zEZ9d_.log`
- Decisions: kept the preserved-scope fix narrow by refreshing only active seed-backed rows for the current bank and product type immediately before preserved detail reuse, instead of widening this slice into a broader registry reseed or migration job. For Money Master, used the existing supporting-artifact merge pattern rather than adding a Scotia-only extraction special case
- Verification:
  - `api/service/.venv/Scripts/python.exe -m unittest api.service.tests.test_source_catalog_collection_runner api.service.tests.test_source_catalog`
  - passed
  - `python -m unittest worker.discovery.tests.test_registry_catalog worker.pipeline.tests.test_normalization`
  - passed
  - `api/service/.venv/Scripts/python.exe -m api_service.source_catalog_collection_runner --plan-path tmp/source-catalog-collections/run_20260420_222518_scotia_savings_collect_b1zEZ9d_.json`
  - completed successfully; `SCOTIA-SAV-005` fetched from the new U.S. Dollar interest account URL and `SCOTIA-SAV-004` validated with supplemented rate fields
- Known issues: `SCOTIA-SAV-005` still has a candidate-level `required_field_missing` validation error after the stale URL is fixed. That issue is now isolated and reproducible against the live page content
- Next step: inspect the normalized and validated artifacts for `SCOTIA-SAV-005`, identify which required field is still missing, and decide whether the correct fix belongs in savings extraction heuristics or in a Scotia-specific supporting merge

## 2026-04-21 - Aggregate Refresh Auto Queue and Dashboard Health

- WBS: `5.6`, `5.7`, `5.8`, `5.13`
- Status: `done`
- Goal: make approved canonical changes propagate to public aggregate snapshots automatically, preserve latest-successful serving on failure, and expose the refresh state on a real admin health route with manual retry
- Why now: `/products` was showing zero products even though `canonical_product` already had live approved rows because no successful aggregate snapshot existed yet. The current review approval flow wrote canonical truth but did not enqueue the post-commit aggregate refresh step described in the design docs, so public serving could silently drift from admin truth
- Outcome: added `db/migrations/0010_aggregate_refresh_queue.sql` with a new `aggregate_refresh_request` table, implemented `api_service.aggregate_refresh` plus `api_service.aggregate_refresh_runner`, and wired `approve` / `edit-approve` to insert queue rows in the same transaction before launching a background runner after commit. The runner now coalesces queued requests into one refresh execution, reuses the existing aggregate worker persistence path, and keeps public serving on the latest successful snapshot when newer refreshes fail. Added `GET /api/admin/dashboard-health` and `POST /api/admin/dashboard-health/retry`, then shipped the live `/admin/health/dashboard` surface with pending, stale, failed, and healthy status visibility plus manual retry
- Not done: this slice did not introduce a broader scheduler, lease-expiry governance, or a second publish approval gate. The queue is single-scope for the current Canada public aggregate baseline and intentionally keeps operator control to visibility plus retry
- Key files: `db/migrations/0010_aggregate_refresh_queue.sql`, `api/service/api_service/aggregate_refresh.py`, `api/service/api_service/aggregate_refresh_runner.py`, `api/service/api_service/main.py`, `api/service/tests/test_aggregate_refresh.py`, `app/admin/src/app/admin/health/dashboard/page.tsx`, `app/admin/src/app/admin/health/dashboard/retry/route.ts`, `app/admin/src/components/fpds/admin/health-dashboard-surface.tsx`, `app/admin/src/lib/admin-api.ts`, `app/admin/src/components/application-shell5.tsx`, `api/service/README.md`, `app/admin/README.md`, `db/README.md`, `README.md`
- Decisions: kept `aggregate_refresh_run` as execution history and added a separate queue table instead of overloading execution rows with `queued` semantics. Kept refresh asynchronous and post-commit so review approval never depends on public projection success. Chose visibility plus retry over a second public-release approval because review approval is already the human gate in Phase 1
- Verification:
  - `python -m unittest tests.test_aggregate_refresh tests.test_run_retry tests.test_public_products tests.test_review_detail`
  - passed in `api/service`
  - `python -m compileall api_service`
  - passed in `api/service`
  - `pnpm run typecheck`
  - passed in `app/admin`
- Known issues: the queue currently assumes one active Canada public aggregate scope and relies on the single-runner advisory lock rather than a broader scheduler or lease system. If the runtime later needs multi-country or per-scope refresh governance, the queue contract should expand explicitly instead of growing implicitly
- Next step: apply `0010_aggregate_refresh_queue.sql` to the target database, restart the admin API so the new routes and runner module are available, then approve or edit-approve one review task and confirm `/admin/health/dashboard` moves through `pending` to `healthy` while `/products` continues serving the latest successful snapshot

## 2026-04-21 - Customer Reports Cleanup

- WBS: documentation hygiene
- Status: `done`
- Goal: remove the retired external reporting docs and scrub related references so the docs set matches the current operating boundary
- Why now: the Product Owner asked to delete the retired reporting folder and remove related references from the remaining docs
- Outcome: deleted the retired reporting documents, removed the old report-specific journal entry, and tightened the Phase 1 QA checklist so evidence now stays under `docs/00-governance/` without referencing a separate external summary artifact
- Not done: did not introduce a replacement reporting location or a new external-reporting workflow
- Key files: `docs/00-governance/development-journal.md`, `docs/00-governance/phase-1-no-bxpf-test-checklist.md`
- Decisions: treated the retired reporting area as intentionally removed rather than relocated, and removed direct historical references so future readers do not chase deleted paths
- Verification:
  - `Get-ChildItem -Name docs`
  - showed only `00-governance`, `01-planning`, `02-requirements`, `03-design`, and `README.md`
  - `git status --short docs`
  - showed two modified governance docs and two deleted reporting files
  - `git diff --check`
  - passed
- Known issues: generic product-domain uses of the word `customer` still remain elsewhere in requirements, API, and UI docs because they are unrelated to the deleted reporting folder
- Next step: if external reporting is needed again later, define a new approved location and governance rule before reintroducing shareable reporting artifacts

## 2026-04-21 - Runtime Reseed Removal for Resettable Registry State

- WBS: `5.15`, `5.16`
- Status: `done`
- Goal: stop bank, product type, source catalog, and generated source rows from silently repopulating after an operator reset so empty-state replay testing is possible without dropping the whole DB
- Why now: after truncating `bank` and `product_type_registry`, the Product Owner saw those rows come back after logging in again and reasonably treated that as an unwanted runtime migration path. The real problem was not auth-session migration, but API and admin reads that were reseeding from committed JSON baselines or refreshing active seed scope behind the scenes
- Outcome: removed runtime reseeding from `product_types.py`, `source_catalog.py`, and `source_registry.py`, removed the background-runner seed-scope refresh that rewrote active source rows before preserved-detail reuse, and updated the admin product-type surface copy so it no longer implies protected built-in types. Bank, product type, source catalog, and source registry tables now stay empty after operator truncation until an explicit import, migration replay, or admin write repopulates them
- Not done: did not rewrite historical SQL migrations that insert the original bank and product type baseline on a brand-new database. Those inserts still happen only when a database is recreated and migrations are applied from scratch, and changing that behavior should be treated as a separate migration-strategy decision because existing environments may depend on append-only history
- Key files: `api/service/api_service/product_types.py`, `api/service/api_service/source_catalog.py`, `api/service/api_service/source_registry.py`, `api/service/api_service/source_catalog_collection_runner.py`, `api/service/tests/test_product_types.py`, `api/service/tests/test_source_catalog.py`, `api/service/tests/test_source_registry.py`, `api/service/tests/test_source_catalog_collection_runner.py`, `app/admin/src/components/fpds/admin/product-type-registry-surface.tsx`, `app/admin/src/components/fpds/admin/product-type-detail-dialog-content.tsx`, `api/service/README.md`, `app/admin/README.md`, `docs/03-design/source-registry-refresh-and-approval-policy.md`
- Decisions: kept the fix on runtime behavior and operator-facing copy instead of mutating already-applied historical SQL files. Retained committed JSON baselines only as discovery hints and offline import material, not as an automatic DB repair path
- Verification:
  - runtime code search no longer returns `ensure_product_type_registry_seeded`, `_ensure_bank_and_catalog_seeded`, `_ensure_source_registry_seeded`, or `_refresh_active_seed_scope_rows` inside `api/service/api_service`
  - remaining automatic bootstrap found during inspection is limited to historical fresh-DB migration inserts in `db/migrations/0001_initial_baseline.sql` for `bank` and `db/migrations/0007_dynamic_product_type_onboarding.sql` for `product_type_registry`
- Known issues: a fully fresh database created by replaying the current migration chain will still receive the historical bank and product type baseline rows from those SQL files. That path is no longer tied to login or admin browsing, but it remains relevant for teardown-and-rebuild environments
- Next step: if the Product Owner wants brand-new databases to start empty as well, choose an explicit migration strategy first rather than quietly editing historical migration files

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
| 2026-04-14 | Added the WBS 5.11 grid/dashboard cross-filter implementation entry and verification results |
| 2026-04-15 | Added the WBS 5.13 freshness and metric note wording entry and verification results |
| 2026-04-15 | Added the public hydration warning guard entry and verification results |
| 2026-04-15 | Added the interim Phase 1 no-BXPF test checklist entry |
| 2026-04-15 | Added the source registry admin MVP documentation baseline entry |
| 2026-04-15 | Added the WBS 5.15 source registry admin MVP implementation entry |
| 2026-04-15 | Added the WBS 5.15 source registry unique-scope fix entry |
| 2026-04-15 | Added the WBS 5.15 source registry null-filter query fix entry |
| 2026-04-15 | Added the WBS 5.15 bank and source-catalog admin refinement entry |
| 2026-04-16 | Added the API service worker import path fix entry |
| 2026-04-16 | Added the admin hydration warning guard entry and verification results |
| 2026-04-16 | Added the bank registry modal workflow refresh entry and verification results |
| 2026-04-19 | Added the source-catalog async queue and snapshot hardening entry |
| 2026-04-19 | Added the preserved-detail fallback fix entry for source-catalog background runs |
| 2026-04-19 | Added the per-run isolation and stage-timeout guard entry for source-catalog background runs |
| 2026-04-19 | Added the BMO browser snapshot fallback entry |
| 2026-04-20 | Added the review detail list-value trace fix entry |
| 2026-04-20 | Added the review detail dedicated product-name override entry |
| 2026-04-20 | Added the review detail approved-name display fix entry |
| 2026-04-20 | Added the review detail candidate-name sync-on-edit-approve entry |
| 2026-04-20 | Added the candidate product-name backfill SQL entry |
| 2026-04-20 | Added the approved-review reopen-for-edit-approve entry |
| 2026-04-20 | Added the edited-review reopen-for-additional-edit-approve entry |
| 2026-04-20 | Added the repeated edit-approve product-version constraint fix entry |
| 2026-04-20 | Added the worker psql Windows command-length hardening entry |
| 2026-04-20 | Added the failed run retry from run detail entry |
| 2026-04-20 | Added the CIBC review validation clarification and money extraction hardening entry |
| 2026-04-20 | Added the multi-bank collection partial-failure hardening and generic title cleanup entry |
| 2026-04-20 | Added the partial-failure hardening live rerun verification entry |
| 2026-04-20 | Added the Scotia savings seed-scope refresh and Money Master follow-up entry |
| 2026-04-21 | Added the aggregate refresh auto-queue and dashboard health entry |
| 2026-04-21 | Removed the retired external reporting artifacts and scrubbed related governance references |
| 2026-04-21 | Removed runtime reseeding and seed-scope refresh behavior so bank, product type, source catalog, and source registry tables now stay empty after operator resets until explicitly repopulated |
