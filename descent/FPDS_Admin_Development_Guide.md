# FPDS Admin Development Guide

2026-10-07 · Audience: Developers responsible for country-specific localization and feature additions and fixes

Use this file to learn how to start development, where to make common changes, and how to use AI skills.

## 1. Understanding the Project

FPDS Admin is a tool for managing the results of collecting and automatically validating official financial product information. Its features include collection countries, Banks, Runs, and Review.

| Location | Responsibility |
|---|---|
| app/admin | Next.js/TypeScript screens, user input, and calls to the Python API |
| api/service | FastAPI authentication, permissions, country-specific data, business APIs, and collection run coordination |
| worker | Official source discovery, HTML/PDF retrieval and parsing, and financial information extraction, normalization, and validation |
| db/migrations | PostgreSQL schema change history |
| shared | Contracts for language, design, security, and shared configuration |
| storage | Private source storage contract |
| app/public | Separate Public app; modify only when the change also affects public results |

The flow is **Admin → API → Worker/DB → approved Public projection**. The browser does not access the DB or source storage directly. See the [Admin route list](../app/admin/routes.manifest.json) for actual screen paths and the [User Manual](FPDS_Admin_사용자_매뉴얼.md) for operating instructions.

## 2. Running the Project for the First Time

Prepare a separate development clone. You need Node 24, pnpm (as specified in package.json), Python 3.12 or later, uv, and a development PostgreSQL instance. Actual collection tests also require private storage and the necessary provider credentials.

Run the following from the repository root.

```powershell
uv sync --frozen
uv sync --directory api/service --frozen
pnpm --dir app/admin install --frozen-lockfile
```

The API and Worker have independent Python environments. Set up both projects and run API tests in the api/service environment.

Copy .env.dev.example to a local .env.dev and app/admin/.env.example to app/admin/.env.local. Do not overwrite existing files. Replace the example placeholders with development environment values. Do not commit DB URLs, session/CSRF secrets, or storage/provider keys to Git.

Follow the [DB README](../db/README.md) for new database prerequisites, the full migration application order, and setup verification. Use the bootstrap procedure in the [API README](../api/service/README.md) for the first account. Run migrations and account creation against the intended development DB.

Start the servers in two separate terminals.

```powershell
# Terminal 1: repository root
$env:FPDS_ENV_FILE = '.env.dev'
uv run --directory api/service uvicorn api_service.main:app --reload --host localhost --port 4000
```

```powershell
# Terminal 2: repository root
pnpm --dir app/admin run dev
```

API health check: http://localhost:4000/healthz · Admin: http://localhost:3001/admin/login

Verify the development environment indicator, country selection, and login/logout. Do not install dependencies, build, or restart services in an existing workspace while collection is running.

## 3. Country-Specific Localization

First, define the target country, UI language, product types, currency, and official financial institution sources. For example, using a Japanese UI and collecting Japanese financial products are separate concerns. The current UI languages are EN/KO/JA.

| Change | Main locations | What to verify |
|---|---|---|
| UI language, menus, and error messages | [admin-i18n.ts](../app/admin/src/lib/admin-i18n.ts), app/admin/src/components, [shared locale configuration](../shared/i18n/locale-config.json) | Check locale types, selectors, fallback, propagation through URLs, and text within components together. Adding JSON translations alone is not enough |
| Date, number, and currency formatting | admin-i18n.ts and the relevant UI formatter | Distinguish the display language from the actual product currency. Formatting changes must not change financial values or units |
| Collection country | [countries.py](../api/service/api_service/countries.py), [country catalog](../api/service/api_service/country_catalog.py), country_registry | Country activation, login/switching, and blocking access to IDs from other countries. Activating a country alone does not make it ready for collection |
| Local product names and search terms | [product_type_localization.py](../api/service/api_service/product_type_localization.py), Product Type/bank coverage configuration | Map local names and official site languages to the actual product types. Renaming must not cause products with different financial meanings to be treated as the same type |
| Required financial information and currency | [market profile](../worker/pipeline/fpds_market_profile.py), [country defaults](../worker/country_defaults.py), [field contract](../worker/pipeline/fpds_field_contract.py) | Explicit contracts and official evidence for the new country. Do not infer rules by copying another country's rate, term, or currency rules |
| Official sources and collection | API bank/source catalog, worker/discovery | Official domains, source language, product identity and evidence, and SSRF protection |

