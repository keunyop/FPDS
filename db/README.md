# FPDS Database Baseline

This directory holds the database and migration baseline for WBS `2.3`.

Current decisions:
- PostgreSQL is the baseline database.
- Migrations are SQL-first so the repo is not blocked on a framework or ORM choice.
- Primary keys use application-generated `text` ids for now, which avoids taking a UUID extension dependency before the runtime is chosen.
- Flexible candidate and canonical field payloads live in `jsonb` until the implementation needs stricter column-level expansion.
- `pgvector` is intentionally deferred from the first migration. `0012_evidence_chunk_embeddings.sql` adds the first evidence-chunk embedding side table, while metadata-only retrieval fallback remains allowed when the migration or rows are unavailable in early `dev`.
- Runtime admin and API reads no longer auto-reseed `bank`, `product_type_registry`, `source_registry_catalog_item`, or `source_registry_item` from committed JSON seed baselines. Empty tables now remain empty until an explicit operator write, import step, or full migration replay repopulates them.

Files:
- `migrations/0001_initial_baseline.sql`: core schema and seed data
- `migrations/0002_admin_auth.sql`: DB-backed admin user, session, and login-attempt tables for `WBS 4.1`
- `migrations/0003_aggregate_refresh.sql`: aggregate snapshot execution history plus public projection tables
- `migrations/0009_backfill_review_edit_approved_candidate_product_name.sql`: backfills `normalized_candidate.product_name` plus `candidate_payload.product_name` from the latest stored `edit_approve` product-name override
- `migrations/0010_aggregate_refresh_queue.sql`: aggregate refresh request queue for auto-enqueued review approvals and manual retry
- `migrations/0011_admin_signup_requests.sql`: login-id-first admin auth updates plus approval-gated signup requests
- `migrations/0012_evidence_chunk_embeddings.sql`: pgvector-backed `evidence_chunk_embedding` side table for vector-assisted evidence retrieval
- `migrations/0013_operator_managed_product_types.sql`: removes the historical product-type classification flag so every product type is an operator-managed DB row
- `migrations/0014_canonical_deposit_taxonomy_backfill.sql`: restores canonical chequing, savings, and GIC subtype taxonomy rows when operator-managed product types have been reset or recreated
- `migrations/0015_phase1_review_confidence_policy.sql`: lowers the Phase 1 auto-approve confidence policy to `0.82` while preserving validation-error and force-review gates

How to apply when a database is available:

```powershell
psql $env:FPDS_DATABASE_URL -f db/migrations/0001_initial_baseline.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0002_admin_auth.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0003_aggregate_refresh.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0009_backfill_review_edit_approved_candidate_product_name.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0010_aggregate_refresh_queue.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0011_admin_signup_requests.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0012_evidence_chunk_embeddings.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0013_operator_managed_product_types.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0014_canonical_deposit_taxonomy_backfill.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0015_phase1_review_confidence_policy.sql
```

Notes:
- `psql` is available in the prepared local toolchain, but the migrations still need a reachable Postgres target.
- Use the connection target from `.env.dev.example` or `.env.prod.example`.
- Keep future migrations additive and append-only where possible.
- Put extension-specific or vendor-specific migrations in later numbered files.
- Historical fresh-DB bootstrap inserts still exist in `0001_initial_baseline.sql` for `bank` only. `product_type_registry` is schema-only in the current migration chain; chequing, savings, GIC, and any later product types must be registered through admin/operator DB writes.
