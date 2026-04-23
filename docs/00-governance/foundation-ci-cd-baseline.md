# FPDS Foundation CI/CD Baseline

Version: 1.0
Date: 2026-04-07
Status: Approved Baseline for WBS 2.10
Source Documents:
- `docs/01-planning/WBS.md`
- `docs/archive/01-planning/prototype-backlog.md`
- `docs/00-governance/harness-engineering-baseline.md`
- `docs/03-design/dev-prod-environment-spec.md`
- `docs/03-design/monitoring-error-tracking-baseline.md`
- `docs/00-governance/decision-log.md`

---

## 1. Purpose

This document closes `WBS 2.10 CI/CD baseline`.

Goals:
- define the current minimum pipeline that can run today without locking the repo to a framework too early
- keep local and CI checks aligned by reusing the same PowerShell entrypoints
- make it clear which parts of CD are intentionally deferred because infrastructure and secrets are not provisioned yet

---

## 2. Baseline Decisions

1. GitHub Actions is the current CI baseline.
2. CI should call repository scripts instead of reimplementing validation logic directly in YAML.
3. The baseline must work even when product runtime packages do not exist yet.
4. `lint`, `typecheck`, `test`, and `build` checks remain conditional and are auto-detected from any tracked `package.json`.
5. JavaScript package-script checks are `pnpm-first` to match the approved runtime baseline, with fallback only when a package explicitly signals `npm`.
6. When a tracked JavaScript package exists, CI should provide Node and allow the shared package-check entrypoint to install dependencies if `node_modules` is missing.
6. Deployment automation is not enabled in this baseline because real hosts, secrets, and promotion rules are still external prerequisites.

---

## 3. Current Pipeline Shape

The current baseline workflow is `.github/workflows/harness.yml`.

It runs these stages:

| Stage | Script | Purpose |
|---|---|---|
| repo and docs validation | `scripts/harness/repo-doctor.ps1` | required files, Markdown links, PowerShell syntax, JSON syntax |
| foundation contract validation | `scripts/harness/validate-foundation-baseline.ps1` | env examples, observability artifacts, provider rules |
| project checks | `scripts/harness/invoke-project-checks.ps1` | auto-discovered package scripts in `lint`, `typecheck`, `test`, `build` order with pnpm-first package-manager detection and dependency install when needed |
| cleanup audit | `scripts/harness/cleanup-audit.ps1` | report-only hygiene and drift summary artifact |

---

## 4. Local and CI Parity

Local entrypoint:
- `powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1`

CI entrypoint:
- the same foundation checks are executed inside GitHub Actions

Rule:
- if a check matters in CI, it should be runnable locally through repository scripts
- CI should prepare the minimum tool runtime, such as Node plus Corepack for tracked frontend packages, but keep package-script orchestration inside the shared repository entrypoint

---

## 5. What This Baseline Does Not Do Yet

This baseline does not yet include:
- preview or production deployment
- secret injection from a hosted platform
- database migration apply step against a real environment
- object storage provisioning
- release promotion, rollback, or environment approval gates

These are intentionally deferred because WBS `2.x` is still building the foundation contract and no production deployment target has been approved inside the repo.

---

## 6. What Codex Can Do and What The Product Owner Must Do

Codex can:
- maintain the CI scripts and workflow
- add future package-level checks as runtime code appears
- keep the pipeline and docs aligned

The Product Owner or infrastructure owner must:
- choose the real deployment platform and branch/environment promotion policy
- provision GitHub Actions secrets or an equivalent secret source
- approve deployment targets, domains, and environment ownership

---

## 7. Follow-On Work Unlocked

This baseline supports:
- `2.8` security baseline checks
- `2.9` route skeleton work with future package scripts
- `3.x` prototype pipeline implementation with repeatable CI validation
- later deployment automation after runtime and infra decisions are concrete

---

## 8. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| `2.10` | Sections 2-7 |

---

## 9. Change History

| Date | Change |
|---|---|
| 2026-04-07 | Initial foundation CI/CD baseline created for WBS 2.10 |
| 2026-04-11 | Clarified that future JavaScript project checks are pnpm-first so WBS 4 package bootstrap aligns with the approved runtime baseline |
| 2026-04-13 | Clarified that CI should prepare Node plus Corepack and allow the shared project-check entrypoint to install missing frontend dependencies |
