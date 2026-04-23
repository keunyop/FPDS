# FPDS Database Baseline

This directory holds the database and migration baseline for WBS `2.3`.

Current decisions:
- PostgreSQL is the baseline database.
- Migrations are SQL-first so the repo is not blocked on a framework or ORM choice.
- Primary keys use application-generated `text` ids for now, which avoids taking a UUID extension dependency before the runtime is chosen.
- Flexible candidate and canonical field payloads live in `jsonb` until the implementation needs stricter column-level expansion.
- `pgvector` is intentionally deferred from the first migration. Metadata-only retrieval fallback is allowed in early `dev`.
- Runtime admin and API reads no longer auto-reseed `bank`, `product_type_registry`, `source_registry_catalog_item`, or `source_registry_item` from committed JSON seed baselines. Empty tables now remain empty until an explicit operator write, import step, or full migration replay repopulates them.

Files:
- `migrations/0001_initial_baseline.sql`: core schema and seed data
- `migrations/0002_admin_auth.sql`: DB-backed admin user, session, and login-attempt tables for `WBS 4.1`
- `migrations/0003_aggregate_refresh.sql`: aggregate snapshot execution history plus public projection tables
- `migrations/0009_backfill_review_edit_approved_candidate_product_name.sql`: backfills `normalized_candidate.product_name` plus `candidate_payload.product_name` from the latest stored `edit_approve` product-name override
- `migrations/0010_aggregate_refresh_queue.sql`: aggregate refresh request queue for auto-enqueued review approvals and manual retry
- `migrations/0011_admin_signup_requests.sql`: login-id-first admin auth updates plus approval-gated signup requests

How to apply when a database is available:

```powershell
psql $env:FPDS_DATABASE_URL -f db/migrations/0001_initial_baseline.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0002_admin_auth.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0003_aggregate_refresh.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0009_backfill_review_edit_approved_candidate_product_name.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0010_aggregate_refresh_queue.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0011_admin_signup_requests.sql
```

Notes:
- `psql` is available in the prepared local toolchain, but the migrations still need a reachable Postgres target.
- Use the connection target from `.env.dev.example` or `.env.prod.example`.
- Keep future migrations additive and append-only where possible.
- Put extension-specific or vendor-specific migrations in later numbered files.
- Historical fresh-DB bootstrap inserts still exist in `0001_initial_baseline.sql` for `bank` and in `0007_dynamic_product_type_onboarding.sql` for `product_type_registry`. Those are applied only when migrations are replayed on a new database; they are no longer mirrored by runtime reseed logic.
