# FPDS Docs Map

Status: Active navigation index
Last updated: 2026-07-29

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

### 2.2 Planning

- `docs/01-planning/plan.md`: execution plan
- `docs/01-planning/WBS.md`: current work breakdown and task status
- `docs/01-planning/canada-big5-source-registry.md`: active source coverage baseline for Phase 1
- `docs/01-planning/fpds-customer-demo-scenario.md`: customer demo scenario for Admin collection through Public results, including AI/usage talking points and ChatGPT image prompts

### 2.3 Requirements

- `docs/02-requirements/FPDS_Requirements_Definition_v1_5.md`: requirements baseline
- `docs/02-requirements/scope-baseline.md`: scope, non-goals, release cutline, and build-start rule

### 2.4 Design

Start from [docs/03-design/README.md](03-design/README.md).

Most commonly needed:
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
