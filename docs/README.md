# FPDS Docs Map

Current RBC correction: [direct collection, reusable price/rate proof and publication verification](00-governance/rbc-generic-collection-corrections-2026-10-07.md).

Current deposit-proof correction: [Oaken generic tables, actual-input regressions and four verified publications](00-governance/oaken-generic-collection-corrections-2026-10-07.md).

Current collection implementation: [Admin evidence parity and release gates](00-governance/admin-collection-parity-implementation-2026-10-06.md).

Status: Active navigation index · Updated: 2026-10-07

Use this map to find the current contract or operating document. Dated reports
record historical results; product counts and test totals are not live status.
Archived documents retain traceability and do not override current policy.

## Start an Admin handover

| Read in order | Purpose |
|---|---|
| [Handover guide](../descent/README.md) | Steps, owner responsibilities and acceptance gates |
| [Admin developer guide (Korean draft)](../descent/FPDS_Admin_개발_가이드.md) · [AI skills](../descent/ai-skills/README.md) | Local setup, code entrypoints, implementation workflows and portable SKILL.md package |
| [Scope and source inventory](../00-Scope/scope.md) | Included source, transfer exclusions and document ownership |
| [Admin user manual](../descent/FPDS_Admin_사용자_매뉴얼.md) | Current operator workflow |
| [Operations handbook](../descent/05-operations-handbook.md) | Daily checks, incidents and security/restore boundaries |
| [Minimum playbook](01-planning/fpds-admin-handover-minimum-playbook.md) | Environment rehearsal, training, UAT and cutover |
| [Services and accounts](../00-Scope/external-services-and-accounts.md) | External dependencies and ownership template |
| [Database inventory](../00-Scope/database-migrations-schema-erd.md) | Migration catalogue, schema and ERD |
| [Technical review](../descent/02-release-readiness.md) | Dated verification and remaining owner actions |

Review is historical and read-only. Current collection uses automatic acceptance
or exclusion; account/signup approval remains separate. Read the
[collection accuracy policy](03-design/collection-accuracy-policy.md) before
collection work.

Latest requested collection plan: [ordinary Admin acquisition, financial proof and actual Public acceptance](01-planning/admin-collection-publication-parity-plan-2026-10-06.md). Planning only; implementation and live acceptance remain subsequent slices.

