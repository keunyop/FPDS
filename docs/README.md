# FPDS Docs Map

Status: Active navigation index
Last updated: 2026-09-16

This file is the main entrypoint for `docs/`.

Default rule:
- Read only the active docs first.
- Ignore `docs/archive/` unless you are validating a past decision, gate record, or prototype artifact.

## 1. Resume A Codex Session

Before substantive work, read in this order:
1. `README.md`
2. `docs/00-governance/development-journal.md`
3. this docs map

Then route by task instead of loading every active document:

| Task affects | Read next |
|---|---|
| product behavior, scope, or acceptance | requirements definition and `scope-baseline.md` |
| delivery selection, sequencing, or status | `plan.md` and `WBS.md` |
| architecture or a settled baseline | `decision-log.md` and relevant design docs |
| an active risk, issue, assumption, or dependency | `raid-log.md` |
| a runtime boundary | that boundary's README plus relevant contracts/design docs |
| UI or visual behavior | design docs index, both frontend baselines, relevant surface/locale docs, and the Admin/Public README |
| harness, CI, or repository-wide checks | `harness-engineering-baseline.md` |

This keeps the startup context current without spending context on unrelated
requirements, planning, or design material.

## 2. Active Documents

### 2.1 Governance

- [RBC/BMO recovery assessment](00-governance/collection-accuracy-oneoff-rbc-bmo-2026-09-30.md): 11 exclusions retained, cross-attribute zero validation corrected
- [CIBC/Scotiabank one-off recovery](00-governance/collection-accuracy-oneoff-scotia-2026-09-30.md): 11 products checked, Basic Plus restored, no new model calls
- [One-off Vancity recovery](00-governance/collection-accuracy-oneoff-vancity-2026-09-30.md): exact product currency properties, one automatic restoration, zero model calls
- [One-off TD recovery](00-governance/collection-accuracy-oneoff-td-2026-09-30.md): zero-model evidence reuse, one automatic restoration and unchanged product scope

- [Economical accuracy recovery](00-governance/collection-accuracy-recovery-2026-09-30.md): manifest diagnosis, bounded collection, reuse and actual Public results

- [Live collection accuracy pilot](00-governance/collection-accuracy-pilot-2026-09-30.md): real-source exclusion fixes, automatic product recovery and operational checks

- [Collection accuracy assessment](00-governance/collection-accuracy-audit-2026-09-30.md): new automatic gates, verification and existing-data impact

- [CA/US collection alignment](00-governance/public-collection-alignment-2026-09-29.md): bounded comparison fields, six applied corrections, cost and remaining gaps

- [Official bank link sample](00-governance/public-bank-link-check-2026-09-26.md): initial P1-4 URL checks and operator follow-up

- [Home Top 5 bounded data completion](00-governance/home-top5-data-completion-2026-09-24.md): official-source corrections, condition counts and pending US reviews

- [Public deposit comparison self-review](00-governance/public-deposit-comparison-review-2026-09-24.md): INDEXED GIC/Oaken official-source review and bounded data limitations

- [Public rate correction and self-review](00-governance/public-rate-correction-2026-09-16.md): API/UI rate semantics, published-data audit and separately authorized one-record correction

- `docs/00-governance/working-agreement.md`: collaboration and document authority rules
- `docs/00-governance/development-journal.md`: recent implementation memory and resume context
- `docs/00-governance/decision-log.md`: active decisions and historical decision trail
- `docs/00-governance/raid-log.md`: active risks, assumptions, issues, and dependencies
- `docs/00-governance/scope-change-control.md`: scope change rules
- `docs/00-governance/stage-gate-checklist.md`: gate criteria
- `docs/00-governance/roadmap.md`: broader delivery roadmap
- `docs/00-governance/milestone-tracker.md`: milestone board
- `docs/00-governance/phase-1-no-bxpf-test-checklist.md`: current interim QA checklist
- `docs/00-governance/harness-engineering-baseline.md`: repo validation and harness behavior
- `docs/00-governance/foundation-ci-cd-baseline.md`: CI baseline
- `docs/00-governance/codex-internet-domain-allowlist.md`: allowed external domains for source work

- [Public UI/UX review](00-governance/public-ui-ux-review-2026-09-28.md): confirmed usability fixes and local regression verification

