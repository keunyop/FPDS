# FPDS Design References

Read only the contracts affected by the task. The
[development guide](../../descent/FPDS_Admin_개발_가이드.md) explains the usual
country/localization and feature workflows.

## Data, API And Security

- [Collection accuracy](collection-accuracy-policy.md): automatic acceptance
  or exclusion, optional facts and legacy cutover constraints.
- [Financial fields](financial-product-field-contract.md): exact types, units
  and evidence requirements.
- [Canonical model](domain-model-canonical-schema.md).
- [Ingestion states](workflow-state-ingestion-design.md) and
  [Run, publication and historical Review](review-run-publish-audit-state-design.md).
- [API contracts](api-interface-contracts.md).
- [Security and access](security-access-control-design.md).
- [Source governance](source-registry-refresh-and-approval-policy.md).
- [Data retention](bounded-data-retention-policy.md).

## Admin And Localization

- [Current operator manual](../../descent/FPDS_Admin_사용자_매뉴얼.md).
- [Admin information architecture](admin-information-architecture.md).
- [Design system](fpds-design-system.md) and [Stripe benchmark](fpds_design_system_stripe_benchmark.md).
- [Localization and fallback](localization-governance-and-fallback-policy.md).
- [Vendor adoption](shadcnblocks-adoption-log.md),
  [inventory](shadcnblocks-block-inventory.md) and [overrides](ui-override-register.md).

## Environment And Operations

- [Dev/prod environment](dev-prod-environment-spec.md).
- [Migration baseline](db-migration-baseline.md) and
  [current migration/schema inventory](../../00-Scope/database-migrations-schema-erd.md).
- [Private evidence storage](object-storage-evidence-bucket-baseline.md).
- [Monitoring](monitoring-error-tracking-baseline.md).

## Public, When Included In The Request

- [Product grid](product-grid-information-architecture.md),
  [metrics](insight-dashboard-metric-definition.md) and
  [visualization](product-type-visualization-principles.md).
- [Deposit comparisons](public-deposit-comparison-policy.md),
  [curated comparisons](public-curated-comparison-policy.md),
  [comparison lists](public-comparison-list-policy.md) and
  [scenario calculator](public-scenario-calculator-policy.md).
- [Verification freshness](public-verification-freshness-policy.md) and
  [bank handoff](public-bank-handoff-policy.md).
- [Comparison guides](public-comparison-guides-policy.md) and
  [blog](public-blog-policy.md).

Dated updates in retained contracts override their earlier baseline sections.
Use current source/tests to verify behavior when extending a contract; older
WBS labels are historical references, not a new development gate.
