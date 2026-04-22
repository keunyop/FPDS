# FPDS API Service

This package is the live FastAPI runtime package for the completed admin slices through `WBS 5.15` plus the first public aggregate-backed read APIs from `WBS 5.7` and `5.8`.

Current scope:
- anonymous public aggregate-backed product and dashboard read APIs
- DB-backed admin user accounts
- DB-backed admin sessions
- login, logout, and session introspection routes
- review queue list route backed by `review_task` and `normalized_candidate`
- review-task detail read route with field-level trace, evidence metadata, model-run references, and decision history context
- run list route backed by `ingestion_run` with protected run-state diagnostics
- run detail read route with source processing summary, error summary, related review tasks, and usage summary
- change-history list route backed by `change_event` with protected canonical chronology and manual-override audit context
- audit-log list route backed by `audit_event` with protected append-only chronology, actor and target context, and review/run drilldowns
- usage dashboard route backed by `llm_usage_record` with protected totals, richer scope metadata, per-model, per-agent, per-run, trend, and anomaly drilldown aggregations
- bank registry list/detail/create/update routes backed by `bank`
- guarded bank delete support for operator-created bank profiles when only admin-managed coverage or generated-source rows exist
- source catalog list/detail/create/update routes backed by `source_registry_catalog_item`
- source catalog-selected collection launch backed by grouped `ingestion_run` creation and an API-side collection runner
- read-only source registry list/detail routes backed by generated `source_registry_item`
- approve, reject, defer, and edit-approve review mutations
- approved and edited review tasks can be reopened through `edit_approve` for follow-up operator corrections without reopening reject/defer paths
- canonical product/version creation or update side effects for approved decisions
- edit-approve manual overrides can now carry reviewer-corrected product names and sync that name into both the canonical product record and the stored normalized candidate
- review and manual-override audit events plus change-event emission
- login failure tracking and auth audit events
- bootstrap CLI for the first operator account

Current routes:
- `GET /api/public/products`
- `GET /api/public/filters`
- `GET /api/public/dashboard-summary`
- `GET /api/public/dashboard-rankings`
- `GET /api/public/dashboard-scatter`
- `POST /api/admin/auth/login`
- `POST /api/admin/auth/logout`
- `GET /api/admin/auth/session`
- `GET /api/admin/review-tasks`
- `GET /api/admin/review-tasks/:reviewTaskId`
- `GET /api/admin/runs`
- `GET /api/admin/runs/:runId`
- `POST /api/admin/runs/:runId/retry`
- `GET /api/admin/dashboard-health`
- `POST /api/admin/dashboard-health/retry`
- `GET /api/admin/change-history`
- `GET /api/admin/audit-log`
- `GET /api/admin/llm-usage`
- `GET /api/admin/sources`
- `GET /api/admin/banks`
- `POST /api/admin/banks`
- `GET /api/admin/banks/:bankCode`
- `PATCH /api/admin/banks/:bankCode`
- `DELETE /api/admin/banks/:bankCode`
- `GET /api/admin/source-catalog`
- `POST /api/admin/source-catalog`
- `GET /api/admin/source-catalog/:catalogItemId`
- `PATCH /api/admin/source-catalog/:catalogItemId`
- `POST /api/admin/source-catalog/collect`
- `GET /api/admin/sources`
- `POST /api/admin/sources`
- `GET /api/admin/sources/:sourceId`
- `PATCH /api/admin/sources/:sourceId`
- `POST /api/admin/source-collections`
- `POST /api/admin/review-tasks/:reviewTaskId/approve`
- `POST /api/admin/review-tasks/:reviewTaskId/reject`
- `POST /api/admin/review-tasks/:reviewTaskId/edit-approve`
- `POST /api/admin/review-tasks/:reviewTaskId/defer`
- `GET /healthz`

## Local Run

Apply the DB baseline in order:

```powershell
psql $env:FPDS_DATABASE_URL -f db/migrations/0001_initial_baseline.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0002_admin_auth.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0003_aggregate_refresh.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0004_source_registry_admin.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0005_source_registry_unique_scope_fix.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0006_bank_catalog_management.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0007_dynamic_product_type_onboarding.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0008_discovery_metadata_persistence.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0009_backfill_review_edit_approved_candidate_product_name.sql
psql $env:FPDS_DATABASE_URL -f db/migrations/0010_aggregate_refresh_queue.sql
```