When adding support for a new country, proceed in this order: **market/product contracts → language and display → sources/collection → API and screens → regression verification**. If the request is only for UI translation, do not also change market configuration. Korean/Japanese language support does not mean that the corresponding country's financial rules are implemented.

Preserve product names, original bank text, and rate conditions in the source language. Translate only UI labels. Set defaults for a new country explicitly after verifying that market's requirements and evidence.

## 4. Adding and Modifying Features

| Task | Starting point |
|---|---|
| Screens, forms, lists, and dialogs | app/admin/src/app/admin, app/admin/src/components/fpds/admin |
| Styles and base components | app/admin/src/app/globals.css, app/admin/src/components/ui |
| UI-to-API integration | app/admin/src/lib/admin-api.ts, the relevant route.ts proxy |
| Business APIs | api/service/api_service/main.py and feature-specific service files |
| DB fields | A new migration in db/migrations and the related API/Worker persistence |
| Collection errors or omissions | api/service/api_service/source_collection_runner.py and the relevant Worker pipeline service/persistence |

Verify feature changes as one flow: screen → API → storage/processing → tests. A UI-only display change does not require a DB change. Reuse existing components and semantic tokens, and consult the [current UI standards](../docs/03-design/fpds_design_system_stripe_benchmark.md) when changing the design.

Core contracts to preserve:

- The API session determines the country. Do not expand country access through browser query parameters or request bodies. The server validates roles and CSRF for operational data mutations.
- Approve only financial facts backed by official evidence. Automatically exclude products with insufficient required information, and do not create a manual product approval queue.
- Read the [Collection Accuracy Policy](../docs/03-design/collection-accuracy-policy.md) and [Financial Field Contract](../docs/03-design/financial-product-field-contract.md) when making changes.
- Preserve existing migrations, source fixtures/hashes, and product version/change history. For DB or security changes, consult the [Retention Policy](../docs/03-design/bounded-data-retention-policy.md) and [Security Contract](../docs/03-design/security-access-control-design.md).

## 5. AI Skills for Future Work

Skills are instructions that guide the AI to the appropriate change locations and verification criteria for each task.

| Skill file | Purpose | Input to give the AI | Expected output |
|---|---|---|---|
| [fpds-localize-market](ai-skills/fpds-localize-market/SKILL.md) | Language/display localization and support for new country/product markets | Country, locale, product types, official sources, and change scope | Modified code/configuration, market-specific evidence/contracts, and regression results for existing countries and languages |
| [fpds-change-feature](ai-skills/fpds-change-feature/SKILL.md) | Feature additions and changes across screens, APIs, and the DB | User flow, expected outcome, reproduction examples, and permitted data changes | Minimal implementation, an application plan for any related migrations, and success/failure tests |
| [fpds-fix-collection](ai-skills/fpds-fix-collection/SKILL.md) | Correcting collection failures, omissions, and incorrect financial values for local banks | Bank/country/type/Run, preserved evidence, and expected facts | Reproduction of the first defect, a shared-path fix, regressions using official evidence, and actual approval/exclusion results |
| [fpds-verify-change](ai-skills/fpds-verify-change/SKILL.md) | Change verification and deployment preparation | Diff, acceptance criteria, target environment, and existing check results | Tests appropriate to the impact, unresolved items, application/recovery order, and actual execution results |

The simplest way to use a skill is to ask the AI to read its file. Resolve file paths relative to the FPDS clone root.

```text
Read descent/FPDS_Admin_Development_Guide.md and
descent/ai-skills/fpds-localize-market/SKILL.md before starting the work.
Target: [country / UI language / product types]
Request: [language/display changes or collection support for the market]
Acceptance criteria: [user flow and expected results to verify]
Environment and permitted operations: [development clone, fixtures, or explicitly specified dev DB operations]
Run the relevant regressions and summarize the changed files, results, and remaining items.
```

Use the same format with fpds-change-feature for feature changes or fpds-fix-collection for collection errors. Apply fpds-verify-change for the final verification.

To register skills with Codex, copy each required skill folder in full into .agents/skills in the recipient's clone or .agents/skills in the user's home directory, then verify that it is recognized. Once registered, you can invoke a skill with a name such as `$fpds-localize-market`. [Official skill location guide](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)