Latest read-only collection assessment: [National Bank direct evidence opportunities and remaining gates](00-governance/development-journal.md#2026-10-06---national-bank-direct-evidence-feasibility-without-admin-api); no new approvals or publications. Previous assessment: [Laurentian](00-governance/laurentian-direct-evidence-assessment-2026-10-05.md).

Latest ordinary-process verification: [essential-evidence research redesign and runtime limits](00-governance/ordinary-collection-redesign-2026-10-05.md). This local result is distinct from direct data publication.

Latest collection result: [RBC reusable price/rate/identity corrections and fifteen verified publications](00-governance/rbc-generic-collection-corrections-2026-10-07.md). Previous result: [Oaken generic deposit-proof corrections and four verified publications](00-governance/oaken-generic-collection-corrections-2026-10-07.md). Previous result: [Manulife generic information-record corrections and five verified publications](00-governance/manulife-generic-collection-corrections-2026-10-06.md). Previous result: [Laurentian generic native-proof corrections and three verified publications](00-governance/laurentian-generic-collection-corrections-2026-10-05.md). Previous result: [FAIRSTONE / FNBC / HAVENTREE shared corrections and direct publication](00-governance/three-bank-generic-collection-corrections-2026-10-05.md). Previous result: [DESJARDINS / EQBANK](00-governance/desjardins-eqbank-collection-corrections-2026-10-04.md).

## Resume development

Read [root README](../README.md), [development journal](00-governance/development-journal.md),
then this map. Select only the documents needed for the slice:

| Task affects | Read next |
|---|---|
| Product behavior, scope or acceptance | [Requirements](02-requirements/FPDS_Requirements_Definition_v1_5.md), [scope baseline](02-requirements/scope-baseline.md) |
| Delivery selection or sequencing | [Plan](01-planning/plan.md), [WBS](01-planning/WBS.md) |
| Architecture or a settled baseline | [Decision log](00-governance/decision-log.md) and relevant design docs |
| Risk, issue or dependency | [RAID log](00-governance/raid-log.md) |
| Runtime boundary | [Admin](../app/admin/README.md), [API](../api/service/README.md), [Worker](../worker/README.md), [DB](../db/README.md), [Storage](../storage/README.md), or [Public](../app/public/README.md) README |
| UI or visual behavior | [Design index](03-design/README.md), both frontend baselines and relevant surface/locale docs |
| Harness, CI or repository checks | [Harness baseline](00-governance/harness-engineering-baseline.md) |

## Current contracts and planning

- [Working agreement](00-governance/working-agreement.md): collaboration and authority.
- [Scope change control](00-governance/scope-change-control.md) and
  [stage gates](00-governance/stage-gate-checklist.md): approval boundaries.
- [Roadmap](00-governance/roadmap.md) and
  [milestone tracker](00-governance/milestone-tracker.md): broader delivery context.
- [Phase 1 QA checklist](00-governance/phase-1-no-bxpf-test-checklist.md):
  bounded operational verification.
- [Canada Big 5 source registry](01-planning/canada-big5-source-registry.md):
  original source baseline; live registry state is database-owned.
- [Demo scenario](01-planning/fpds-customer-demo-scenario.md):
  supporting presentation material; verify older workflow copy against current policy.

Start technical design from the [design index](03-design/README.md). Common contracts:

- [Collection accuracy](03-design/collection-accuracy-policy.md) and
  [financial field contract](03-design/financial-product-field-contract.md).
- [Canonical domain/schema](03-design/domain-model-canonical-schema.md),
  [ingestion states](03-design/workflow-state-ingestion-design.md),
  [review/run/publish history](03-design/review-run-publish-audit-state-design.md).
- [API contracts](03-design/api-interface-contracts.md) and
  [security/access control](03-design/security-access-control-design.md).
- [Environment specification](03-design/dev-prod-environment-spec.md),
  [migration baseline](03-design/db-migration-baseline.md),
  [private storage](03-design/object-storage-evidence-bucket-baseline.md),
  [bounded retention](03-design/bounded-data-retention-policy.md).
- [Source registry policy](03-design/source-registry-refresh-and-approval-policy.md).
- [FPDS design system](03-design/fpds-design-system.md),
  [frontend benchmark](03-design/fpds_design_system_stripe_benchmark.md),
  [Admin IA](03-design/admin-information-architecture.md),
  [localization](03-design/localization-governance-and-fallback-policy.md).
- [Admin purpose and features](03-design/fpds-admin-purpose-and-features.md):
  detailed Korean overview; historical reviewer actions are superseded by the
  current accuracy policy.
- [CI baseline](00-governance/foundation-ci-cd-baseline.md) and
  [source domain allowlist](00-governance/codex-internet-domain-allowlist.md).

Source-backed test fixtures remain under `worker/pipeline/tests/fixtures/`;
they are part of reproducible verification, not disposable build output.

## Implementation and operation records

Use the [development journal](00-governance/development-journal.md) for the dated
sequence and the linked report for exact evidence and limitations. Recent examples:

| Record | What it proves |
|---|---|
| [Coast Capital evidence corrections, 2026-10-03](00-governance/coast-collection-evidence-corrections-2026-10-03.md) | Three local automatic passes and shared discovery/terms fixes; no deployment or data publication |
| [CIBC collection redesign, 2026-10-03](00-governance/cibc-collection-redesign-2026-10-03.md) | Shared evidence parity and fourteen applied automatic publications; rollout separate |
| [BMO direct publication, 2026-10-03](00-governance/bmo-direct-publication-2026-10-03.md) | Applied data result and exclusions; no runtime deployment |
| [BMO direct comparison, 2026-10-03](00-governance/bmo-chequing-direct-comparison-2026-10-03.md) | Official comparison and saved-input correction |
| [Generic root cause, 2026-10-03](00-governance/bmo-generic-collection-root-cause-2026-10-03.md) | Shared collection correction and verification |
| [Evidence improvements, 2026-10-02](00-governance/generic-collection-evidence-improvements-2026-10-02.md) | Generic source selection and captured evidence |
| [Optional checking rates, 2026-10-02](00-governance/optional-checking-rates-2026-10-02.md) | Typed optional evidence and omissions |
| [Legacy accuracy assessment, 2026-09-30](00-governance/collection-accuracy-audit-2026-09-30.md) | Approved 355-product/470-review cutover history |

Other dated reports remain in `00-governance/`; they are not deleted or
automatically restored to Public. Local implementation, deployment and data
publication are separate facts.

## Historical and private material

[Archive index](archive/README.md) routes closed gates, prototype evidence and
the [pre-cleanup docs map](archive/00-governance/docs-map-before-handover-cleanup-2026-10-03.md).
Open these only to verify a historical result or reference.

Active contracts and source-backed regression fixtures stay in their current
paths. Private client evidence belongs in the restricted handover store described
by [scope](../00-Scope/scope.md); credentials, raw operational evidence and local
collection files do not belong in the source transfer.
