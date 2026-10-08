# FPDS Workspace

FPDS collects official financial-product information, validates it automatically,
and serves authenticated Admin operations and approved Public projections.
The MVP is complete. Further development focuses on the recipient's countries,
languages and requested features.

Start with the **[Admin development guide](descent/FPDS_Admin_개발_가이드.md)**.
It contains setup, localization, feature changes, verification and the four AI
skills in one Korean document. Read the affected package README and specific
contracts only when needed.

## Source map

| Boundary | Role and instructions |
|---|---|
| Admin | [app/admin](app/admin/README.md): Next.js UI and API proxies |
| API | [api/service](api/service/README.md): FastAPI, sessions, country scope and services |
| Worker | [worker](worker/README.md): discovery, capture, extraction and validation |
| Database | [db](db/README.md): ordered SQL migrations and operations |
| Private storage | [storage](storage/README.md): evidence access and object layout |
| Shared | [shared](shared/README.md): contracts, security, design and localization |
| Public | [app/public](app/public/README.md): separate anonymous application |

Use an isolated development clone for installs, builds and release verification
while an existing workspace is collecting products. API and Worker use separate
Python environments. Exact setup and test commands are in the development guide.

## References when needed

- [Operator manual](descent/FPDS_Admin_사용자_매뉴얼.md) and
  [operations handbook](descent/05-operations-handbook.md): everyday work and incidents.
- [Operational handover](descent/README.md): account ownership, environment transfer,
  restore, UAT and cutover. MVP completion does not certify these external actions.
- [Source inventory](00-Scope/scope.md),
  [services/accounts](00-Scope/external-services-and-accounts.md) and
  [database inventory](00-Scope/database-migrations-schema-erd.md).
- [Technical contracts](docs/README.md) and
  [repository checks](docs/00-governance/harness-engineering-baseline.md).
- [Development journal](docs/00-governance/development-journal.md): investigate
  relevant changes or deployment/data results; reading the entire history is
  unnecessary.

## Data and access rules

Collection automatically accepts evidenced facts or excludes incomplete
candidates. Review is read-only history. Keep account/security approvals,
authentication, authorization, CSRF and country isolation intact.

Preserve exact currency, rates, terms and conditions under the
[accuracy policy](docs/03-design/collection-accuracy-policy.md) and
[field contract](docs/03-design/financial-product-field-contract.md). Verified
optional facts survive; unknown facts stay absent. Public never exposes raw
evidence, private storage access or secrets.

Source, tests, fixtures, migrations, lockfiles and environment examples are
handover inputs. Local environments, generated output, secrets and private
collection evidence are excluded from source delivery. Operational recovery
records remain available; obsolete MVP plans, gate documents and duplicate
manuals can be retrieved from Git history.
