# FPDS Archive

Status: Historical reference only
Last updated: 2026-04-22

This folder keeps documents that are intentionally out of the default development path.

Default rule:
- Do not read anything here during normal implementation work.
- Only open archived docs when you need to verify an old prototype result, gate decision, or previous planning baseline.

## Archived Areas

- `00-governance/`: closed gate notes, pre-WBS-3 readiness guidance, and completed QA evidence
- `01-planning/`: prototype-only planning docs and prototype evidence artifacts

## Why These Files Moved

These files were kept for traceability, but they no longer need to shape day-to-day implementation:
- Gate A, B, and C decisions are already reflected in active status docs.
- Prototype planning docs are no longer current after WBS 3 completion and WBS 5 start.
- Raw prototype evidence JSON is historical evidence, not active guidance.

## Codex Rule

If you are resuming work, go back to:
1. `README.md`
2. `docs/README.md`
3. `docs/00-governance/development-journal.md`

Only then open archive files if a live doc explicitly requires historical verification.

*** Add File: docs/03-design/README.md
# FPDS Design Docs

Status: Active design index
Last updated: 2026-04-22

Use this file to avoid opening every design doc.

## Core Runtime Design

- `domain-model-canonical-schema.md`: canonical fields, validation, and taxonomy
- `workflow-state-ingestion-design.md`: ingestion workflow stages and state model
- `review-run-publish-audit-state-design.md`: review, run, publish, and audit lifecycle
- `api-interface-contracts.md`: public, admin, internal, and external interface contracts
- `security-access-control-design.md`: auth, RBAC, CSRF, SSRF, and browser security baseline
- `source-registry-refresh-and-approval-policy.md`: source registry governance and admin update rules

## Infrastructure Baselines

- `dev-prod-environment-spec.md`: active env contract
- `db-migration-baseline.md`: DB baseline
- `object-storage-evidence-bucket-baseline.md`: object storage baseline
- `monitoring-error-tracking-baseline.md`: observability contract
- `localization-governance-and-fallback-policy.md`: i18n ownership and fallback

## Public Experience

- `product-grid-information-architecture.md`
- `insight-dashboard-metric-definition.md`
- `product-type-visualization-principles.md`

## Admin Experience

- `admin-information-architecture.md`
- `fpds-design-system.md`
- `fpds_design_system_stripe_benchmark.md`
- `shadcnblocks-adoption-log.md`
- `shadcnblocks-block-inventory.md`
- `ui-override-register.md`

## Historical Or Less Common Design References

Open only when the current slice needs them:
- `environment-separation-strategy.md`
- `source-snapshot-evidence-storage-strategy.md`
- `retrieval-vector-starting-point.md`
- `aggregate-cache-refresh-strategy.md`
- `system-context-diagram.md`
- `erd-draft.md`
- `homepage-discovery-scoring-enhancement.md`

