# FPDS DB and Migration Baseline

Version: 1.0
Date: 2026-04-07
Status: Approved Baseline for WBS 2.3
Source Documents:
- `docs/01-planning/WBS.md`
- `docs/03-design/erd-draft.md`
- `docs/03-design/workflow-state-ingestion-design.md`
- `docs/03-design/review-run-publish-audit-state-design.md`
- `docs/03-design/domain-model-canonical-schema.md`
- `docs/03-design/retrieval-vector-starting-point.md`
- `docs/03-design/dev-prod-environment-spec.md`

---

## 1. Purpose

This document closes `WBS 2.3 DB and migration baseline setup`.

Goals:
- define the first migration strategy before a framework or ORM is chosen
- capture the minimum schema needed for prototype ingestion, reviewability, canonical history, publish tracking, usage, and audit
- make clear which database concerns are included now and which are intentionally deferred

---

## 2. Baseline Decisions

1. The baseline database is `Postgres`.
2. The migration format is plain SQL, stored in-repo, so work is not blocked on a framework choice.
3. Primary keys remain application-generated `text` ids for now.
4. Core query fields stay relational, while rapidly changing canonical and candidate payload details stay in `jsonb`.
5. `pgvector` is not part of the first migration because `dev` is allowed to run in metadata-only retrieval mode; it is introduced by a later additive migration for vector-assisted evidence retrieval.
6. Auth-vendor-specific tables, session tables, and dashboard aggregate tables are deferred to follow-on WBS items.

---

## 3. Included in the First Migration

### 3.1 Reference and Policy Tables

- `bank`
- `taxonomy_registry`
- `processing_policy_config`
- `migration_history`

### 3.2 Ingestion and Evidence Tables

- `ingestion_run`
- `source_document`
- `source_snapshot`
- `run_source_item`
- `parsed_document`
- `evidence_chunk`
- `model_execution`

### 3.3 Candidate, Review, and Canonical Tables

- `normalized_candidate`
- `review_task`
- `review_decision`
- `canonical_product`
- `product_version`
- `field_evidence_link`
- `change_event`

### 3.4 Publish, Usage, and Audit Tables

- `publish_item`
- `publish_attempt`
- `llm_usage_record`
- `audit_event`

### 3.5 Seed Data

The first migration seeds:
- Canada Big 5 bank reference rows
- Canada deposit taxonomy v1 subtypes
- initial processing policy placeholders needed by routing and validation follow-on work

---

## 4. Deferred from This Baseline

The following are intentionally not in `0001`:
- `pgvector` extension and embedding side table in `0001`; these are now owned by the later `0012_evidence_chunk_embeddings.sql` migration
- auth vendor tables and session persistence schema
- translation resources
- dashboard metric and ranking snapshot tables
- BX-PF payload detail tables
- framework-specific migration runner code

Reasons:
- `pgvector` is allowed to lag in early `dev`, and the worker must fall back to metadata-only retrieval when `0012` has not been applied or embedding rows are missing
- auth implementation is owned by `WBS 2.5`
- dashboard persistence is not needed for the prototype-ready minimum
- BX-PF exact payload detail belongs to later publish work

---

## 5. Schema Shape Rules

The first migration must honor these constraints:
- source identity is unique by `bank_code + normalized_source_url + source_type`
- review queue unit is `candidate`
- run state, review state, publish state, and change event type use constrained values from the approved design docs
- `review_decision`, `publish_attempt`, and `audit_event` are append-only history tables
- `field_evidence_link` must point to either a candidate or a product version, but not both at once
- audit rows must never require secret values

---

## 6. Migration Strategy

Current strategy:
- `db/migrations/0001_initial_baseline.sql` creates the core schema and seed data
- later migrations should stay additive whenever possible
- extension-specific or vendor-specific steps should land in later numbered files
- `db/migrations/0012_evidence_chunk_embeddings.sql` adds the first pgvector side table for `evidence_chunk` embeddings and leaves existing metadata-only retrieval compatible

Current limitation:
- the workspace does not currently include `psql`, so the migration was prepared but not executed locally

---

## 7. Hand-off to Follow-On Work

This baseline is the input for:
- `2.4` object storage and evidence path setup
- `2.5` admin auth scaffold
- `3.1` to `3.7` prototype ingestion flow implementation
- `4.x` review, trace, run, usage, and audit surfaces
- `6.x` publish tracker and reconciliation work

---

## 8. WBS Mapping

| WBS ID | Closure in This Document |
|---|---|
| `2.3` | Sections 2-7 |

---

## 9. Change History

| Date | Change |
|---|---|
| 2026-04-07 | Initial DB and migration baseline created for WBS 2.3 |
