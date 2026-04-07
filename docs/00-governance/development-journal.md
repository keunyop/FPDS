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

---

## 7. Change History

| Date | Change |
|---|---|
| 2026-04-07 | Initial development journal created |
| 2026-04-07 | Rewrote the journal in clean UTF-8 text and added the WBS 2.2 entry |
