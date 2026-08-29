# FPDS Bounded Data Retention Policy

Version: 1.0
Date: 2026-08-13
Status: Active Product Owner Baseline

## 1. Objective

Keep the minimum database state required for trustworthy Admin review, current
Public products, collection reuse, authentication controls, and canonical
history. Operational telemetry must not grow without a bound.

This policy supersedes earlier append-only audit, LLM usage, embedding-side-
table, and dashboard-materialization requirements wherever they conflict.

## 2. Permanent Business Records

The following remain durable because they are current product truth or a direct
operator workflow record:

- bank, country, Product Type, taxonomy, and processing policy registries
- canonical products, product versions, and current Public projections
- normalized candidates, review tasks, review decisions, and change events
- field evidence links and every evidence chunk referenced by one of those links
- source identity, snapshots, and parsed-document identity needed for source
  reuse and trace resolution
- publish queue/attempt state when the connector is used
- model executions that are candidate-referenced or are the latest Review AI
  verification result

`review_decision` and `change_event` are the retained operator/canonical
chronology. They are not duplicated into a generic audit-event stream.

## 3. Bounded Operational Records

`fpds_apply_data_retention()` owns the executable policy:

- retain the latest two completed aggregate snapshots per refresh scope and
  country; remove failed snapshots after 14 days
- retain every field-linked evidence chunk, every chunk from the latest fetched
  snapshot of each source document, and chunks selected by an active run;
  remove older unlinked chunks
- recover an ingestion run still marked `started` after 12 hours as failed
- retain candidate-linked and latest Review AI model executions; remove other
  completed diagnostic executions after 14 days
- retain login attempts for 24 hours and expired/revoked sessions for 7 days
- retain completed/failed aggregate requests for 14 days
- after 14 days, reduce run and source-stage JSON to identity, correlation,
  retry, state, count, and decision fields used by the Admin run workflow

The function is idempotent and is run explicitly by an operator during
maintenance.

## 4. Removed Storage

The following are no longer physical tables:

- `audit_event`
- `llm_usage_record`
- `evidence_chunk_embedding`
- `dashboard_metric_snapshot`
- `dashboard_ranking_snapshot`
- `dashboard_scatter_snapshot`

`audit_event` and `llm_usage_record` exist temporarily as empty compatibility
views with discard-only write triggers. Current writers use plain inserts that
these views absorb while guaranteeing that no rows are stored; pre-`0040`
processes that still use `ON CONFLICT` must be drained before migration. The
Admin Audit and Usage routes and pages are removed. Runtime schema discovery
must therefore treat both base tables and compatibility views as eligible
relations; checking physical tables alone is not a valid post-`0040` readiness
test.

Evidence retrieval uses the metadata-scored path. Public dashboard metrics,
rankings, and scatter data are derived at request time from the latest retained
`public_product_projection` snapshot.

## 5. Safety Invariants

- Never remove a chunk referenced by `field_evidence_link`.
- Never remove the latest source snapshot's chunks or chunks used by an active
  run.
- Never remove the latest completed Public snapshot for a country/scope.
- Never remove current canonical product, product version, review, or change
  history rows as an operational cleanup shortcut.
- Authentication, authorization, CSRF, login throttling, safe fetch, and Public
  evidence privacy remain unchanged.
- A migration or manual cleanup must compare latest Public snapshot IDs and
  product counts before and after and must verify zero orphan evidence links.

## 6. Operational Reclamation

Normal retention deletes make space reusable inside PostgreSQL. A scoped
`VACUUM (FULL, ANALYZE)` may be run only when no ingestion or aggregate refresh
is active and only against the explicitly inspected tables that were compacted.
