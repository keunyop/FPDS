# FPDS CI Baseline

Updated: 2026-10-07. The MVP runtime exists; this document describes the current
repository workflow.

The [GitHub Actions workflow](../../.github/workflows/harness.yml) runs on push,
pull request and manual dispatch. It uses Ubuntu, Node 24 and PowerShell to call
scripts/harness/invoke-foundation-checks.ps1, then produces and uploads a cleanup
audit report.

| Stage | Repository script |
|---|---|
| Required paths, Markdown references, PowerShell/JSON syntax | scripts/harness/repo-doctor.ps1 |
| Env and observability contract checks | scripts/harness/validate-foundation-baseline.ps1 |
| Available package lint/typecheck/test/build scripts | scripts/harness/invoke-project-checks.ps1 |
| Report-only cleanup audit | scripts/harness/cleanup-audit.ps1 |

JavaScript checks use the package's declared manager with pnpm-first detection;
missing dependencies may be installed. The foundation command uses the first
three scripts locally and in CI. See [validation instructions](harness-engineering-baseline.md).

API/Worker Python behavior tests must be run separately using their README
commands. Do not infer complete runtime verification from the foundation result.

This workflow does not deploy Admin/API/Worker, apply production migrations,
provision storage, rotate secrets or prove restore/UAT. Those actions use the
recipient's target environment and authorized operational procedures in the
[handover guide](../../descent/README.md). A green CI result is evidence for
release review, not proof of deployment or published financial data.
