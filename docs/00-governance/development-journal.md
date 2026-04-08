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

---

## 7. Change History

| Date | Change |
|---|---|
| 2026-04-07 | Initial development journal created |
| 2026-04-07 | Rewrote the journal in clean UTF-8 text and added the WBS 2.2 entry |
| 2026-04-07 | Added the WBS 2.3 DB and migration baseline entry |
| 2026-04-07 | Added the WBS 2.4 object storage and evidence bucket baseline entry |
| 2026-04-07 | Added the combined WBS 2.7 and 2.10 monitoring and foundation CI baseline entry |
