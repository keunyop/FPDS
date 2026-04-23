# FPDS Harness Engineering Baseline

Version: 1.1
Date: 2026-04-09
Status: Active
Source Documents:
- `docs/00-governance/working-agreement.md`
- `docs/00-governance/stage-gate-checklist.md`
- `docs/00-governance/decision-log.md`
- `docs/01-planning/WBS.md`
- `docs/archive/01-planning/prototype-backlog.md`
- `docs/02-requirements/scope-baseline.md`
- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`

---

## 1. Purpose

This document fixes the repository harness baseline that should exist before WBS `2` and WBS `3` work moves forward.

Goals:
- lock the basic workflow guardrails before product implementation starts
- keep Product Owner visibility high with small, reviewable slices
- separate harness work from product implementation so the build hold rule stays intact

This is not a product feature approval document.
Its scope is the repository harness and workflow guardrails only.

---

## 2. Baseline Decisions

1. `AGENTS.md` keeps only short, always-on operating rules.
2. Before substantive work starts, the agent reads `AGENTS.md`, root `README.md`, and `docs/00-governance/development-journal.md`.
3. The pre-commit hook runs on `staged files only`.
4. The pre-commit hook auto-fixes only low-risk text hygiene issues and stays quiet on success.
5. Cleanup audit starts as `report-only` and does not auto-delete or auto-refactor files.
6. Repository-wide validation runs in CI.
7. The harness does not start product code implementation by itself.
8. Foundation baseline checks use one shared local and CI entrypoint for env or observability contracts and future package-script checks.
9. Future package-script checks should follow the approved runtime baseline, so JavaScript package checks are `pnpm-first` with fallback only when a package explicitly declares `npm`.
10. When project checks run against a real JavaScript package, the shared package-check entrypoint may install missing dependencies first so local and CI runs do not depend on prewarmed `node_modules`.

---

## 3. Harness Scope

Included:
- `AGENTS.md`
- root `README.md`
- `docs/00-governance/development-journal.md`
- Git hook entrypoint and install script
- staged-only pre-commit checks
- repo doctor
- report-only cleanup audit
- CI workflow for harness checks

Excluded:
- app, api, or worker feature implementation
- parser, DB, API, UI, or BX-PF connector implementation
- cleanup auto-delete
- autonomous refactor loops

---

## 4. Hook Model

### 4.1 Pre-Commit

Current pre-commit scope:
- staged text file trailing whitespace and final newline fixes
- staged Markdown local reference validation
- staged PowerShell syntax validation

Behavior:
- success stays quiet
- failures stop the commit and show a clear message
- the hook does not expand staged checks to a full-repo scan

### 4.2 CI

CI runs repository-wide validation for:
- required harness file presence
- Markdown reference validation
- PowerShell syntax validation
- JSON syntax validation
- foundation env and observability baseline validation
- future package-script checks such as `lint`, `typecheck`, `test`, and `build`
- missing JavaScript dependencies may be installed by the shared project-check entrypoint before those scripts run
- cleanup audit report generation

---

## 5. Cleanup Audit Model

Cleanup audit is `report-only`.

Current findings scope:
- broken local doc references
- trailing whitespace
- missing required harness files
- `TODO`, `FIXME`, and `HACK` markers

Possible future scope:
- unused code, import, or export checks
- unused env key checks
- dependency vulnerability reporting
- docs-versus-code drift checks

These should be added only after product code exists and the Product Owner agrees with the extra enforcement cost.

---

## 6. Development Journal Model

When a meaningful slice is completed, add a slice summary to `docs/00-governance/development-journal.md`.

Purpose:
- let the next Codex session resume without rereading the whole codebase
- give the Product Owner a compact record of outcome, verification, and known gaps
- keep handoff inside the repository instead of depending on chat history

Each entry should record at least:
- slice name and date
- goal and why the slice was done now
- actual repo or product impact
- key files
- decisions or constraints
- commands that were run for verification
- known issues and the next natural step

Do not turn the journal into:
- a full code walkthrough
- a pasted commit diff
- a chat transcript

---

## 7. File Map

| Path | Role |
|---|---|
| `AGENTS.md` | agent operating rules |
| `README.md` | repository entrypoint |
| `docs/00-governance/development-journal.md` | implementation memory and resume log |
| `.githooks/pre-commit` | Git hook entrypoint |
| `scripts/harness/install-hooks.ps1` | local hook install |
| `scripts/harness/pre-commit.ps1` | staged-only hook logic |
| `scripts/harness/repo-doctor.ps1` | repository health gate |
| `scripts/harness/validate-foundation-baseline.ps1` | env and observability baseline validation |
| `scripts/harness/invoke-foundation-checks.ps1` | local and CI foundation entrypoint |
| `scripts/harness/cleanup-audit.ps1` | report-only cleanup audit |
| `scripts/harness/invoke-project-checks.ps1` | future package-script checks |
| `.github/workflows/harness.yml` | foundation CI baseline |

---

## 8. Operating Notes

- Install hooks locally with `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/install-hooks.ps1`.
- Run the same foundation baseline used by CI with `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1`.
- Before substantive work starts, read `AGENTS.md`, root `README.md`, and `docs/00-governance/development-journal.md`.
- Keep `docs/README.md` as the docs map entrypoint.
- Strengthen project checks only after package management and runtime bootstrap are real, not hypothetical.
- When JavaScript package checks become real, prefer `pnpm` and allow `npm` only when the package explicitly signals it through `packageManager` or lockfile shape.
- For real JavaScript packages in CI, provide a pinned Node runtime and let the shared project-check entrypoint install dependencies when `node_modules` is missing.
- If cleanup audit ever moves beyond report-only, get Product Owner approval first.
- When a meaningful implementation slice ends, update `docs/00-governance/development-journal.md` in the same turn.

---

## 9. Change History

| Date | Change |
|---|---|
| 2026-04-07 | Initial harness engineering baseline created |
| 2026-04-07 | Added development journal rule for resume-friendly slice summaries |
| 2026-04-09 | Rewrote the document in ASCII-first format and added startup read order to include the development journal alongside `AGENTS.md` and root `README.md` |
| 2026-04-11 | Updated project-check guidance so future JavaScript runtime checks are pnpm-first in line with the approved runtime baseline |
| 2026-04-13 | Clarified that live JavaScript package checks may install missing dependencies and should run in CI with a pinned Node runtime |
