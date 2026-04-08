# FPDS Workspace

This repository is currently a docs-first FPDS workspace. The main project map lives in [docs/README.md](docs/README.md).

Current status:
- Gate A is `Pass`.
- Product Owner-directed implementation is active for Foundation work in WBS `2`.
- Harness engineering is installed and foundation scaffolds are now active for WBS `2` and upcoming WBS `3`.
- WBS `2.2` env templates are now tracked as placeholder-only docs and example files.
- WBS `2.5` auth scaffold is now tracked as a vendor-neutral session and RBAC baseline.
- WBS `2.6` i18n scaffold now includes EN/KO/JA resource files, locale config, and glossary seed data.
- WBS `2.7` observability baseline is documented with safe error and structured event examples.
- WBS `2.8` security baseline now includes browser-policy, safe-fetch, and secret-inventory scaffold files.
- WBS `2.9` public and admin route skeletons now exist as route manifests plus shell placeholders.
- WBS `2.10` foundation CI now reuses the same local PowerShell checks in GitHub Actions.

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

Run the full foundation baseline checks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1
```

Run the report-only cleanup audit:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1
```

Optional future project-wide checks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-project-checks.ps1
```

## Environment Templates

- Environment source of truth: [docs/03-design/dev-prod-environment-spec.md](docs/03-design/dev-prod-environment-spec.md)
- Example files: `.env.dev.example`, `.env.prod.example`
- Shared config landing zone: [shared/config/README.md](shared/config/README.md)

Rules:
- Only placeholder values are committed.
- Real secrets and exact production origins stay out of git.
- `dev` is the only local development environment shape for now.
- Real BX-PF credentials and write-back are `prod` only.

## Database Baseline

- DB source of truth: [docs/03-design/db-migration-baseline.md](docs/03-design/db-migration-baseline.md)
- Migration entrypoint: [db/README.md](db/README.md)

Rules:
- Postgres is the baseline database.
- Migrations stay SQL-first until we intentionally choose a framework or ORM.
- Early schema keeps flexible payloads in `jsonb` and defers `pgvector` to later work.

## Object Storage Baseline

- Storage source of truth: [docs/03-design/object-storage-evidence-bucket-baseline.md](docs/03-design/object-storage-evidence-bucket-baseline.md)
- Storage entrypoint: [storage/README.md](storage/README.md)

Rules:
- Object storage is private by default.
- Browser surfaces must not receive raw object paths or direct bucket access.
- `dev` and `prod` storage boundaries stay separated by bucket or top-level prefix.

## Auth and Security Scaffold

- Security entrypoint: [shared/security/README.md](shared/security/README.md)
- Auth session contract: [shared/security/auth-session.contract.json](shared/security/auth-session.contract.json)
- Browser security policy scaffold: [shared/security/browser-security-policy.json](shared/security/browser-security-policy.json)
- Admin API auth routes: [api/admin/auth/README.md](api/admin/auth/README.md)

Rules:
- Admin auth stays `server-session` based.
- No auth vendor is locked in yet.
- CSRF, cookie, CORS, and safe-fetch rules are scaffolded now so later runtime code does not invent its own policy.

## I18n and Route Scaffold

- I18n entrypoint: [shared/i18n/README.md](shared/i18n/README.md)
- Locale config: [shared/i18n/locale-config.json](shared/i18n/locale-config.json)
- Public routes: [app/public/routes.manifest.json](app/public/routes.manifest.json)
- Admin routes: [app/admin/routes.manifest.json](app/admin/routes.manifest.json)

Rules:
- `en` is the default locale and fallback root.
- `ko` and `ja` starter resources are scaffolded but remain draft until reviewed.
- Route shells reserve the public and admin structure without forcing a framework router yet.

## What The Harness Does

- `pre-commit` only inspects staged files.
- The hook auto-fixes low-risk text hygiene issues such as trailing spaces and missing final newline.
- The hook validates staged Markdown references and staged PowerShell syntax.
- Foundation checks validate env examples, observability artifacts, JSON syntax, and future package scripts.
- Success stays quiet. Failures stop the commit with a clear message.
- Cleanup audit is `report-only` by design.
- CI runs repository-wide checks without starting product implementation.
- Completed implementation slices should be summarized in the development journal for future resume.

## Observability Baseline

- Monitoring baseline: [docs/03-design/monitoring-error-tracking-baseline.md](docs/03-design/monitoring-error-tracking-baseline.md)
- Shared observability landing zone: [shared/observability/README.md](shared/observability/README.md)
- `dev` keeps monitoring disabled by default.
- `prod` is aligned to a `sentry` provider label, but the real DSN stays out of git.

## Current Top-Level Layout

- `app/` browser-facing surfaces for public, admin, and prototype viewer
- `api/` public, admin, and internal API boundaries
- `db/` SQL-first migration baseline and database notes
- `storage/` object storage and evidence bucket baseline
- `worker/` private discovery, pipeline, publish, and runtime workers
- `shared/` cross-surface contracts, domain, config, i18n, observability, and security modules
- `docs/` project requirements, governance, planning, and design
- `scripts/harness/` hook, audit, and verification scripts
- `.githooks/` Git hook entrypoints
- `.github/workflows/` CI for the harness