### 2.2 Planning

- `docs/01-planning/plan.md`: execution plan
- `docs/01-planning/WBS.md`: current work breakdown and task status
- `docs/01-planning/fpds-admin-handover-minimum-playbook.md`: follow-in-order
  Admin handover checklist with evidence and stop gates
- `docs/01-planning/canada-big5-source-registry.md`: active source coverage baseline for Phase 1
- `docs/01-planning/fpds-customer-demo-scenario.md`: customer demo scenario for Admin collection through Public results, including AI/usage talking points and ChatGPT image prompts

### 2.3 Requirements

- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`: requirements baseline
- `docs/02-requirements/scope-baseline.md`: scope, non-goals, release cutline, and build-start rule

### 2.4 Design

- [Same-amount calculator](03-design/public-scenario-calculator-policy.md): two-product scenarios, rounding and privacy contract

Start from [docs/03-design/README.md](03-design/README.md).

Most commonly needed:
- [SwitchaBank blog](03-design/public-blog-policy.md): bank comparison article, source checks, SEO and content maintenance
- [Authored comparison guides](03-design/public-comparison-guides-policy.md): newcomer entry, sources/corrections and localized guide discovery
- [Deposit comparison conditions](03-design/public-deposit-comparison-policy.md): matching type/currency/basis/maturity and calculator eligibility
- [Public verification freshness](03-design/public-verification-freshness-policy.md): separate snapshot/product dates, read-only overdue report, manual review cadence
- [FPDS Admin purpose and complete feature guide (Korean)](03-design/fpds-admin-purpose-and-features.md): source-verified workflow, screens, roles, automation, and current versus deferred scope
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/03-design/financial-product-field-contract.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/03-design/review-run-publish-audit-state-design.md`
- `docs/03-design/api-interface-contracts.md`
- `docs/03-design/security-access-control-design.md`
- `docs/03-design/source-registry-refresh-and-approval-policy.md`
- `docs/03-design/dev-prod-environment-spec.md`
- `docs/03-design/db-migration-baseline.md`
- `docs/03-design/object-storage-evidence-bucket-baseline.md`
- `docs/03-design/fpds-design-system.md`
- `docs/03-design/fpds_design_system_stripe_benchmark.md`
- `docs/03-design/admin-information-architecture.md`

### 2.5 Golden Test Fixtures

- `worker/pipeline/tests/fixtures/golden/`: source-backed reference datasets for admin collection and review testing

### 2.6 Client Handoff

- `README.md`: runtime map, startup context, and full verification commands
- `docs/01-planning/fpds-admin-handover-minimum-playbook.md`: primary Admin
  execution entrypoint for the Product Owner and handover manager
- [Admin scope and checklist](../00-Scope/scope.md): signed Admin boundary, deliverable map, and final
  handover checklist
- [external services and accounts](../00-Scope/external-services-and-accounts.md): current external-service
  inventory plus safe account/ownership template
- [database migrations, schema, and ERD](../00-Scope/database-migrations-schema-erd.md): complete migration catalogue,
  shared-dev schema status, data dictionary, and ERD
- `app/admin/README.md`: operator workflow, route/code map, and Admin safety boundaries
- `app/public/README.md`: Public route, data, localization, and evidence boundaries
- `api/service/README.md`: live API runtime and endpoint map

## 3. Status Labels

Use this interpretation when deciding what to read:
- `active`: default reading path for implementation work
- `supporting`: read when the current slice touches that topic
- `historical`: past gate, prototype, or evidence record; skip by default
- `archive`: retained for traceability only; skip by default

## 4. Archive Boundary

Archived material now lives under [docs/archive/README.md](archive/README.md).

By default, Codex should not read:
- past gate review notes
- prototype planning documents
- prototype evidence packs and raw stage outputs
- pre-WBS-3 owner readiness guidance

Open archive docs only when you need to verify how a past decision or prototype result was recorded.

## 5. Cleanup Notes

The docs set was simplified on `2026-04-22` and reconciled for handoff on
`2026-07-28`:
- historical gate and prototype docs moved to `docs/archive/`
- the design benchmark doc was rewritten as a short current baseline
- the development journal was reduced to recent resume context
- stale route-shell placeholders and partial API scaffold manifests were removed;
  current app manifests point directly to live implementation files
