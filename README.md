# FPDS Workspace

## Owned deposit tables and Oaken publication - 2026-10-07

Parser v14/process `2026-10-07-owned-deposit-table-v5` preserve named deposit
rate rows, complete sibling term/interest-payment tables and observed product
links. Explicit percent/annual units, literal term boundaries and actual
companion document/snapshot origins are required. Unconditional account-wide
fee declarations stay separate from registered-account restrictions; later
qualifications/linked notes, partial grids and unresolved cashability exclude.
Acquisition diagnoses the same complete named variants as normalization.
Verified same-record optional facts survive; financial/security essentials and
research budgets remain unchanged. Four directly collected Oaken products are
verified on Public; serving still reports v4, so future Admin use needs the
API/Worker release. No deployment/restart occurred in this operation.
[Diagnosis, corrections, publication and verification limits](docs/00-governance/oaken-generic-collection-corrections-2026-10-07.md).

## Actual Admin named-companion correction - 2026-10-06

Ordinary captured PDFs without a discovery parent bind through exact named
native financial declarations, retaining actual current origins and existing
financial/security gates. Process: `2026-10-06-named-companion-binding-v4`;
parser v13. The latest National live batch published/updated one product;
six priorities pass the corrected same-input/read-only-origin replay. Serving
rollout and live acceptance remain separate from this corrective code result.
[Actual failure and verification](docs/00-governance/admin-collection-parity-implementation-2026-10-06.md#actual-national-run-companion-binding-correction---2026-10-06).

## Native information records and Manulife publication - 2026-10-06

Parser v12 preserves named card information boxes, embedded mortgage APR term
subgroups and owned credit-limit annual notes. Semantic navigation does not
become product currency evidence. Current-rate leads stay within existing
research/link caps; unnamed companion fees do not overwrite owned prices.
Same-capture registered optional facts and explicit typed security survive
normalization and unchanged origin/financial essentials. Complete native
conditions are checked at the final gate. Process version:
`2026-10-06-native-information-proof-v2`.
[Diagnosis, verified publication and deployment limits](docs/00-governance/manulife-generic-collection-corrections-2026-10-06.md).

## Native financial record correction - 2026-10-05

Literal CMS sibling paths require an observed root DOM convention; unavailable
HTTP-200 documents are excluded at discovery, capture and retained parse.
Parser v11 preserves explicit percent headers, native term rows and complete
uniquely linked legal notes. Exact annual term tables retain typed values through
normalization without invented days or shortened conditions. Qualified mortgage
rows keep their own terms; conflicting rows cannot supply comparison facts.
GIC cashability requires complete access proof. These are generic evidence
representations, with unchanged essentials and no manual product review.
Process version: `2026-10-05-native-rate-proof-v2`.
[Diagnosis, regressions and publication](docs/00-governance/laurentian-generic-collection-corrections-2026-10-05.md).

## Essential evidence research - 2026-10-05

Ordinary Admin collection now diagnoses missing required proof after initial
capture/parse, follows observed official product/companion links for at most two
waves, then runs final extraction, normalization, validation and promotion.
Additional evidence is capped at two URLs per detail and 48 per Run; planning
uses at most eight constrained model calls per Run. Optional gaps never trigger
research. Companions remain evidence-only and all financial/security gates apply.
`/healthz` and private Run receipts report `collection_process_version` so a
source change can be distinguished from the serving collection process.
[Root cause, verification and release limits](docs/00-governance/ordinary-collection-redesign-2026-10-05.md).
This implementation requires coordinated API/runner and Worker rollout; isolated
rehearsal is neither deployment nor a canonical/Public publication result.

FPDS (Finance Product Data Service) collects official financial-product evidence
and serves authenticated Admin operations and anonymous Public projections.
This repository contains both applications; the current handover covers Admin
and its API, worker, database and private-storage dependencies.

## Admin handover

Start with the [handover guide](descent/README.md), then use these documents:

| Need | Document |
|---|---|
| Developer workflow and portable AI skills (Korean draft) | [Admin developer guide](descent/FPDS_Admin_개발_가이드.md) · [AI skills](descent/ai-skills/README.md) |
| Included source, exclusions and document ownership | [Scope and source inventory](00-Scope/scope.md) |
| Current operator instructions | [Admin user manual](descent/FPDS_Admin_사용자_매뉴얼.md) |
| Daily checks and incident handling | [Operations handbook](descent/05-operations-handbook.md) |
| Environment, rehearsal, UAT and cutover sequence | [Minimum handover playbook](docs/01-planning/fpds-admin-handover-minimum-playbook.md) |
| External services and ownership template | [Services and accounts](00-Scope/external-services-and-accounts.md) |
| Migration catalogue, schema and ERD | [Database inventory](00-Scope/database-migrations-schema-erd.md) |
| Recorded readiness issues and owner actions | [Pre-handover technical review](descent/02-release-readiness.md) |

Document cleanup is not release approval. Client ownership, clean-clone
verification, restore rehearsal, UAT and Production GO remain separate gates.
Use an isolated clone for builds, installs and release verification while the
current workspace is collecting products.

## Current collection behavior

Daily Admin work is **Overview → Runs → Banks**. Review is read-only history
under **More tools**, alongside Sources, Product Types, Changes, Countries and
Public Health. Runs supports safe 15-second Auto refresh and Search;
Advanced filters start collapsed. Banks uses Search and shows current eligible
published-product counts beside generated sources. Product Type details manage
country-owned required/optional collection targets while protecting mandatory
financial requirements.

Collection accepts only current, product-scoped, officially evidenced facts
through automatic validation, or excludes incomplete candidates. It creates no
human product-review queue. Verified optional facts are retained when the same
evidence proves them; unknown optional facts are omitted. Account/signup
approval, authentication, RBAC, CSRF and private-evidence controls remain active.

The [collection accuracy policy](docs/03-design/collection-accuracy-policy.md)
and [financial field contract](docs/03-design/financial-product-field-contract.md)
govern exact currency, rates, terms and conditional transaction/access/security
essentials. Public uses approved projections and never exposes raw evidence.

The [development journal](docs/00-governance/development-journal.md) records
dated implementation and data outcomes. The latest CIBC operation is
[2026-10-03 collection redesign and publication](docs/00-governance/cibc-collection-redesign-2026-10-03.md):
fourteen additional automatic publications, fifteen CIBC Public products and
CA 50 / US 5 at verification. The earlier [BMO data result](docs/00-governance/bmo-direct-publication-2026-10-03.md)
is retained. These counts are dated outcomes, not a live catalogue status.
Local code, deployed runtime and published data must be checked separately.

## Runtime and source map

| Path | Role | Start here |
|---|---|---|
| `app/admin/` | Authenticated Next.js UI and same-origin API proxies | [Admin README](app/admin/README.md) |
| `api/service/` | FastAPI, sessions, permissions and domain services | [API README](api/service/README.md) |
| `worker/` | Discovery, capture, parsing, extraction, normalization and validation | [Worker README](worker/README.md) |
| `db/` | Ordered SQL migrations and database operations | [DB README](db/README.md) |
| `storage/` | Private object-storage layout and access contract | [Storage README](storage/README.md) |
| `shared/` | Shared contracts, financial rules, config, design and localization | [Shared README](shared/README.md) |
| `app/public/` | Separate anonymous Public application | [Public README](app/public/README.md) |
| `scripts/harness/` | Repository checks | [Harness baseline](docs/00-governance/harness-engineering-baseline.md) |
| `scripts/maintenance/` | Explicit maintenance and historical data-operation tools | Read the corresponding dated journal/report before use |
| `descent/`, `00-Scope/` | Handover instructions, inventory and owner records | [Handover guide](descent/README.md) |
| `docs/` | Requirements, planning, design and governance | [Docs map](docs/README.md) |

Python uses `uv`; frontends use TypeScript, Next.js App Router and `pnpm`.
Admin sessions are owned by the Python API. Admin and Public page/code maps are
[Admin routes](app/admin/routes.manifest.json) and
[Public routes](app/public/routes.manifest.json).
Public-only deployment adapters (`app.py`, `vercel.json`) are not the
long-running Admin collection host.

Generated caches, local environments, logs, private evidence and one-off
`tmp/` tools are not handover source. Their local copies are retained for
active collection and historical diagnosis. See the
[source inventory](00-Scope/scope.md) before preparing a transfer.

## Development and verification

Read this file, the [development journal](docs/00-governance/development-journal.md),
then the [docs map](docs/README.md). Follow the map to the relevant boundary README.
Copy placeholder environment examples into local, untracked settings only in
the intended environment. Real credentials remain outside Git.

The boundary READMEs contain startup commands. Admin release verification in
an isolated clone uses:

```powershell
pnpm --dir app/admin run typecheck
pnpm --dir app/admin run test
pnpm --dir app/admin run build
uv run --directory api/service python -m unittest discover -s tests -p "test_*.py"
uv run python -m unittest discover -s worker -p "test_*.py"
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/invoke-foundation-checks.ps1
git diff --check
```

The foundation entrypoint includes package checks and can install missing
dependencies and build apps. For documentation cleanup in a collecting workspace,
use the narrower checks:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/repo-doctor.ps1
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/validate-foundation-baseline.ps1
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/harness/cleanup-audit.ps1
git diff --check
```

Cleanup audit reports findings; it does not delete files. The Git pre-commit hook
checks staged text, Markdown references and PowerShell syntax. Install it with
`scripts/harness/install-hooks.ps1` in the intended development clone.

## Scope and retained history

The [requirements](docs/02-requirements/FPDS_Requirements_Definition_v1_5.md),
[scope baseline](docs/02-requirements/scope-baseline.md),
[plan](docs/01-planning/plan.md) and [WBS](docs/01-planning/WBS.md) govern approved
delivery. The [decision log](docs/00-governance/decision-log.md) and
[RAID log](docs/00-governance/raid-log.md) preserve decisions and unresolved risks.
This cleanup adds no country/type, consumer banking, personalized recommendation,
public evidence access, billing, BX-PF write-back or recurring collection.

Historical gate/prototype records stay in the [archive](docs/archive/README.md).
The [pre-cleanup README snapshot](docs/archive/00-governance/workspace-readme-before-handover-cleanup-2026-10-03.md)
preserves earlier implementation summaries and dated outcomes; it is not current
operator guidance. Existing `goal.md` remains while earlier independently owned
acceptance items are unresolved.
