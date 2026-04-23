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
