# FPDS Bounded Data Retention Policy

Version: 1.1
Date: 2026-08-30
Status: Active Product Owner Baseline

## 1. Objective

Keep the minimum database state required for trustworthy Admin review, current
product records, collection reuse, authentication controls, and canonical
history. Operational telemetry must not grow without a bound.

This policy supersedes earlier append-only audit, LLM usage, embedding-side-
table, and dashboard-materialization requirements wherever they conflict.

## 2. Permanent Business Records

The following remain durable because they are current product truth or a direct
operator workflow record:

- bank, country, Product Type, taxonomy, and processing policy registries
- canonical products and product versions
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

`fpds_apply_admin_data_retention()` owns the executable policy:

- retain every field-linked evidence chunk, every chunk from the latest fetched
  snapshot of each source document, and chunks selected by an active run;
  remove older unlinked chunks
- recover an ingestion run still marked `started` after 12 hours as failed
- retain candidate-linked and latest Review AI model executions; remove other
  completed diagnostic executions after 14 days
- retain login attempts for 24 hours and expired/revoked sessions for 7 days
- after 14 days, reduce run and source-stage JSON to identity, correlation,
  retry, state, count, and decision fields used by the Admin run workflow

Migration 0049 registers the Admin retention function. Earlier datasets stay in place. Admin retention never reads or trims them.

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

Evidence retrieval uses the metadata-scored path.

## 5. Safety Invariants

- Never remove a chunk referenced by `field_evidence_link`.
- Never remove the latest source snapshot's chunks or chunks used by an active
  run.
- Never remove current canonical product, product version, review, or change
  history rows as an operational cleanup shortcut.
- Authentication, authorization, CSRF, login throttling, safe fetch and
  evidence privacy remain unchanged.
- A migration or manual cleanup must compare canonical product counts before and after and must verify zero orphan evidence links.

## 6. Operational Reclamation

Normal retention deletes make space reusable inside PostgreSQL. A scoped
`VACUUM (FULL, ANALYZE)` may be run only when no ingestion
is active and only against the explicitly inspected tables that were compacted.

## 7. Routine maintenance

Run the existing function explicitly during routine DB maintenance, including
after a sustained collection period. A weekly operator check prevents the
14-day diagnostic data from accumulating indefinitely; this is an operating
cadence, not a new collection scheduler or recovery feature.

Confirm the intended database and no active ingestion work. Record
active product counts and protected evidence before/after.
Rehearse in a transaction and roll back first:

```sql
BEGIN;
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '60s';
SELECT fpds_apply_admin_data_retention();
ROLLBACK;
```

Apply in a separate transaction only after the retention summary and permanent
record and evidence invariants pass, then commit. Verify zero orphan
field links and unchanged current snapshots/products. Normal deletes reclaim
reusable DB space; they do not reverse billed egress. Hot-path query/request
reduction and runtime rollout are separate from historical storage cleanup.
