# FPDS Repository Validation

Updated: 2026-10-07. Use this reference for harness, CI and validation changes.
Normal feature work starts with the
[development guide](../../descent/FPDS_Admin_개발_가이드.md) and affected package README.

## Choose The Relevant Check

| Check | Command or entrypoint |
|---|---|
| Required files, Markdown references, PowerShell/JSON syntax | scripts/harness/repo-doctor.ps1 |
| Env example and observability contracts | scripts/harness/validate-foundation-baseline.ps1 |
| Detected package lint/typecheck/test/build scripts | scripts/harness/invoke-project-checks.ps1 |
| All three above | scripts/harness/invoke-foundation-checks.ps1 |
| Report-only hygiene/links/TODO audit | scripts/harness/cleanup-audit.ps1 |

Example from the repository root:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/validate-foundation-baseline.ps1
git diff --check
```

Run affected runtime behavior tests from the package README as well. Package
script detection does not replace the explicit API and Worker Python tests.
Documentation-only changes do not require application builds.

Full foundation/project checks may install missing JavaScript dependencies and
run builds. Use an isolated clone when another workspace is serving or collecting.
Repo doctor scans local text files, including some untracked temporary material;
report such findings separately and verify the tracked delivery set. Do not
remove operational evidence merely to make a workspace scan pass.

## Shared Rules

- Keep local and CI logic in repository scripts; see the
  [CI baseline](foundation-ci-cd-baseline.md).
- The pre-commit hook validates staged files only and may fix trailing whitespace
  and final newlines. It also checks Markdown references and PowerShell syntax.
- Cleanup audit is report-only. Deletion requires the task's scope and a consumer
  check; it must preserve source fixtures, migrations, private evidence and
  unrelated work.
- Mandatory harness paths are defined by scripts/harness/shared.ps1.
- Keep a concise [journal entry](development-journal.md) for meaningful completed
  work with actual results and known limits. Historical MVP gate documents are
  no longer startup prerequisites.