Create the first operator account:

```powershell
cd api/service
uv run python -m api_service.bootstrap_admin_user --env-file ..\..\.env.dev --email admin@example.com --display-name "Admin Operator" --role admin
```

Run the API:

```powershell
cd ..\..
$env:FPDS_ENV_FILE=".env.dev"
uv run --directory api/service uvicorn api_service.main:app --reload --host localhost --port 4000
```

## Notes

- Public read routes now use the latest successful `aggregate_refresh_run` snapshot and read from `public_product_projection`.
- Approve and edit-approve now queue `aggregate_refresh_request` rows inside the same review-decision transaction, then launch a background aggregate refresh runner after commit so public serving can stay on the latest successful snapshot without blocking review writes.
- `/api/admin/dashboard-health` now exposes aggregate freshness, queue state, serving fallback, stale detection, and manual retry availability for the Canada public aggregate domain.
- Public dashboard summary, ranking, and scatter responses currently derive request-time filtered results from the latest successful projection snapshot so they can share the same filter vocabulary as the product grid without requiring precomputed per-filter dashboard scopes.
- The settings loader now reads both `FPDS_ALLOWED_PUBLIC_ORIGINS` and `FPDS_ALLOWED_ADMIN_ORIGINS`, and the live CORS middleware allows the combined origin set because the same FastAPI service now fronts both public and admin browser surfaces.
- Passwords are hashed with Python's built-in `scrypt`.
- The session cookie is still `fpds_admin_session` per the shared auth contract.
- Login throttling is DB-backed with per-account lockout and recent-attempt checks.
- The review queue route defaults to active `queued` and `deferred` tasks and supports search, filters, pagination, and sort against the persisted prototype review-task data.
- Review detail now returns candidate fields, field-selectable trace groups, enriched evidence metadata, model execution references, current canonical continuity match, and append-only decision history for `/admin/reviews/:reviewTaskId`.
- Run status now returns filtered run list rows plus run detail payloads for `/admin/runs` and `/admin/runs/:runId`, including run alias fields, source processing summary, derived stage summary, error events, related review tasks, and usage aggregation.
- Failed run detail now exposes retry availability for supported collection runs, and `POST /api/admin/runs/:runId/retry` requeues failed `source_catalog_collection` or `source_collection` attempts while linking the old run as `retried` and the new run as its next attempt.
- Change history now returns filtered canonical change events for `/admin/changes`, including changed-field summaries, linked review/run context, and manual-override audit context when available.
- Audit log now returns filtered append-only audit events for `/admin/audit`, including actor snapshots, target context, request metadata, and review/run drilldowns where those entities exist.
- LLM usage now returns dashboard-v1 aggregates for `/api/admin/llm-usage`, including time-range, provider, stage, and search filters, scope coverage metadata, share percentages, daily trend deltas, and richer anomaly drilldown candidates.
- Bank, product type, and source catalog management now treat the DB as the operational source of truth immediately; if those tables are empty, the admin/runtime surfaces now stay empty until an operator or explicit import/seed step repopulates them.
- Bank creation now accepts optional initial coverage product types and creates the related `source_registry_catalog_item` rows in the same admin write flow so the bank modal can start with coverage already attached.
- Bank create and update now accept homepage URLs without an explicit scheme by normalizing them to `https://...`, while still rejecting invalid non-http(s) values with a validation error instead of a server crash.
- Bank delete now removes only the bank profile plus admin-managed coverage and generated-source rows; if collected source documents or downstream candidate/product history already exist, the API blocks deletion with a conflict response so operational history is not orphaned.
- Existing bank homepage values are no longer auto-repaired from committed seed data during runtime reads or admin writes; reset and replay flows now preserve intentionally empty operator-managed state.
- Source catalog collection now treats a catalog item as `bank homepage + product coverage`, regenerates `source_registry_item` rows from the bank homepage on each collect, and queues the homepage-discovery plus materialization work on a background API-side runner before the deeper worker stages continue.
- Source catalog collect now creates `ingestion_run` rows immediately and returns a fast queued response so `/admin/banks` and compatibility source-catalog actions no longer wait on homepage discovery or candidate-page validation before responding.
- Homepage-first collection still preserves the existing active detail scope when no replacement detail rows are found, and the queued background runner now reuses that preserved active detail scope for collection instead of incorrectly closing the run as a no-detail partial completion.
- Bank-wide source-catalog collect now launches one background runner process per bank/product run instead of one sequential batch process for the whole bank list, so a hung product-type collect no longer leaves later runs stuck in `Started`.
- Downstream worker stages launched by `source_collection_runner` now have a configurable `FPDS_SOURCE_COLLECTION_STAGE_TIMEOUT_SECONDS` watchdog. If a worker stage hangs past that limit, the run is closed as `failed` with a timeout summary instead of remaining indefinitely `started`.
- Snapshot capture now supports a targeted headless-browser PDF fallback for domains listed in `FPDS_SOURCE_BROWSER_FALLBACK_DOMAINS`. This is intended for banks such as BMO where non-browser HTTPS fetches can be reset or timed out even though the page still renders in a normal browser. The stored snapshot content type becomes `application/pdf`, which the downstream parse stage already supports, while HTML-only fetch paths still reject non-HTML fallback payloads so homepage discovery does not accidentally score a PDF error page as HTML.
- Homepage-first discovery now uses bounded hybrid scoring over the candidate set instead of AI-only fallback after heuristic failure: deterministic candidate generation still happens first, but the API layer now runs AI parallel candidate scoring when configured, uses stronger product-type-description terms in heuristic scoring, validates tentative detail pages with page-level evidence scoring, and persists generated-source `discovery_metadata` for explainability.
- The bank list payload now includes its attached coverage items so `/admin/banks` can drive multi-bank bulk collect without reopening each bank detail modal first.
- Homepage-first source generation can still use committed fallback discovery hints from the repo baselines when link extraction comes up empty, but those hints no longer write rows back into the live DB automatically.
- Source collection plans now carry generated-source discovery metadata into the worker registry payload so the runtime `source_document.source_metadata` stays aligned with the source registry explanation fields.
- The background source-collection runner now launches worker stages through the repo-root `uv` project environment instead of the API service virtualenv, so worker-only dependencies such as `beautifulsoup4` and `pypdf` resolve correctly during collection.
- Discovery, registry refresh, and snapshot capture now merge the active registry's `allowed_domains` into the env allowlist, which keeps bank-scoped safe fetch behavior aligned with the selected source registry during Big 5 collection.
- Snapshot capture now runs source fetches concurrently inside the same run, and the shared fetch timeout baseline moved to `90` seconds to better tolerate slower Big 5 pages without stretching bank-wide collection wall-clock time linearly per source.
- Downstream collection stages now stop when snapshot capture produces no usable sources, and they only process the subset of sources whose snapshots were actually stored or reused so the final run error reflects the real failing stage more accurately.
- `POST /api/admin/sources` and `PATCH /api/admin/sources/:sourceId` are intentionally kept as read-only error responses in the MVP so the live operator flow stays centered on `/api/admin/banks` and `/api/admin/source-catalog`.
- Dynamic product-type onboarding is now live for the admin registry and collection pipeline: `/api/admin/product-types` now supports list/create/detail/update/delete for operator-defined types, delete is blocked when bank coverage or generated sources still reference the type, bank coverage writes validate against the registry, source collection plans carry product-type definitions into the worker stages, and non-canonical types use the generic AI extraction or normalization fallback path with safe manual-review routing.
- The current source-collection MVP keeps candidate-producing scope centered on selected `detail` sources and only auto-includes the existing TD savings supporting sources already required by the live normalization path.
- Review detail reads now emit `evidence_trace_viewed` audit events so sensitive trace access is queryable alongside decision and auth history.
- Approve and edit-approve now perform the first runtime canonical upsert/change-event side effects using a conservative prototype continuity match of country, bank, product family, product type, subtype, and product name.
- Review write routes now require the stored session plus matching `X-CSRF-Token` header.
- Later admin write routes can keep reusing the same session and CSRF token model.
- The settings loader now resolves a relative `FPDS_ENV_FILE` from either the current working directory or the repo root, so `.env.dev` works both from the workspace root and from inside `api/service`.
- `api/service/tests/test_ops_scenario_qa.py` now gives the service layer a Gate C-focused operator scenario test that verifies review decision side effects, change history linkage, audit continuity, and run-detail drilldown context together.
