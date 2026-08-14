# FPDS Database Baseline

This directory holds the database and migration baseline for WBS `2.3`.

Current decisions:
- PostgreSQL is the baseline database.
- Migrations are SQL-first so the repo is not blocked on a framework or ORM choice.
- Primary keys use application-generated `text` ids for now, which avoids taking a UUID extension dependency before the runtime is chosen.
- Opaque technical IDs stay stable across country moves and imports. Country is
  part of bank/source business uniqueness and country-owned lookup indexes,
  rather than being concatenated into every technical primary key.
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
- `migrations/0023_versioned_parsed_documents.sql`: permits one immutable parsed artifact per snapshot and parser version so parser upgrades can reparse without overwriting earlier evidence lineage
- `migrations/0024_deposit_field_contract_defaults.sql`: aligns deposit product-type expected fields with the executable cross-bank field contract and records the registry change in history
- `migrations/0025_country_scoped_admin.sql`: adds the enabled-country registry,
  country-bound Admin sessions and ingestion runs, country/bank composite
  integrity, country-aware source uniqueness, and country-qualified product
  lookup indexes
- `migrations/0026_country_registry_management.sql`: adds the stored English
  country-name fallback and country registry lookup index used by the
  admin-only prepared-country activation workflow
- `migrations/0027_standalone_ai_operations.sql`: permits operational
  `model_execution` and `llm_usage_record` rows without an ingestion run so
  country-scoped AI registry actions can retain execution and cost lineage
- `migrations/0028_source_catalog_coverage_evidence.sql`: preserves the
  official Product Type coverage URL that justified each catalog row so
  collection can start from that verified route
- `migrations/0029_collection_ai_autopilot_policy.sql`: enables bounded
  collection-time AI review remediation and the official-grounding thresholds
  that allow dynamic/lending candidates to use normal policy auto-approval
- `migrations/0030_collection_approval_field_policy.sql`: replaces the
  all-requested-field approval denominator with identity plus populated or
  blocking decision fields; empty optional fields are explicit omissions
- `migrations/0031_catalog_coverage_route_evidence.sql`: adds private structured
  evidence for verified product-specific consumer-brand coverage domains and
  explicit not-currently-offered catalog outcomes
- `migrations/0032_comparison_grade_collection_quality.sql`: supersedes the
  populated-only lending approval denominator, adds rate-summary coverage to
  lending field registries, and activates comparison-grade AI policy notes
- `migrations/0033_essential_field_low_touch_publication.sql`: narrows current
  Deposit and Lending registry rows to type-specific comparison essentials,
  requires complete essential grounding, and makes partial-source/confidence
  warnings non-blocking by themselves
- `migrations/0034_country_product_market_profiles.sql`: backfills active US
  source rows to the versioned US comparison contract, records market-profile
  lineage in discovery metadata, reclassifies governing documents as
  supporting evidence, and removes known action/calculator detail rows from
  active collection scope
- `migrations/0035_collection_publication_automation.sql`: adds the singleton
  recurring collection/recovery policy used by the API scheduler
- `migrations/0036_us_pricing_evidence_companions.sql`: moves active US card
  sources to the current market profile and requests the range-preserving
  `purchase_interest_rate_summary` alongside annual fee and purchase rate
- `migrations/0037_us_pricing_companion_scope_cleanup.sql`: inactivates generic
  online-banking service agreements mistakenly linked as pricing companions
  while retaining their source history
- `migrations/0038_us_cross_product_support_cleanup.sql`: inactivates legacy US
  credit-card supporting rows that actually point to auto/vehicle-loan pages;
  the runtime also excludes any future active supporting row with a conflicting
  Product Type fingerprint
- `migrations/0039_us_credit_card_apr_range_contract.sql`: makes the qualified
  Purchase APR summary the preferred US credit-card rate requirement, leaving
  an exact fixed scalar rate as a bounded alternative rather than reducing a
  disclosed range to its lower endpoint

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
psql $env:FPDS_DATABASE_URL -f db/migrations/0023_versioned_parsed_documents.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0024_deposit_field_contract_defaults.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0025_country_scoped_admin.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0026_country_registry_management.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0027_standalone_ai_operations.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0028_source_catalog_coverage_evidence.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0029_collection_ai_autopilot_policy.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0030_collection_approval_field_policy.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0031_catalog_coverage_route_evidence.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0032_comparison_grade_collection_quality.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0033_essential_field_low_touch_publication.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0034_country_product_market_profiles.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0035_collection_publication_automation.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0036_us_pricing_evidence_companions.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0037_us_pricing_companion_scope_cleanup.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0038_us_cross_product_support_cleanup.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0039_us_credit_card_apr_range_contract.sql
```

Notes:
- `psql` is available in the prepared local toolchain, but the migrations still need a reachable Postgres target.
- Use the connection target from `.env.dev.example` or `.env.prod.example`.
- Keep future migrations additive and append-only where possible.
- Put extension-specific or vendor-specific migrations in later numbered files.
- Historical fresh-DB bootstrap inserts still exist in `0001_initial_baseline.sql` for `bank` only. `product_type_registry` is schema-only until later additive migrations; `0019_canada_lending_product_types.sql` registers the approved lending baseline, `0020_canada_recognized_banks_full_coverage.sql` expands the Canadian bank/logo baseline and source-catalog coverage, `0021_vancity_credit_union_full_coverage.sql` adds Vancity to that coverage set, and `0022_bank_logo_asset_refresh.sql` upgrades eligible favicon defaults to verified official logo assets. Future product types should still be registered through admin/operator DB writes or explicit approved migrations.
- `country_registry` is the operational allowlist for Admin login. Adding a new
  country is an explicit enablement step and does not by itself authorize
  collection or release for that market.
- Country removal is an `inactive` status transition rather than row deletion,
  preserving country-scoped foreign keys and historical records.
- Apply `0027` before enabling AI bank onboarding. Standalone operational AI
  rows keep `run_id=NULL`; their country and operation lineage lives in
  execution/usage metadata, while ingestion-backed executions remain linked to
  their run as before.
- Apply `0028` before relying on AI onboarding coverage evidence as the
  collection entry route. Existing catalog rows remain valid with a null
  coverage URL and continue to use bounded homepage discovery.
- Apply `0029` to persist the Product Owner-approved collection AI autopilot,
  80% official-grounding thresholds, and per-run cost bound. Code defaults to
  the same enabled policy so deployment does not silently revert to blanket
  manual review if the migration and runtime roll out together.
- Apply `0030` to keep the 80% safety threshold while changing its denominator
  to approval-relevant fields. Identity and an official source remain
  mandatory, and ambiguous product boundaries, partial source failures, and
  invalid taxonomy remain hard blockers.
- Apply `0032` to require rate/price plus the product-type-specific amount or
  term facts independently of the 80% score. An APR range or conditional rate
  formula remains source text in `interest_rate_summary`; it is not coerced to
  a misleading scalar.
- Apply `0033` to make the smaller essential-field contract authoritative for
  new collection, Review, approval, and Public projection. It supersedes the
  active 80% policies with 100% coverage of the smaller set and removes
  `partial_source_failure` from force-review policy without weakening identity,
  taxonomy, type/range, conflict, or ambiguity blockers.
- Apply `0034` before the next US recollection so existing registry rows request
  the US market-profile essentials and retain their profile key/version. The
  migration changes source roles/status only for deterministic US legal,
  enrollment, service, and calculator non-product patterns; canonical product
  status still changes only through the audited remediation workflow.
