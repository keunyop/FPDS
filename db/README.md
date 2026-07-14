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
- `migrations/0016_auto_promotion_aggregate_trigger.sql`: allows aggregate refresh requests triggered by audited candidate auto-promotion
- `migrations/0017_canonical_identity_alias_repair.sql`: repairs common bank and product-type identity aliases such as RBC/TD/SCOTIA and GIC
- `migrations/0018_canonical_source_document_identity_repair.sql`: realigns `source_document_id` values with canonical bank/url/type identity after alias repair
- `migrations/0019_canada_lending_product_types.sql`: registers the Canada retail lending Product Type baseline (`credit-card`, `mortgage`, `personal-loan`, `line-of-credit`) plus generic `other` lending taxonomy fallback rows
- `migrations/0020_canada_recognized_banks_full_coverage.sql`: adds bank logo metadata, registers recognized Canadian retail/direct banking brands, and creates active source-catalog coverage for every active Canadian bank/Product Type pair
- `migrations/0021_vancity_credit_union_full_coverage.sql`: registers Vancity per Product Owner request and creates active source-catalog coverage for every active Product Type
- `migrations/0022_bank_logo_asset_refresh.sql`: replaces recognized-bank favicon defaults with verified official logo assets while preserving operator-supplied custom logo URLs

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
psql $env:FPDS_DATABASE_URL -f db/migrations/0016_auto_promotion_aggregate_trigger.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0017_canonical_identity_alias_repair.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0018_canonical_source_document_identity_repair.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0019_canada_lending_product_types.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0020_canada_recognized_banks_full_coverage.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0021_vancity_credit_union_full_coverage.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0022_bank_logo_asset_refresh.sql
```

Notes:
- `psql` is available in the prepared local toolchain, but the migrations still need a reachable Postgres target.
- Use the connection target from `.env.dev.example` or `.env.prod.example`.
- Keep future migrations additive and append-only where possible.
- Put extension-specific or vendor-specific migrations in later numbered files.
- Historical fresh-DB bootstrap inserts still exist in `0001_initial_baseline.sql` for `bank` only. `product_type_registry` is schema-only until later additive migrations; `0019_canada_lending_product_types.sql` registers the approved lending baseline, `0020_canada_recognized_banks_full_coverage.sql` expands the Canadian bank/logo baseline and source-catalog coverage, `0021_vancity_credit_union_full_coverage.sql` adds Vancity to that coverage set, and `0022_bank_logo_asset_refresh.sql` upgrades eligible favicon defaults to verified official logo assets. Future product types should still be registered through admin/operator DB writes or explicit approved migrations.
