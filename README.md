# FPDS Workspace

This repository is currently a docs-first FPDS workspace. The main project map lives in [docs/README.md](docs/README.md).

Current status:
- Gate A is `Pass`.
- Product implementation is still on hold until the Product Owner explicitly starts development.
- Harness engineering is installed so we can begin WBS 2 and WBS 3 on cleaner rails when you say go.

## Start Here

- Project docs map: [docs/README.md](docs/README.md)
- Working agreement: [docs/00-governance/working-agreement.md](docs/00-governance/working-agreement.md)
- WBS: [docs/01-planning/WBS.md](docs/01-planning/WBS.md)
- Harness baseline: [docs/00-governance/harness-engineering-baseline.md](docs/00-governance/harness-engineering-baseline.md)
- Development journal: [docs/00-governance/development-journal.md](docs/00-governance/development-journal.md)

## Harness Commands

Install Git hooks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/install-hooks.ps1
```

Run repository health checks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1
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

- `pre-commit` only inspects staged files.
- The hook auto-fixes low-risk text hygiene issues such as trailing spaces and missing final newline.
- The hook validates staged Markdown references and staged PowerShell syntax.
- Success stays quiet. Failures stop the commit with a clear message.
- Cleanup audit is `report-only` by design.
- CI runs repository-wide checks without starting product implementation.
- Completed implementation slices should be summarized in the development journal for future resume.

## Current Top-Level Layout

- `docs/` project requirements, governance, planning, and design
- `scripts/harness/` hook, audit, and verification scripts
- `.githooks/` Git hook entrypoints
- `.github/workflows/` CI for the harness
