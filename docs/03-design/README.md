# FPDS Design Docs

Status: Active design index
Last updated: 2026-09-12

Use this file to avoid opening every design doc.

## Core Runtime Design

- `domain-model-canonical-schema.md`: canonical fields, validation, and taxonomy
- `financial-product-field-contract.md`: cross-bank field types, units, field notes, evidence merge, and collection verification
- `workflow-state-ingestion-design.md`: ingestion workflow stages and state model
- `review-run-publish-audit-state-design.md`: review, run, publish, and audit lifecycle
- `api-interface-contracts.md`: public, admin, internal, and external interface contracts
- `security-access-control-design.md`: auth, RBAC, CSRF, SSRF, and browser security baseline
- `source-registry-refresh-and-approval-policy.md`: source registry governance and admin update rules
- `bounded-data-retention-policy.md`: active keep/expire/remove rules for
  evidence, run metadata, Public snapshots, model executions, auth records,
  and removed operational log tables

## Infrastructure Baselines

- `dev-prod-environment-spec.md`: active env contract
- `db-migration-baseline.md`: DB baseline
- `object-storage-evidence-bucket-baseline.md`: object storage baseline
- `monitoring-error-tracking-baseline.md`: observability contract
- `localization-governance-and-fallback-policy.md`: i18n ownership and fallback

## Public Experience

- [Persistent comparison lists](public-comparison-list-policy.md): country-scoped selection, noindex sharing, device save/delete and current-data rechecks

- [Curated Canadian comparisons](public-curated-comparison-policy.md): purpose pages, shared launch gate, Home fallbacks and bounded search discovery

- [Deposit comparison and estimates](public-deposit-comparison-policy.md): compatible currency/basis/terms, scenario inputs and unavailability

- [Product verification freshness](public-verification-freshness-policy.md): elapsed review/expiry policy, separate snapshot timing and manual operator report

- `product-grid-information-architecture.md`
- `insight-dashboard-metric-definition.md`
- `product-type-visualization-principles.md`

## Admin Experience

- [FPDS Admin purpose and complete feature guide (Korean)](fpds-admin-purpose-and-features.md): current implementation inventory verified against source on 2026-09-12

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
